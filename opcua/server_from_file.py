from opcua import Server, ua
from datetime import datetime
import time
import xml.etree.ElementTree as ET

# Dictionary to map variables to labels
variable_to_label = {}

class VariableChangeHandler:
    def datachange_notification(self, node, val, data):
        label = variable_to_label.get(node, "Unknown")
        timestamp = datetime.now().isoformat()
        print(f"[{timestamp}] Variable '{label}' changed value to: {val}. node: {node.nodeid}")

def load_nodes_from_xml(server, namespace_uri, xml_file):
    """Loads nodes from an XML file and adds them to the OPC UA server."""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Error loading XML file: {e}")
        return
    
    namespace_index = server.get_namespace_index(namespace_uri)

    def create_node(element, parent_node):
        node_id = element.get('NodeId')
        browse_name_element = element.find('BrowseName')
        display_name_element = element.find('DisplayName')

        if not (node_id and browse_name_element is not None):
            print(f"Skipping invalid node: {element.tag}")
            return
        
        browse_name = browse_name_element.text
        display_name = display_name_element.text if display_name_element is not None else browse_name

        if node_id.startswith('ns=2;'):
            node_id = node_id.replace('ns=2;', f'ns={namespace_index};')

        if element.tag.endswith('UAObject'):
            new_node = parent_node.add_object(node_id, browse_name, display_name=display_name)
        elif element.tag.endswith('UAVariable'):
            data_type_element = element.find('DataType')
            if data_type_element is not None:
                data_type = data_type_element.text
                if data_type.startswith('ns=2;'):
                    data_type = data_type.replace('ns=2;', f'ns={namespace_index};')
                try:
                    data_type_id = ua.NodeId.from_string(data_type)
                except ValueError:
                    data_type_id = ua.NodeId(ua.ObjectIds.BaseDataType)

                # Assign a default value based on the data type
                default_value = ua.Variant(0, ua.VariantType.Int32)  # Default to Int32 if unknown
                new_node = parent_node.add_variable(node_id, browse_name, default_value, display_name=display_name)
                new_node.set_access_level(ua.AccessLevel.CurrentRead | ua.AccessLevel.CurrentWrite)
                variable_to_label[new_node] = browse_name
            else:
                new_node = parent_node.add_variable(node_id, browse_name, ua.Variant(0, ua.VariantType.Int32), display_name=display_name)
                new_node.set_access_level(ua.AccessLevel.CurrentRead | ua.AccessLevel.CurrentWrite)
                variable_to_label[new_node] = browse_name
        else:
            return
        
        description_element = element.find('Description')
        if description_element is not None:
            new_node.set_description(description_element.text)

        references = element.find('References')
        if references is not None:
            for reference in references:
                reference_type = reference.get('ReferenceType')
                target_id = reference.text
                if target_id and target_id.startswith('ns=2;'):
                    target_id = target_id.replace('ns=2;', f'ns={namespace_index};')
                
                if reference_type == 'i=47':  # HasComponent
                    target_element = root.find(f".//*[@NodeId='{reference.text}']")
                    if target_element is not None:
                        create_node(target_element, new_node)

    root_object = root.find(".//UAObject[@BrowseName='1:AssetAdminShell']")
    if root_object is not None:
        objects = server.get_objects_node()
        create_node(root_object, objects)

def main():
    server = Server()
    server.set_endpoint("opc.tcp://127.0.0.1:4840/freeopcua/server/")

    namespace_uri = "http://admin-shell.io/samples/i4aas/instance/"
    idx = server.register_namespace(namespace_uri)

    load_nodes_from_xml(server, namespace_uri, "uav_submodel.xml")

    server.start()
    print("OPC UA Server is running at opc.tcp://127.0.0.1:4840/freeopcua/server/")

    handler = VariableChangeHandler()
    subscription = server.create_subscription(10, handler)

    for var in variable_to_label.keys():
        subscription.subscribe_data_change(var)
    
    try:
        while True:
            print(f"Server time: {datetime.now().isoformat()}")
            time.sleep(10)
    except KeyboardInterrupt:
        print("Shutting down OPC UA Server...")
    finally:
        server.stop()
        print("OPC UA Server stopped.")

if __name__ == "__main__":
    main()
