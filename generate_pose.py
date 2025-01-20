import cohere
import json
import time
import os
import re

co = cohere.ClientV2("")

def query_command_r_plus_08_2024(user_prompt, system_prompt=None):
    if system_prompt is None:
        system_prompt = "You are a helpful assistant."
    try:
        response = co.chat(
            model="command-r-plus-08-2024",  # 可以选择适当的模型
            messages=[{"role": "system", "content": system_prompt}, 
                    {"role": "user", "content": user_prompt}],
            safety_mode="NONE", 
            temperature=0.6,
        )
        # 打印实时生成的内容
        print(response)
        result_text = response.message.content[0].text
        return result_text.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None
def query_command_r_plus_08_2024_streaming(user_prompt, system_prompt=None):
    if system_prompt is None:
        system_prompt = "You are a helpful assistant."
    try:
        response = co.chat_stream(
            model="command-r-plus-08-2024",  # 可以选择适当的模型
            messages=[{"role": "system", "content": system_prompt}, 
                    {"role": "user", "content": user_prompt}],
            safety_mode="NONE", 
            temperature=0.6,
        )
        # 打印实时生成的内容
        result_text = ""
        for event in response:
            if event.type == "content-delta":
                result_text += event.delta.message.content.text
                print(event.delta.message.content.text, end="")  # 实时显示生成的内容
        return result_text.strip()
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Theoritical Teacher in the overview graph
def planning_pose(user_prompt):
    system_prompt = '''You are a helpful assistant. Your task is to plan a motion animation for a character based on the given description.
You can choose the most suitable approach from the following options:

1. Decompose into Key Poses: This approach is ideal for complex motions.

2. Base Pose with Partial Movements: This approach is suitable for simpler motions.

You should select the appropriate approach and provide the reason for your choice in the following format:
{
    "scheme": "Decompose into Key Poses",
    "reason": "The motion is complex, with significant differences between each key pose. Therefore, it should be decomposed into key poses.",
    "choice": 1
}

Another example:
{
    "scheme": "Base Pose with Partial Movements",
    "reason": "The motion is repetitive, with the overall body remaining relatively still while only the hand moves back and forth. Therefore, it is better to use the base pose with partial movements approach.",
    "choice": 2
}
'''
    return query_command_r_plus_08_2024(user_prompt, system_prompt)

def plan_pose_design_for_whole_body(user_prompt):
    system_prompt = '''You are a helpful assistant. You can design the overall human movement plan based on the user's actions and requirements. You only need to output the overall movement and rotation of the body, without considering any details. 
For example: 
    Input: A person is doing a handstand. 
    Output: 
    [ 
        {"time":"0.0s","body transform":"The body is upright, preparing to begin the handstand"}, 
        {"time":"1.0s","body transform":"The body rotates 180 degrees from back, starting the handstand"}, 
        {"time":"2.0s","body transform":"The body is still inverted at a 180-degree angle, maintaining the handstand position"}, 
        {"time":"3.0s","body transform":"The body rotates back to an upright position, completing the handstand and returning to standing"} 
    ] 
Another example: 
    Input: A person is running and then turns back halfway. 
    Output: 
    [ 
        {"time":"0.0s","body transform":"The body moves forward 0.3m"}, 
        {"time":"1.0s","body transform":"The body moves forward 0.3m"}, 
        {"time":"2.0s","body transform":"The body rolls 180 degrees from right, turning around"}, 
        {"time":"3.0s","body transform":"The body moves forward 0.3m"}, 
        {"time":"4.0s","body transform":"The body moves forward 0.3m"} 
    ]

You should specify the directions of movement and rotation. For movement, the possible directions are forward, backward, left, right, up, and down. For rotation, the directions include roll to the left, roll to the right, pitch forward, tilt to the left, and tilt to the right. You can combine these directions flexibly and use approximate values to indicate the extent of the movement or rotation.
'''
    return query_command_r_plus_08_2024(user_prompt, system_prompt)
