import time
import logging
from config import TEST_CONFIG, COMMANDS, RESPONSE_PREFIXES


class AgingTest:
    def __init__(self, serial_manager):
        self.serial_mgr = serial_manager
        self.results = []

    def run_single_cycle(self, cycle_num):
        """执行单次老化测试循环"""
        logging.info(f"=== 开始第 {cycle_num} 次循环 ===")

        # 1. 发送进入老化测试命令
        logging.info("发送进入老化测试命令...")
        self.serial_mgr.send_command('left', COMMANDS['enter_aging_left'])
        self.serial_mgr.send_command('right', COMMANDS['enter_aging_right'])

        # 2. 验证进入老化响应
        left_response = self.serial_mgr.read_response('left')
        right_response = self.serial_mgr.read_response('right')

        # 使用更宽松的验证方式
        left_ok = self.verify_enter_aging_response(left_response)
        right_ok = self.verify_enter_aging_response(right_response)

        if not (left_ok and right_ok):
            logging.error("进入老化测试失败")
            # 记录详细错误信息
            left_error = self.get_response_error(left_response, 'left')
            right_error = self.get_response_error(right_response, 'right')
            logging.error(f"左脚错误: {left_error}")
            logging.error(f"右脚错误: {right_error}")
            return False, "进入老化测试失败"

        logging.info("成功进入老化测试")

        # 3. 等待老化完成
        wait_time = TEST_CONFIG['aging_duration'] * TEST_CONFIG['aging_per_cycle']
        logging.info(f"等待老化完成 ({wait_time}秒)...")

        # 简化等待逻辑，每60秒记录一次
        for i in range(wait_time):
            if i % 60 == 0:
                remaining = wait_time - i
                logging.info(f"剩余等待时间: {remaining}秒")
            time.sleep(1)

        # 4. 获取老化结果
        logging.info("获取老化测试结果...")
        self.serial_mgr.send_command('left', COMMANDS['get_result_left'])
        self.serial_mgr.send_command('right', COMMANDS['get_result_right'])

        left_result = self.serial_mgr.read_response('left')
        right_result = self.serial_mgr.read_response('right')

        # 5. 解析结果
        left_data = self.parse_result(left_result, 'left')
        right_data = self.parse_result(right_result, 'right')

        # 6. 记录结果
        success = left_data['success'] and right_data['success']
        result_info = {
            'cycle': cycle_num,
            'success': success,
            'left': left_data,
            'right': right_data,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        self.results.append(result_info)

        if success:
            logging.info(f"循环 {cycle_num} 成功 - 左脚: {left_data['pass_count']}/{left_data['total_count']}, "
                         f"右脚: {right_data['pass_count']}/{right_data['total_count']}")
        else:
            logging.error(f"循环 {cycle_num} 失败 - 左脚: {left_data.get('error', '未知错误')}, "
                          f"右脚: {right_data.get('error', '未知错误')}")

        return success, result_info

    def verify_enter_aging_response(self, response):
        """验证进入老化测试的响应（更宽松的验证）"""
        if not response:
            return False

        response_hex = response.hex().upper()

        # 检查标准响应格式
        if response_hex.startswith('55BBFF03'):
            return True

        # 检查设备实际返回的响应格式
        if response_hex.startswith('55BBFF07'):
            return True

        # 检查其他可能的有效响应
        if '55BBFF' in response_hex:
            logging.info(f"检测到可能的有效响应: {response_hex}")
            return True

        return False

    def get_response_error(self, response, port):
        """获取响应错误信息"""
        if not response:
            return "无响应"

        response_hex = response.hex().upper()

        if '55BBFF' in response_hex:
            return f"响应格式不匹配: {response_hex}"
        else:
            return f"无效响应: {response_hex}"

    def parse_result(self, response, port):
        """解析老化结果"""
        if not response:
            return {'success': False, 'error': '无响应'}

        response_hex = response.hex().upper()
        logging.info(f"解析{port}响应: {response_hex}")

        # 验证响应格式
        if not (response_hex.startswith('55BBFF07') or response_hex.startswith('55BBFF03')):
            return {'success': False, 'error': '响应格式错误'}

        try:
            # 响应格式: 55 BB FF 07 41 00 00 00 05 00 03
            # 或者: 55 BB FF 07 04 01 00 00 02 04 00
            # 第7-8字节: 总次数, 第9-10字节: 通过次数

            if len(response) >= 11:
                # 根据实际响应格式调整字节位置
                total_count = (response[7] << 8) + response[8]
                pass_count = (response[9] << 8) + response[10]

                logging.info(f"{port}解析成功: 总次数={total_count}, 通过次数={pass_count}")

                return {
                    'success': True,
                    'total_count': total_count,
                    'pass_count': pass_count,
                    'port': port
                }
            else:
                error_msg = f'响应长度不足: {len(response)}字节'
                logging.error(error_msg)
                return {'success': False, 'error': error_msg}
        except Exception as e:
            error_msg = f'解析错误: {e}'
            logging.error(error_msg)
            return {'success': False, 'error': error_msg}

    def run_complete_test(self):
        """运行完整测试"""
        logging.info(f"开始老化测试，总循环次数: {TEST_CONFIG['total_cycles']}")

        success_count = 0
        for cycle in range(1, TEST_CONFIG['total_cycles'] + 1):
            try:
                success, result = self.run_single_cycle(cycle)

                if success:
                    success_count += 1

                # 循环间等待
                if cycle < TEST_CONFIG['total_cycles']:
                    logging.info(f"等待 {TEST_CONFIG['wait_time']} 秒后进入下一次循环...")
                    time.sleep(TEST_CONFIG['wait_time'])
            except Exception as e:
                logging.error(f"第{cycle}次循环发生异常: {e}")
                # 记录失败结果
                error_result = {'success': False, 'error': str(e)}
                result_info = {
                    'cycle': cycle,
                    'success': False,
                    'left': error_result,
                    'right': error_result,
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                self.results.append(result_info)

        # 生成报告
        self.generate_report(success_count)

    def generate_report(self, success_count):
        """生成测试报告"""
        total_cycles = TEST_CONFIG['total_cycles']
        success_rate = (success_count / total_cycles) * 100 if total_cycles > 0 else 0

        logging.info("=== 测试完成 ===")
        logging.info(f"总循环次数: {total_cycles}")
        logging.info(f"成功次数: {success_count}")
        logging.info(f"失败次数: {total_cycles - success_count}")
        logging.info(f"成功率: {success_rate:.2f}%")

        # 保存详细结果到文件
        self.save_detailed_results()

    def save_detailed_results(self):
        """保存详细结果到文件"""
        try:
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"aging_test_results_{timestamp}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                f.write("老化测试详细结果\n")
                f.write("=" * 50 + "\n")

                for result in self.results:
                    f.write(f"循环 {result['cycle']} - {result['timestamp']}\n")
                    f.write(f"  状态: {'成功' if result['success'] else '失败'}\n")

                    if result['success']:
                        f.write(f"  左脚: 通过{result['left']['pass_count']}/总计{result['left']['total_count']}\n")
                        f.write(f"  右脚: 通过{result['right']['pass_count']}/总计{result['right']['total_count']}\n")
                    else:
                        f.write(f"  左脚错误: {result['left'].get('error', '未知')}\n")
                        f.write(f"  右脚错误: {result['right'].get('error', '未知')}\n")
                    f.write("\n")

            logging.info(f"详细结果已保存到: {filename}")
        except Exception as e:
            logging.error(f"保存结果文件失败: {e}")