import os
import csv
import json

# 文件路径
data_dir = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\dataset\kit-ml\2017-06-22"
val_file = r"E:\000CCCProject\ChatPoseBlender\blender-pose-generator\dataset\KIT-ML-20241225T030244Z-001\KIT-ML\val.txt"
output_csv = r"output.csv"

# 读取 val.txt 中的文件名数字
def read_val_file(val_file):
    with open(val_file, 'r') as f:
        lines = f.readlines()
    # 提取文件名中的数字
    return [line.strip().split('.')[0] for line in lines]

# 读取 JSON 文件内容
def read_json_file(json_path):
    try:
        with open(json_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

# 写入 CSV 文件
def write_to_csv(data, output_csv):
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        # 写入表头
        writer.writerow(["Number", "Content"])
        # 写入数据
        writer.writerows(data)

# 主流程
def main():
    # 读取 val.txt
    numbers = read_val_file(val_file)
    print(numbers)
    # 处理数据
    results = []
    for number in numbers:
        json_file = os.path.join(data_dir, f"{number}_annotations.json")
        content = read_json_file(json_file)
        if content:
            results.append([number, json.dumps(content)])

    # 写入 CSV
    write_to_csv(results, output_csv)
    print(f"数据已保存到 {output_csv}")

if __name__ == "__main__":
    main()
