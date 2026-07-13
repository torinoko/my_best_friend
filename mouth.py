import os
import random
import re
import subprocess
import threading
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# パス

BASE_DIR = Path(__file__).resolve().parent
SOUNDS_DIR = BASE_DIR / "sounds"
FILLERS_DIR = SOUNDS_DIR / "fillers"

HELLO_WAV_PATH = SOUNDS_DIR / "hello.wav"
GOOD_BYE_WAV_PATH = SOUNDS_DIR / "matane.wav"
REPLY_WAV_PATH = BASE_DIR / "reply.wav"

# 設定

VOICEVOX_URL = os.getenv("VOICEVOX_URL", "http://localhost:50021")

AUDIO_DEVICE = os.getenv(
    "AUDIO_DEVICE",
    "plughw:CARD=seeed2micvoicec,DEV=0",
)

SPEAKER_ID = int(
    os.getenv("VOICEVOX_SPEAKER_ID", "48")
)

VOICEVOX_VOLUME_SCALE = float(
    os.getenv("VOICEVOX_VOLUME_SCALE", "1.0")
)

SPEECH_CHUNK_MAX_LENGTH = int(
    os.getenv("SPEECH_CHUNK_MAX_LENGTH", "70")
)

FILLER_INTERVAL_SECONDS = float(
    os.getenv("FILLER_INTERVAL_SECONDS", "3.0")
)

# 共有状態
# 複数の aplay が同時に音声デバイスを使用しないようにする
_audio_lock = threading.Lock()

# 音声ファイル再生

def _play(path: Path | str, wait: bool = True) -> None:
    audio_path = Path(path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"音声ファイルが見つかりません: {audio_path}"
        )

    command = [
        "aplay",
        "-D",
        AUDIO_DEVICE,
        str(audio_path),
    ]

    if not wait:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return

    with _audio_lock:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
        )

    if result.returncode != 0:
        error_message = result.stderr.strip()

        raise RuntimeError(
            f"音声の再生に失敗しました: {audio_path}\n"
            f"終了コード: {result.returncode}\n"
            f"{error_message}"
        )


# VOICEVOX

def _create_voice(
    text: str,
    output_path: Path | str = REPLY_WAV_PATH,
) -> None:
    if not text.strip():
        raise ValueError("読み上げる文章が空です。")

    query_response = requests.post(
        f"{VOICEVOX_URL}/audio_query",
        params={
            "text": text,
            "speaker": SPEAKER_ID,
        },
        timeout=10,
    )
    query_response.raise_for_status()

    audio_query = query_response.json()
    audio_query["volumeScale"] = VOICEVOX_VOLUME_SCALE

    synthesis_response = requests.post(
        f"{VOICEVOX_URL}/synthesis",
        params={
            "speaker": SPEAKER_ID,
        },
        json=audio_query,
        timeout=30,
    )
    synthesis_response.raise_for_status()

    Path(output_path).write_bytes(
        synthesis_response.content
    )


def _split_for_speech(
    text: str,
    max_length: int = SPEECH_CHUNK_MAX_LENGTH,
) -> list[str]:
    normalized_text = re.sub(
        r"\s+",
        " ",
        text.strip(),
    )

    if not normalized_text:
        return []

    sentences = re.findall(
        r".+?[。！？!?]|.+$",
        normalized_text,
    )

    chunks: list[str] = []
    current_chunk = ""

    for sentence in sentences:
        sentence = sentence.strip()

        if not sentence:
            continue

        if len(sentence) > max_length:
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""

            chunks.extend(
                _split_long_sentence(
                    sentence,
                    max_length=max_length,
                )
            )
            continue

        if not current_chunk:
            current_chunk = sentence
            continue

        if len(current_chunk) + len(sentence) <= max_length:
            current_chunk += sentence
        else:
            chunks.append(current_chunk)
            current_chunk = sentence

    if current_chunk:
        chunks.append(current_chunk)

    return chunks

