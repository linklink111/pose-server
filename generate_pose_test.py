# 一个用来直接测试 generate pose 的文件

from generate_pose import *

def sample1_plan_generate_scheme():
    pose_prompt = "A person is petting a cat."
    result = plan_generation_scheme(pose_prompt)
    print(result)

if __name__ == "__main__":
    sample1_plan_generate_scheme()