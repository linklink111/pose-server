from flask import Flask, request, jsonify
from flask_cors import CORS
import cohere
import csv
import io

app = Flask(__name__)

# 启用CORS
CORS(app, resources={r"/chat": {"origins": "http://172.18.170.54:8080"}})

# 从环境变量中读取API Key
import os
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
co = cohere.ClientV2("P3ROmZfQlTu1Cp8A3Eom1bWrnVgWZFDhNl92WTah")

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', 'command-r-plus-08-2024')
    system_prompt_pose_code = '''
        I'm a helpful assistant capable of generating code to create specific poses based on user input.

        The generated pose code consists of a series of commands, each formatted as follows:

        operation, bone_name, direction, angle
        For example:

        rotate, mixamorig1LeftArm, x, 60
        rotate, mixamorig1RightArm, x, 60
        rotate, mixamorig1Head, x, 60
        ...
        Please write each command on a separate line.

        Breakdown of the command components:

        Operation: Currently, only rotate is supported.
        Bone Name: Specifies the target bone for the rotation. Available bone names include:
        mixamorig1RightArm, mixamorig1RightForeArm, mixamorig1Head, mixamorig1RightHand, mixamorig1RightShoulder, mixamorig1Hips, mixamorig1Spine, mixamorig1Spine1, mixamorig1Spine2, mixamorig1UpLeg, mixamorig1Leg, mixamorig1Foot
        (Left-side equivalents are also available.)
        Direction: Indicates the axis of rotation.  Options are x, y, and z.
        Angle: Defines the degree of rotation.
    '''

    try:
        response = co.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt_pose_code,
                },
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

@app.route('/analyze_skeleton', methods=['POST'])
def analyze_skeleton():
    data = request.get_json()
    bone_names = data.get('bone_names')
    
    if not bone_names:
        return jsonify({'error': 'No bone names provided'}), 400

    # 模拟分析过程，实际应用中应调用LLM或其他分析工具
    # 这里假设返回一个简单的CSV文本
    csv_data = [
        ['common_name', 'bone_name'],
        ['Head', 'mixamorig1Head'],
        ['Left Arm', 'mixamorig1LeftArm'],
        ['Right Arm', 'mixamorig1RightArm'],
        # 添加更多映射关系
    ]

    # 将CSV数据转换为字符串
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(csv_data)
    csv_text = output.getvalue()

    return jsonify({'csv_text': csv_text})

# 需要解决的问题：
# 1. LLM生成的旋转方向不合理：先生成pose analysis text， 然后生成相对于身体坐标的旋转指令，最后翻译成世界坐标的旋转指令
# 2. 移动手、脚IK似乎很难实现
def IK_predictor():
    pass

if __name__ == '__main__':
    app.run(debug=True)