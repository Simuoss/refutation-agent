# config.py
# 存放项目的所有配置信息

# 音频参数
SAMPLE_RATE = 16000
CHANNELS = 1
DTYPE = 'int16'
FORMAT_PCM = 'pcm'
BLOCK_SIZE = 3200

# 模型名称
ASR_MODEL = 'paraformer-realtime-v2'
LLM_MODEL = 'qwen-plus-2025-07-14' # 注意：原始代码中的模型名称带有日期，这里使用通用名称

# 默认人设Prompt
DEFAULT_SYSTEM_PROMPT = (
    "你是一个宇宙第一杠精AI。你的唯一任务就是反驳用户说的每一句话。"
    "无论用户观点多么正确，你都要找到清奇的角度进行反驳。"
    "你的回复必须：简短、犀利、幽默、出其不意。"
    "不要有任何多余的解释、道歉或开场白，直接开杠！"
)


# VAD能量阈值，低于此值被认为是静默。可以根据你的麦克风灵敏度调整。
VAD_ENERGY_THRESHOLD = 200 
# 静默超时时间（秒），持续静默超过这个时间会主动重置ASR连接
SILENCE_TIMEOUT_SECONDS = 20.0