import os
import sys
import signal
import dashscope
import pyaudio
from openai import OpenAI
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
from dotenv import load_dotenv

# --- 1. 全局变量和配置 ---

# 将客户端声明为全局变量，但在此处不初始化
llm_client = None # <--- 修改：声明为全局变量
recognition = None # <--- 修改：声明为全局变量

# PyAudio 音频流相关变量
mic = None
stream = None

# 录音参数
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
FORMAT_PCM = 'pcm'
BLOCK_SIZE = 3200

# DashScope API Key 初始化函数
def init_dashscope_api_key():
    """
    从 .env 文件或环境变量加载 DashScope API Key。
    成功则返回 Key，失败则退出程序。
    """
    load_dotenv()
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        print("错误：未在 .env 文件或环境变量中找到 DASHSCOPE_API_KEY！", file=sys.stderr)
        sys.exit(1)
    print("DashScope API Key 已成功加载。")
    return api_key # <--- 修改：返回加载到的key

# --- 2. 大语言模型调用模块 (无任何修改) ---

def get_refutation_from_llm(text_to_refute: str):
    """
    调用Qwen大模型生成反驳内容。
    """
    # 检查 llm_client 是否已初始化
    if not llm_client:
        print("\n[错误] LLM客户端未初始化！")
        return

    print("\n[🤖 AI杠精 正在思考...]")
    
    system_prompt = (
        "你是一个宇宙第一杠精AI。你的唯一任务就是反驳用户说的每一句话。"
        "无论用户观点多么正确，你都要找到清奇的角度进行反驳。"
        "你的回复必须：简短、犀利、幽默、出其不意。"
        "不要有任何多余的解释、道歉或开场白，直接开杠！"
    )
    
    try:
        completion = llm_client.chat.completions.create(
            model="qwen-plus-2025-07-14",
            messages=[
                {'role': 'system', 'content': system_prompt},
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
        
    except Exception as e:
        print(f"\n[错误] 调用大模型失败: {e}")

# --- 3. 实时语音识别回调 (无任何修改) ---

class RefutationCallback(RecognitionCallback):
    def on_open(self) -> None:
        global mic, stream
        print("\n[🎤 语音识别服务已连接，请开始说话...]")
        mic = pyaudio.PyAudio()
        stream = mic.open(format=pyaudio.paInt16,
                          channels=CHANNELS,
                          rate=SAMPLE_RATE,
                          input=True)

    def on_close(self) -> None:
        global mic, stream
        print("[🎤 语音识别服务已关闭。]")
        if stream:
            stream.stop_stream()
            stream.close()
        if mic:
            mic.terminate()
        stream = mic = None

    def on_error(self, message) -> None:
        print(f"[错误] 语音识别出错: {message.message}", file=sys.stderr)
        self.on_close()
        os._exit(1)

    def on_event(self, result: RecognitionResult) -> None:
        sentence = result.get_sentence()
        if 'text' in sentence and RecognitionResult.is_sentence_end(sentence):
            user_text = sentence['text']
            print(f"识别到你说: {user_text}")
            get_refutation_from_llm(user_text)

# --- 4. 主程序入口 ---

def signal_handler(sig, frame):
    """处理 Ctrl+C 中断信号"""
    global recognition
    print("\n[程序] 收到退出信号，正在停止...")
    if recognition:
        recognition.stop()
    sys.exit(0)

if __name__ == '__main__':
    print("[程序] AI自动反驳Agent启动中...")
    
    # --- 关键改动：在这里统一初始化所有需要Key的服务 ---
    
    # 1. 首先，获取到API Key
    api_key = init_dashscope_api_key()
    
    # 2. 使用获取到的Key，分别配置两个服务
    # 为 dashscope SDK 本身设置key
    dashscope.api_key = api_key 
    
    # 为 OpenAI 兼容模式的客户端设置key
    llm_client = OpenAI(
        api_key=api_key, # <--- 关键改动：使用真实的key进行初始化
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    )
    print("大模型客户端(LLM Client)已成功初始化。")
    # ----------------------------------------------------
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        callback = RefutationCallback()
        recognition = Recognition(
            model='paraformer-realtime-v2',
            format=FORMAT_PCM,
            sample_rate=SAMPLE_RATE,
            callback=callback
        )
        
        recognition.start()
        print("[提示] 程序已就绪。按 Ctrl+C 退出。")
        
        while True:
            if stream and not stream.is_stopped():
                try:
                    data = stream.read(BLOCK_SIZE, exception_on_overflow=False)
                    recognition.send_audio_frame(data)
                except (IOError, OSError) as e:
                    print(f"音频读取错误: {e}, 可能是设备断开连接。")
                    break
            else:
                break
    
    except Exception as e:
        print(f"程序启动失败: {e}")
    
    finally:
        if recognition:
            recognition.stop()
        print("[程序] 已退出。")