# Pose Designer + Physical Teacher(Relative Position)
def generate_pose_design(user_prompt):
    system_prompt = '''You are a helpful assistant. You can design a pose for a character.
    You should output it as a JSON object, with the following keys:
    "time": The time of the pose.
    "pose": The pose, which should be a relative joint position, like "left hand slightly above the head."
    For example:
    [
        {"time": 0.5, "pose": "left hand moderately above the head. the waist is slightly bent over. the root is rotated 90 degrees. The head is slightly bent over."},
        {"time": 1.0, "pose": "right hand slightly below the hip, and left foot is above the ground."},
        {"time": 2.0, "pose": "left foot is touching the chest. left hand is moderately in the left of the chest to keep balance."},
        {"time": 3.0, "pose": "right foot maximally above the ground, and maximally stretch forward the body center."},
    ]
    - You can use adverbs such as 'below', 'above', 'on the left', 'on the right' to describe positions.
    - You should only move these joints with world locations: left hand, right hand, left foot, right foot, and hip.
    - You can use any body part name as a reference, such as chest, waist, back, shoulders, etc., except for the joints listed above. You can also use 'ground', 'body center', and 'its original position'.
    - You should locate the joint as accurately as possible, for example, if you can use 'left_shoulder' as a reference, you  shouldn't use 'body' as a reference.
    - You can use 'touching', 'slightly', 'moderately', or 'maximally' to describe the distance between the joint and the body part, indicating the level of extension of the limb.
    - If the body is moving, the hip should be moved.
    - You can generate a reasonable number of objects and reasonably distribute the time based on the rhythm of the action.
    - If the body is moving, you should move the root to move the whole body, or if the body is rolling or flipping, you should rotate the root, like "rotate the root 90 degrees."
    - You should try to generate movement motions for the left hand, right hand, left foot, right foot, and hip to maintain overall balance in the body's movement.
    - You can describe more joint cooperative movements to make the motion natural and realistic.
    - If the person is holding an object, describe the hand's position instead of the object.
    '''
    return query_command_r_plus_08_2024(user_prompt, system_prompt)

def generate_pose_design_streaming(user_prompt):
    system_prompt = '''You are a helpful assistant. You can design a pose for a character.
    You should output it as a JSON object, with the following keys:
    "time": The time of the pose.
    "pose": The pose, which should be a relative joint position, like "left hand slightly above the head."
    For example:
    [
        {"time": 0.5, "pose": "left hand moderately above the head."},
        {"time": 1.0, "pose": "right hand slightly below the hip, and left foot is above the ground."},
        {"time": 2.0, "pose": "left foot is touching the chest."},
        {"time": 3.0, "pose": "right foot maximally above the ground"},
    ]
    - You can use adverbs such as 'below', 'above', 'on the left', 'on the right' to describe positions.
    - You should only describe these joints before using 'above' or 'below': left hand, right hand, left foot, right foot, and hip.
    - After 'above' or 'below', you can use any body part name, such as chest, waist, back, shoulders, etc., except for the joints listed above. You can also use 'ground', 'body center'.
    - You can use 'touching', 'slightly', 'moderately', or 'maximally' to describe the distance between the joint and the body part, indicating the level of extension of the limb.
    - You can generate a reasonable number of objects and reasonably distribute the time based on the rhythm of the action.
    - You should try to generate movement motions for the left hand, right hand, left foot, right foot, and hip to maintain overall balance in the body's movement.
    - You can describe more joint cooperative movements to make the motion natural and realistic.
    '''
    return query_command_r_plus_08_2024_streaming(user_prompt, system_prompt)


