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