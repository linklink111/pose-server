from flask import Flask, request, jsonify
from flask_cors import CORS
import cohere

app = Flask(__name__)

# 启用CORS
CORS(app, resources={r"/chat": {"origins": "http://172.18.170.54:8080"}})

# 从环境变量中读取API Key
import os
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
co = cohere.ClientV2(COHERE_API_KEY)

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

        # 解析Cohere API的响应
        if response.message and response.message.content:
            content = response.message.content[0].text
            return jsonify({'response': content})
        else:
            return jsonify({'error': 'Invalid response from Cohere API'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)