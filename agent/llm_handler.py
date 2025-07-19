# agent/llm_handler.py
import logging
from openai import OpenAI, APIConnectionError, RateLimitError
import config
from ui.webview_window import RefutationWebViewWindow, StreamingAIResponse

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, client: OpenAI, window: RefutationWebViewWindow):
        self.client = client
        self.window = window
        self.system_prompt = config.DEFAULT_SYSTEM_PROMPT

    def get_response(self, text_to_refute: str):
        """获取AI回复并通过WebView显示"""
        if not self.client or not self.window:
            logger.error("LLM客户端或WebView窗口未初始化！")
            return

        logger.info("[🤖 AI杠精 正在思考...]")
        
        # 在UI上显示用户听到的内容
        self.window.add_user_message(text_to_refute)
        
        try:
            completion = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': text_to_refute}
                ],
                stream=True,
            )

            logger.info("[🤖 AI杠精 生成中...]")
            
            response_text = ""
            with StreamingAIResponse(self.window) as stream:
                for chunk in completion:
                    content = chunk.choices[0].delta.content
                    if content:
                        response_text += content
                        stream.append(content)
                        # 仍然在控制台打印，方便调试
                        print(content, end="", flush=True)
            
            print() # 换行
            logger.info(f"AI回复完成: {response_text}")
            return response_text

        except APIConnectionError as e:
            logger.error(f"LLM网络连接失败: {e.__cause__}")
        except RateLimitError as e:
            logger.warning("LLM请求频率过高，请稍后再试。")
        except Exception as e:
            logger.error(f"调用大模型时发生未知错误: {e}", exc_info=True)
