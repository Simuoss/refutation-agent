# agent/main_agent.py
import time
import threading
import logging
from openai import OpenAI
from .asr_handler import ASRHandler
from .llm_handler import LLMHandler
from ui.webview_window import RefutationWebViewWindow

logger = logging.getLogger(__name__)

class MainAgent:
    def __init__(self, api_key: str, window: RefutationWebViewWindow):
        logger.info("初始化Agent...")
        self.api_key = api_key
        self.window = window
        
        self.llm_client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        logger.info("大模型客户端(LLM Client)已成功初始化。")

        self.llm_handler = LLMHandler(self.llm_client, self.window)
        self.asr_handler = None
        
        self._stop_event = threading.Event()
        self._thread = None

    def handle_asr_result(self, text: str):
        """处理ASR识别结果"""
        logger.info(f"收到ASR结果: {text}")
        # 将LLM调用放入单独的线程，以避免阻塞ASR处理
        threading.Thread(target=self.llm_handler.get_response, args=(text,), daemon=True).start()

    def _run_loop(self):
        """
        Agent的主守护循环，实现自动重连。
        """
        logger.info("Agent后台守护进程开始运行...")
        
        # 等待UI准备就绪
        if self.window.wait_for_ready(timeout=10):
            logger.info("检测到WebView UI已准备就绪")
            self.window.show_listening_status()
        else:
            logger.warning("WebView UI未能在超时时间内准备就绪")
        
        while not self._stop_event.is_set():
            logger.info("="*20 + " 启动新ASR会话 " + "="*20)
            try:
                self.asr_handler = ASRHandler(on_sentence_end_callback=self.handle_asr_result)
                self.asr_handler.start_session()
                
                if self.window.is_ready():
                    self.window.show_listening_status()
                
                self.asr_handler.run_audio_loop()
                
                if self._stop_event.is_set():
                    break
                
                logger.warning("ASR会话已断开。")

            except Exception as e:
                logger.error(f"ASR处理器发生未知异常: {e}", exc_info=True)
            
            if not self._stop_event.is_set():
                logger.info("将在2秒后尝试重新连接...")
                time.sleep(2)
        
        logger.info("Agent后台守护进程已停止。")

    def run(self):
        """在后台线程中启动Agent的守护循环"""
        if self._thread is not None and self._thread.is_alive():
            logger.warning("Agent已经在运行中。")
            return
            
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止Agent的守护循环"""
        logger.info("Agent正在停止...")
        self._stop_event.set()
        
        if self.asr_handler:
            self.asr_handler.stop()
        
        if self._thread is not None:
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning("Agent后台线程未能正常停止。")
