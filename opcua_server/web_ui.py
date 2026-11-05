import json
import os
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Flask, render_template_string, send_from_directory
import logging

log = logging.getLogger(__name__)


class DataManager:
    """Manages OPC UA variable data with statistics and history for the web UI."""
    
    def __init__(self):
        self.properties: Dict[str, Dict[str, Any]] = {}
        self.total_events = 0
        self.start_time = time.time()
        self.last_update = None
        self._lock = threading.Lock()
    
    def update_property(self, variable: str, value: Any, node_id: str, timestamp: float):
        """Update property data with new value and maintain statistics."""
        with self._lock:
            if variable not in self.properties:
                self.properties[variable] = {
                    'name': variable,
                    'node_id': node_id,
                    'value': None,
                    'last_value': None,
                    'event_count': 0,
                    'first_seen': timestamp,
                    'last_update': None,
                    'history': []
                }
            
            prop = self.properties[variable]
            prop['last_value'] = prop['value']
            prop['value'] = value
            prop['event_count'] += 1
            prop['last_update'] = timestamp
            
            # Keep last 100 values for history/charts
            prop['history'].append({
                'timestamp': timestamp,
                'value': value
            })
            if len(prop['history']) > 100:
                prop['history'].pop(0)
            
            self.total_events += 1
            self.last_update = timestamp
    
    def get_property_stats(self, variable: str) -> Optional[Dict[str, Any]]:
        """Get statistics for a specific property."""
        with self._lock:
            return self.properties.get(variable, None)
    
    def get_all_properties(self) -> Dict[str, Dict[str, Any]]:
        """Get all properties with their current stats."""
        with self._lock:
            return dict(self.properties)
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get overall server statistics."""
        with self._lock:
            return {
                'total_events': self.total_events,
                'active_properties': len(self.properties),
                'uptime_seconds': time.time() - self.start_time,
                'last_update': self.last_update,
                'start_time': self.start_time
            }


class WebUIServer:
    """Flask web server for the OPC UA dashboard (polling-based)."""
    
    def __init__(self, data_manager: DataManager, host='127.0.0.1', port=5000):
        self.data_manager = data_manager
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.app.config['SECRET_KEY'] = 'opcua-server-ui-secret'
        
        self.setup_routes()
        
        # Suppress Flask/Werkzeug logs unless in debug mode
        if not log.isEnabledFor(logging.DEBUG):
            logging.getLogger('werkzeug').setLevel(logging.WARNING)
    
    def setup_routes(self):
        """Setup Flask routes."""
        
        @self.app.route('/')
        def index():
            """Serve the main dashboard page."""
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            try:
                with open(os.path.join(static_dir, 'index.html'), 'r') as f:
                    return f.read()
            except FileNotFoundError:
                return """
                <h1>OPC UA Dashboard</h1>
                <p>Dashboard files not found. Please ensure the static files are in the correct location.</p>
                <p>Expected location: <code>{}</code></p>
                """.format(static_dir)
        
        @self.app.route('/static/<path:filename>')
        def static_files(filename):
            """Serve static files."""
            static_dir = os.path.join(os.path.dirname(__file__), 'static')
            return send_from_directory(static_dir, filename)
        
        @self.app.route('/api/stats')
        def api_stats():
            """API endpoint for current statistics."""
            return json.dumps({
                'summary': self.data_manager.get_summary_stats(),
                'properties': self.data_manager.get_all_properties()
            }, default=str)
    
    def start(self):
        """Start the web server in a separate thread."""
        def run_server():
            try:
                log.info(f"Starting Web UI server at http://{self.host}:{self.port}")
                self.app.run(
                    host=self.host, 
                    port=self.port, 
                    debug=False, 
                    use_reloader=False
                )
            except Exception as e:
                log.error(f"Web server failed to start: {e}")
                import traceback
                log.error(traceback.format_exc())
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        # Give the server a moment to start
        time.sleep(0.5)
        return server_thread


class UIVariableChangeHandler:
    """Variable change handler that also feeds the web UI."""

    def __init__(self, variable_map: Dict, latency_log_path: str, data_manager: DataManager, web_server: WebUIServer):
        """Initialize the latency log and keep references to the UI components."""
        self.variable_map = variable_map
        self.latency_log_path = latency_log_path
        self.data_manager = data_manager
        self.web_server = web_server
        
        try:
            os.makedirs(os.path.dirname(self.latency_log_path) or '.', exist_ok=True)
        except Exception:
            pass
        self._fp = open(self.latency_log_path, 'a', buffering=1)  # line-buffered

    def datachange_notification(self, node, val, data):
        """Update the UI data and write a latency record for each variable change."""
        server_recv_ts = time.time()
        label = self.variable_map.get(node.nodeid, "unknown")
        
        parsed = None
        raw_payload = None
        
        # Parse the incoming value
        try:
            if isinstance(val, bytes):
                raw_payload = val.decode('utf-8', errors='replace')
            elif isinstance(val, str):
                raw_payload = val
            else:
                if hasattr(val, 'Value'):
                    inner = val.Value
                    if isinstance(inner, bytes):
                        raw_payload = inner.decode('utf-8', errors='replace')
                    elif isinstance(inner, str):
                        raw_payload = inner
                    else:
                        try:
                            raw_payload = json.dumps(inner, default=str)
                        except Exception:
                            raw_payload = str(inner)
                else:
                    try:
                        raw_payload = json.dumps(val, default=str)
                    except Exception:
                        raw_payload = str(val)
            
            # Try to parse as JSON
            try:
                parsed = json.loads(raw_payload) if raw_payload is not None else None
            except Exception:
                try:
                    import re
                    if raw_payload:
                        m = re.search(r"\{.*\}", raw_payload)
                        if m:
                            parsed = json.loads(m.group(0))
                except Exception:
                    parsed = None
        except Exception:
            parsed = None
        
        if not isinstance(parsed, dict):
            parsed = {}
        
        # Extract the actual value for UI display
        ui_value = parsed.get('value', val)
        if hasattr(ui_value, 'Value'):
            ui_value = ui_value.Value
        
        # Update data manager (UI will poll for updates)
        self.data_manager.update_property(
            variable=label,
            value=ui_value,
            node_id=str(node.nodeid),
            timestamp=server_recv_ts
        )
        
        record = {
            'event': 'variable_updated',
            'node_id': str(node.nodeid),
            'variable': label,
            'value': parsed.get('value', None),
            'message_id': parsed.get('id', None),
            'recv_ts': parsed.get('recv_ts', None),
            'processed_ts': parsed.get('processed_ts', None),
            'server_recv_ts': server_recv_ts,
        }
        
        try:
            self._fp.write(json.dumps(record, default=str) + '\n')
        except Exception:
            log.exception('Failed to write latency record to file')
        
        log.debug(json.dumps(record))
    
    def close(self):
        try:
            if hasattr(self, '_fp') and not self._fp.closed:
                self._fp.flush()
                self._fp.close()
        except Exception:
            pass