def generate_pose_code(time, pose_desc, body_world_pos):
    system_prompt = f'''You are a helpful assistant. You can translate user's pose description into blender code.
The user descriptions are relative positions, like "left hand is slightly above the head."
You can reference to the world position of the body parts, and then output the blender code to achieve the pose.
for example:
    user prompt: 
        time: 1.5
        pose description: left hand is slightly above the head.
        assume the the head's position is (0,0,1.65)
    you output:
        left_hand.location = (armature.matrix_world @ left_hand.matrix).inverted() @ (Vector((0, 0, 1.65)) + Vector((0, 0, 0.2)))
        left_hand.keyframe_insert(data_path="location", frame=1.5*24) # 1.5 is the time,24 is frame rate

- you can output multiple lines if there are multiple body parts involved.
slightly above: add Vector((0,0,0.2)) (or more or less depending on your judgment).
- For distance description:
    miderately above: add Vector((0,0,0.5)) (or more or less depending on your judgment).
    maximally above: add Vector((0,0,1)) (or more or less depending on your judgment).
    slightly below: add Vector((0,0,-0.2)) (or more or less depending on your judgment).
    slightly on the left: add Vector((0.2,0,0)) (or more or less depending on your judgment).
    slightly on the right: add Vector((-0.2,0,0)) (or more or less depending on your judgment).
    touching: add Vector((0,0,0)) (or more or less depending on your judgment).
    and so on, reason based on your common sense, you can twick the values and signs peoperly.
- Output the code text only, without ```python prefix.
- Keep the structure of code.

- Only left_hand, right_hand, left_foot, right_foot can be moved.
- The time is given, write it as the given number.
- You can simultaneously move the feet and the hip to move the character while he is in motion.
- Use your common sense to evaluate whether the movement result might cause an abnormal limb position. If it does, adjust it slightly in another direction.

- You can rotate the hip, waist, chest, shoulder, left_shoulder, right_shoulder, neck, head, by:
    waist.rotation_euler.x += 0.1 # (or more or less depending on your judgment)
- You can move the left_elbow, right_elbow, left_knee, right_knee slightly to make them point to a direction by:
    left_elbow.location.x += 0.1  # (or more or less depending on your judgment)
When rotating, +z is right, -z is left, +y is roll back from left, -y is roll back from right, +x is forward, -x is backward.(This is differenent from moving axis)
- You can move the root to move the whole body by:
    root.location.y += 0.1  # (or more or less depending on your judgment)
    Note that for root movement, +y is forward, -y is backward, +x is right, -x is left, +z is up, -z is down.
- You can rotate the root to rotate the whole body, especially when the character is hand-standing or doing a backflip by:
    root.rotation_euler.z += 0.1  # (or more or less or other directions depending on your judgment)
    Remember when rotating, +y is right, -y is left, +z is roll back from left, -z is roll back from right, -x is forward, +x is backward.(This is differenent from moving axis)
- If the person is holding an object, move the hand's position instead of the object.
'''
    user_prompt = f'''time:{time},
    pose description:{pose_desc},
    body part positions to reference:{body_world_pos}
'''
    pose_code = query_command_r_plus_08_2024(user_prompt, system_prompt)
    # pose_code = modify_pose_code_world_position_re(pose_code)
    pose_code = modify_pose_code_prefix_concat(pose_code, time)
    return pose_code

def generate_pose_code_batch(pose_desc, body_world_pos):
    system_prompt = f'''You are a helpful assistant. You can translate user's pose description into blender code.
The user descriptions are relative positions, like "left hand is slightly above the head."
You can reference to the world position of the body parts, and then output the blender code to achieve the pose.
for example:
    user prompt: 1.0: left hand is slightly above the head.
        assume the the head's position is (0,0,1.65)
    you output:
        left_hand.keyframe_insert(data_path="location", frame=0.5*24) # 0.5 is slightly before the time, 24 is the frame rate. This is done to add a lead-in to the motion. The advance time depends on the speed of the action. If time is 0.0 this step can be skipped.
        left_hand.location = (armature.matrix_world @ left_hand.matrix).inverted() @ (Vector((0, 0, 1.65)) + Vector((0, 0, 0.2)))
        left_hand.keyframe_insert(data_path="location", frame=1.0*24) # 1.0 is the time, 24 is frame rate
you can output multiple lines if there are multiple body parts involved.

slightly above: add Vector((0,0,0.2))
miderately above: add Vector((0,0,0.5))
maximally above: add Vector((0,0,1))
slightly below: add Vector((0,0,-0.2))
slightly on the left: add Vector((0.2,0,0))
slightly on the right: add Vector((-0.2,0,0))
touching: add Vector((0,0,0))
and so on, reason based on your common sense, you can twick the values and signs peoperly.
output the code text only, without ```python prefix.
Keep the structure of code.

only left_hand, right_hand, left_foot, right_foot can be moved.
Use your common sense to evaluate whether the movement result might cause an abnormal limb position. If it does, adjust it slightly in another direction.
'''
    user_prompt = f'''time:{time},
    pose description:{pose_desc},
    body part positions to reference:{body_world_pos}
'''
    pose_code = query_command_r_plus_08_2024(user_prompt, system_prompt)
    # pose_code = modify_pose_code_world_position_re(pose_code)
    pose_code = modify_pose_code_prefix_concat(pose_code)
    return pose_code


