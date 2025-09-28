from http.client import responses

# import serial
# import time
#
# # 配置参数（根据实际情况修改）
# SERIAL_CONFIG = {
#     'left_port': 'COM26',  # 串口端口
#      'right_port': 'COM28',
#     'baud_rate': 9600,  # 波特率
#     'timeout': 5  # 超时时间(秒)
# }
#
# # 命令定义（示例：进入老化测试命令）
# LEFT_COMMAND = bytes.fromhex('55 AA FF 02 04 01 ')  # 左脚进入老化命令
# LEFT_EXPECTED_RESPONSE = bytes.fromhex('55 BB FF 07 04 01 00 00 02 04 00')  # 左预期响应
#
# RIGHT_COMMAND = bytes.fromhex('55 AA FF 02 09 00')  # 左脚进入老化命令
# RIGHT_EXPECTED_RESPONSE = bytes.fromhex('55 BB FF 07 04 01 00 00 02 04 00')  # 左预期响应
#
# def serial_test():
#     serials = None
#     try:
#         # open the left serial
#         left_serials = serial.Serial(port= SERIAL_CONFIG['left_port'],
#                                 baudrate=SERIAL_CONFIG['baud_rate'],
#                                 timeout=SERIAL_CONFIG['timeout'])
#         if not left_serials.is_open:
#             print(f"can't open serail {SERIAL_CONFIG['left_port']}")
#             return
#         print(f'serial {SERIAL_CONFIG['left_port']}')
#
#         right_serials = serial.Serial(port= SERIAL_CONFIG['right_port'],
#                                 baudrate=SERIAL_CONFIG['baud_rate'],
#                                 timeout=SERIAL_CONFIG['timeout'])
#         if not right_serials.is_open:
#             print(f"can't open serail {SERIAL_CONFIG['right_port']}")
#             return
#         print(f'serial {SERIAL_CONFIG['right_port']}')
#
#         # send left command
#         print(f'send left commad: {LEFT_COMMAND.hex().upper()}')
#         left_serials.write(LEFT_COMMAND)
#         time.sleep(3)
#         left_read_data = left_serials.read(len(LEFT_EXPECTED_RESPONSE))
#         print(f'left received the data: {left_read_data.hex().upper()}')
#
#         if left_serials == LEFT_EXPECTED_RESPONSE:
#             print("The left successful")
#         else:
#             print(f"The left verification failed")
#
#         # send right command
#         print(f'send right commad: {RIGHT_COMMAND.hex().upper()}')
#         right_serials.write(RIGHT_COMMAND)
#         time.sleep(3)
#         right_read_data = right_serials.read(len(RIGHT_EXPECTED_RESPONSE))
#         print(f'left received the data: {right_read_data.hex().upper()}')
#
#         if right_read_data == RIGHT_EXPECTED_RESPONSE:
#             print("The right successful")
#         else:
#             print(f"The right verification failed")
#     except serial.SerialException as e:
#         print(f"serial error :{str(e)}")
#     except Exception as e:
#         print(f'send: {str(e)}')
#     finally:
#         if serials and serials.is_open:
#             serials.close()
#             print(f"serails {SERIAL_CONFIG['right_port']} close")
#
# if __name__ == "__main__":
#     serial_test()
import serial
import time
import logging

# 配置日志（替代print，支持级别控制和格式化）
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("SerialTest")

# 配置参数（集中管理，便于维护）
CONFIG = {
    "ports": {
        "left": {"port": "COM26", "command": bytes.fromhex("55 AA FF 02 09 01"),
                 "expected": bytes.fromhex("55 BB FF 07 04 01 00 00 02 04 00")},
        "right": {"port": "COM28", "command": bytes.fromhex("55 AA FF 02 09 00"),
                  "expected": bytes.fromhex("55 BB FF 07 04 00 00 00 02 04 00")}
    },
    "serial_params": {
        "baudrate": 9600,
        "timeout": 5,
        "wait_after_send": 3  # 发送后等待响应的时间(秒)
    }
}


