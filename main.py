import time
import sys

import brain
import ears
import mouth

EXIT_KEYWORDS = [
    "またね",
    "ばいばい",
    "バイバイ",
    "おやすみ",
    "さよなら",
    "さようなら",
]

def should_exit(text: str) -> bool:
    return any(keyword in text for keyword in EXIT_KEYWORDS)

def main() -> None:
    print("------------------------------------------")
    print("   とりのこ システム 起動完了（音声対話モード）")
    print("   終了するには Ctrl + C を押してください")
    print("------------------------------------------")

    mouth.hello()

    print("システムが安定するまで少しお待ちください...")
    time.sleep(3)

    try:
        while True:
            user_voice = ears.listen()

            if not user_voice:
                continue

            print(f"文鳥: {user_voice}")

            if should_exit(user_voice):
                mouth.say_good_bye()
                break

            print("なの：考え中...")
            response_text = brain.generate_response(user_voice)

            mouth.speak(response_text)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print()
        mouth.say_good_bye()

if __name__ == "__main__":
    main()
