# agent/main_agent.py
import time
import threading
import logging
from openai import OpenAI
from .asr_handler import ASRHandler
from .llm_handler import LLMHandler

logger = logging.getLogger(__name__)

class MainAgent:
    def __init__(self, api_key: str):
        logger.info("初始化Agent...")
        self.api_key = api_key
        
        self.llm_client = OpenAI(
            api_key=self.api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        logger.info("大模型客户端(LLM Client)已成功初始化。")

        self.llm_handler = LLMHandler(self.llm_client)
        self.asr_handler = None # 将在run循环中创建
        
        # --- 核心改动：增加停止标志 ---
        self._stop_event = threading.Event()

    def handle_asr_result(self, text: str):
        self.llm_handler.get_response(text)

    def run(self):
        """
        启动Agent的主守护循环，实现自动重连。
        """
        logger.info("Agent守护进程开始运行...")
        while not self._stop_event.is_set():
            logger.info("="*20 + " 启动新ASR会话 " + "="*20)
            try:
                # 每次循环都创建一个新的ASRHandler实例
                self.asr_handler = ASRHandler(on_sentence_end_callback=self.handle_asr_result)
                self.asr_handler.start_session()
                
                # 运行音频循环直到连接丢失
                self.asr_handler.run_audio_loop()
                
                # 如果是正常停止，则退出循环
                if self._stop_event.is_set():
                    break
                
                logger.warning("ASR会话已断开。")

            except Exception as e:
                logger.error(f"ASR处理器发生未知异常: {e}", exc_info=True)
            
            if not self._stop_event.is_set():
                logger.info("将在2秒后尝试重新连接...")
                time.sleep(2)

    def stop(self):
        """
        停止Agent的守护循环。
        """
        logger.info("Agent正在停止...")
        self._stop_event.set()
        if self.asr_handler:
            self.asr_handler.stop()
