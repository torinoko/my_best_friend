import time

import brain
import ears
import mouth


def main():
    print("------------------------------------------")
    print("   とりのこ システム 起動完了 (音声対話モード)")
    print("   終了するには Ctrl + C を押してください")
    print("------------------------------------------")

    print("システムが安定するまで少しお待ちください...")
    time.sleep(2)

    mouth.hello()

    try:
        while True:
            user_voice = ears.listen()

            if not user_voice:
                continue

            print(f"文鳥: {user_voice}")

            if mouth.good_bye_if_needed(user_voice):
                break

            print("なの：考え中...")
            mouth.think_once()

            response_text = brain.generate_response(user_voice)

            print(f"なの：{response_text}")
            mouth.speak(response_text)

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nまたおしゃべりしようね。ばいばい！")

if __name__ == "__main__":
    main()