def modify_pose_code_world_position_re(pose_code):
    """
    修改姿态代码，将局部位置赋值转换为世界位置计算，代码输出为单行。
    :param pose_code: 输入的姿态代码字符串。
    :return: 修改后的代码字符串。
    """
    def transform_match(match):
        """
        根据匹配内容生成简化的单行世界坐标计算代码。
        """
        bone_name = match.group(1)  # 捕获骨骼名称
        local_position = match.group(2)  # 捕获局部坐标
        armature_name = match.group(3)  # 捕获骨架名称
        
        # 单行世界坐标计算和赋值，使用 Vector 和 Matrix
        return (
            f"{bone_name}.location = bpy.data.objects['{armature_name}'].matrix_world @ "
            f"bpy.data.objects['{armature_name}'].pose.bones['{bone_name}'].matrix @ "
            f"Vector{local_position}  # 世界坐标赋值"
        )
    
    # 更新匹配规则：匹配更通用的骨骼名称
    pattern = r"(\S+)\.location\s*=\s*(\(.+\))\s*#\s*armature\s*=\s*(\w+)"
    
    # 替换匹配到的内容
    modified_code = re.sub(pattern, transform_match, pose_code)
    return modified_code

def modify_pose_code_prefix_concat(pose_code,time):
    prefix = '''import bpy
from mathutils import Vector, Matrix

armature = bpy.data.objects['rig']
bpy.context.view_layer.objects.active = armature

left_hand = armature.pose.bones['c_hand_ik.l']
right_hand = armature.pose.bones['c_hand_ik.r']
left_foot = armature.pose.bones['c_foot_ik.l']
right_foot = armature.pose.bones['c_foot_ik.r']
hip =  armature.pose.bones['c_root_master.x']

left_knee = armature.pose.bones['c_leg_pole.l']
right_knee = armature.pose.bones['c_leg_pole.r']
left_elbow = armature.pose.bones['c_arms_pole.l']
right_elbow = armature.pose.bones['c_arms_pole.r']

# for  rotation
hip = armature.pose.bones['c_root_master.x']
waist = armature.pose.bones['c_spine_01.x']
chest = armature.pose.bones['c_spine_02.x']
shoulder = armature.pose.bones['c_spine_03.x']
left_shoulder = armature.pose.bones['c_shoulder.l']
right_shoulder = armature.pose.bones['c_shoulder.r']
neck = armature.pose.bones['c_neck.x']
root = armature.pose.bones['c_traj']
head = armature.pose.bones['c_head.x']
'''

    suffix = f'''
left_hand.keyframe_insert(data_path="location", frame={time}*24)
right_hand.keyframe_insert(data_path="location", frame={time}*24)
left_foot.keyframe_insert(data_path="location", frame={time}*24)
right_foot.keyframe_insert(data_path="location", frame={time}*24)
hip.keyframe_insert(data_path="location", frame={time}*24)
waist.keyframe_insert(data_path="location", frame={time}*24)
chest.keyframe_insert(data_path="location", frame={time}*24)
shoulder.keyframe_insert(data_path="location", frame={time}*24)
left_shoulder.keyframe_insert(data_path="location", frame={time}*24)
right_shoulder.keyframe_insert(data_path="location", frame={time}*24)
neck.keyframe_insert(data_path="location", frame={time}*24)
left_knee.keyframe_insert(data_path="location", frame={time}*24)
right_knee.keyframe_insert(data_path="location", frame={time}*24)
left_elbow.keyframe_insert(data_path="location", frame={time}*24)
right_elbow.keyframe_insert(data_path="location", frame={time}*24)
root.keyframe_insert(data_path="location", frame={time}*24)
head.keyframe_insert(data_path="location", frame={time}*24)
'''
    # Remove lines containing "```" from pose_code
    pose_code = '\n'.join(line for line in pose_code.split('\n') if '```' not in line)
    return prefix + pose_code + suffix

