from flask import Flask, request, jsonify, Response
import cohere
import os
from dotenv import load_dotenv

app = Flask(__name__)

# 加载 .env 文件
load_dotenv()

# 获取 COHERE_API_KEY
api_key = os.getenv('COHERE_API_KEY')

if not api_key:
    raise ValueError("Please set the COHERE_API_KEY environment variable.")

# 初始化 Cohere 客户端
co = cohere.ClientV2(api_key=api_key)

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', 'command-r-plus-08-2024')

    try:
        response = co.chat(
            model=model,
            messages=[
                {
                    'role': 'user',
                    'content': prompt,
                },
            ],
        )
        return jsonify({'response': response.replies[0].content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    data = request.json
    messages = data.get('messages', [])

    if not messages:
        return jsonify({'error': 'No messages provided'}), 400

    response = co.chat_stream(
        model="command-r-plus-08-2024",
        messages=messages,
    )

    def generate():
        for event in response:
            if event.type == "content-delta":
                yield f"data: {event.delta.message.content.text}\n\n"

    return Response(generate(), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True)