# 版本信息：command r v2，
# 主要特点：
#     1. 分帧生成 pose code；（未实现）
#     2. 暂时先只生成移动，不生成旋转；（已实现）
#     3. 采用相对位置（例如手在头的上方）；(实现中)
# 主要问题：
# 改进方向：1. 每一帧都审核，一帧一帧来（在blender里做成交互式审核的，人审核/LLM审核都可以）；
# 这样一整个写到一个文件里，由于导入了bpy所以只能在blender里运行，会输出很多底层消息，调试起来不方便，所以接下来不再维护这个文件，
# 改成用这个文件开一个server，在Blender里按按钮的时候把数据发送过来分析请求。
# 此外，动画帧改成逐步生成（按一次按钮生成一个关键帧），不再一次性生成所有关键帧。

# 接口定义：
# 1. generate_pose_code
# 2. generate_
# try:
#     import bpy
#     from mathutils import Vector
# except ImportError:
#     print("请在Blender中运行这个程序。Please run this script in Blender.")
#     exit()
import cohere
import time
import os

co = cohere.ClientV2("P3ROmZfQlTu1Cp8A3Eom1bWrnVgWZFDhNl92WTah")

# 获取骨骼位置函数
def get_joint_world_position(action, armature, joint_name, frame_number):
    """
    获取指定骨骼在指定帧的世界坐标。如果没有找到 F 曲线，直接使用骨骼的位置。
    
    参数：
    - action: 动作数据（bpy.types.Action）
    - armature: 骨架对象（bpy.types.Object）
    - joint_name: 骨骼名称（字符串）
    - frame_number: 帧编号（整数）
    """
    if not armature or not armature.pose.bones.get(joint_name):
        print(f"无效的骨架或骨骼名称: {joint_name}")
        return None

    # 设置当前帧
    bpy.context.scene.frame_set(frame_number)

    # 如果有动作并尝试从 F 曲线获取位置
    local_position = None
    if action:
        fcurves = action.fcurves
        x_curve = next((fc for fc in fcurves if fc.data_path == f'pose.bones["{joint_name}"].location' and fc.array_index == 0), None)
        y_curve = next((fc for fc in fcurves if fc.data_path == f'pose.bones["{joint_name}"].location' and fc.array_index == 1), None)
        z_curve = next((fc for fc in fcurves if fc.data_path == f'pose.bones["{joint_name}"].location' and fc.array_index == 2), None)

        if x_curve and y_curve and z_curve:
            local_position = Vector((
                x_curve.evaluate(frame_number),
                y_curve.evaluate(frame_number),
                z_curve.evaluate(frame_number)
            ))

    # 如果没有 F 曲线，直接从骨骼获取局部位置
    if local_position is None:
        bone = armature.pose.bones[joint_name]
        local_position = bone.location

    # 获取骨骼的变换矩阵
    bone = armature.pose.bones[joint_name]
    bone_matrix_world = bone.matrix @ armature.matrix_world

    # 转换到世界坐标
    world_position = bone_matrix_world @ local_position
    return world_position
def query_body_part_position(body_part_name, frame_number):
    """查询指定骨骼在指定帧的位置"""
    # 获取当前对象及其动画数据
    obj = bpy.context.object
    if obj and obj.animation_data and obj.animation_data.action:
        action = obj.animation_data.action
        return get_joint_world_position(action, body_part_name, frame_number)
    else:
        print("当前对象没有动画数据")
        return None
functions_map = {
    "query_body_part_position":query_body_part_position,
}



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

def pose_design_to_relative(user_prompt):
    system_prompt = '''你是一个帮助用户将绝对姿态转换为相对姿态的助理。用户将输入一个角色的姿态序列，你需要输出每一帧的姿态相对前一帧的变换描述，基于骨骼节点的位移、旋转或特定部位的位置变化。输出格式为：
    时间戳: [骨骼部位名称] 相对变换描述；
例如：
用户输入：
0.0s: 站立姿势，双手下垂；
1.0s: 一只手（右手）缓慢抬起来，举到空中；
2.0s: 右手快速挥下；
3.0s: 回到初始的站立姿势。

你的输出应为：
0.0s: 右手起始位置，放在臀部旁边；
1.0s: 右手从臀部旁边抬至头顶上方；
2.0s: 右手从头顶位置挥至胸前，最大伸展；
3.0s: 右手从胸前回到臀部旁边。
请确保所有姿态都以某个身体部位的定位为参考。'''

    # 使用streaming获取内容
    response = co.chat_stream(
        model="command-r-plus-08-2024",  # 可以选择适当的模型
        messages=[{"role": "system", "content": system_prompt}, 
                  {"role": "user", "content": user_prompt}],
    )
    
    # 打印实时生成的内容
    pose_description_relative = ""
    for event in response:
        if event.type == "content-delta":
            pose_description_relative += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时显示生成的内容
    
    return pose_description_relative.strip()

