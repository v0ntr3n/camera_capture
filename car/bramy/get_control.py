import struct
import sys
import threading
import time
from pathlib import Path

import can
import pygame
from sensor_msgs.msg import Image
from std_msgs.msg import Float32MultiArray

import rclpy
from rclpy.node import Node

# Initialize pygame and joystick
pygame.init()
pygame.joystick.init()

# Check if a joystick is connected
if pygame.joystick.get_count() == 0:
    print("No joystick detected!")
    sys.exit()

# Initialize the first joystick
joystick = pygame.joystick.Joystick(0)
joystick.init()

print(f"Joystick connected: {joystick.get_name()}")

# Button map (for common Xbox 360 controller)
button_names = {
    0: "A",
    1: "B",
    # 2: "X",
    3: "X",
    4: "Y",
    # 5: "RB",
    # 6: "Back",
    # 7: "Start",
    # 8: "Xbox",
    10: "Left Stick",
    11: "Right Stick",
}
class get_control(Node):
    def __init__(self):
        super().__init__('get_control')
        self.bus = can.Bus(interface='socketcan', channel='can0')
        self.speed = 0
        self.angle = 90
        self.set_value()
        self.create_subscription(
            Image,
            'color_image',
            self._rgb_callback,
            1  # QoS: queue size
        )
        self.targeFolder = Path.home() / "Downloads" / "Target"
        threading.Thread(target=self.detect, daemon=True).start()
        self.CamState = False


    def detect(self):
        try:
            while True:
                for event in pygame.event.get():
                    if event.type == pygame.JOYBUTTONDOWN:
                        buttonName = button_names.get(event.button, f'Unknown {event.button}')
                        if buttonName == 'A':
                            self.control(-25, self.angle)
                        elif buttonName == 'Y':
                            self.control(25, self.angle)

                        elif buttonName == 'X':
                            self.control(self.speed, self.angle - 10)
                        elif buttonName == 'B':
                            self.control(self.speed, self.angle + 10)
                        elif buttonName == 'Right Stick':
                            self.get_logger().info("Start camera")
                            self.CamState = True
                        elif buttonName == 'Left Stick':
                            self.CamState = False
                            self.get_logger().info("Stop camera")
                        self.get_logger().info(f"Button Pressed: {buttonName}")

                    if event.type == pygame.JOYBUTTONUP:
                        buttonName = button_names.get(event.button, f'Unknown {event.button}')
                        if buttonName == 'Y':
                            self.control(-25, self.angle)
                            self.get_logger().info("Stop")
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            pygame.quit()

    def _rgb_callback(self, msg):
        """
        Callback for the color image topic.
        Converts the ROS Image message to OpenCV format (BGR8).
        """
        try:
            if self.CamState:
                cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
                self._rgb_image = cv_image

                filename = f"rgb_{int(time.time()*1000)}_{self.angle}.jpg"
                save_path = self.targeFolder / filename
                cv_image.imwrite(str(save_path), cv_image)
                self.get_logger().info(f"Saved RGB image to {save_path}")

        except Exception as e:
            self.get_logger().error(f'Error converting RGB image: {e}')
            self._rgb_image = None
    
    def set_value(self):
        data = struct.pack('>hh', int(self.speed), 90 + int(self.angle))
        msg = can.Message(
            arbitration_id=0x21, data=data, is_extended_id=False
        )
        try:
            self.bus.send(msg)
            # print(f"Message sent on {self.bus.channel_info}")
        except can.CanError:
            self.get_logger().info("Message NOT sent")

    def control(self, speed, angle):
        self.get_logger().info(f"{speed}, {angle}")
        if speed == self.speed and angle == self.angle:
            return
        self.speed = speed
        self.angle = angle
        if self.speed >= 100:
            self.speed = 100
        if self.speed <= -100:
            self.speed = -100
        if self.angle >= 90:
            self.angle = 90
        if self.angle <= -90:
            self.angle = -90
        self.set_value()

def main(arg=None):
    rclpy.init()
    node = get_control()
    rclpy.spin(node)
    rclpy.shutdown()

if __name__ == '__main__':
    main()