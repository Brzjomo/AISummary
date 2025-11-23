import os
import json
import sys
from pathlib import Path
from typing import List, Dict, Optional


class JSONLGenerator:
    """
    为阿里通义批处理API生成JSONL文件的工具
    遵循阿里通义JSONL规范：
    - UTF-8编码
    - 每行一个独立JSON对象
    - 单文件≤50,000请求，≤500MB
    - 每行≤6MB
    - 所有请求使用相同模型
    """
    
    # 常量定义
    MAX_REQUESTS_PER_FILE = 50000  # 单文件最大请求数
    MAX_FILE_SIZE_MB = 500  # 单文件最大大小（MB）
    MAX_LINE_SIZE_MB = 6  # 单行最大大小（MB）
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    MAX_LINE_SIZE_BYTES = MAX_LINE_SIZE_MB * 1024 * 1024
    
    def __init__(self, model: str, temperature: float, system_prompt: str, 
                 input_dir: str, input_extensions: List[str], output_dir: str,
                 output_extension: str = 'json'):
        """
        初始化JSONL生成器
        
        Args:
            model: 模型名称（如'qwen-plus'）
            temperature: 温度值（0.0-2.0）
            system_prompt: 系统提示词
            input_dir: 输入文件目录
            input_extensions: 输入文件扩展名列表
            output_dir: 输出JSONL文件目录
            output_extension: 输出的content文件扩展名
        """
        self.model = model
        self.temperature = float(temperature)  # 保持为数字类型
        self.system_prompt = system_prompt
        self.input_dir = input_dir
        self.input_extensions = [ext.lower() if ext.startswith('.') else f'.{ext.lower()}' 
                                 for ext in input_extensions]
        self.output_dir = output_dir
        self.output_extension = output_extension
        
        # 创建输出目录
        os.makedirs(self.output_dir, exist_ok=True)
    
    def find_input_files(self) -> List[str]:
        """查找目录中的所有输入文件"""
        matched_files = []
        for root, dirs, files in os.walk(self.input_dir):
            for file in files:
                file_ext = os.path.splitext(file)[1].lower()
                if file_ext in self.input_extensions:
                    matched_files.append(os.path.join(root, file))
        return sorted(matched_files)
    
    def read_file_content(self, file_path: str) -> Optional[str]:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"  错误：无法读取文件 {file_path}: {e}")
            return None
    
    def create_request_object(self, custom_id: str, file_content: str) -> Dict:
        """
        创建单个请求对象
        遵循阿里通义批处理API格式
        """
        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": self.model,
                "temperature": self.temperature,
                "messages": [
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": file_content
                    }
                ]
            }
        }
    
    def validate_request_size(self, request_json: str) -> bool:
        """验证单个请求大小是否符合限制"""
        size_bytes = len(request_json.encode('utf-8'))
        if size_bytes > self.MAX_LINE_SIZE_BYTES:
            print(f"  警告：请求大小 {size_bytes / (1024*1024):.2f}MB 超过限制 {self.MAX_LINE_SIZE_MB}MB")
            return False
        return True
    
    def save_jsonl_file(self, requests: List[Dict], base_filename: str = 'batch') -> str:
        """
        保存JSONL文件
        如果文件过大，自动分割
        """
        output_files = []
        current_requests = []
        current_size_bytes = 0
        file_index = 1
        
        for idx, request in enumerate(requests):
            request_json = json.dumps(request, ensure_ascii=False, separators=(',', ':'))
            request_size = len(request_json.encode('utf-8')) + 1  # +1 for newline
            
            # 检查大小限制
            if not self.validate_request_size(request_json):
                print(f"  跳过：custom_id={request['custom_id']} 的请求过大")
                continue
            
            # 如果添加这个请求会超过限制，则保存当前文件
            if (len(current_requests) >= self.MAX_REQUESTS_PER_FILE or
                current_size_bytes + request_size > self.MAX_FILE_SIZE_BYTES) and current_requests:
                
                output_file = self._write_jsonl_file(current_requests, base_filename, file_index)
                output_files.append(output_file)
                current_requests = []
                current_size_bytes = 0
                file_index += 1
            
            current_requests.append(request)
            current_size_bytes += request_size
        
        # 保存最后一批请求
        if current_requests:
            output_file = self._write_jsonl_file(current_requests, base_filename, file_index)
            output_files.append(output_file)
        
        return output_files
    
    def _write_jsonl_file(self, requests: List[Dict], base_filename: str, index: int) -> str:
        """写入单个JSONL文件"""
        # 生成输出文件名
        if index > 1:
            output_filename = f"{base_filename}_part{index}.jsonl"
        else:
            output_filename = f"{base_filename}.jsonl"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for request in requests:
                    json_line = json.dumps(request, ensure_ascii=False, separators=(',', ':'))
                    f.write(json_line + '\n')
            
            file_size_mb = os.path.getsize(output_path) / (1024 * 1024)
            print(f"  已保存：{output_filename} ({len(requests)} 个请求, {file_size_mb:.2f}MB)")
            return output_path
        
        except Exception as e:
            print(f"  错误：无法保存文件 {output_path}: {e}")
            return None
    
    def generate_jsonl(self, base_filename: str = 'batch') -> List[str]:
        """
        生成JSONL文件
        
        Args:
            base_filename: 输出文件的基础名称（不含扩展名）
        
        Returns:
            生成的输出文件路径列表
        """
        print(f"开始生成JSONL批处理文件...")
        print(f"  模型: {self.model}")
        print(f"  温度: {self.temperature}")
        print(f"  输入目录: {self.input_dir}")
        print(f"  输入文件类型: {', '.join([ext.lstrip('.') for ext in self.input_extensions])}")
        print(f"  输出目录: {self.output_dir}")
        print()
        
        # 扫描输入文件
        input_files = self.find_input_files()
        
        if not input_files:
            print(f"未找到指定类型的输入文件")
            return []
        
        print(f"找到 {len(input_files)} 个输入文件")
        print()
        
        # 生成请求对象
        requests = []
        skipped_count = 0
        
        for i, file_path in enumerate(input_files, 1):
            file_name = os.path.basename(file_path)
            custom_id = f"{i:05d}"  # 使用5位数字作为custom_id
            
            # 读取文件内容
            content = self.read_file_content(file_path)
            if content is None:
                skipped_count += 1
                continue
            
            # 创建请求对象
            request = self.create_request_object(custom_id, content)
            requests.append(request)
            
            print(f"[{i}/{len(input_files)}] 已加载：{file_name} (custom_id: {custom_id})")
        
        if not requests:
            print("未能加载任何文件")
            return []
        
        print()
        print(f"成功加载 {len(requests)} 个文件，跳过 {skipped_count} 个")
        print()
        
        # 保存JSONL文件
        output_files = self.save_jsonl_file(requests, base_filename)
        
        print()
        print(f"=== 生成摘要 ===")
        print(f"输入文件数: {len(requests)}")
        print(f"输出文件数: {len(output_files)}")
        print(f"总请求数: {len(requests)}")
        
        return output_files


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='为阿里通义批处理API生成JSONL文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python generate_jsonl.py qwen-plus 1.3 "You are helpful" ./input -e txt
  python generate_jsonl.py qwen-plus 1.3 "You are helpful" ./input -e txt,srt -o ./output
        """
    )
    
    parser.add_argument('model', help='模型名称（如：qwen-plus）')
    parser.add_argument('temperature', type=float, help='温度值（0.0-2.0）')
    parser.add_argument('system_prompt', help='系统提示词')
    parser.add_argument('input_dir', help='输入文件目录')
    parser.add_argument('-e', '--extensions', default='txt', 
                       help='输入文件扩展名（逗号分隔，默认：txt）')
    parser.add_argument('-o', '--output', default=None,
                       help='输出目录（默认：输入目录）')
    parser.add_argument('-n', '--name', default='batch',
                       help='输出文件名前缀（默认：batch）')
    
    args = parser.parse_args()
    
    # 检查输入目录
    if not os.path.exists(args.input_dir):
        print(f"错误：输入目录 '{args.input_dir}' 不存在")
        return 1
    
    # 确定输出目录
    output_dir = args.output if args.output else args.input_dir
    
    # 解析扩展名
    extensions = [ext.strip() for ext in args.extensions.split(',')]
    
    # 验证温度值
    if not (0.0 <= args.temperature <= 2.0):
        print(f"错误：温度值必须在0.0-2.0之间")
        return 1
    
    # 生成JSONL
    generator = JSONLGenerator(
        model=args.model,
        temperature=args.temperature,
        system_prompt=args.system_prompt,
        input_dir=args.input_dir,
        input_extensions=extensions,
        output_dir=output_dir
    )
    
    output_files = generator.generate_jsonl(args.name)
    
    if output_files:
        print("\n✅ 生成完成！")
        return 0
    else:
        print("\n❌ 生成失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
