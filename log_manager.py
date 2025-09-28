# ==================================================
# !/usr/bin/env python
# @Author: simon.zhang
# @Date: 2025/9/25 10:50
# @FileName: log_manager.py
# @Email: wangfu_zhang@ggec.com.cn
# ==================================================
import logging
import os
from datetime import datetime


def setup_logging(device_id="Device1"):
    """设置日志系统"""
    # 创建日志目录
    log_dir = "aging_test_logs"
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 生成日志文件名 - 现在正确使用 device_id
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"aging_test_{device_id}_{timestamp}.log")

    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()  # 同时输出到控制台
        ]
    )

    return log_file