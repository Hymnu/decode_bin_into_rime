import base64
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename, asksaveasfilename

# 定义掩码和自定义 Base64 编码表
MASK = 0x2D382324
TABLE = b"qogjOuCRNkfil5p4SQ3LAmxGKZTdesvB6z_YPahMI9t80rJyHW1DEwFbc7nUVX2-"
DECODE_TABLE = bytes.maketrans(TABLE, bytes(range(64)))

def decode(data: bytes):
    # 检查输入数据是否符合要求
    assert len(data) % 4 == 2
    assert (base64_remainder := data[-2] - 65) in {0, 1, 2} and data[-1] == 0

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
            assert transformed.pop() == 0

    result = bytearray()

    # 进行掩码和位操作
    for i in range(0, len(transformed) // 4 * 4, 4):
        chunk = MASK ^ int.from_bytes(transformed[i : i + 4], byteorder="little")
        chunk = (chunk & 0x1FFFFFFF) << 3 | chunk >> 29
        result += chunk.to_bytes(4, byteorder="little")

    # 处理剩余的字节
    if remainder := transformed[i + 4:]:
        chunk = MASK ^ int.from_bytes(remainder, byteorder="little")
        result += chunk.to_bytes(4, byteorder="little")[: len(remainder)]

    return result

def decode_bin(input_path: str, output_path: str):
    # 检查输入和输出文件的扩展名
    assert input_path.endswith(".bin") and output_path.endswith(".txt")
    with open(input_path, "rb") as f, open(output_path, "wb") as output:
        output.write(b"\xff\xfe")  # 写入 UTF-16LE 的 BOM
        f.seek(1)  # 跳过文件头的第一个字节
        for line in f:
            if data := line[1:-1]:  # 去掉每行的首尾字节
                output.write(decode(data))
                output.write(b"\n\0")  # 写入换行符和空字节

def main():
    # 初始化Tkinter但不显示主窗口
    Tk().withdraw()
    
    # 打开文件选择对话框
    input_path = askopenfilename(
        title="选择百度输入法词库文件",
        filetypes=[("百度输入法词库", "*.bin"), ("所有文件", "*.*")]
    )
    
    if not input_path:
        print("未选择文件，程序退出")
        return
    
    # 自动生成输出路径（相同目录，扩展名改为.txt）
    output_dir = os.path.dirname(input_path)
    input_filename = os.path.basename(input_path)
    output_filename = os.path.splitext(input_filename)[0] + ".txt"
    default_output = os.path.join(output_dir, output_filename)
    
    # 保存文件对话框
    output_path = asksaveasfilename(
        title="保存转换结果",
        initialfile=output_filename,
        initialdir=output_dir,
        defaultextension=".txt",
        filetypes=[("文本文件", "*.txt")]
    )
    
    if not output_path:
        print("未指定输出路径，程序退出")
        return
    
    # 执行转换
    decode_bin(input_path, output_path)
    print(f"转换完成! 结果已保存到: {output_path}")

if __name__ == "__main__":
    main()