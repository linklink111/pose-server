# 一个用来直接测试 generate pose 的文件

from generate_pose import *

import os

import os
import json

def sample1_plan_generate_scheme():
    motion_prompt = "A person plays the violin."
    
    # 确保output文件夹存在
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    # 基础文件名
    base_filename = motion_prompt.replace(" ", "_").replace(":", "_").replace("/", "_")
    
    # 获取已有文件数量
    existing_files = [f for f in os.listdir(output_dir) if f.startswith(base_filename) and f.endswith(".txt")]
    new_file_number = len(existing_files) + 1
    output_file = os.path.join(output_dir, f"{base_filename}_{new_file_number}.txt")
    
    # 写入文件
    with open(output_file, "w", encoding="utf-8") as file:
        scheme = plan_generation_scheme(motion_prompt)
        file.write("====================================\n")
        file.write("Generation scheme:\n")
        file.write("====================================\n")
        file.write(f"{scheme}\n")
        
        transform_for_whole_body = plan_transform_for_whole_body(motion_prompt)
        file.write("====================================\n")
        file.write("Transform for whole body:\n")
        file.write("====================================\n")
        file.write(f"{transform_for_whole_body}\n")
        
        pose_design = generate_pose_design(motion_prompt, body_transform=transform_for_whole_body)
        file.write("====================================\n")
        file.write("Pose design:\n")
        file.write("====================================\n")
        file.write(f"{pose_design}\n")
        
        reviewed_pose_design = review_pose_design(pose_design)
        file.write("====================================\n")
        file.write("Reviewed pose design:\n")
        file.write("====================================\n")
        file.write(f"{reviewed_pose_design}\n")

    print(f"Output written to: {output_file}")
    
    # 写入 JSON 文件
    json_file = os.path.join(output_dir, f"{base_filename}_{new_file_number}_reviewed_pose.json")
    with open(json_file, "w", encoding="utf-8") as json_out:
        json_out.write(reviewed_pose_design)  # 直接写入字符串

    print(f"Reviewed pose design written to: {json_file}")



if __name__ == "__main__":
    sample1_plan_generate_scheme()