def generate_pose_code_frame_by_frame(pose_description_relative,bone_mapping):
    # 按行分成列表
    lines = pose_description_relative.split('\n')
    final_code = ""
    for line in lines:
        code = generate_pose_code_for_frame(line,bone_mapping)
        final_code += "\n"
        final_code += code
    return final_code
def generate_pose_code_for_frame(
    pose_description, 
    bone_mapping,
    last_frame_state=None, 
    direction_text=None, 
    model_info_text=None, 
    theory_hint=""
):
    """
    将单个姿态描述转换为 Blender Python 代码。
    
    参数：
    - pose_description: 单帧的姿态描述，例如 "右手抬至头顶上方"
    - last_frame_state: 上一帧的状态数据（可选）
    - direction_text: 空间方向说明（可选）
    - model_info_text: 模型信息说明（可选）
    - theory_hint: 理论提示（可选）
    
    返回：
    - 生成的 Blender Python 代码字符串
    """
    # 初始化系统提示和用户输入
    system_prompt = f"""
    你是一个帮助用户将姿态描述转换为 Blender Python 代码的助理。
    你是一个帮助用户将姿态转换为 Blender Python 代码的助理。
    你可以调用工具查找身体部位的位置，但是注意要用英文名称查找，可查找的名称有:{bone_mapping.keys()}
    例如：
    输入：1.5s:右手抬至头顶上方轻微距离。
    你可以先调用工具查询上一帧的头的位置(注意要用英文名称查找)
    输出：
    frame=1.5*24
    right_hand.location.z = [头的位置]+(0.1,0.1,0.1)  # 查到的上一帧头的位置旁边（轻微：0.1，中等：0.3，极大：0.5）
    right_hand.keyframe_insert(data_path="location", frame=frame)
    """
    user_prompt = f"""
    Pose description: {pose_description}
    {theory_hint}
    请根据描述生成相应的 Blender Python 代码。
    """
    
    # 消息队列，初始化包含系统和用户消息
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # 初始化工具列表（可以包含特定的工具实现，如查询上一帧状态等）
    tools = [
        {
            "name": "query_body_part_position",
            "description": "在 Blender 的姿态工作区中查询指定骨骼节点在特定帧的位置。",
            "parameters": {
                "body_part_name": {
                    "description": "要查询位置的骨骼名称。",
                    "type": "str",
                    "required": True
                },
                "frame_number": {
                    "description": "要查询的帧号。",
                    "type": "int",
                    "required": True
                }
            }
        }
    ]

    try:
        # 第一次调用生成工具计划和初始响应
        response = co.chat(model="command-r-plus-08-2024", messages=messages, tools=tools)

        while response.message.tool_calls:
            print("\n工具计划：")
            print(response.message.tool_plan)

            # 处理工具调用并执行
            for tool_call in response.message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                print(f"调用工具：{tool_name} | 参数：{tool_args}")
                
                # 示例工具调用执行
                tool_result = execute_tool(tool_name, tool_args)  # 替换为实际工具执行逻辑
                print("工具结果：", tool_result)

                # 添加工具调用结果到消息队列
                tool_content = [{"type": "document", "document": {"data": json.dumps(tool_result)}}]
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                })
            
            # 再次调用模型，发送更新后的消息队列
            response = co.chat(model="command-r-plus-08-2024", messages=messages, tools=tools)

        # 最终生成的代码
        print("\n最终响应内容：")
        final_code = response.message.content[0].text
        print(final_code)
        return final_code.strip()

    except Exception as e:
        print(f"生成过程中出错: {e}")
        return ""

def execute_tool(tool_name, tool_args):
    """
    示例工具执行函数，根据工具名称和参数执行实际逻辑。
    """
    if tool_name == "web_search_tool":
        return web_search(**tool_args)  # 替换为实际搜索逻辑
    else:
        raise NotImplementedError(f"未知工具：{tool_name}")


