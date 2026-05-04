import brain
import mouth
import ears
import time

def main():
    print("------------------------------------------")
    print("   とりのこ システム 起動完了 (音声対話モード)")
    print("   エンターキーを押すと聞き取りを開始します")
    print("   終了するには Ctrl + C を押してください")
    print("------------------------------------------")

    print("システムが安定するまで少しお待ちください...")
    time.sleep(2)
    mouth.hello()

    try:
        while True:
            user_voice = ears.listen()

            if user_voice:
                print(f"文鳥: {user_voice}")
                
                ret = mouth.good_by(user_voice)
                if ret:
                    break
        
                print("なの：考え中...")
                response_text = brain.generate_response(user_voice)

                print(f"なの：{response_text}")

                mouth.speak(response_text)

                time.sleep(0.5)
            else:
                continue

    except KeyboardInterrupt:
        print("\nまたおしゃべりしようね。ばいばい！")

if __name__ == "__main__":
    main()