def generate_scheduled_pose(pose_desc, pose_code):
    system_prompt = f'''You are a helpful assistant.
Please generate a 

'''


#  异常检测与优化（deprecated）======================================================
# 1. 重心优化：通过调整hip的位置大体跟随中心，减小重心失衡带来的物理不真实感；
# 2. 关节优化：通过检查和调整关节的旋转值，减少关节角度过小或过大带来的形体错误；
# 3. 旋转优化：通过常识推测手、头、脚、肩膀的旋转。
# 输入： 从Blender反馈的姿态状态
# 输出： 

def check_hands(pose_prompt,all_pose_design,time,pose_design,pose_state):
    system_prompt = '''You are a helpful assistant. You can check the positions of the hands to judge whether it is reasonable for the pose design.'''
    user_prompt = f'''Please check the hands in the pose design. The overall pose design is as follows:
    {pose_prompt},
    and it is one of the key pose in the pose series:{all_pose_design}
    at time {time},{pose_design},
    currently, it is implemented as a state, in this state, {pose_state},
    Please give me a feedback. If the hands are not reasonable, please give me a new pose design. If the hands are reasonable, but the hand position is not adhere to the design, please give me a feedback.'''
    return query_command_r_plus_08_2024(user_prompt, system_prompt)

# 重心优化本质上是hip位置的优化
def optimize_hip():
    pass  

def refine_pose_code(overall_desc, current_desc, pose_code, body_world_pos):
    system_prompt = '''You are a helpful assistant. You can refine the pose code to make it more realistic.
   
'''

#  异常检测与优化（deprecated）======================================================

# 检查-分析-执行(后面两步合并)
# 由于pose code对pose design的执行不一定彻底，并且pose design也不一定合理，所以需要多次检查，直到最终的姿态符合pose prompt

def check_pose(bone_mapping,pose_prompt,pose_design):
    bone_mapping_dict = json.loads(bone_mapping)
    stem_prompt = '''You are a helpful assistant. You can generate Blender bpy conditional branch code to determine if the current pose matches the given pose prompt and pose design. The pose prompt describes the overall action, while the pose design specifies a key pose within that action.
For example:
    Pose prompt: A person is performing a handstand.
    Pose design:
    Your output:
    {
        "check_list" :{
            ["hands on the ground", "hand below the head","feet above the head"],
        }
        "check_code":"if left_hand.location.z < head.location.z:\n    print("left hand below the head")\nelse:\n    print("left hand above the head)\nif right_hand.location.z < head.location.z:\n    print("right hand below the head")\nelse:\n    print("right hand above the head)\nif left_foot.location.z > head.location.z:\n    print("left foot above the head")\nelse:\n    print("left foot below the head)\nif right_foot.location.z > head.location.z"
    }
    - You should focus on the locations of left_hand, right_hand, left_foot, right_foot.
    - You should compare their locations to other reference body parts, like head, chest, waist, etc.
    '''
    user_prompt = f'''Please check the pose design. The overall pose prompt is as follows:
    {pose_prompt},
    and it is one of the key pose in the pose series:{pose_design}.
    the bones you can use are:{bone_mapping_dict.keys()}
    Please output the check list and the branch codes to check them.
    '''
    return query_command_r_plus_08_2024(user_prompt, system_prompt)

# Analysis and response to check results
def analyze_check_results(check_result):
    system_prompt = '''You are a helpful assistant.You can analyze the check results and decide how to move the joints to fix the errors.
    Example:
    check result:
    {   
        "check list item":"hands on the ground",
        "check result":False,
        "extra info":"left_hand.location = (0.12,-0.20,-0.1)"
    }
    your output:
    {   
        "response":["move down left_hand"],
        "response code":"left_hand.location.z -= 0.1"
    }
    '''
    user_prompt = f'''Please analyze the check results. The check result is as follows:
    {check_result}.
    Please output the response and the branch codes to fix the errors.
    '''
    return query_command_r_plus_08_2024(user_prompt, system_prompt)

