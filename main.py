# main.py
import os
import sys
import signal
import dashscope
from dotenv import load_dotenv
from agent.main_agent import MainAgent

agent = None

def init_dashscope_api_key():
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误：未在 .env 文件或环境变量中找到 DASHSCOPE_API_KEY！", file=sys.stderr)
        sys.exit(1)
    print("DashScope API Key 已成功加载。")
    return api_key

def signal_handler(sig, frame):
    """处理 Ctrl+C 中断信号"""
    global agent
    print("\n[程序] 收到退出信号，正在停止...")
    if agent:
        agent.stop() # 调用新的停止方法

# --- 文件内容基本不变，除了 signal_handler 的调用目标 ---

if __name__ == '__main__':
    print("[程序] AI自动反驳Agent启动中...")
    
    signal.signal(signal.SIGINT, signal_handler)

    try:
        api_key = init_dashscope_api_key()
        dashscope.api_key = api_key 
        
        agent = MainAgent(api_key=api_key)
        agent.run() # 启动守护循环

    except KeyboardInterrupt:
        # 主动捕获KeyboardInterrupt，防止在sleep时按Ctrl+C导致栈追踪信息打印
        print("\n[程序] 已通过Ctrl+C确认退出。")
    except Exception as e:
        print(f"程序启动时发生致命错误: {e}")
    
    finally:
        print("[程序] 已退出。")