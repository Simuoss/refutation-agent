# agent/llm_handler.py
import logging
from openai import OpenAI, APIConnectionError, RateLimitError
import config

logger = logging.getLogger(__name__)

class LLMHandler:
    def __init__(self, client: OpenAI):
        self.client = client
        self.system_prompt = config.DEFAULT_SYSTEM_PROMPT

    def get_response(self, text_to_refute: str):
        if not self.client:
            logger.error("LLM客户端未初始化！")
            return

        logger.info("[🤖 AI杠精 正在思考...]")
        
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
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    response_text += content
                    # 对于流式输出，我们仍然使用print来保持实时显示效果
                    print(content, end="", flush=True)
            print()  # 换行
            logger.info(f"AI回复完成: {response_text}")

        # --- 核心改动：捕获更具体的异常 ---
        except APIConnectionError as e:
            logger.error(f"LLM网络连接失败: {e.__cause__}")
        except RateLimitError as e:
            logger.warning("LLM请求频率过高，请稍后再试。")
        except Exception as e:
            logger.error(f"调用大模型时发生未知错误: {e}", exc_info=True)
