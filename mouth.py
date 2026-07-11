import os
import random
import json
import requests
import subprocess
import threading
import time
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

VOICEVOX_URL = os.environ.get("VOICEVOX_URL", "http://localhost:50021")
AUDIO_DEVICE = os.environ.get("AUDIO_DEVICE", "plughw:2,0")
SPEAKER_ID = int(os.environ.get("VOICEVOX_SPEAKER_ID", "48"))
REPLY_WAV_PATH = "reply.wav"
FILLERS = list(Path("sounds/fillers").glob("*.wav"))

class ThinkingVoicePlayer:
    def __init__(self):
        self._stop_event = threading.Event()
        self._thread = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._loop,
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()

        if self._thread:
            self._thread.join()

    def _loop(self):
        while not self._stop_event.is_set():

            path = random.choice(FILLERS)

            subprocess.run(
                ["aplay", "-D", AUDIO_DEVICE, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            time.sleep(3)

            if self._stop_event.is_set():
                return

thinking_player = ThinkingVoicePlayer()

def start_thinking_voice():
    thinking_player.start()

def stop_thinking_voice():
    thinking_player.stop()

def speak(text: str):
    try:
        _create_voice(text)
        _play(REPLY_WAV_PATH, wait=True)

    except Exception as e:
        print("❌ VOICEVOX連携エラー")
        print(type(e))
        print(e)

def hello():
    print("こんにちは。今日はどんなおしゃべりする？")
    _play("sounds/hello.wav", wait=True)

def say_good_bye() -> None:
    print("またおしゃべりしようね。ばいばい！")
    _play("sounds/matane.wav", wait=True)

def _play(path: str, wait: bool = True):
    command = ["aplay", "-D", AUDIO_DEVICE, path]

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
