import json
import os
import random
import subprocess
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE", "plughw:2,0")
SPEAKER_ID = int(os.environ.get("VOICEVOX_SPEAKER_ID", "48"))
VOICEVOX_VOLUME_SCALE = float(os.environ.get("VOICEVOX_VOLUME_SCALE", "2.0"))
REPLY_WAV_PATH = "reply.wav"
FILLERS = list(Path("sounds/fillers").glob("*.wav"))


EXIT_KEYWORDS = [
    "またね",
    "ばいばい",
    "バイバイ",
    "おやすみ",
    "さよなら",
    "さようなら",
]

THINKING_SOUNDS = [
    "sounds/soudana.wav",
    "sounds/soudane.wav",
]

def _play(path: str, wait: bool = True):
    command = ["aplay", "-D", AUDIO_DEVICE, str(random.choice(FILLERS))]

    if wait:
        subprocess.run(command, check=False)
    else:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

def _create_voice(text: str, output_path: str = REPLY_WAV_PATH):
    query_response = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={"text": text, "speaker": SPEAKER_ID},
        timeout=10,
    )
    query_response.raise_for_status()

    query = query_response.json()
    query["volumeScale"] = VOICEVOX_VOLUME_SCALE

    synthesis_response = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={"speaker": SPEAKER_ID},
        headers={"Content-Type": "application/json"},
        data=json.dumps(query),
        timeout=30,
    )
    synthesis_response.raise_for_status()

    with open(output_path, "wb") as f:
        f.write(synthesis_response.content)

def speak(text: str):
    try:
        _create_voice(text)
        print("🔊 再生します:", text)
        _play(REPLY_WAV_PATH, wait=True)

    except Exception as e:
        print("❌ VOICEVOX連携エラー")
        print(type(e))
        print(e)

def think_once():
    """考え中の一言を一回だけ再生する。"""
    path = random.choice(THINKING_SOUNDS)
    _play(path, wait=True)

def hello():
    print("こんにちは。今日はどんなおしゃべりする？")
    _play("sounds/hello.wav", wait=True)


def good_bye_if_needed(text: str) -> bool:
    if not any(word in text for word in EXIT_KEYWORDS):
        return False

    print("またおしゃべりしようね、ばいばい！")
    _play("sounds/matane.wav", wait=True)
    time.sleep(1)

    return True
