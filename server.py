from flask import Flask, request, jsonify
from flask_cors import CORS
import cohere
import csv
import io
from flask_socketio import SocketIO, emit
import sqlite3
from chat_prompts import *
import os
import logging
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app)

# 启用CORS
CORS(app, resources={r"/chat": {"origins": "http://172.18.170.54:8080"}})

# 从环境变量中读取API Key
COHERE_API_KEY = os.getenv('COHERE_API_KEY')
co = cohere.ClientV2("P3ROmZfQlTu1Cp8A3Eom1bWrnVgWZFDhNl92WTah")

# 连接到 SQLite 数据库（如果不存在则会创建）
conn = sqlite3.connect('results.db')
cursor = conn.cursor()

# 创建表
cursor.execute('''
CREATE TABLE IF NOT EXISTS results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taskid INTEGER,
    prompt TEXT,
    response TEXT
)
''')

# 提交更改
conn.commit()

# 配置日志记录器
log_dir = 'logs'
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', 'command-r-plus-08-2024')
    system_prompt_pose_code = prompt_pc

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
            # 插入数据库
            task_id = insert_task(prompt, content)
            socketio.emit('update_results', {'results': get_all_results()})
            logging.info(f"Task ID: {task_id}, Prompt: {prompt}, Response: {content}")
            return jsonify({'response': content})
        else:
            return jsonify({'error': 'Invalid response from Cohere API'}), 500
    except Exception as e:
        logging.error(f"Error in /chat: {str(e)}")
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

@app.route('/generate_pose', methods=['POST'])
def generate_pose():
    data = request.get_json()
    prompt = data.get('prompt')
    model = data.get('model', 'command-r-plus-08-2024')
    
    # 系统提示暂时留空
    system_prompt = ''

    # 先添加一个条目到数据库中
    task_id = insert_task(prompt, 'Processing...')
    socketio.emit('update_results', {'results': get_all_results()})
    logging.info(f"Task ID: {task_id}, Prompt: {prompt}, Status: Processing...")

    try:
        response = co.chat(
            model=model,
            messages=[
                {
                    'role': 'system',
                    'content': system_prompt,
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
            # 更新数据库中的内容
            update_task(task_id, content)
            socketio.emit('update_results', {'results': get_all_results()})
            logging.info(f"Task ID: {task_id}, Prompt: {prompt}, Response: {content}")
            return jsonify({'response': content})
        else:
            return jsonify({'error': 'Invalid response from Cohere API'}), 500
    except Exception as e:
        logging.error(f"Error in /generate_pose: {str(e)}")
        return jsonify({'error': str(e)}), 500

def get_all_results():
    cursor.execute('SELECT * FROM results')
    rows = cursor.fetchall()
    results = [{'taskid': row[1], 'prompt': row[2], 'response': row[3]} for row in rows]
    return results

def insert_task(prompt, response):
    cursor.execute('INSERT INTO results (prompt, response) VALUES (?, ?)', (prompt, response))
    conn.commit()
    return cursor.lastrowid

def update_task(task_id, response):
    cursor.execute('UPDATE results SET response = ? WHERE taskid = ?', (response, task_id))
    conn.commit()

@app.route('/get_recent_result', methods=['GET'])
def get_recent_result():
    # 查询最近的10条记录
    cursor.execute('SELECT * FROM results ORDER BY id DESC LIMIT 10')
    rows = cursor.fetchall()
    
    # 将查询结果转换为字典列表
    results = [{'taskid': row[1], 'prompt': row[2], 'response': row[3]} for row in rows]
    
    # 返回结果
    return jsonify({'results': results})

# 需要解决的问题：
# 1. LLM生成的旋转方向不合理：先生成pose analysis text， 然后生成相对于身体坐标的旋转指令，最后翻译成世界坐标的旋转指令
# 2. 移动手、脚IK似乎很难实现
def IK_predictor():
    pass

if __name__ == '__main__':
    socketio.run(app, debug=True)