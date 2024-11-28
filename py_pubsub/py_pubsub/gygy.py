import sys
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt, QTimer

class ImageSubscriberNode(Node):
    def __init__(self):
        super().__init__('image_subscriber')
        self.subscription = self.create_subscription(
            Image,
            '/cones',  # Topic from the publisher node
            self.image_callback,
            10)
        self.bridge = CvBridge()
        self.current_image = None

    def image_callback(self, msg):
        try:
            # Convert ROS image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            self.current_image = cv_image
        except Exception as e:
            self.get_logger().error(f"Failed to convert image: {e}")

class ImageDisplayWindow(QWidget):
    def __init__(self, image_subscriber_node):
        super().__init__()
        self.image_subscriber_node = image_subscriber_node

        # Set up the PyQt5 GUI
        self.setWindowTitle('ROS2 Image Viewer')
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

        # Set up the layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Set up a QTimer to regularly update the GUI with new images
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(100)  # Update every 100 ms

    def update_image(self):
        # If a new image is available from the ROS2 subscriber, display it
        if self.image_subscriber_node.current_image is not None:
            # Convert OpenCV image (BGR) to QImage (RGB)
            cv_image = self.image_subscriber_node.current_image
            height, width, channel = cv_image.shape
            bytes_per_line = 3 * width
            q_image = QImage(cv_image.data, width, height, bytes_per_line, QImage.Format_RGB888).rgbSwapped()

            # Display the image in the QLabel
            self.label.setPixmap(QPixmap.fromImage(q_image))

def main(args=None):
    # Initialize ROS2
    rclpy.init(args=args)

    # Create the ROS2 image subscriber node
    image_subscriber_node = ImageSubscriberNode()

    # Create the PyQt5 application
    app = QApplication(sys.argv)

    # Create the main window to display the images
    window = ImageDisplayWindow(image_subscriber_node)
    window.show()

    # Create a QTimer to periodically spin the ROS2 node (to receive messages)
    ros_timer = QTimer()
    ros_timer.timeout.connect(lambda: rclpy.spin_once(image_subscriber_node, timeout_sec=0.01))
    ros_timer.start(10)  # Spin ROS every 10 ms

    # Start the PyQt5 event loop
    sys.exit(app.exec_())

    # After exiting the PyQt5 loop, shut down ROS2
    image_subscriber_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
