# 串口配置（根据实际连接修改）
SERIAL_CONFIG = {
    'left_port': 'COM26',  # 左脚串口
    'right_port': 'COM28',  # 右脚串口
    'baudrate': 9600,
    'timeout': 5
}

# 测试参数
TEST_CONFIG = {
    'total_cycles': 203,  # 总循环次数
    'aging_per_cycle': 5,  # 每次循环老化次数
    'aging_duration': 426,  # 单次老化时间(秒)
    'wait_time': 5,  # 等待时间(秒)
}

# 命令定义（根据您的文档）
COMMANDS = {
    # 进入老化测试命令
    'enter_aging_left': bytes.fromhex('55 AA FF 02 09 01'),  # 左脚进入老化
    'enter_aging_right': bytes.fromhex('55 AA FF 02 09 00'),  # 右脚进入老化

    # 获取老化结果命令
    # 'get_result_left': bytes.fromhex('55 AA FF 02 41 01'),  # 获取左脚结果
    # 'get_result_right': bytes.fromhex('55 AA FF 02 41 00'),  # 获取右脚结果
}

# 预期响应前缀（简化验证逻辑）
RESPONSE_PREFIXES = {
    'enter_aging': bytes.fromhex('55 BB FF 04'),  # 进入老化响应
    'aging_result': bytes.fromhex('55 BB FF 04'),  # 老化结果响应
}