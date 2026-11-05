import time
import threading
import asyncio
from collections import deque
from asyncua import Client
from typing import Dict, Optional

class OPCUAClient:
    """
    A client to connect to and interact with an OPC UA server using a 
    non-blocking background async event loop and a bounded FIFO message buffer with TTL.
    """
    def __init__(self, endpoint: str, logger):
        self.endpoint = endpoint
        self.logger = logger
        self.is_connected = False

        self.namespace_uri = "http://matheus.edu/UAV-AAS/"
        self.ns_idx = 2 
        
        # Thread-safe boundary structures
        self.buffer = deque(maxlen=200)
        self.buffer_lock = threading.Lock()
        
        self._node_cache: Dict[str, object] = {}
        # Reduced TTL to aggressively drop stale telemetry when network backs up
        self.MAX_AGE_SECONDS = 1.5  
        
        self._write_count = 0
        self._failed_writes = 0
        self.retry_interval = 0.1

        # Asyncio bridging components
        self.loop = asyncio.new_event_loop()
        self.data_available = None  # Will be initialized inside the async loop
        self.client = None
        
        # Start the dedicated event loop in a background thread
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def _run_loop(self):
        """Sets up and runs the asyncio event loop in the background thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self._async_worker())

    async def _async_worker(self):
        """Asynchronous background worker to handle network I/O without blocking."""
        self.client = Client(url=self.endpoint, timeout=1.0)
        self.data_available = asyncio.Event()

        while True:
            try:
                # Handle connection state
                if not self.is_connected:
                    try:
                        # Clean up old client state and kill broken watchdogs
                        if self.client is not None:
                            try:
                                await self.client.disconnect()
                            except Exception:
                                pass
                        
                        # Instantiate a completely new client for a fresh session
                        self.client = Client(url=self.endpoint, timeout=1.0)
                        await self.client.connect()
                        self.ns_idx = await self.client.get_namespace_index(self.namespace_uri)
                        self.is_connected = True
                        self.logger.info(f"Connected to OPC UA server at {self.endpoint}")
                    except Exception as e:
                        self.logger.warning(f"Reconnection failed: {e}")
                        await asyncio.sleep(self.retry_interval)
                        continue
                
                # Wait for data or timeout
                try:
                    await asyncio.wait_for(self.data_available.wait(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass
                
                # Clear the event BEFORE draining the buffer to eliminate the race condition
                self.data_available.clear()
                
                batch_items = []
                with self.buffer_lock:
                    while self.buffer:
                        batch_items.append(self.buffer.popleft())
                
                if not batch_items:
                    continue

                # 1. Deduplicate & TTL Check (Synchronous math)
                latest_updates = {}
                dropped_traces = []
                current_time = time.time()
                
                for item in batch_items:
                    trace = item['trace']
                    if (current_time - trace['t_recv']) <= self.MAX_AGE_SECONDS:
                        node_id = item['node_id']
                        if node_id in latest_updates:
                            dropped_traces.append((latest_updates[node_id]['trace'], "DROPPED_DEDUP"))
                        latest_updates[node_id] = item
                    else:
                        dropped_traces.append((trace, "DROPPED_TTL"))

                for trace, reason in dropped_traces:
                    self.logger.info(f"[LATENCY_TRACE] id={trace['msg_id']}|node={trace['node_id']}|status={reason}|t0={trace['t_recv']:.4f}|t1={trace['t_proc']:.4f}|t2={trace['t_buf']:.4f}|t3=0|t4=0")

                if not latest_updates:
                    continue

                # 2. Prepare the batch
                nodes_to_write = []
                values_to_write = []
                valid_items = []
                
                for node_id, item in latest_updates.items():
                    node = self._get_cached_node(node_id)
                    if node is not None:
                        nodes_to_write.append(node)
                        values_to_write.append(item['value'])
                        valid_items.append(item)
                    else:
                        self._failed_writes += 1
                        trace = item['trace']
                        self.logger.info(f"[LATENCY_TRACE] id={trace['msg_id']}|node={trace['node_id']}|status=FAILED_NO_NODE|t0={trace['t_recv']:.4f}|t1={trace['t_proc']:.4f}|t2={trace['t_buf']:.4f}|t3=0|t4=0")

                # 3. Network Write (Asynchronous)
                if nodes_to_write:
                    # [T3] Start sending
                    t_send_start = time.time()
                    
                    # asyncua bulk write implementation
                    await self.client.write_values(nodes_to_write, values_to_write)
                    
                    # [T4] Finish sending
                    t_send_end = time.time()
                    
                    # Log successful writes
                    for item in valid_items:
                        trace = item['trace']
                        self.logger.info(f"[LATENCY_TRACE] id={trace['msg_id']}|node={trace['node_id']}|status=SUCCESS|t0={trace['t_recv']:.4f}|t1={trace['t_proc']:.4f}|t2={trace['t_buf']:.4f}|t3={t_send_start:.4f}|t4={t_send_end:.4f}")

            except Exception as e:
                # [T4] Failed on network level
                t_send_end = time.time()
                error_msg = str(e)
                status = "FAILED_TYPE" if "BadTypeMismatch" in error_msg else "FAILED_NET"
                
                for item in valid_items:
                    trace = item['trace']
                    self.logger.error(f"[LATENCY_TRACE] id={trace['msg_id']}|node={trace['node_id']}|status={status}|t0={trace['t_recv']:.4f}|t1={trace['t_proc']:.4f}|t2={trace['t_buf']:.4f}|t3={t_send_start:.4f}|t4={t_send_end:.4f}")
                
                if status == "FAILED_TYPE":
                    self._failed_writes += len(nodes_to_write)
                else:
                    self.is_connected = False                    
                    self._node_cache.clear()
                    if self.client:
                        try:
                            await self.client.disconnect()
                        except Exception:
                            pass
                            
                    await asyncio.sleep(self.retry_interval)

    def _get_cached_node(self, node_id: str) -> Optional[object]:
        """Fetch and cache OPC UA node handles locally."""
        full_node_id = f"ns={self.ns_idx};{node_id}"
        if full_node_id in self._node_cache:
            return self._node_cache[full_node_id]
            
        try:
            # get_node is synchronous in asyncua as it only instantiates the object locally
            if self.client:
                node = self.client.get_node(full_node_id)
                self._node_cache[full_node_id] = node
                return node
            return None
        except Exception as e:
            self.logger.error(f"Failed to get node {full_node_id}: {e}")
            return None

    def write_value(self, node_id: str, value: any, trace: dict):
        """
        Synchronous non-blocking write. Adds data to the queue and wakes the async loop thread-safely.
        """
        self._write_count += 1
        
        # [T2] Added to buffer
        trace['t_buf'] = time.time() 
        
        with self.buffer_lock:
            self.buffer.append({'node_id': node_id, 'value': value, 'trace': trace})
            
        # Thread-safely trigger the asyncio event from the ROS2 thread
        if self.data_available is not None:
            self.loop.call_soon_threadsafe(self.data_available.set)

    def disconnect(self):
        """Disconnects the client and stops the background state gracefully."""
        self.is_connected = False
        
        async def _do_disconnect():
            if self.client:
                try:
                    await self.client.disconnect()
                    self.logger.info("Disconnected from OPC UA server")
                except Exception:
                    pass
                    
        if self.loop.is_running():
            asyncio.run_coroutine_threadsafe(_do_disconnect(), self.loop)