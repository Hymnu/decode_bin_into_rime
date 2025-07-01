import base64
import os
import re
import tkinter as tk
from tkinter import filedialog
import datetime
import secrets
import binascii

# 定义掩码和自定义 Base64 编码表
MASK = 0x2D382324
TABLE = b"qogjOuCRNkfil5p4SQ3LAmxGKZTdesvB6z_YPahMI9t80rJyHW1DEwFbc7nUVX2-"
DECODE_TABLE = bytes.maketrans(TABLE, bytes(range(64)))

def generate_random_filename(prefix="", suffix=""):
    """生成随机16进制文件名"""
    # 生成8字节随机值（16个十六进制字符）
    random_bytes = secrets.token_bytes(8)
    hex_name = binascii.hexlify(random_bytes).decode('ascii')
    return f"{prefix}{hex_name}{suffix}"

def decode_bin_data(data: bytes):
    """解码百度词库二进制数据行"""
    # 检查输入数据是否符合要求
    if len(data) % 4 != 2:
        return None
    base64_remainder = data[-2] - 65
    if base64_remainder not in {0, 1, 2} or data[-1] != 0:
        return None

    # 使用自定义 Base64 编码表解码
    data = data.translate(DECODE_TABLE)
    transformed = bytearray()

    # 解码逻辑
    for i in range(0, len(data) - 2, 4):
        high_bits = data[i + 3]
        transformed += bytes((
            data[i] | (high_bits & 0b110000) << 2,
            data[i + 1] | (high_bits & 0b1100) << 4,
            data[i + 2] | (high_bits & 0b11) << 6,
        ))

    # 去掉多余的填充字节
    if base64_remainder:
        for i in range(3 - base64_remainder):
            if transformed and transformed[-1] == 0:
                transformed.pop()

    result = bytearray()

    # 进行掩码和位操作
    for i in range(0, len(transformed) // 4 * 4, 4):
        chunk = MASK ^ int.from_bytes(transformed[i:i+4], byteorder="little")
        chunk = (chunk & 0x1FFFFFFF) << 3 | chunk >> 29
        result += chunk.to_bytes(4, byteorder="little")

    # 处理剩余的字节
    if remainder := transformed[i+4:]:
        chunk = MASK ^ int.from_bytes(remainder, byteorder="little")
        result += chunk.to_bytes(4, byteorder="little")[:len(remainder)]
    
    return result

def extract_cn_entry(line_str):
    """提取中文词条"""
    match = re.match(r'^([^(]+)\(([^)]+)\)\s+(\d+)', line_str)
    if not match:
        return None
    
    word = match.group(1)
    pinyin = match.group(2).replace('|', ' ')  # 转换拼音格式
    weight = match.group(3)
    return f"{word}\t{pinyin}\t{weight}"

def extract_en_entry(line_str):
    """提取英文词条"""
    parts = line_str.split('\t')
    if len(parts) < 5:
        return None
    
    word = parts[0].strip()
    frequency = parts[3]  # 第四个字段（索引3）是词频
    if not word:
        return None
    
    return f"{word}\t{frequency}"

def parse_bin_file(input_path):
    """解析百度词库文件，返回中文和英文词条列表"""
    cn_entries = []
    en_entries = []
    section = None  # 当前处理的段类型
    
    with open(input_path, "rb") as bin_file:
        bin_file.seek(1)  # 跳过文件头的第一个字节
        
        for line in bin_file:
            if len(line) < 2:
                continue
                
            # 去掉每行的首尾字节
            data = line[1:-1]
            if not data:
                continue
                
            # 解码二进制数据
            decoded_bytes = decode_bin_data(data)
            if decoded_bytes is None:
                continue
                
            try:
                # 将解码后的字节转换为字符串（UTF-16LE编码）
                line_str = decoded_bytes.decode('utf-16-le').strip()
                if not line_str:
                    continue
                    
                # 检查是否为分段标记
                if line_str.startswith('<') and line_str.endswith('>'):
                    section = line_str[1:-1].lower()  # 提取段类型
                    continue
                    
                # 根据当前段类型处理内容
                if section == 'cnword':
                    entry = extract_cn_entry(line_str)
                    if entry:
                        cn_entries.append(entry)
                elif section == 'enword':
                    entry = extract_en_entry(line_str)
                    if entry:
                        en_entries.append(entry)
            except UnicodeDecodeError:
                continue
                
    return cn_entries, en_entries

def create_rime_header(dict_name):
    """创建Rime词库头部元数据"""
    current_date = datetime.datetime.now().strftime("%Y.%m.%d")
    return [
        "# Rime dictionary",
        "# encoding: utf-8",
        "#",
        f"name: {dict_name}",
        f'version: "{current_date}"',
        "sort: by_weight",
        "---"
    ]

def write_rime_dict(entries, output_path, dict_name):
    """将词条写入Rime词库文件"""
    header = create_rime_header(dict_name)
    with open(output_path, 'w', encoding='utf-8') as outfile:
        outfile.write("\n".join(header) + "\n")
        outfile.write("\n".join(entries))

def process_bin_file(input_path, output_dir):
    """处理整个百度词库文件并生成Rime词库"""
    # 生成随机文件名（16个十六进制字符）
    random_base = generate_random_filename()
    
    # 中文词库文件名和词库名称
    cn_base = random_base + "_cn"
    cn_filename = cn_base + ".dict.yaml"  # 文件名包含后缀
    cn_output_path = os.path.join(output_dir, cn_filename)
    cn_dict_name = cn_base  # 词库名称不包含后缀
    
    # 英文词库文件名和词库名称
    en_base = random_base + "_en"
    en_filename = en_base + ".dict.yaml"  # 文件名包含后缀
    en_output_path = os.path.join(output_dir, en_filename)
    en_dict_name = en_base  # 词库名称不包含后缀
    
    # 解析输入文件
    cn_entries, en_entries = parse_bin_file(input_path)
    
    # 写入中文词库
    if cn_entries:
        write_rime_dict(cn_entries, cn_output_path, cn_dict_name)
    
    # 写入英文词库
    if en_entries:
        write_rime_dict(en_entries, en_output_path, en_dict_name)
    
    return cn_output_path, en_output_path, len(cn_entries), len(en_entries)

def main():
    """主函数：处理文件选择"""
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 选择输入文件
    input_path = filedialog.askopenfilename(
        title="选择百度输入法词库文件",
        filetypes=[("百度输入法词库", "*.bin"), ("所有文件", "*.*")]
    )
    if not input_path:
        print("未选择输入文件，操作取消")
        return
    
    # 获取输出目录（输入文件所在目录）
    output_dir = os.path.dirname(input_path)
    
    try:
        cn_path, en_path, cn_count, en_count = process_bin_file(input_path, output_dir)
        print(f"转换完成! 成功转换 {cn_count} 个中文词条和 {en_count} 个英文词条")
        print(f"中文词库: {cn_path}")
        print(f"英文词库: {en_path}")
    except Exception as e:
        print(f"转换过程中出错: {str(e)}")

if __name__ == "__main__":
    main()