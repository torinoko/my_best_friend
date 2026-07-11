import os
import pyaudio
import wave
import struct
import math
from groq import Groq

def record_audio(filename="input.wav", silence_limit=1.0):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 2
    RATE = 16000
    DEVICE_INDEX = 0

    THRESHOLD = 300
    CHUNKS_TO_START = 2
    DEVICE_ADDRESS = 'hw:0,0'

    p = pyaudio.PyAudio()

    target_index = None
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if DEVICE_ADDRESS in info.get('name'):
            target_index = i
            break

    # もし見つからなければ、名前の一部 "seeed" で探す
    if target_index is None:
        for i in range(p.get_device_count()):
            if "seeed" in p.get_device_info_by_index(i).get('name'):
                target_index = i
                break

    try:
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            input_device_index=DEVICE_INDEX,
            frames_per_buffer=CHUNK
        )
    except Exception as e:
        print(f"⚠️ 指定デバイス(Index:{DEVICE_INDEX})で失敗しました。デフォルトを使います: {e}")
        stream = p.open(
            format=FORMAT,
            channels=CHANNELS,
            rate=RATE,
            input=True,
            frames_per_buffer=CHUNK
        )
    
    print("👂 聞いてるよ...（お話ししてね）")
    
    frames = []
    silent_chunks = 0
    limit_chunks = int(silence_limit * RATE / CHUNK)
    has_started_talking = False 
    trigger_chunks = 0

    while True:
        data = stream.read(CHUNK, exception_on_overflow=False)
        
        count = len(data) // 2
        shorts = struct.unpack("%dh" % count, data)
        sum_squares = sum(s**2 for s in shorts)
        rms = math.sqrt(sum_squares / count) if count > 0 else 0
        #print(f"rms: {rms}")

        if not has_started_talking:
            if rms > THRESHOLD:
                trigger_chunks += 1
                if trigger_chunks >= CHUNKS_TO_START:
                    has_started_talking = True
                    print("▶️ はい、聞こえたなの！")
                    frames.append(data)
            else:
                trigger_chunks = 0
                continue
        else:
            frames.append(data)
            if rms > THRESHOLD:
                silent_chunks = 0
            else:
                silent_chunks += 1
                if silent_chunks > limit_chunks:
                    print("⏹️ ちょっと待ってね……")
                    break

    stream.stop_stream()
    stream.close()
    p.terminate()

    if len(frames) == 0:
        return False

    wf = wave.open(filename, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()
    return True

def listen(filename="input.wav"):
    """ Groq APIで文字起こし """
    if not record_audio(filename):
        return ""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    try:
        with open(filename, "rb") as f:
            transcription = client.audio.transcriptions.create(
                file=(filename, f.read()),
                model="whisper-large-v3",
                language="ja"
            )
        return transcription.text
    except Exception as e:
        print(f"❌ 文字起こしエラー: {e}")
        return ""