def init_serial(port, **kwargs):
    """封装串口初始化逻辑，返回串口对象或None"""
    try:
        ser = serial.Serial(port=port, **kwargs)
        if ser.is_open:
            logger.info(f"serial {port} 初始化成功")
            return ser
        logger.error(f"串口 {port} 初始化失败（未打开）")
        return None
    except serial.SerialException as e:
        logger.error(f"串口 {port} 初始化错误: {str(e)}")
        return None


def send_and_verify(ser, port_name, command, expected_resp, wait_time):
    """封装发送命令+验证响应的逻辑，返回测试结果"""
    if not ser or not ser.is_open:
        logger.error(f"{port_name} 串口未就绪，跳过测试")
        return False

    try:
        # 发送命令
        ser.write(command)
        logger.info(f"{port_name} 发送命令: {command.hex().upper()}")

        # 等待响应
        time.sleep(wait_time)

        # 读取响应
        resp = ser.read(len(expected_resp))
        logger.info(f"{port_name} 接收响应: {resp.hex().upper()}")

        # 验证响应
        if resp == expected_resp:
            logger.info(f"{port_name} 测试通过")
            return True
        else:
            logger.warning(f"{port_name} 测试失败（响应不匹配）")
            return False
    except serial.SerialException as e:
        logger.error(f"{port_name} 通信错误: {str(e)}")
        return False


def main():
    # 初始化所有串口（使用上下文管理器思想，确保资源释放）
    serials = {}
    try:
        # 初始化左右串口
        for name, cfg in CONFIG["ports"].items():
            ser = init_serial(
                port=cfg["port"],
                baudrate=CONFIG["serial_params"]["baudrate"],
                timeout=CONFIG["serial_params"]["timeout"]
            )
            if ser:
                serials[name] = ser

        # 执行测试（若串口初始化成功）
        if serials:
            for name, ser in serials.items():
                cfg = CONFIG["ports"][name]
                send_and_verify(
                    ser=ser,
                    port_name=name.capitalize(),  # 首字母大写（Left/Right）
                    command=cfg["command"],
                    expected_resp=cfg["expected"],
                    wait_time=CONFIG["serial_params"]["wait_after_send"]
                )
        else:
            logger.error("所有串口初始化失败，无法执行测试")

    except Exception as e:
        logger.error(f"测试流程异常: {str(e)}", exc_info=True)
    finally:
        # 确保所有串口关闭（关键优化：之前只关了一个，现在遍历所有）
        for name, ser in serials.items():
            if ser and ser.is_open:
                ser.close()
                logger.info(f"串口 {CONFIG['ports'][name]['port']} 已关闭")


if __name__ == "__main__":
    main()



#
#
#
# def main():
#     ser = None
#     try:
#         # 1. 打开串口
#         ser = serial.Serial(
#             port=SERIAL_CONFIG['left_port'],
#             baudrate=SERIAL_CONFIG['baud_rate'],
#             timeout=SERIAL_CONFIG['timeout']
#         )
#
#         if not ser.is_open:
#             print(f"无法打开串口 {SERIAL_CONFIG['port']}")
#             return
#
#         print(f"串口 {SERIAL_CONFIG['port']} 已打开")
#
#         # 2. 发送指令
#         print(f"发送命令: {TEST_COMMAND.hex().upper()}")
#         ser.write(TEST_COMMAND)
#
#         # 3. 等待设备响应（可选，根据设备响应速度调整）
#         time.sleep(0.1)
#
#         # 4. 读取返回
#         response = ser.read(len(EXPECTED_RESPONSE))  # 读取与预期响应长度相同的数据
#         print(f"收到响应: {response.hex().upper()}")
#
#         # 5. 验证响应是否符合预期
#         if response == EXPECTED_RESPONSE:
#             print("响应符合预期，接口正常")
#         else:
#             print("响应不符合预期，接口异常")
#
#     except serial.SerialException as e:
#         print(f"串口错误: {str(e)}")
#     except Exception as e:
#         print(f"发生错误: {str(e)}")
#     finally:
#         # 6. 关闭串口
#         if ser and ser.is_open:
#             ser.close()
#             print(f"串口 {SERIAL_CONFIG['port']} 已关闭")
#
#
# if __name__ == "__main__":
#     main()
