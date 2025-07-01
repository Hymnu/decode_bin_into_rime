import re
import tkinter as tk
from tkinter import filedialog
import datetime

def convert_line(line):
    """转换单行文本到目标格式"""
    match = re.match(r'^([^(]+)\(([^)]+)\)\s+(\d+)', line)
    """匹配对象：3个捕获组
    ^([^(]+): 捕获词条，直到第一个左括号
    \(([^)]+)\): 捕获拼音，括号内的内容
    \s+(\d+): 捕获数字（权重），前面有一个或多个空格（实际仅一个）
    """
    if not match:
        return None
    
    word = match.group(1)
    pinyin = match.group(2).replace('|', ' ')# 百度拼音用竖线分隔，rime为空格
    weight = match.group(3)
    
    return f"{word}\t{pinyin}\t{weight}"

def convert_file(input_path, output_path):
    """转换整个文件"""
    # 检测文件编码
    with open(input_path, 'rb') as f:
        bom = f.read(2)
        encoding = 'utf-16-le' if bom == b'\xff\xfe' else 'utf-8'
    
    # 读取并转换内容
    converted_lines = []
    with open(input_path, 'r', encoding=encoding) as infile:
        for line in infile:
            line = line.strip()
            if line:
                converted = convert_line(line)
                if converted:
                    converted_lines.append(converted)
    
    # 准备Rime词库头部元数据
    current_date = datetime.datetime.now().strftime("%Y.%m.%d")
    header = [
        "# Rime dictionary",
        "# encoding: utf-8",
        "#",
        f"name: baidu",
        f'version: "{current_date}"',
        "sort: by_weight",
        "---"
    ]
    
    # 写入输出文件
    with open(output_path, 'w', encoding='utf-8') as outfile:
        # 写入头部元数据
        outfile.write("\n".join(header) + "\n")
        # 写入转换后的词条
        outfile.write("\n".join(converted_lines))

def main():
    """主函数：处理文件选择"""
    root = tk.Tk()
    root.withdraw()
    
    # 选择输入文件
    input_path = filedialog.askopenfilename(
        title="选择百度词库文本文件",
        filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
    )
    if not input_path:
        print("未选择输入文件，操作取消")
        return
    
    # 自动生成输出路径（使用.dict.yaml扩展名）
    output_dir = os.path.dirname(input_path)
    input_filename = os.path.basename(input_path)
    output_filename = os.path.splitext(input_filename)[0] + ".dict.yaml"
    output_path = os.path.join(output_dir, output_filename)
    
    # 执行转换
    convert_file(input_path, output_path)
    print(f"转换完成! Rime词库已保存到: {output_path}")

if __name__ == "__main__":
    import os
    main()