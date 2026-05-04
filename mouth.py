import os
import requests
import json
import random
import subprocess
import time
import config

def speak(text):
    url = config.VOICEVOX_URL
    speaker_id = 48
    
    try:
        res1 = requests.post(
            f"{url}/audio_query",
            params={"text": text, "speaker": speaker_id}
        )
        query = res1.json()

        res2 = requests.post(
            f"{url}/synthesis",
            params={"speaker": speaker_id},
            data=json.dumps(query)
        )
        
        with open("reply.wav", "wb") as f:
            f.write(res2.content)
            
        os.system("aplay -D plughw:1,0 reply.wav")
        
    except Exception as e:
        print(f"❌ VOICEVOX連携エラー: {e}")

# 繋ぎ
def play_filler():
    fillers = ["untone.wav", "ettone.wav", "anone.wav", "eto.wav", "soudana.wav", "soudane.wav"]
    target = random.choice(fillers)
    subprocess.Popen(["aplay", "-D", "plughw:1,0", f"sounds/{target}"])

# 最初の挨拶
def hello():
    text = "こんにちは。今日はどんなおしゃべりする？"
    print(text)
    subprocess.Popen(["aplay", "-D", "plughw:1,0", "sounds/hello.wav"])

# お別れの挨拶 
def good_by(text):
    exit_keywords = ["またね", "ばいばい", "バイバイ", "おやすみ", "さよなら", "さようなら"]
            
    if any(word in text for word in exit_keywords):
            text = "またおしゃべりしようね、ばいばい！"
            print(text)
            subprocess.Popen(["aplay", "-D", "plughw:1,0", "sounds/matane.wav"])
            # 少し余韻を置いてから終了
            time.sleep(1)
            return True
    else:
        return False

