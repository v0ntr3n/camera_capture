import cv2
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

import rclpy
from bramy.camera.astra_camera import Camera
from rclpy.node import Node


class CameraPublisher(Node):
    def __init__(self):
        super().__init__('camera_publisher')
        self.bridge = CvBridge()
        self.camera = Camera()
        self.timer = self.create_timer(1.0 / 30.0, self.timer_callback)

    def timer_callback(self):
        try:
            color = self.camera.get_color()

            color_msg = self.bridge.cv2_to_imgmsg(color, encoding='rgb8')

            self.color_pub.publish(color_msg)
        except Exception as e:
            self.get_logger().error(f'Error publishing frames: {e}')

def main(args=None):
    rclpy.init(args=args)
    node = CameraPublisher()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
