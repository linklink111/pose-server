import requests

# 设置接口 URL
BASE_URL = "http://127.0.0.1:5000/api/post_generate_pose_design"

# 测试数据
test_payload = {
    "user_prompt": "Design a dynamic dance pose with a cheerful vibe."
}

def test_post_generate_pose_design():
    try:
        # 发送 POST 请求
        response = requests.post(BASE_URL, json=test_payload)
        
        # 检查响应状态码
        if response.status_code == 201:
            print("✅ Test Passed!")
            print("Response Data:", response.json())
        else:
            print("❌ Test Failed!")
            print(f"Status Code: {response.status_code}")
            print("Response:", response.json())
    except Exception as e:
        print("❌ Test Failed with Exception!")
        print(str(e))

if __name__ == "__main__":
    test_post_generate_pose_design()
