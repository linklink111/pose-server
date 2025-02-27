import cohere
import json
import time
import os
import re

co = cohere.ClientV2("HTwK0MTkqJuhqY3PZEUoBlNAmWPSSEOQMFWlVR0J")

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
    
def generate_pose_design(user_prompt):
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
    You can use adverbs such as 'below', 'above', 'on the left', 'on the right' to describe positions.
    You should only describe these joints before using 'above' or 'below': left hand, right hand, left foot, right foot, and hip.
    After 'above' or 'below', you can use any body part name, such as chest, waist, back, shoulders, etc., except for the joints listed above. You can also use 'ground', 'body center', and 'its original position'.
    You can use 'touching', 'slightly', 'moderately', or 'maximally' to describe the distance between the joint and the body part, indicating the level of extension of the limb.
    You can generate a reasonable number of objects and reasonably distribute the time based on the rhythm of the action.
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
    You can use adverbs such as 'below', 'above', 'on the left', 'on the right' to describe positions.
    You should only describe these joints before using 'above' or 'below': left hand, right hand, left foot, right foot, and hip.
    After 'above' or 'below', you can use any body part name, such as chest, waist, back, shoulders, etc., except for the joints listed above. You can also use 'ground', 'body center'.
    You can use 'touching', 'slightly', 'moderately', or 'maximally' to describe the distance between the joint and the body part, indicating the level of extension of the limb.
    You can generate a reasonable number of objects and reasonably distribute the time based on the rhythm of the action.
    You should try to generate movement motions for the left hand, right hand, left foot, right foot, and hip to maintain overall balance in the body's movement.
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
you can output multiple lines if there are multiple body parts involved.

slightly above: add Vector((0,0,0.2)) (or more or less depending on your judgment).
miderately above: add Vector((0,0,0.5)) (or more or less depending on your judgment).
maximally above: add Vector((0,0,1)) (or more or less depending on your judgment).
slightly below: add Vector((0,0,-0.2)) (or more or less depending on your judgment).
slightly on the left: add Vector((0.2,0,0)) (or more or less depending on your judgment).
slightly on the right: add Vector((-0.2,0,0)) (or more or less depending on your judgment).
touching: add Vector((0,0,0)) (or more or less depending on your judgment).
and so on, reason based on your common sense, you can twick the values and signs peoperly.
output the code text only, without ```python prefix.
Keep the structure of code.

only left_hand, right_hand, left_foot, right_foot can be moved.
the time is given, write it as the given number.
You can simultaneously move the feet and the hip to move the character while he is in motion.
Use your common sense to evaluate whether the movement result might cause an abnormal limb position. If it does, adjust it slightly in another direction.

you can rotate the hip, waist, chest, shoulder, left_shoulder, right_shoulder, neck, head, by:
    waist.rotation_euler.x += 0.1 # (or more or less depending on your judgment)
you can move the left_elbow, right_elbow, left_knee, right_knee to make them point to a direction by:
    left_elbow.location.x += 0.1  # (or more or less depending on your judgment)
when rotating, +z is right, -z is left, +y is roll back from left, -y is roll back from right, +x is forward, -x is backward.(This is differenent from moving axis)
    
'''
    user_prompt = f'''time:{time},
    pose description:{pose_desc},
    body part positions to reference:{body_world_pos}
'''
    pose_code = query_command_r_plus_08_2024(user_prompt, system_prompt)
    # pose_code = modify_pose_code_world_position_re(pose_code)
    pose_code = modify_pose_code_prefix_concat(pose_code)
    return pose_code

def generate_pose_code_batch(pose_desc, body_world_pos):
    system_prompt = f'''You are a helpful assistant. You can translate user's pose description into blender code.
The user descriptions are relative positions, like "left hand is slightly above the head."
You can reference to the world position of the body parts, and then output the blender code to achieve the pose.
for example:
    user prompt: 1.0: left hand is slightly above the head.
        assume the the head's position is (0,0,1.65)
    you output:
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

def modify_pose_code_prefix_concat(pose_code):
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
left_elbow = armature.pose.bones['c_arm_pole.l']
right_elbow = armature.pose.bones['c_arm_pole.r']

# for  rotation
hip = armature.pose.bones['c_root_master.x']
waist = armature.pose.bones['c_spine_01.x']
chest = armature.pose.bones['c_spine_02.x']
shoulder = armature.pose.bones['c_spine_03.x']
left_shoulder = armature.pose.bones['c_shoulder.l']
right_shoulder = armature.pose.bones['c_shoulder.r']
neck = armature.pose.bones['c_neck.x']
'''
    return prefix + pose_code

#  异常检测与优化
# 1. 重心优化：通过调整hip的位置大体跟随中心，减小重心失衡带来的物理不真实感；
# 2. 关节优化：通过检查和调整关节的旋转值，减少关节角度过小或过大带来的形体错误；
# 3. 旋转优化：通过常识推测手、头、脚、肩膀的旋转。
# 输入： 从Blender反馈的姿态状态
# 输出： 

# 中心优化本质上是hip位置的优化
def optimize_hip():
    pass  