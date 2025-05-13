import sys

sys.path.append('.')

# 去除 BOM 字符并保存新的文件
def remove_bom(input_file, output_file):
    # 以二进制模式读取文件
    with open(input_file, 'rb') as f:
        content = f.read()

    # 检查文件是否以 BOM 字符开始，并去除 BOM 字符
    if content.startswith(b'\xef\xbb\xbf'):
        content = content[3:]

    # 将去除 BOM 后的内容写入新的文件
    with open(output_file, 'wb') as f:
        f.write(content)

    print(f"已成功去除 BOM 字符并保存为：{output_file}")

# 文件路径（您可以修改为自己的文件路径）
input_file = './requirements.txt'  # 输入文件路径
output_file = './requirements_cleaned.txt'  # 输出文件路径

# 调用函数去除 BOM 字符
remove_bom(input_file, output_file)