# 百度输入法词库转换工具

## 功能概述

本工具（one_step_decoding.py）用于将百度输入法的词库文件（.bin格式）转换为Rime输入法兼容的词库文件。

主要功能：
1. 解析百度输入法词库的二进制格式
2. 分离中文词条和英文词条
3. 生成符合Rime标准的词库文件
4. 自动生成随机文件名（16位十六进制）

## 输入输出说明

### 输入文件
- 百度输入法导出的词库文件（.bin格式）
- 文件内容包含中文词条、英文词条和其他系统词条

### 输出文件
程序会生成两个输出文件到输入文件所在目录：

1. **中文词库文件**：
   - 文件名：`[随机16进制]_cn.dict.yaml`
   - 格式：
     ```
     # Rime dictionary
     # encoding: utf-8
     #
     ---
     name: [文件名]_cn
     version: "当前日期"
     sort: by_weight
     ...
     词语1	拼音1	权重1
     词语2	拼音2	权重2
     ```

2. **英文词库文件**：
   - 文件名：`[随机16进制]_en.dict.yaml`
   - 格式：
     ```
     # Rime dictionary
     # encoding: utf-8
     #
     name: [文件名]_en
     version: "当前日期"
     sort: by_weight
     ---
     word1	frequency1
     word2	frequency2
     ...
     ```

## 使用说明

1. win下运行程序（one_step_decoding.py）
2. 选择百度输入法词库文件（.bin格式）
3. 程序会自动在根目录下生成两个文件：
   - `[16位随机十六进制]_cn.dict.yaml`（中文词库）
   - `[16位随机十六进制]_en.dict.yaml`（英文词库）
4. 手动修改文件名、name字段（须保持一致）
5. 将生成的词库文件放入Rime的用户文件夹
6. 在输入法词库（.dict.yaml词库文件）中引用，重新部署

## 文件名生成规则

程序会自动生成随机的16进制文件名：
- 使用8字节随机值（16个十六进制字符）
- 中文词库添加 `_cn` 后缀
- 英文词库添加 `_en` 后缀
- 扩展名为 `.dict.yaml`

例如：
- 中文词库：`a1b2c3d4e5f6g7h8_cn.dict.yaml`
- 英文词库：`a1b2c3d4e5f6g7h8_en.dict.yaml`

## 词库名称设置

词库的 `name` 字段设置为输出文件的名称（不含扩展名）：
- 中文词库：`[随机十六进制]_cn`
- 英文词库：`[随机十六进制]_en`

## 组件化设计

程序采用模块化设计，主要功能组件：
1. `generate_random_filename()` - 生成随机文件名
2. `decode_bin_data()` - 按行解码二进制数据
3. `extract_cn_entry()` - 提取中文词条
4. `extract_en_entry()` - 提取英文词条
5. `parse_bin_file()` - 解析.bin词库
6. `create_rime_header()` - Rime词库头部数据
7. `write_rime_dict()` - 写入词库文件
8. `process_bin_file()` - 处理整个转换流程

## 注意事项

1. 程序会自动跳过无效行和无法解析的内容
2. 输出文件使用UTF-8编码（无BOM）
3. 中文词条格式：`词语\t拼音\t权重`
4. 英文词条格式：`单词\t词频`（使用第四个字段作为词频）
5. 如果某类词条为空，则不生成对应的输出文件