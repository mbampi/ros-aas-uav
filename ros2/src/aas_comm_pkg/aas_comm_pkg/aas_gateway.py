import rclpy
from .subscriber_node import MultiTopicSubscriber
from .topic_mapper import TopicNodeIdMapper

def main(args=None):
    rclpy.init(args=args)
    try:
        print("[Main] Loading topic-node ID mappings...")
        mapping = TopicNodeIdMapper.map_topics_to_node_ids("map.yaml", "uav_submodel.xml")
        node = MultiTopicSubscriber(mapping, "opc.tcp://127.0.0.1:4840/freeopcua/server/")
        print("[Main] Node started...")
        rclpy.spin(node)
    except Exception as e:
        print(f"[Main] Exception: {e}")
    finally:
        if 'node' in locals():
            node.opcua_client.disconnect()
            node.destroy_node()
        rclpy.shutdown()
        print("[Main] Shutdown complete")

if __name__ == '__main__':
    main()