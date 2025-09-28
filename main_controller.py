import logging
import time
from serial_manager import SerialManager
from aging_test import AgingTest
from config import TEST_CONFIG


def setup_logging():
    """设置日志"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f"aging_test_{time.strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def main():
    """主函数"""
    try:
        setup_logging()

        # 显示测试信息
        total_time_hours = (TEST_CONFIG['total_cycles'] *
                            (TEST_CONFIG['aging_duration'] * TEST_CONFIG['aging_per_cycle'] +
                             TEST_CONFIG['wait_time'])) / 3600

        logging.info("=== AI眼镜老化测试系统 ===")
        logging.info(f"总循环次数: {TEST_CONFIG['total_cycles']}")
        logging.info(f"每次循环老化次数: {TEST_CONFIG['aging_per_cycle']}")
        logging.info(f"单次老化时间: {TEST_CONFIG['aging_duration']}秒")
        logging.info(f"预计总时间: {total_time_hours:.2f}小时")

        # 初始化串口和测试
        serial_mgr = SerialManager()
        aging_test = AgingTest(serial_mgr)

        # 运行测试
        aging_test.run_complete_test()

    except KeyboardInterrupt:
        logging.info("用户中断测试")
    except Exception as e:
        logging.error(f"测试错误: {e}")
    finally:
        # 清理资源
        if 'serial_mgr' in locals():
            serial_mgr.close_ports()
        logging.info("测试结束")


if __name__ == "__main__":
    main()