# pose transition直接生成代码版,一次生成多帧+初始姿态为t-pose版
def generate_pose_code_sequence_streaming(pose_sequence,direction_text,model_info_text, theory_hint=""):
    # header 
    '''
    left_hand = armature.pose.bones['c_hand_ik.l']
    right_hand = armature.pose.bones['c_hand_ik.r']
    left_foot = armature.pose.bones['c_foot_ik.l']
    right_foot = armature.pose.bones['c_foot_ik.r']
    hip =  armature.pose.bones['c_root_master.x']
    '''
    # direction_text = "前方是-y，后方是+y，左边是-x，右边是+x，上方是+z，下方是-z。"
    # model_info_text = "角色身高是1.7m，臂长是0.5m，腿长是0.8m。"
   
    system_prompt = f"""
    你是个有帮助的助手，你可以根据描述生成 Blender 代码。
    例如，如果姿势描述是“举起手臂”，则代码将相应地旋转肩关节和肘关节。
    你可以根据需要移动以下部位：左手，右手，左脚，右脚，臀部，左膝，右膝，左肘，右肘。
    如果不需要移动身体部位，它将保持last pose的姿势。仅列出需要移动或旋转的部位。
    你只能移动这些关节，不能旋转它们。

    例如：
    pose sequence:（初始状态为t-pose）
    0.0s: 站立姿势，双手下垂；
    1.0s: 一只手（右手）缓慢抬起来，举到空中（假设右手拿着网球拍）；
    2.0s: 右手快速挥下;
    3.0s: 回到初始的站立姿势。

    代码示例如下：(注意方向：{direction_text}{model_info_text}，请根据这些信息生成合理的值)
    # 设置帧速率
    frame_rate = 24  # 每秒 24 帧

    # 初始站立姿势
    frame_start = 0 * frame_rate
    left_hand.location = (0.0, 0.0, 0.0)  # 左手保持初始位置
    right_hand.location = (0.0, 0.0, 0.0)  # 右手保持初始位置
    left_hand.keyframe_insert(data_path="location", frame=frame_start)
    right_hand.keyframe_insert(data_path="location", frame=frame_start)

    # 1.0s: 右手缓慢举起到头部上方
    frame_1 = 1.0 * frame_rate
    right_hand.location.z += 1.2  # 上举右手
    right_hand.keyframe_insert(data_path="location", frame=frame_1)
    right_hand.keyframe_insert(data_path="rotation_euler", frame=frame_1)

    # 2.0s: 右手快速挥动向下
    frame_2 = 2.0 * frame_rate
    right_hand.location.z -= 1.0  # 向下挥动
    right_hand.location.x += 0.5  # 同时手臂向前移动
    right_hand.keyframe_insert(data_path="location", frame=frame_2)
    right_hand.keyframe_insert(data_path="rotation_euler", frame=frame_2)

    # 3.0s: 回到初始站立姿势
    frame_3 = 3.0 * frame_rate
    right_hand.location = (0.0, 0.0, 0.0)  # 回到初始位置
    right_hand.keyframe_insert(data_path="location", frame=frame_3)
    
    """

    # user_prompt = f"""  
    # Skeleton Mapping: {skeleton_mapping}
    # pose_sequence: {pose_sequence}
    # Please help me generate the blender code.
    # {theory_hint}
    # """
    # skeleton_mapping现在似乎不需要了
    user_prompt = f"""  
    pose_sequence: {pose_sequence}
    Please help me generate the blender code.
    {theory_hint}
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

def pose_code_direction_check_and_fix(pose_code, direction_text):
    """
    检查 Blender Pose Code 中的方向是否与注释描述一致，并修正代码。

    参数:
    - pose_code: str，包含骨骼动作的代码。
    - direction_text: str，方向描述，例如 "前方是-y，后方是+y，左边是-x，右边是+x，上方是+z，下方是-z"。

    返回:
    - str，修正后的代码。
    """
    system_prompt = f"""
    你是一个代码检查助手，专注于解析和修正 Blender Pose Code 的方向问题。你的任务是：
    1. 检查代码注释与坐标方向操作是否一致。
    2. 如果发现不一致，修正代码并确保修正后的代码功能与注释描述匹配。
    3. 返回修正后的代码，并保持注释与代码一致。
    
    ### 输入
    - 一个描述方向的文本，例如："{direction_text}"。
    - 用户提供的 Pose Code。

    ### 输出
    - 修正后的代码。

    ### 示例
    #### 输入
    ```
    direction_text = "前方是-y，后方是+y，左边是-x，右边是+x，上方是+z，下方是-z"
    Pose Code:
    # 0.5s: 左脚向前迈出一步，重心前倾
    frame_0_5 = 0.5 * frame_rate
    left_foot.location.x -= 0.4  # 左脚向前迈出
    hip.location.x -= 0.1  # 重心稍微前倾
    left_foot.keyframe_insert(data_path="location", frame=frame_0_5)
    hip.keyframe_insert(data_path="location", frame=frame_0_5)
    ```

    #### 输出
    ```
    # 0.5s: 左脚向前迈出一步，重心前倾
    frame_0_5 = 0.5 * frame_rate
    left_foot.location.y -= 0.4  # 左脚向前迈出
    hip.location.y -= 0.1  # 重心稍微前倾
    left_foot.keyframe_insert(data_path="location", frame=frame_0_5)
    hip.keyframe_insert(data_path="location", frame=frame_0_5)
    ```
    """

    # 构建 user_prompt
    user_prompt = f"""
    direction_text = "{direction_text}"
    Pose Code:
    {pose_code}
    """

    # 调用 co.chat_stream 进行方向检查和修正
    response = co.chat_stream(
        model="command-r-plus-08-2024",
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
    )

    # 实时获取生成内容
    fixed_code = ""
    for event in response:
        if event.type == "content-delta":
            fixed_code += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时打印输出

    return fixed_code.strip()
  
# 在 posecode 的前面插入 bone map
def bone_map_header_insert(bone_mapping, pose_code):
    system_prompt = '''
    请根据pose code中用到的骨骼，和输入的bone mapping，在最前面添加类似于下面的bone map header，
    例如：
    pose code:
        left_hand.location.x += arm_length * 0.6  
        left_hand.location.z -= 0.3  
        right_hand.location = hip.location + (0.2, 0, 0) 
        left_foot.location.z += foot_distance * 0.3  
    bone mapping:
        left_hand,c_hand_ik.l
        right_hand,c_hand_ik.r
        left_foot,c_foot_ik.l
        right_foot,c_foot_ik.r
        hip,c_root_master.x
        left_elbow,c_arms_pole.l
        right_elbow,c_arms_pole.r
        left_knee,c_leg_pole.l
        right_knee,c_leg_pole.r
        head(rotate only),c_head.x
    由于pose code中出现了left_hand，right_hand，left_foot，所以需要添加以下的bone map header：
        left_hand = armature.pose.bones['c_hand_ik.l']
        right_hand = armature.pose.bones['c_hand_ik.r']
        left_foot = armature.pose.bones['c_foot_ik.l']
    除此之外，添加这几行：
        import bpy
        # 获取骨骼对象
        armature = bpy.data.objects['rig']  # 替换为你的骨骼名称，如果用户没有给出则不变
        bpy.context.view_layer.objects.active = armature
# =============================================
    添加完成之后输出添加后的结果：
        import bpy
        # 获取骨骼对象
        armature = bpy.data.objects['rig']  # 替换为你的骨骼名称，如果用户没有给出则不变
        bpy.context.view_layer.objects.active = armature

        left_hand = armature.pose.bones['c_hand_ik.l']
        right_hand = armature.pose.bones['c_hand_ik.r']
        left_foot = armature.pose.bones['c_foot_ik.l']

        left_hand.location.x += arm_length * 0.6  
        left_hand.location.z -= 0.3  
        right_hand.location = hip.location + (0.2, 0, 0) 
        left_foot.location.z += foot_distance * 0.3  
    '''
    user_prompt = f"""
    请帮我添加 bone map header
    pose code:
    {pose_code}
    bone mapping:
    {bone_mapping}
    """
    # 使用streaming获取内容
    response = co.chat_stream(
        model="command-r-plus-08-2024",  # 可以选择适当的模型
        messages=[{"role": "system", "content": system_prompt}, 
                  {"role": "user", "content": user_prompt}],
    )
    
    # 打印实时生成的内容
    pose_code_with_header = ""
    for event in response:
        if event.type == "content-delta":
            pose_code_with_header += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时显示生成的内容
    
    return pose_code_with_header.strip()

def bone_map_header_insert_re(bone_mapping, pose_code):
    """
    在给定的 pose_code 前面插入 bone map header，基于提供的骨骼映射。
    """
    # 如果 bone_mapping 是字典
    if isinstance(bone_mapping, dict):
        bone_map = bone_mapping
    else:
        # 如果是字符串形式，则解析为字典
        bone_map = {}
        for line in bone_mapping.strip().split("\n"):
            key, value = map(str.strip, line.split(","))
            bone_map[key] = value

    # 提取 pose_code 中用到的骨骼变量
    used_bones = set(re.findall(r"\b(\w+)\.location", pose_code))

    # 找到与骨骼变量匹配的映射
    header_lines = [
        "import bpy",
        "# 获取骨骼对象",
        "armature = bpy.data.objects['rig']  # 替换为你的骨骼名称",
        "bpy.context.view_layer.objects.active = armature",
    ]
    for bone_var in used_bones:
        if bone_var in bone_map:
            header_lines.append(f"{bone_var} = armature.pose.bones['{bone_map[bone_var]}']")

    # 生成最终代码
    header = "\n".join(header_lines) + "\n\n"
    return header + pose_code


def convert_to_world_coordinates(input_code):
    """
    将 Blender 骨骼代码中的 `+=` 和 `-=` 操作转换为基于世界坐标方向的逻辑。
    """
    # 定义 system prompt
    system_prompt = """
    你是一个代码生成助手，专注于处理 Blender 的骨骼操作代码。你的任务是解析用户提供的代码，将所有涉及 `+=` 或 `-=` 的骨骼位置操作改为基于世界坐标的逻辑，同时保持代码的功能和结构一致。

    ### 转换规则：
    1. 如果代码中出现 `pose_bone.location +=` 或 `pose_bone.location -=`，需要将其改为基于世界坐标系方向的操作：
       - 使用当前骨骼的世界坐标系方向，将操作中的方向矢量正确转换到局部坐标系中。
       - 保留增量值的大小，只转换方向。

    ### 转换示例：
    #### 输入代码：
    ```python
    right_hand.location.z += 0.4
    ```

    #### 输出代码：
    ```python
    import bpy
    from mathutils import Vector, Matrix

    # 获取骨骼对象
    # 转换基于世界坐标方向的增量
    right_hand.location += (armature.matrix_world @ (right_hand.parent.matrix if right_hand.parent else Matrix())).inverted() @ Vector((0, 0, 0.4))
    ```

    ### 示例：
    #### 输入代码：
    ```python
    import bpy
    from mathutils import Vector, Matrix

    # 获取骨骼对象
    armature = bpy.data.objects['rig']
    bpy.context.view_layer.objects.active = armature

    right_hand = armature.pose.bones['c_hand_ik.r']
    right_hand.location.z += 0.4
    ```

    #### 输出代码：
    import bpy
    from mathutils import Vector, Matrix

    # 获取骨骼对象
    armature = bpy.data.objects['rig']
    bpy.context.view_layer.objects.active = armature

    right_hand = armature.pose.bones['c_hand_ik.r']
    # 对于任何骨骼请都严格按照这个方式来写，不要单独计算world matrix，否则会出错
    right_hand.location += (armature.matrix_world @ (right_hand.parent.matrix if right_hand.parent else Matrix())).inverted() @ Vector((0, 0, 0.4))
    ```
    

    """

    # 构建 user prompt
    user_prompt = f"""
    请帮我将以下代码中所有 `+=` 和 `-=` 的骨骼位置操作转换为基于世界坐标方向的逻辑：

    {input_code}
    """

    # 调用 co.chat_stream 生成结果
    response = co.chat_stream(
        model="command-r-plus-08-2024",  # 模型选择
        messages=[{"role": "system", "content": system_prompt},
                  {"role": "user", "content": user_prompt}],
    )

    # 实时获取生成内容
    converted_code = ""
    for event in response:
        if event.type == "content-delta":
            converted_code += event.delta.message.content.text
            print(event.delta.message.content.text, end="")  # 实时打印输出

    return converted_code.strip()

import re

def convert_to_world_coordinates_re(input_code):
    """
    将 Blender 骨骼代码中的 `+=` 和 `-=` 操作转换为基于世界坐标方向的逻辑。
    """

    def replacement(match):
        # 提取匹配组
        bone_var = match.group(1)  # 骨骼变量名，例如 right_hand
        axis = match.group(2)      # 操作的轴，例如 x, y, z
        operator = match.group(3)  # 操作符 += 或 -=
        value = match.group(4)     # 增量值，例如 0.4
        
        # 构造基于世界坐标转换的代码
        direction = {"x": "Vector((1, 0, 0))", "y": "Vector((0, 1, 0))", "z": "Vector((0, 0, 1))"}
        vector_sign = "+" if operator == "+=" else "-"
        converted = (
            f"{bone_var}.location {operator} "
            f"(armature.matrix_world @ ({bone_var}.parent.matrix if {bone_var}.parent else Matrix())).inverted() @ "
            f"Vector({vector_sign}{direction[axis]} * {value})"
        )
        return converted

    # 正则表达式匹配骨骼位置操作
    pattern = r"(\w+)\.location\.(x|y|z)\s*(\+=|-=)\s*([\d\.\-]+)"
    
    # 替换匹配的增量操作
    converted_code = re.sub(pattern, replacement, input_code)

    # 添加必要的导入和注释
    header = """\
import bpy
from mathutils import Vector, Matrix

# 确保代码基于世界坐标方向进行增量操作
"""
    return header + converted_code

def write_to_file(output_path, **contents):
    """
    将内容写入文件，每部分以标题分隔。

    :param output_path: 输出文件路径
    :param contents: 以标题为键，内容为值的字典
    """
    with open(output_path, "w", encoding="utf-8") as file:
        for title, content in contents.items():
            file.write(f"{title}=======================================:\n")
            file.write(content + "\n\n")

def write_final_code(final_code_path, final_code):
    """
    将最终的代码单独写入一个 Python 文件。

    :param final_code_path: 最终代码输出路径
    :param final_code: 最终代码内容
    """
    with open(final_code_path, "w", encoding="utf-8") as file:
        file.write(final_code)

if __name__ == "__main__":
    overall_start_time = time.time()
    timing_info = []

    # 初始参数
    direction_text = "前方是+y，后方是-y，左边是-x，右边是+x，上方是+z，下方是-z。"
    model_info_text = "角色身高是1.7m，臂长是0.5m，腿长是0.8m。"
    bone_mapping_path = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\boneMapping\arp_map2"
    output_file_path = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\output\pose_output00001.txt"
    final_code_path = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\Scripts\pose_generator\final_code.py"

    # 步骤计时封装
    def timed_step(description, func, *args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        timing_info.append(f"{description} took {elapsed_time:.4f} seconds")
        return result

    # 流程
    bone_mapping = timed_step("Loading bone mapping", load_bone_mapping, bone_mapping_path)
    pose_description = timed_step("Generating pose description", pose_design_streaming, "A person slaps with his left hand.")
    pose_description_relative = timed_step("Adjusting pose description", pose_design_to_relative, pose_description)
    pose_code = timed_step("Generating pose code sequence", generate_pose_code_frame_by_frame, pose_description_relative, bone_mapping)
    # pose_code_fixed = timed_step("Checking bone directions", lambda x: x, pose_code)  # 如需实际修正，可替换为具体函数
    pose_code_fixed = timed_step("Checking bone directions", pose_code_direction_check_and_fix, pose_code, direction_text)  # 如需实际修正，可替换为具体函数
    pose_code_with_header = timed_step("Inserting bone mapping header", bone_map_header_insert_re, bone_mapping, pose_code_fixed)
    pose_code_convert_to_world_coord = timed_step("Converting to world coordinates", convert_to_world_coordinates_re, pose_code_with_header)

    # 写入文件
    timed_step("Writing output to file", write_to_file, output_file_path,
               Timing_Info="\n".join(timing_info),
               Pose_Description=pose_description,
               Pose_Code=pose_code,
               Pose_Code_Check_Direction=pose_code_fixed,
               Pose_Code_with_Header=pose_code_with_header,
               Pose_Code_Converted_to_World_Coord=pose_code_convert_to_world_coord)

    # 单独写入最终代码
    write_final_code(final_code_path, pose_code_convert_to_world_coord)

    # 记录总时间并追加至文件
    overall_elapsed_time = time.time() - overall_start_time
    timing_info.append(f"Total execution time: {overall_elapsed_time:.4f} seconds")
    with open(output_file_path, "a", encoding="utf-8") as file:
        file.write(f"Timing Information=======================================:\n{timing_info[-1]}\n")
