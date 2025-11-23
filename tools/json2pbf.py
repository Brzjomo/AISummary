import os
import json
import glob
import sys
from pathlib import Path

class JsonToPbfConverter:
    """
    将JSON文件转换为PotPlayer书签文件(PBF)的工具
    确保使用正确的UTF-16 LE编码并包含BOM
    """
    
    def __init__(self, input_directory=".", output_directory=None):
        self.input_directory = input_directory
        # 如果未指定输出目录，则使用输入目录作为输出目录
        self.output_directory = output_directory if output_directory is not None else input_directory

        # 创建输出目录
        os.makedirs(self.output_directory, exist_ok=True)
    
    def find_json_files(self):
        """查找目录中的所有JSON文件"""
        pattern = os.path.join(self.input_directory, "**", "*bookmarks.json")
        json_files = glob.glob(pattern, recursive=True)
        
        # 如果没有找到，尝试非递归查找
        if not json_files:
            pattern = os.path.join(self.input_directory, "*bookmarks.json")
            json_files = glob.glob(pattern)
        
        # 如果没有找到特定格式的，查找所有JSON文件
        if not json_files:
            pattern = os.path.join(self.input_directory, "**", "*.json")
            json_files = glob.glob(pattern, recursive=True)
            
            if not json_files:
                pattern = os.path.join(self.input_directory, "*.json")
                json_files = glob.glob(pattern)
        
        return json_files
    
    def parse_json_file(self, json_file_path):
        """解析JSON文件"""
        try:
            print(f"正在解析: {json_file_path}")

            # 读取原始文本，以便在必要时移除代码块围栏
            with open(json_file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            # 移除可能的UTF-8 BOM
            if text.startswith('\ufeff'):
                text = text.lstrip('\ufeff')

            # 如果以 ```json 开头，移除该行及其后面的换行
            stripped = text.lstrip()
            if stripped.startswith('```json'):
                # 找到第一个换行的位置并截断到其后
                first_newline = stripped.find('\n')
                if first_newline != -1:
                    stripped = stripped[first_newline+1:]
                else:
                    # 整个文件就是一行 ```json，清空
                    stripped = ''

            else:
                stripped = text

            # 如果以 ``` 结尾，则去掉末尾的 ``` 及前后的空白
            if stripped.rstrip().endswith('```'):
                stripped = stripped.rstrip()
                # 移除最后的三个反引号
                stripped = stripped[:-3].rstrip()

            # 最后尝试解析JSON字符串
            data = json.loads(stripped)
            
            # 检查JSON结构
            if 'bookmarks' in data:
                bookmarks = data['bookmarks']
                print(f"  找到 {len(bookmarks)} 个书签")
                return bookmarks
            else:
                # 尝试直接读取书签数组
                if isinstance(data, list) and len(data) > 0 and all(
                    isinstance(item, dict) and 'time_formatted' in item for item in data
                ):
                    print(f"  找到 {len(data)} 个书签 (直接数组)")
                    return data
                else:
                    print(f"  错误: JSON文件格式不正确")
                    return None
                    
        except Exception as e:
            print(f"  解析JSON文件时出错: {e}")
            return None
    
    def time_formatted_to_milliseconds(self, time_str):
        """将时间格式(HH:MM:SS.mmm)转换为毫秒"""
        try:
            # 分割小时、分钟、秒和毫秒
            time_parts = time_str.split('.')
            if len(time_parts) != 2:
                print(f"  错误: 时间格式不正确: {time_str}")
                return 0
            
            hms_part = time_parts[0]  # HH:MM:SS
            ms_part = time_parts[1]   # mmm
            
            # 分割小时、分钟、秒
            hms_parts = hms_part.split(':')
            if len(hms_parts) != 3:
                print(f"  错误: 时间格式不正确: {time_str}")
                return 0
            
            hours = int(hms_parts[0])
            minutes = int(hms_parts[1])
            seconds = int(hms_parts[2])
            milliseconds = int(ms_part)
            
            # 计算总毫秒数
            total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000 + milliseconds
            return total_ms
            
        except Exception as e:
            print(f"  转换时间格式时出错: {time_str}, 错误: {e}")
            return 0
    
    def convert_bookmarks_to_pbf_format(self, bookmarks):
        """将书签列表转换为PBF格式字符串，确保末尾有正确的空行"""
        pbf_lines = ["[Bookmark]"]
        
        for i, bookmark in enumerate(bookmarks):
            # 获取书签信息
            index = bookmark.get('index', str(i))
            name = bookmark.get('name', f'Bookmark_{i}')
            time_formatted = bookmark.get('time_formatted', '00:00:00.000')
            
            # 转换为毫秒
            milliseconds = self.time_formatted_to_milliseconds(time_formatted)
            
            # 创建PBF行
            pbf_line = f"{index}={milliseconds}*{name}*"
            pbf_lines.append(pbf_line)
        
        # 添加空行 - 使用下一个索引号
        next_index = len(bookmarks)
        pbf_lines.append(f"{next_index}=")
        
        return '\n'.join(pbf_lines)
    
    def save_pbf_file(self, pbf_content, output_path):
        """将PBF内容保存为UTF-16LE编码的文件，包含BOM"""
        try:
            # 使用UTF-16LE编码写入文件，包含BOM
            with open(output_path, 'wb') as f:
                # 写入UTF-16 LE BOM
                f.write(b'\xFF\xFE')
                # 将内容编码为UTF-16 LE
                f.write(pbf_content.encode('utf-16-le'))
            
            print(f"  已保存: {output_path}")
            return True
            
        except Exception as e:
            print(f"  保存PBF文件时出错: {e}")
            return False
    
    def process_all_files(self):
        """处理所有JSON文件"""
        json_files = self.find_json_files()
        
        if not json_files:
            print(f"在目录 {self.input_directory} 中未找到JSON文件")
            return
        
        print(f"找到 {len(json_files)} 个JSON文件")
        
        successful_conversions = 0
        
        for json_file in json_files:
            bookmarks = self.parse_json_file(json_file)
            
            if bookmarks:
                # 生成输出文件名
                file_name = Path(json_file).stem
                # 移除可能的_bookmarks后缀
                if file_name.endswith('_bookmarks'):
                    file_name = file_name[:-10]  # 移除"_bookmarks"
                
                output_path = os.path.join(self.output_directory, f"{file_name}.pbf")
                
                # 转换为PBF格式
                pbf_content = self.convert_bookmarks_to_pbf_format(bookmarks)
                
                # 保存PBF文件
                if self.save_pbf_file(pbf_content, output_path):
                    successful_conversions += 1
                    
                # 显示生成的PBF内容预览
                # print("  生成的PBF文件内容预览:")
                # for line in pbf_content.split('\n'):
                #     print(f"    {line}")
            else:
                print(f"  转换失败: {json_file}")
        
        print(f"\n=== 转换摘要 ===")
        print(f"输入目录: {self.input_directory}")
        print(f"输出目录: {self.output_directory}")
        print(f"总JSON文件数: {len(json_files)}")
        print(f"成功转换: {successful_conversions}")
        print(f"失败: {len(json_files) - successful_conversions}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='将JSON文件转换为PotPlayer书签文件(PBF)')
    parser.add_argument('input_dir', nargs='?', default='.', 
                       help='包含JSON文件的目录 (默认: 当前目录)')
    parser.add_argument('-o', '--output', default=None,
                       help='输出目录 (默认: 与输入目录相同)')
    
    args = parser.parse_args()
    
    # 检查输入目录是否存在
    if not os.path.exists(args.input_dir):
        print(f"错误: 目录 '{args.input_dir}' 不存在")
        return 1

    # 如果未指定输出目录，则使用输入目录
    output_dir = args.output if args.output is not None else args.input_dir

    # 创建转换器并处理文件
    converter = JsonToPbfConverter(args.input_dir, output_dir)
    converter.process_all_files()
    
    return 0

# 直接运行时的简单接口
if __name__ == "__main__":
    # 如果提供了命令行参数，使用argparse
    if len(sys.argv) > 1:
        sys.exit(main())
    
    # 否则使用简单交互式界面
    print("=== JSON转PBF文件转换器 ===")
    print("将JSON书签文件转换为PotPlayer书签文件(.pbf)")
    
    input_dir = input("请输入包含JSON文件的目录路径 (留空使用当前目录): ").strip()
    if not input_dir:
        input_dir = "."

    output_dir = input("请输入输出目录 (留空使用输入目录): ").strip()
    if not output_dir:
        output_dir = input_dir
    
    # 创建转换器并处理文件
    converter = JsonToPbfConverter(input_dir, output_dir)
    converter.process_all_files()
    
    print("\n转换完成!")
