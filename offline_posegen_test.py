import cohere
import os

co = cohere.ClientV2("P3ROmZfQlTu1Cp8A3Eom1bWrnVgWZFDhNl92WTah")

def generate_pose_description_streaming(user_prompt):
    system_prompt = """
    You are a helpful assistant, you can tell how to move each joint of a human armature to make a pose adhere to user prompt. 
    You may move the following parts if necessary: left hand, right hand, left foot, right foot, hips, left knee, right knee, left elbow, right elbow. 
    If a body part does not need to be moved, it will stay in the default T-pose position. Only list the parts that need to be moved or rotated.
    例如：用户输入："一个standing pose，双手自然下垂"
    你将输出：
    初始姿势：Tpose
    左手：位置移动到臀部旁边；
    右手：位置移动到臀部旁边；
    """

    example = "For example, to raise the arm, move the hand joint upward, rotate the shoulder joint upward."

    # 拼接system prompt 和 example
    system_prompt_combined = f"{system_prompt}\n\n{example}"
    
    # 使用streaming获取内容
    response = co.chat_stream(
        model="command-r-plus-08-2024",  # 可以选择适当的模型
        messages=[{"role": "system", "content": system_prompt_combined}, 
                  {"role": "user", "content": user_prompt}],
    )
    
    # 打印实时生成的内容
    pose_description = ""
    for event in response:
        if event.type == "content-delta":
            pose_description += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时显示生成的内容
    
    return pose_description.strip()


# 从文件中加载骨骼映射
def load_bone_mapping(file_path):
    bone_mapping = {}
    try:
        with open(file_path, 'r') as file:
            for line in file:
                # 去除每行的换行符并分割成两部分
                line = line.strip()
                if line:  # 跳过空行
                    simplified_bone, actual_bone = line.split(',', 1)
                    bone_mapping[simplified_bone.strip()] = actual_bone.strip()
    except Exception as e:
        print(f"Error reading bone mapping file: {e}")
    
    return bone_mapping

# 使用加载的骨骼映射生成Blender代码
def generate_blender_code_streaming(skeleton_mapping, pose_description):
    # 拼接输入
    system_prompt = f"""
    You are a helpful assistant, you can generate blender code according to the description. 
    For example, if the pose description is 'raise the arm,' the code will rotate the shoulder and elbow joints accordingly. 
    You may move the following parts if necessary: left hand, right hand, left foot, right foot, hips, left knee, right knee, left elbow, right elbow. 
    If a body part does not need to be moved, it will stay in the default T-pose position. Only list the parts that need to be moved or rotated.
    there is an example for the code:

    bone = obj.pose.bones["bone_name"]
    bone.location += (0.0, 0.0, 1.0)  // 你可以使用绝对位置(=)或相对移动(+=)
    bone.rotation_euler += (0, 0, 1)  
    
    """

    user_prompt = f"""
    Skeleton Mapping: {skeleton_mapping}
    Pose Description: {pose_description}
    Please help me generate the blender code.
    """

    # 使用streaming获取内容
    response = co.chat_stream(
        model="command-r-plus-08-2024",  # 选择适当的模型
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
    )

    # 处理streaming响应
    blender_code = ""
    for event in response:
        if event.type == "content-delta":
            blender_code += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时显示Blender代码


    return blender_code.strip()

def pose_design_streaming(user_prompt):
    system_prompt = '''你是一个乐于助人的助理，你可以根据用户输入的提示设计角色想要动作的关键姿势。
    例如：用户输入："一个人在做着向下挥动网球拍的动作."
    你将输出包括时间规划和姿势规划：
    0.0s: 站立姿势，双手下垂；
    1.0s: 一只手（右手）缓慢抬起来，举到空中（假设右手拿着网球拍）；
    2.0s: 右手快速挥下;
    3.0s: 回到初始的站立姿势。
    '''
    # 使用streaming获取内容
    response = co.chat_stream(
        model="command-r-plus-08-2024",  # 可以选择适当的模型
        messages=[{"role": "system", "content": system_prompt}, 
                  {"role": "user", "content": user_prompt}],
    )
    
    # 打印实时生成的内容
    pose_description = ""
    for event in response:
        if event.type == "content-delta":
            pose_description += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时显示生成的内容
    
    return pose_description.strip()

    
if __name__ == "__main__":
    # pose design
    pose_description = pose_design_streaming("A person slaps with his left hand.")
    # # 示例：生成Pose描述流式输出
    # user_prompt_1 = "The character should hold a sword above its head."

    # pose_description = generate_pose_description_streaming(user_prompt_1)
    # # print("\nFinal Pose Description:", pose_description)


    # # 示例：从文件中加载骨骼映射并生成Blender代码
    # bone_mapping_path = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\boneMapping"
    # bone_mapping = load_bone_mapping(bone_mapping_path)
    # # 使用加载的骨骼映射生成Blender代码
    # blender_code = generate_blender_code_streaming(bone_mapping, pose_description)
    # print("\n\nFinal Blender Code:", blender_code)
