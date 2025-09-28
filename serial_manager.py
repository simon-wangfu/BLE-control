import serial
import time
import logging
import re
from config import SERIAL_CONFIG


class SerialManager:
    def __init__(self):
        self.serials = {}  # 存储左右脚串口对象
        self.initialize_ports()

    def initialize_ports(self):
        """初始化串口"""
        try:
            # 初始化左脚串口
            self.serials['left'] = serial.Serial(
                port=SERIAL_CONFIG['left_port'],
                baudrate=SERIAL_CONFIG['baudrate'],
                timeout=SERIAL_CONFIG['timeout']
            )

            # 初始化右脚串口
            self.serials['right'] = serial.Serial(
                port=SERIAL_CONFIG['right_port'],
                baudrate=SERIAL_CONFIG['baudrate'],
                timeout=SERIAL_CONFIG['timeout']
            )

            time.sleep(2)  # 等待串口稳定
            logging.info(f"串口初始化成功: 左脚={SERIAL_CONFIG['left_port']}, 右脚={SERIAL_CONFIG['right_port']}")

        except Exception as e:
            logging.error(f"串口初始化失败: {e}")
            raise

    def send_command(self, port, command):
        """发送命令到指定串口"""
        try:
            if port in self.serials:
                # 清空输入缓冲区，避免读取到旧数据
                self.serials[port].reset_input_buffer()

                self.serials[port].write(command)
                logging.info(f"向{port}脚发送命令: {command.hex().upper()}")
            else:
                logging.error(f"未知的端口: {port}")
        except Exception as e:
            logging.error(f"发送命令到{port}失败: {e}")

    def read_response(self, port, max_attempts=3):
        """读取指定串口的响应，尝试从数据中提取有效帧"""
        try:
            if port not in self.serials:
                return None

            time.sleep(1)  # 等待设备响应

            # 读取所有可用数据
            response = self.serials[port].read_all()

            if not response:
                logging.warning(f"{port}脚无响应")
                return None

            hex_str = response.hex().upper()
            logging.info(f"{port}脚原始响应: {hex_str}")

            # 尝试从数据中提取有效的响应帧
            valid_frame = self.extract_valid_frame(hex_str, port)

            if valid_frame:
                logging.info(f"{port}脚提取的有效帧: {valid_frame}")
                return bytes.fromhex(valid_frame)
            else:
                logging.warning(f"{port}脚未找到有效帧")
                return None

        except Exception as e:
            logging.error(f"读取{port}响应失败: {e}")
            return None

    def extract_valid_frame(self, hex_data, port):
        """从十六进制字符串中提取有效的响应帧"""
        # 可能的响应帧模式
        patterns = [
            r'55BBFF07[0-9A-F]{12}',  # 11字节完整帧
            r'55BBFF03[0-9A-F]{6}',  # 7字节帧
        ]

        for pattern in patterns:
            matches = re.findall(pattern, hex_data)
            if matches:
                # 返回最后一个匹配（最新响应）
                return matches[-1]

        # 如果没有找到完整帧，尝试查找帧头
        if '55BBFF' in hex_data:
            # 查找最后一个55BBFF的位置
            last_index = hex_data.rfind('55BBFF')
            if last_index != -1:
                # 尝试提取从帧头开始的22个字符（11字节）
                if last_index + 22 <= len(hex_data):
                    potential_frame = hex_data[last_index:last_index + 22]
                    logging.info(f"{port}脚提取的潜在帧: {potential_frame}")
                    return potential_frame

        return None

    def verify_response(self, response, expected_prefix):
        """验证响应是否以预期前缀开头"""
        if not response:
            return False

        # 将响应转换为十六进制字符串进行比较
        response_hex = response.hex().upper()
        prefix_hex = expected_prefix.hex().upper()

        return response_hex.startswith(prefix_hex)

    def close_ports(self):
        """关闭所有串口"""
        for port, ser in self.serials.items():
            if ser and ser.is_open:
                ser.close()
                logging.info(f"关闭{port}脚串口")