def _split_long_sentence(
    sentence: str,
    max_length: int,
) -> list[str]:
    parts = re.findall(
        r".+?[、,]|.+$",
        sentence,
    )

    chunks: list[str] = []
    current_chunk = ""

    for part in parts:
        part = part.strip()

        if not part:
            continue

        if not current_chunk:
            current_chunk = part
            continue

        if len(current_chunk) + len(part) <= max_length:
            current_chunk += part
        else:
            chunks.append(current_chunk)
            current_chunk = part

    if current_chunk:
        chunks.append(current_chunk)

    # 読点もない非常に長い文字列への最終的な安全策
    safe_chunks: list[str] = []

    for chunk in chunks:
        if len(chunk) <= max_length:
            safe_chunks.append(chunk)
            continue

        for index in range(0, len(chunk), max_length):
            safe_chunks.append(
                chunk[index:index + max_length]
            )

    return safe_chunks


def _speak_chunk(text: str) -> None:
    _create_voice(
        text=text,
        output_path=REPLY_WAV_PATH,
    )

    _play(
        REPLY_WAV_PATH,
        wait=True,
    )


def speak(text: str) -> None:
    chunks = _split_for_speech(text)

    if not chunks:
        print("⚠️ 読み上げる文章がありません。")
        return

    try:
        for chunk in chunks:
            print(f"🔊 なの：{chunk}")
            _speak_chunk(chunk)

    except requests.RequestException as error:
        print("❌ VOICEVOXとの通信に失敗しました。")
        print(type(error))
        print(error)

    except Exception as error:
        print("❌ 音声生成または再生に失敗しました。")
        print(type(error))
        print(error)

# 考え中ボイス

class ThinkingVoicePlayer:
    def __init__(
        self,
        fillers_dir: Path = FILLERS_DIR,
        interval_seconds: float = FILLER_INTERVAL_SECONDS,
    ) -> None:
        self._fillers_dir = fillers_dir
        self._interval_seconds = interval_seconds

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        fillers = self._load_fillers()

        if not fillers:
            print(
                "⚠️ sounds/fillers 以下に"
                "WAVファイルがありません。"
            )
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            args=(fillers,),
            daemon=True,
            name="thinking-voice-player",
        )

        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join()

        self._thread = None

    def _load_fillers(self) -> list[Path]:
        if not self._fillers_dir.exists():
            return []

        return sorted(
            self._fillers_dir.glob("*.wav")
        )

    def _run(self, fillers: list[Path]) -> None:
        previous_path: Path | None = None

        while not self._stop_event.is_set():
            candidates = [
                path
                for path in fillers
                if path != previous_path
            ]

            if not candidates:
                candidates = fillers

            selected_path = random.choice(candidates)
            previous_path = selected_path

            try:
                _play(
                    selected_path,
                    wait=True,
                )

            except Exception as error:
                print("⚠️ 考え中ボイスの再生に失敗しました。")
                print(type(error))
                print(error)
                return

            if self._stop_event.wait(
                self._interval_seconds
            ):
                return

_thinking_player = ThinkingVoicePlayer()

def start_thinking_voice() -> None:
    _thinking_player.start()

def stop_thinking_voice() -> None:
    _thinking_player.stop()

# 定型音声

def hello() -> None:
    print("なの：こんにちは。今日はどんなおしゃべりする？")

    try:
        _play(
            HELLO_WAV_PATH,
            wait=True,
        )

    except Exception as error:
        print("❌ 起動時の挨拶を再生できませんでした。")
        print(type(error))
        print(error)


def say_good_bye() -> None:
    print("またおしゃべりしようね。ばいばい！")

    try:
        _play(
            GOOD_BYE_WAV_PATH,
            wait=True,
        )

    except Exception as error:
        print("❌ 終了時の挨拶を再生できませんでした。")
        print(type(error))
        print(error)