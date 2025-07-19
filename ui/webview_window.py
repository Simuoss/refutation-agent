# ui/webview_window.py
from typing import Optional
import webview
import time
import logging
import os
import json

logger = logging.getLogger(__name__)

class Api:
    def __init__(self, window_instance):
        self._window = window_instance

    def destroy(self):
        """关闭窗口"""
        logger.info("从JS API请求关闭窗口")
        self._window.stop()

    def resize(self, delta_x, delta_y):
        """根据增量调整窗口大小"""
        if self._window.window:
            current_width, current_height = self._window.window.width, self._window.window.height
            new_width = current_width + delta_x
            new_height = current_height + delta_y
            self._window.window.resize(new_width, new_height)

class RefutationWebViewWindow:
    """AI杠精半透明竖向小窗口"""
    
    def __init__(self, width: int = 280, height: int = 600):
        self.width = width
        self.height = height
        self.window = None
        self.is_running = False
        self.js_api = Api(self)
        
        # 获取web文件路径
        self.web_dir = os.path.join(os.path.dirname(__file__), 'web')
        self.html_path = os.path.join(self.web_dir, 'index.html')
        
        # 确保web文件存在
        if not os.path.exists(self.html_path):
            logger.error(f"HTML文件不存在: {self.html_path}")
            raise FileNotFoundError(f"HTML文件不存在: {self.html_path}")
    
    def start(self):
        """创建窗口 - 必须在主线程中调用"""
        if self.is_running:
            logger.warning("窗口已经在运行中")
            return
            
        self.is_running = True
        
        try:
            # 获取屏幕尺寸并计算窗口位置（右侧边缘）
            import tkinter as tk
            root = tk.Tk()
            screen_width = root.winfo_screenwidth()
            screen_height = root.winfo_screenheight()
            root.destroy()
            
            # 计算窗口位置（屏幕右侧，垂直居中）
            x = screen_width - self.width - 20  # 距离右边缘20像素
            y = (screen_height - self.height) // 2  # 垂直居中
            
            # 创建webview窗口，启用无边框模式
            self.window = webview.create_window(
                title='AI杠精',
                url=self.html_path,
                js_api=self.js_api,
                width=self.width,
                height=self.height,
                x=x,
                y=y,
                min_size=(200, 400),
                resizable=True,
                shadow=True,
                on_top=True,       # 置顶显示
                transparent=False, # 关闭透明背景以接收鼠标事件
                frameless=True,    # 无边框窗口
                easy_drag=True,    # 允许拖动无边框窗口
            )
            
            logger.info("WebView窗口已创建，准备启动...")
            
        except Exception as e:
            logger.error(f"创建WebView窗口失败: {e}", exc_info=True)
            self.is_running = False
            raise
    
    def run(self):
        """运行窗口 - 阻塞调用，必须在主线程中执行"""
        if not self.is_running:
            logger.error("窗口未启动，请先调用start()方法")
            return
            
        try:
            # 启动webview - 这会阻塞主线程
            webview.start(debug=False, private_mode=False)
            
        except Exception as e:
            logger.error(f"运行WebView窗口失败: {e}", exc_info=True)
        finally:
            self.is_running = False
    
    def stop(self):
        """停止窗口"""
        if self.window:
            self.window.destroy()
        self.is_running = False
        logger.info("WebView窗口已停止")
    
    def is_ready(self) -> bool:
        """检查UI是否准备就绪"""
        # 由于移除了js_api，我们假设窗口创建后很快就绪
        return self.is_running and self.window is not None
    
    def wait_for_ready(self, timeout: int = 10) -> bool:
        """等待UI准备就绪"""
        # 简化处理：给UI一点加载时间
        time.sleep(2)
        return self.is_ready()
    
    def execute_js(self, js_code: str):
        """执行JavaScript代码"""
        if not self.is_running or not self.window:
            logger.warning("窗口未运行，无法执行JavaScript")
            return
            
        try:
            self.window.evaluate_js(js_code)
        except Exception as e:
            logger.error(f"执行JavaScript失败: {e}")
    
    def show_listening_status(self):
        """显示偷听状态"""
        self.execute_js("showListeningStatus();")
    
    def add_user_message(self, text: str):
        """添加用户消息"""
        # 转义JavaScript字符串
        escaped_text = json.dumps(text)
        self.execute_js(f"addUserMessage({escaped_text});")
    
    def start_ai_response(self):
        """开始AI流式回复"""
        self.execute_js("startAIResponse();")
    
    def append_ai_response(self, text: str):
        """追加AI回复内容（流式传输）"""
        # 转义JavaScript字符串
        escaped_text = json.dumps(text)
        self.execute_js(f"appendAIResponse({escaped_text});")
    
    def finish_ai_response(self):
        """完成AI回复"""
        self.execute_js("finishAIResponse();")
    
    def add_message(self, role: str, text: str):
        """兼容旧接口：添加消息"""
        escaped_text = json.dumps(text)
        escaped_role = json.dumps(role)
        self.execute_js(f"addMessage({escaped_role}, {escaped_text});")

class StreamingAIResponse:
    """AI流式回复管理器"""
    
    def __init__(self, window: RefutationWebViewWindow):
        self.window = window
        self.is_streaming = False
    
    def start(self):
        """开始流式回复"""
        if not self.is_streaming:
            self.window.start_ai_response()
            self.is_streaming = True
    
    def append(self, text: str):
        """追加文本"""
        if self.is_streaming:
            self.window.append_ai_response(text)
    
    def finish(self):
        """完成回复"""
        if self.is_streaming:
            self.window.finish_ai_response()
            self.is_streaming = False
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()

# 全局窗口实例
_global_window: Optional[RefutationWebViewWindow] = None

def get_window() -> RefutationWebViewWindow:
    """获取全局窗口实例"""
    global _global_window
    if _global_window is None:
        _global_window = RefutationWebViewWindow()
    return _global_window

def start_window():
    """启动全局窗口"""
    window = get_window()
    window.start()
    return window

def stop_window():
    """停止全局窗口"""
    global _global_window
    if _global_window:
        _global_window.stop()
        _global_window = None
