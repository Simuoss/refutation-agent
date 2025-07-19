# agent/asr_handler.py
import pyaudio
import os
import dashscope
import logging
from dashscope.audio.asr import Recognition, RecognitionCallback, RecognitionResult
import config
import threading
import time
import numpy as np

logger = logging.getLogger(__name__)

class ASRHandler:
    def __init__(self, on_sentence_end_callback):
        self.on_sentence_end_callback = on_sentence_end_callback
        self.mic = None
        self.stream = None
        self.recognition = None
        self._is_running = False
        self._connection_lost = threading.Event()

        class ASRCallback(RecognitionCallback):
            def __init__(self, outer_instance):
                self.outer = outer_instance
            def on_open(self) -> None:
                logger.info("🎤 语音识别服务已连接，请开始说话...")
                try:
                    self.outer.mic = pyaudio.PyAudio()
                    self.outer.stream = self.outer.mic.open(
                        format=pyaudio.paInt16,
                        channels=config.CHANNELS,
                        rate=config.SAMPLE_RATE,
                        input=True
                    )
                    self.outer._is_running = True
                    self.outer._connection_lost.clear()
                except Exception as e:
                    logger.error(f"打开麦克风失败: {e}")
                    self.outer._connection_lost.set()
            def on_close(self) -> None:
                logger.info("🎤 语音识别服务已关闭。")
                self.outer._is_running = False
                if self.outer.stream:
                    if self.outer.stream.is_active():
                        self.outer.stream.stop_stream()
                    self.outer.stream.close()
                if self.outer.mic:
                    self.outer.mic.terminate()
                self.outer.stream = self.outer.mic = None
            def on_error(self, message) -> None:
                logger.error(f"语音识别出错: {message.message}")
                self.outer._connection_lost.set()
                self.on_close()
            def on_event(self, result: RecognitionResult) -> None:
                sentence = result.get_sentence()
                if 'text' in sentence and RecognitionResult.is_sentence_end(sentence):
                    user_text = sentence['text']
                    logger.info(f"识别到你说: {user_text}")
                    if self.outer.on_sentence_end_callback:
                        self.outer.on_sentence_end_callback(user_text)
        
        self.callback = ASRCallback(self)
        self.recognition = Recognition(
            model=config.ASR_MODEL,
            format=config.FORMAT_PCM,
            sample_rate=config.SAMPLE_RATE,
            callback=self.callback
        )

    def start_session(self):
        self.recognition.start()
        logger.info("ASR会话已启动。")

    def run_audio_loop(self):
        """运行音频发送循环，直到连接断开，并增加了VAD逻辑。"""
        
        # --- VAD 逻辑初始化 ---
        last_speech_time = time.time()
        
        while self._is_running and not self._connection_lost.is_set():
            try:
                if self.stream and not self.stream.is_stopped():
                    data = self.stream.read(config.BLOCK_SIZE, exception_on_overflow=False)
                    
                    # --- VAD 核心计算 ---
                    # 将字节数据转换为numpy数组
                    audio_data = np.frombuffer(data, dtype=np.int16)
                    # 计算音量（RMS能量）
                    if audio_data.size > 0:
                        # 先将数据转为64位浮点数再计算，避免整数平方溢出问题
                        audio_data_fp = audio_data.astype(np.float64)
                        # 计算音量（RMS能量）
                        energy = np.sqrt(np.mean(audio_data_fp**2))
                        # logger.debug(f"当前音频能量: {energy:.2f}")  # 注释掉频繁的调试信息
                    else:
                        # 如果音频块为空，则能量为0
                        energy = 0
                    
                    # --- VAD 判断逻辑 ---
                    if energy > config.VAD_ENERGY_THRESHOLD:
                        # 检测到语音，更新说话时间，并发送数据
                        last_speech_time = time.time()
                        self.recognition.send_audio_frame(data)
                    else:
                        # 处于静默状态
                        self.recognition.send_audio_frame(data) # 即使静默也发送数据，让服务端处理
                        if time.time() - last_speech_time > config.SILENCE_TIMEOUT_SECONDS:
                            logger.info(f"检测到超过 {config.SILENCE_TIMEOUT_SECONDS} 秒的持续静默，将主动重置连接以保持活性...")
                            self.stop() # 主动停止
                            break # 退出循环，让守护进程接管

                else:
                    break 
            except (IOError, OSError) as e:
                logger.error(f"音频读取错误: {e}")
                self._connection_lost.set()
                break
    
    def stop(self):
        """外部调用的停止方法。"""
        if self._is_running:
            self._is_running = False
            self._connection_lost.set() # 发送停止信号
            if self.recognition:
                self.recognition.stop()
