import os
from flask import Flask, request, jsonify
from openai import OpenAI

# Initialize Flask
app = Flask(__name__)

# OpenAI client (make sure OPENAI_API_KEY is set in environment)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_prompt(user_input: str) -> str:
    """
    Build prompt safely using triple quotes (properly closed).
    """
    text_prompt = f"""
You are a helpful AI assistant.

User message:
{user_input}

Respond clearly and concisely.
"""
    return text_prompt


@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "Agent running"})


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        user_input = data.get("message", "")

        prompt = build_prompt(user_input)

        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )

        reply = response.output[0].content[0].text

        return jsonify({
            "reply": reply
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
