from flask import Flask, jsonify, request
from generate_pose import generate_pose_design, generate_pose_code, generate_pose_code_batch  # 从 generate_pose.py 导入函数

app = Flask(__name__)

@app.route('/api/post_generate_pose_design', methods=['POST'])
def post_generate_pose_design():
    try:
        # 从请求中获取 `user_prompt`
        request_data = request.json
        if not request_data or 'user_prompt' not in request_data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameter 'user_prompt'."
            }), 400
        
        user_prompt = request_data['user_prompt']
        print(user_prompt)
        
        # 调用 `generate_pose_design` 函数
        result = generate_pose_design(user_prompt)
        
        return jsonify({
            "status": "success",
            "message": "Pose design generated successfully.",
            "data": result
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/api/post_generate_pose_code', methods=['POST'])
def post_generate_pose_code():
    try:
        # 从请求中获取 `pose_description`
        request_data = request.json
        if not request_data or 'pose_description' not in request_data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameter 'pose_description'."
            }), 400
        time = request_data['time']
        pose_description = request_data['pose_description']
        body_world_pos = request_data['body_world_pos']
        print(pose_description)

        # 调用 `generate_pose_code` 函数
        result = generate_pose_code(time, pose_description,body_world_pos)

        return jsonify({
            "status": "success",
            "message": "Pose code generated successfully.",
            "data": result
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@app.route('/api/post_generate_pose_code_batch', methods=['POST'])
def post_generate_pose_code_batch():
    try:
        # 从请求中获取 `time_and_pose_description` 和 `body_world_pos`
        request_data = request.json
        if not request_data or 'time_and_pose_description' not in request_data or 'body_world_pos' not in request_data:
            return jsonify({
                "status": "error",
                "message": "Missing required parameters 'time_and_pose_description' and/or 'body_world_pos'."
            }), 400
        
        time_and_pose_description = request_data['time_and_pose_description']
        body_world_pos = request_data['body_world_pos']
        
        # 调用 `generate_pose_code_batch` 函数
        results = generate_pose_code_batch(time_and_pose_description, body_world_pos)
        
        return jsonify({
            "status": "success",
            "message": "Pose codes generated successfully.",
            "data": results
        }), 201
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True)
