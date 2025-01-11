import numpy as np

# 文件路径
file_path = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\dataset\KIT-ML-20241225T030244Z-001\KIT-ML\new_joints\new_joints\00001.npy"

def load_and_inspect_npy(file_path):
    try:
        # 加载 .npy 文件
        data = np.load(file_path, allow_pickle=True)  # 如果数据包含对象，用 allow_pickle=True
        
        # 输出数据的基本信息
        print("数据类型:", type(data))
        print("数组形状:", data.shape if isinstance(data, np.ndarray) else "非数组数据")
        print("数据类型:", data.dtype if isinstance(data, np.ndarray) else "N/A")
        
        # 打印部分内容，避免因数据过大导致输出混乱
        if isinstance(data, np.ndarray):
            print("\n数据预览:")
            print(data[:min(5, len(data))])  # 仅显示前 5 个元素
        else:
            print("\n数据内容:")
            print(data)
            
    except Exception as e:
        print("加载文件时出错:", str(e))

# 调用函数加载并查看文件
load_and_inspect_npy(file_path)
