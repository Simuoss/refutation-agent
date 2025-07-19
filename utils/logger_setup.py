# utils/logger_setup.py
import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

def setup_global_logger():
    """
    配置全局日志系统，输出到控制台和文件。
    """
    # 创建 logs 文件夹
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # 生成带时间戳的文件名
    log_filename = datetime.now().strftime('log_%Y-%m-%d_%H-%M-%S.log')
    log_filepath = os.path.join('logs', log_filename)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
    )

    # 获取根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO) # 设置根日志器的最低级别

    # --- 配置控制台处理器 ---
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # --- 配置文件处理器 ---
    # RotatingFileHandler: 当文件达到指定大小时，会自动重命名并创建新文件
    # maxBytes=4*1024*1024 (4MB), backupCount=5 (保留最近5个备份)
    file_handler = RotatingFileHandler(
        log_filepath, maxBytes=4 * 1024 * 1024, backupCount=5, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    logging.info("全局日志系统已成功配置。")