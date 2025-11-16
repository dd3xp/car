import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from gpiozero import Motor

'''
1. source install/setup.bash # 在项目目录下执行
2. ros2 run wheels motor_control
3. ros2 run teleop_twist_keyboard teleop_twist_keyboard # 在另一个终端执行
'''

class MotorControlNode(Node):
    def __init__(self):
        super().__init__('motor_control_node')

        # 定义每个电机的GPIO接口
        self.motors = {
            # 前轮：对调 forward/backward
            "left_front":  Motor(forward=27, backward=17, pwm=False),
            "right_front": Motor(forward=20, backward=26, pwm=False),

            # 后轮：保持原来方向
            "left_back":   Motor(forward=13, backward=19, pwm=False),
            "right_back":  Motor(forward=12, backward=16, pwm=False),
        }

        # 订阅 teleop_twist_keyboard 节点发布的 /cmd_vel 主题
        self.subscription = self.create_subscription(
            Twist,
            '/cmd_vel',
            self.cmd_vel_callback,
            10
        )

        self.get_logger().info("✅ 电机控制节点已启动，等待 /cmd_vel 指令...")

    def cmd_vel_callback(self, msg: Twist):
        """接收 /cmd_vel 并转换为每个电机的正反转控制"""
        linear_x = msg.linear.x    # 前后运动
        linear_y = msg.linear.y    # 左右平移（麦克纳姆用）
        angular_z = msg.angular.z  # 旋转

        # ================================
        # 麦克纳姆轮运动学方程
        # ================================
        # 对于右前右后为 //（斜杠朝外），左前左后为 \\（斜杠朝内）的安装方式：
        # wheel_speeds = [LF, RF, LB, RB]
        # LF = linear_x - linear_y - angular_z
        # RF = linear_x + linear_y + angular_z
        # LB = linear_x + linear_y - angular_z
        # RB = linear_x - linear_y + angular_z

        lf = linear_x - linear_y - angular_z
        rf = linear_x + linear_y + angular_z
        lb = linear_x + linear_y - angular_z
        rb = linear_x - linear_y + angular_z

        # 控制信号阈值（0.1以内视为静止）
        threshold = 0.1
        speeds = {"left_front": lf, "right_front": rf,
                  "left_back": lb, "right_back": rb}

        for name, speed in speeds.items():
            motor = self.motors[name]
            if speed > threshold:
                motor.forward()
            elif speed < -threshold:
                motor.backward()
            else:
                motor.stop()

        # 调试信息
        self.get_logger().info(
            f"LF={lf:+.2f}, RF={rf:+.2f}, LB={lb:+.2f}, RB={rb:+.2f}"
        )


def main(args=None):
    rclpy.init(args=args)
    node = MotorControlNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("🛑 手动中断，停止所有电机。")
    finally:
        for motor in node.motors.values():
            motor.stop()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
