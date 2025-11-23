import os
import shutil
import sys
from pathlib import Path


class LogToJsonConverter:
    """
    将.log文件复制并转换为同名.json文件的工具
    只改后缀名，不改内容
    """
    
    def __init__(self, input_directory=".", output_directory=None):
        self.input_directory = input_directory
        # 如果未指定输出目录，则使用输入目录作为输出目录
        self.output_directory = output_directory if output_directory is not None else input_directory
        
        # 创建输出目录
        os.makedirs(self.output_directory, exist_ok=True)
    
    def find_log_files(self):
        """查找目录中的所有.log文件"""
        log_files = []
        
        # 递归查找所有.log文件
        for root, dirs, files in os.walk(self.input_directory):
            for file in files:
                if file.endswith('.log'):
                    log_files.append(os.path.join(root, file))
        
        return log_files
    
    def convert_log_to_json(self, log_file_path):
        """
        将.log文件复制为.json文件
        只改后缀名，保持内容完全不变
        """
        try:
            print(f"正在处理: {log_file_path}")
            
            # 读取原始内容（保持原样）
            with open(log_file_path, 'rb') as f:
                content = f.read()
            
            # 生成输出文件名（只改后缀）
            file_name = Path(log_file_path).stem
            output_dir = self.output_directory
            
            # 如果输出目录与输入目录不同，需要保持目录结构
            if self.output_directory != self.input_directory:
                # 计算相对路径并在输出目录中创建相同的目录结构
                relative_path = os.path.relpath(log_file_path, self.input_directory)
                relative_dir = os.path.dirname(relative_path)
                if relative_dir:
                    output_dir = os.path.join(self.output_directory, relative_dir)
                    os.makedirs(output_dir, exist_ok=True)
            
            output_path = os.path.join(output_dir, f"{file_name}.json")
            
            # 写入JSON文件（二进制模式保证内容完全相同）
            with open(output_path, 'wb') as f:
                f.write(content)
            
            print(f"  已转换: {output_path}")
            return True
            
        except Exception as e:
            print(f"  处理文件时出错: {e}")
            return False
    
    def process_all_files(self):
        """处理所有.log文件"""
        log_files = self.find_log_files()
        
        if not log_files:
            print(f"在目录 {self.input_directory} 中未找到.log文件")
            return 0
        
        print(f"找到 {len(log_files)} 个.log文件")
        print(f"输入目录: {self.input_directory}")
        print(f"输出目录: {self.output_directory}")
        print()
        
        successful_conversions = 0
        
        for log_file in log_files:
            if self.convert_log_to_json(log_file):
                successful_conversions += 1
        
        print(f"\n=== 转换摘要 ===")
        print(f"总.log文件数: {len(log_files)}")
        print(f"成功转换: {successful_conversions}")
        print(f"失败: {len(log_files) - successful_conversions}")
        
        return successful_conversions


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='将.log文件复制并转换为同名.json文件（只改后缀名，内容保持不变）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python log2json.py .                    # 处理当前目录中的所有.log文件
  python log2json.py ./logs               # 处理./logs目录中的所有.log文件
  python log2json.py ./logs -o ./output   # 将转换结果输出到./output目录
        """
    )
    
    parser.add_argument('input_dir', nargs='?', default='.',
                       help='包含.log文件的目录 (默认: 当前目录)')
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
    converter = LogToJsonConverter(args.input_dir, output_dir)
    result = converter.process_all_files()
    
    return 0 if result > 0 or len(converter.find_log_files()) == 0 else 1


# 直接运行时的简单接口
if __name__ == "__main__":
    # 如果提供了命令行参数，使用argparse
    if len(sys.argv) > 1:
        sys.exit(main())
    
    # 否则使用简单交互式界面
    print("=== .log转.json文件转换器 ===")
    print("将.log文件复制并转换为同名.json文件")
    print("（只改后缀名，内容保持不变）")
    print()
    
    input_dir = input("请输入包含.log文件的目录路径 (留空使用当前目录): ").strip()
    if not input_dir:
        input_dir = "."
    
    if not os.path.exists(input_dir):
        print(f"错误: 目录 '{input_dir}' 不存在")
        sys.exit(1)
    
    output_dir = input("请输入输出目录 (留空使用输入目录): ").strip()
    if not output_dir:
        output_dir = input_dir
    
    # 创建转换器并处理文件
    converter = LogToJsonConverter(input_dir, output_dir)
    converter.process_all_files()
    
    print("\n转换完成!")
