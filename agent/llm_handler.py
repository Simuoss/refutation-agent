# agent/llm_handler.py
from openai import OpenAI, APIConnectionError, RateLimitError
import config

class LLMHandler:
    def __init__(self, client: OpenAI):
        self.client = client
        self.system_prompt = config.DEFAULT_SYSTEM_PROMPT

    def get_response(self, text_to_refute: str):
        if not self.client:
            print("\n[错误] LLM客户端未初始化！")
            return

        print("\n[🤖 AI杠精 正在思考...]")
        
        try:
            completion = self.client.chat.completions.create(
                model=config.LLM_MODEL,
                messages=[
                    {'role': 'system', 'content': self.system_prompt},
                    {'role': 'user', 'content': text_to_refute}
                ],
                stream=True,
            )
            
            print("🤖 AI杠精: ", end="")
            for chunk in completion:
                content = chunk.choices[0].delta.content
                if content:
                    print(content, end="", flush=True)
            print("\n")

        # --- 核心改动：捕获更具体的异常 ---
        except APIConnectionError as e:
            print(f"\n[LLM错误] 网络连接失败: {e.__cause__}")
        except RateLimitError as e:
            print(f"\n[LLM错误] 请求频率过高，请稍后再试。")
        except Exception as e:
            print(f"\n[LLM错误] 调用大模型时发生未知错误: {e}")