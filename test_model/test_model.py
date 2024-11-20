from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

DUMMY_MODEL = "gpt-4o-mini"
DUMMY_PROMPT = "You are a helpful Language Model"


@app.route("/", methods=["POST"])
def generate_text():
    data = request.get_json()
    input = data.get("input", "")

    try:
        dummy_api_client = OpenAI()
        completion = dummy_api_client.chat.completions.create(
            model=DUMMY_MODEL,
            messages=[
                {"role": "system", "content": DUMMY_PROMPT},
                {
                    "role": "user",
                    "content": input,
                },
            ],
        )
        student_answer = completion.choices[0].message.content
        return jsonify({"output": student_answer})

    except Exception as e:
        return jsonify({"output": f"System Error: {str(e)}"}), 500


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8888)
