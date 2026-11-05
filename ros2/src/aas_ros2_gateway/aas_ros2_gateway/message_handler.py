# Copyright 2024 Matheus Dussin Bampi
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import importlib
import math
import re
import uuid
import time
import json
from typing import Any, Dict, Optional, Union, List, Callable


class MessageHandler:
    """
    Generic handler for ROS2 messages that dynamically imports message types,
    extracts fields, and applies transformations.
    """
    
    def __init__(self, logger, enums: Optional[Dict] = None):
        """
        Initialize the message handler.
        
        Args:
            logger: ROS2 logger instance
            enums: Dictionary containing enum mappings (e.g., PX4 enums)
        """
        self.logger = logger
        self.enums = enums or {}
        self._message_type_cache = {}
        self._transformations = self._build_transformation_map()
        self._field_path_cache = {}  # Cache parsed field paths

        self._message_count = 0
        self._last_stats_time = time.time()
    
    def import_message_type(self, message_type_string: str):
        """
        Dynamically import a ROS2 message type from a string specification.
        
        Args:
            message_type_string: String like 'px4_msgs.msg.BatteryStatus' or 'std_msgs.msg.String'
            
        Returns:
            The imported message class, or None if import fails
        """
        if message_type_string in self._message_type_cache:
            return self._message_type_cache[message_type_string]
            
        try:
            parts = message_type_string.split('.')
            if len(parts) < 3:
                self.logger.error(f"Invalid message type format: {message_type_string}")
                return None
                
            # Reconstruct module path and class name
            module_path = '.'.join(parts[:-1])  # e.g., 'px4_msgs.msg'
            class_name = parts[-1]  # e.g., 'BatteryStatus'
            
            module = importlib.import_module(module_path)
            message_class = getattr(module, class_name)
            self._message_type_cache[message_type_string] = message_class
            
            self.logger.debug(f"Successfully imported message type: {message_type_string}")
            return message_class
            
        except (ImportError, AttributeError) as e:
            self.logger.error(f"Failed to import message type {message_type_string}: {e}")
            return None
    
    def extract_field_value(self, msg: Any, field_path: str) -> Any:
        """
        Extract a field value from a ROS2 message using a path specification.
        
        Args:
            msg: The ROS2 message instance
            field_path: Path to the field, e.g., 'remaining', 'linear.x', 'q[0]'
            
        Returns:
            The extracted field value, or None if extraction fails
        """
        try:
            current_value = msg
            
            # Handle array indexing and nested field access
            path_parts = self._parse_field_path(field_path)
            
            for part in path_parts:
                if isinstance(part, str):
                    # Regular attribute access
                    current_value = getattr(current_value, part)
                elif isinstance(part, int):
                    # Array/list indexing
                    current_value = current_value[part]

            return current_value
            
        except (AttributeError, IndexError, TypeError) as e:
            self.logger.error(f"Failed to extract field '{field_path}' from message: {e}")
            return None
    
    def _parse_field_path(self, field_path: str) -> List[Union[str, int]]:
        """
        Parse a field path string into a list of access operations with caching.
        
        Args:
            field_path: Path like 'linear.x', 'q[0]', 'accelerometer_m_s2[0]'
            
        Returns:
            List of access operations (strings for attributes, ints for indices)
        """
        # Check cache first
        if field_path in self._field_path_cache:
            return self._field_path_cache[field_path]
            
        path_parts = []
        
        dot_parts = field_path.split('.')
        
        for part in dot_parts:
            if '[' in part and ']' in part:
                match = re.match(r'(\w+)\[(\d+)\]', part)
                if match:
                    field_name = match.group(1)
                    index = int(match.group(2))
                    path_parts.extend([field_name, index])
                else:
                    path_parts.append(part)
            else:
                path_parts.append(part)
        
        # Cache the result
        self._field_path_cache[field_path] = path_parts
        return path_parts
    
    def _build_transformation_map(self) -> Dict[str, Callable]:
        """
        Build the transformation function map.
        
        Returns:
            Dictionary mapping transformation names to functions
        """
        return {
            'identity': lambda value: value,
            'percentage': lambda value: float(value) * 100.0,
            'mm_to_m': lambda value: float(value) / 1000.0,
            'negate': lambda value: -float(value),
            'bool_to_string': lambda value: "ARMED" if bool(value) else "DISARMED",
            'vector_magnitude': self._transform_vector_magnitude,
            'vector_magnitude_2d': self._transform_vector_magnitude_2d,
            'quaternion_to_pitch': self._transform_quaternion_to_pitch,
            'quaternion_to_roll': self._transform_quaternion_to_roll,
            'quaternion_to_yaw': self._transform_quaternion_to_yaw,
            'px4_nav_state_to_string': self._transform_px4_nav_state,
            'px4_arming_state_to_string': self._transform_px4_arming_state,
            'diagnostic_level_to_string': self._transform_diagnostic_level,
            'rc_to_signal_strength': self._transform_rc_signal_strength,
            'manual_control_to_signal_strength': self._transform_manual_control_signal,
            'gps_eph_to_signal_strength': self._transform_gps_eph_to_signal,
            'position_to_json': self._transform_position_to_json,
            'velocity_to_json': self._transform_velocity_to_json,
            'pose_to_json': self._transform_pose_to_json,
            'degrees_to_radians': lambda value: math.radians(float(value)),
            'radians_to_degrees': lambda value: math.degrees(float(value)),
            'meters_per_second_to_kmh': lambda value: float(value) * 3.6
        }
    
    def apply_transformation(self, value: Any, transform_type: str) -> Union[str, float, int]:
        """
        Apply a data transformation to a value using the transformation map.
        
        Args:
            value: The input value to transform
            transform_type: The type of transformation to apply
            
        Returns:
            The transformed value
        """
        transform_func = self._transformations.get(transform_type)
        if transform_func is None:
            self.logger.warning(f"Unknown transformation type: {transform_type}")
            return value
        
        try:
            return transform_func(value)
        except Exception as e:
            self.logger.error(f"Transformation '{transform_type}' failed: {e}")
            return value
    
    # Individual transformation methods
    def _transform_vector_magnitude(self, value: Any) -> float:
        """Calculate magnitude of 2D or 3D vector."""
        if not hasattr(value, '__len__') or len(value) < 2:
            self.logger.warning(f"vector_magnitude requires array input, got: {type(value)}")
            return 0.0
        
        if len(value) == 2:
            return math.sqrt(value[0]**2 + value[1]**2)
        else:
            return math.sqrt(sum(x**2 for x in value[:3]))  # Use first 3 components
    
    def _transform_vector_magnitude_2d(self, value: Any) -> float:
        """Calculate 2D horizontal vector magnitude."""
        if hasattr(value, 'x') and hasattr(value, 'y'):
            return math.sqrt(value.x**2 + value.y**2)
        elif hasattr(value, '__len__') and len(value) >= 2:
            return math.sqrt(value[0]**2 + value[1]**2)
        else:
            self.logger.warning(f"vector_magnitude_2d requires object with x,y or array with 2+ elements")
            return 0.0
    
    def _transform_quaternion_to_pitch(self, value: Any) -> float:
        """Convert quaternion [w, x, y, z] to pitch in degrees."""
        if hasattr(value, 'w') and hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
            w, x, y, z = value.w, value.x, value.y, value.z
        elif hasattr(value, '__len__') and len(value) >= 4:
            w, x, y, z = value[0], value[1], value[2], value[3]
        else:
            self.logger.warning(f"quaternion_to_pitch requires quaternion object or array with 4 elements, got: {type(value)}")
            return 0.0
        
        # Convert quaternion to pitch angle
        sin_pitch = 2.0 * (w * y - z * x)
        sin_pitch = max(-1.0, min(1.0, sin_pitch))
        pitch_rad = math.asin(sin_pitch)
        pitch_deg = math.degrees(pitch_rad)
        
        self.logger.debug(f"Quaternion to pitch: w={w:.3f}, x={x:.3f}, y={y:.3f}, z={z:.3f} -> {pitch_deg:.2f} degrees")
        return pitch_deg
    
    def _transform_quaternion_to_roll(self, value: Any) -> float:
        """Convert quaternion [w, x, y, z] to roll in degrees."""
        if hasattr(value, 'w') and hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
            w, x, y, z = value.w, value.x, value.y, value.z
        elif hasattr(value, '__len__') and len(value) >= 4:
            w, x, y, z = value[0], value[1], value[2], value[3]
        else:
            self.logger.warning(f"quaternion_to_roll requires quaternion object or array with 4 elements, got: {type(value)}")
            return 0.0
        
        # Convert quaternion to roll angle
        sin_roll = 2.0 * (w * x + y * z)
        cos_roll = 1.0 - 2.0 * (x * x + y * y)
        roll_rad = math.atan2(sin_roll, cos_roll)
        roll_deg = math.degrees(roll_rad)
        
        self.logger.debug(f"Quaternion to roll: w={w:.3f}, x={x:.3f}, y={y:.3f}, z={z:.3f} -> {roll_deg:.2f} degrees")
        return roll_deg
    
    def _transform_quaternion_to_yaw(self, value: Any) -> float:
        """Convert quaternion [w, x, y, z] to yaw in degrees."""
        if hasattr(value, 'w') and hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
            w, x, y, z = value.w, value.x, value.y, value.z
        elif hasattr(value, '__len__') and len(value) >= 4:
            w, x, y, z = value[0], value[1], value[2], value[3]
        else:
            self.logger.warning(f"quaternion_to_yaw requires quaternion object or array with 4 elements, got: {type(value)}")
            return 0.0
        
        # Convert quaternion to yaw angle
        sin_yaw = 2.0 * (w * z + x * y)
        cos_yaw = 1.0 - 2.0 * (y * y + z * z)
        yaw_rad = math.atan2(sin_yaw, cos_yaw)
        yaw_deg = math.degrees(yaw_rad)
        
        self.logger.debug(f"Quaternion to yaw: w={w:.3f}, x={x:.3f}, y={y:.3f}, z={z:.3f} -> {yaw_deg:.2f} degrees")
        return yaw_deg
    
    def _transform_px4_nav_state(self, value: Any) -> str:
        """Convert PX4 navigation state enum to string."""
        nav_states = self.enums.get('nav_states', {})
        return nav_states.get(int(value), f"UNKNOWN_STATE_{value}")
    
    def _transform_px4_arming_state(self, value: Any) -> str:
        """Convert PX4 arming state enum to string."""
        arming_states = self.enums.get('arming_states', {})
        return arming_states.get(int(value), f"UNKNOWN_ARMING_{value}")
    
    def _transform_diagnostic_level(self, value: Any) -> str:
        """Convert diagnostic level to string."""
        diagnostic_levels = self.enums.get('diagnostic_levels', {
            0: "OK", 1: "WARN", 2: "ERROR", 3: "STALE"
        })
        return diagnostic_levels.get(int(value), f"UNKNOWN_LEVEL_{value}")
    
    def _transform_rc_signal_strength(self, value: Any) -> float:
        """Convert RC channel value to signal strength percentage."""
        if not isinstance(value, (int, float)):
            return 0.0
        return 90.0 if abs(value) > 0.1 else 10.0
    
    def _transform_manual_control_signal(self, value: Any) -> float:
        """Convert manual control data source to signal strength."""
        signal_map = {0: 85.0, 1: 95.0}  # RC: 85%, Mavlink: 95%
        return signal_map.get(int(value), 50.0)  # Default: 50%
    
    def _transform_gps_eph_to_signal(self, value: Any) -> float:
        """Convert GPS EPH (Estimated Position Horizontal accuracy) to signal strength percentage."""
        try:
            eph = float(value)
            # Convert EPH to signal strength (lower EPH = better signal)
            # EPH is in meters, typical values: 0.5-10m
            if eph <= 0.0:
                return 10.0  # Invalid/no signal
            elif eph <= 1.0:
                return 95.0  # Excellent signal
            elif eph <= 2.5:
                return 80.0  # Good signal
            elif eph <= 5.0:
                return 65.0  # Fair signal
            elif eph <= 10.0:
                return 40.0  # Poor signal
            else:
                return 20.0  # Very poor signal
        except (ValueError, TypeError):
            self.logger.warning(f"Invalid EPH value for signal strength conversion: {value}")
            return 0.0
    
    def _transform_position_to_json(self, value: Any) -> str:
        """Convert position data (with x, y, z attributes) to JSON string."""
        try:
            if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
                position_data = {
                    'x': float(value.x),
                    'y': float(value.y),
                    'z': float(value.z)
                }
            elif hasattr(value, '__len__') and len(value) >= 3:
                position_data = {
                    'x': float(value[0]),
                    'y': float(value[1]),
                    'z': float(value[2])
                }
            else:
                self.logger.warning(f"position_to_json requires object with x,y,z or array with 3+ elements")
                return json.dumps({'x': 0.0, 'y': 0.0, 'z': 0.0})
            
            return json.dumps(position_data)
        except Exception as e:
            self.logger.error(f"Failed to convert position to JSON: {e}")
            return json.dumps({'x': 0.0, 'y': 0.0, 'z': 0.0})
    
    def _transform_velocity_to_json(self, value: Any) -> str:
        """Convert velocity data to JSON string."""
        try:
            if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
                velocity_data = {
                    'vx': float(value.x),
                    'vy': float(value.y),
                    'vz': float(value.z),
                    'speed_2d': math.sqrt(value.x**2 + value.y**2),
                    'speed_3d': math.sqrt(value.x**2 + value.y**2 + value.z**2)
                }
            elif hasattr(value, '__len__') and len(value) >= 3:
                velocity_data = {
                    'vx': float(value[0]),
                    'vy': float(value[1]),
                    'vz': float(value[2]),
                    'speed_2d': math.sqrt(value[0]**2 + value[1]**2),
                    'speed_3d': math.sqrt(value[0]**2 + value[1]**2 + value[2]**2)
                }
            else:
                self.logger.warning(f"velocity_to_json requires object with x,y,z or array with 3+ elements")
                return json.dumps({'vx': 0.0, 'vy': 0.0, 'vz': 0.0, 'speed_2d': 0.0, 'speed_3d': 0.0})
            
            return json.dumps(velocity_data)
        except Exception as e:
            self.logger.error(f"Failed to convert velocity to JSON: {e}")
            return json.dumps({'vx': 0.0, 'vy': 0.0, 'vz': 0.0, 'speed_2d': 0.0, 'speed_3d': 0.0})
    
    def _transform_pose_to_json(self, value: Any) -> str:
        """Convert pose data (position + orientation) to JSON string."""
        try:
            pose_data = {}
            
            # Extract position if available
            if hasattr(value, 'x') and hasattr(value, 'y') and hasattr(value, 'z'):
                pose_data['position'] = {
                    'x': float(value.x),
                    'y': float(value.y),
                    'z': float(value.z)
                }
            
            # Extract orientation if available (assuming quaternion)
            if hasattr(value, 'w'):
                # Full quaternion message
                w, x, y, z = value.w, value.x, value.y, value.z
                
                # Convert to Euler angles
                roll_rad = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
                pitch_rad = math.asin(max(-1.0, min(1.0, 2.0 * (w * y - z * x))))
                yaw_rad = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
                
                pose_data['orientation'] = {
                    'quaternion': {'w': float(w), 'x': float(x), 'y': float(y), 'z': float(z)},
                    'euler_degrees': {
                        'roll': math.degrees(roll_rad),
                        'pitch': math.degrees(pitch_rad),
                        'yaw': math.degrees(yaw_rad)
                    }
                }
            
            return json.dumps(pose_data)
        except Exception as e:
            self.logger.error(f"Failed to convert pose to JSON: {e}")
            return json.dumps({'position': {'x': 0.0, 'y': 0.0, 'z': 0.0}})
    
    def process_message(self, msg: Any, field_path: str, transform_type: str = "identity") -> Union[str, float, int, None]:
        """
        Complete message processing: extract field and apply transformation.
        
        Args:
            msg: The ROS2 message instance
            field_path: Path to the field to extract
            transform_type: Transformation to apply to the extracted value
            
        Returns:
            The processed value ready for OPC UA writing
        """
        raw_value = self.extract_field_value(msg, field_path)
        
        if raw_value is None:
            return None
        
        processed_value = self.apply_transformation(raw_value, transform_type)
        
        return processed_value
    
    
    def create_subscription_callback(self, topic: str, property_name: str, node_id: str, 
                                   field_path: str, transform_type: str, opcua_client) -> callable:
        """
        Create a callback function for a specific topic subscription.
        
        Args:
            topic: ROS2 topic name
            property_name: Property name for logging
            node_id: OPC UA node ID to write to
            field_path: Field path to extract from message
            transform_type: Data transformation to apply
            opcua_client: OPC UA client instance
            
        Returns:
            Callback function for the subscription
        """
        def callback(msg):
            """Generated callback for topic subscription."""
            try:
                # Capture timestamp immediately
                recv_ts = time.time()
                
                # Process message 
                processed_value = self.process_message(msg, field_path, transform_type)
                processed_ts = time.time()
                
                if processed_value is not None:
                    # Create JSON payload
                    write_payload = json.dumps({
                        'id': str(uuid.uuid4()),
                        'topic': topic,
                        'recv_ts': recv_ts,
                        'processed_ts': processed_ts,
                        'value': processed_value
                    })
                    
                    opcua_client.write_value(node_id, write_payload)
                    
                    # Metrics every 1000 messages (to avoid overhead)
                    self._message_count += 1
                    if self._message_count % 1000 == 0:
                        current_time = time.time()
                        elapsed = current_time - self._last_stats_time
                        rate = 1000.0 / elapsed if elapsed > 0 else 0
                        self.logger.info(f"Stats: {self._message_count} msgs, {rate:.0f} msg/s")
                        self._last_stats_time = current_time
                        
            except Exception as e:
                self.logger.error(f"Error processing {topic}: {e}")

        return callback
