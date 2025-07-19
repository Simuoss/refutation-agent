# main.py
import os
import sys
import signal
import dashscope
from dotenv import load_dotenv
import logging
from utils.logger_setup import setup_global_logger
from agent.main_agent import MainAgent
from ui.webview_window import RefutationWebViewWindow

# 在所有逻辑开始前，先配置好日志
setup_global_logger()

agent = None
window = None
logger = logging.getLogger(__name__)

def init_dashscope_api_key():
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        logger.error("未在 .env 文件或环境变量中找到 DASHSCOPE_API_KEY！")
        sys.exit(1)
    logger.info("DashScope API Key 已成功加载。")
    return api_key

def signal_handler(sig, frame):
    """处理 Ctrl+C 中断信号"""
    logger.info("收到退出信号 (Ctrl+C)，正在停止...")
    if agent:
        agent.stop()
    if window and window.window:
        window.window.destroy()
    sys.exit(0)

if __name__ == '__main__':
    logger.info("="*10 + " AI自动反驳Agent启动 " + "="*10)
    
    signal.signal(signal.SIGINT, signal_handler)

    try:
        # 1. 初始化API Key
        api_key = init_dashscope_api_key()
        dashscope.api_key = api_key 
        
        # 2. 创建WebView窗口实例
        window = RefutationWebViewWindow()
        
        # 3. 创建Agent实例，并传入窗口实例
        agent = MainAgent(api_key=api_key, window=window)
        
        # 4. 在后台线程中启动Agent的核心逻辑
        agent.run()
        
        # 5. 在主线程中启动并运行WebView窗口（这将阻塞主线程）
        window.start()
        window.run()

    except KeyboardInterrupt:
        logger.info("程序已通过 Ctrl+C 确认退出。")
    except Exception as e:
        logger.critical(f"程序启动时发生致命错误: {e}", exc_info=True)
    
    finally:
        if agent:
            agent.stop()
        logger.info("="*10 + " 程序已退出 " + "="*10)
