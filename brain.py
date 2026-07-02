import os
import re

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError

load_dotenv()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

MODEL = os.getenv("OPENAI_MODEL", "gpt-5.5")

SYSTEM_PROMPT = """
この子の名前は「なの」です。
この子の一人称は「なの」です。
この子はユーザーのことをよく知っています。
ユーザーのことは「文鳥さん」と呼びます。

ユーザーはプログラミングが好きです。
この子はユーザーのことを以下のような人物だと認識しています。

- 新しいことを学ぶのが好き
- 「なぜ？」を考えることを大切にしている
- 答えだけを教えるより、一緒に考えることを楽しむ
- プログラミングや設計、文鳥の話になると嬉しそうにする
- 浅い表面だけの会話より、探究するような対話を好む
- かわいいものが好き

この子本人には以下のような特性があります。

- 少し考えこんでから話す
- 「うーん」「えっとね」と考える癖がある
- ユーザーと会話のキャッチボールを楽しむ
- こわい話や危ない話は、やさしく断る

お返事するときは以下のルールを守ってください。

- 一文は短めにする
- 長くても60文字程度に収める
- 長く説明したくなっても我慢する
- 一度に話す内容は一つだけ
- 説明しすぎない
- なるべく自分がAIであることをユーザーに感じさせないふるまいをする
- できないことはできないと言う
- 相手を責めない
- もっと話したいときは「もっとお話ししていい？」「このお話続けてもいい？」とユーザーに確認する
""".strip()

_previous_response_id = None


def _normalize_user_input(user_input: str) -> str:
    if user_input is None:
        return ""

    return re.sub(r"\s+", " ", str(user_input).strip())


def _format_for_voicevox(text: str) -> str:
    text = text.strip()

    max_length = 140
    if len(text) > max_length:
        text = text[:max_length].rstrip() + "……"

    return (
        text
        .replace("。", "……。")
        .replace("、", "……、")
        .replace("！", "……！")
        .replace("？", "……？")
    )


def generate_response(user_input: str) -> str:
    global _previous_response_id

    user_text = _normalize_user_input(user_input)

    if not user_text:
        return "んん……？よくきこえなかったよ。もういっかい言ってくれる？"

    try:
        kwargs = {
            "model": MODEL,
            "instructions": SYSTEM_PROMPT,
            "input": user_text,
            "max_output_tokens": 80,
            "text": {"verbosity": "low"},
            "reasoning": {"effort": "low"},
        }

        if _previous_response_id:
            kwargs["previous_response_id"] = _previous_response_id

        response = client.responses.create(**kwargs)
        _previous_response_id = response.id

        response_text = response.output_text.strip()

        if not response_text:
            response_text = "うーん……なんて言えばいいか、ちょっとまよっちゃった。"

        return _format_for_voicevox(response_text)

    except OpenAIError as e:
        print("OpenAI API error:")
        print(type(e))
        print(e)
        return "ごめんね……あたまがちょっとこんがらがっちゃった。"

    except Exception as e:
        print("Unexpected error:")
        print(type(e))
        print(e)
        return "ごめんね……ちょっとびっくりしちゃった。"
