from flask import Flask, request, jsonify
import cohere

app = Flask(__name__)

# 从环境变量中读取API Key
import os
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
print(COHERE_API_KEY)
co = cohere.ClientV2(api_key='qekr0Tz4a4jxbxzY3EMTKkfPlXDQSiyDkBHGweFx')

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

if __name__ == '__main__':
    app.run(debug=True)