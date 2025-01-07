import os
import shutil
from pathlib import Path

def move_files_with_structure(source_dir: str, dest_dir: str, file_types: list[str]):
    """
    将源目录中指定类型的文件移动到目标目录，保持原有的目录结构
    
    Args:
        source_dir: 源目录路径
        dest_dir: 目标目录路径
        file_types: 要移动的文件类型列表，例如 ['.md', '.txt']
    """
    # 转换为Path对象便于处理
    source_path = Path(source_dir)
    dest_path = Path(dest_dir)
    
    # 确保目标目录存在
    dest_path.mkdir(parents=True, exist_ok=True)
    
    # 遍历源目录
    for root, dirs, files in os.walk(source_dir):
        # 将当前路径转换为Path对象
        current_path = Path(root)
        
        # 计算相对路径
        relative_path = current_path.relative_to(source_path)
        
        # 在目标目录中创建对应的子目录
        target_dir = dest_path / relative_path
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 遍历当前目录中的文件
        for file in files:
            file_path = current_path / file
            
            # 检查文件扩展名是否在指定类型列表中
            if file_path.suffix.lower() in file_types:
                # 构建目标文件路径
                dest_file = target_dir / file
                
                # 移动文件
                shutil.move(str(file_path), str(dest_file))
                print(f"已移动: {file_path} -> {dest_file}")

# 使用示例
if __name__ == "__main__":
    # 设置源目录和目标目录
    source_directory = r"D:\Git\github\StructuredFileMover\dist"
    destination_directory = r"D:\Git\github\StructuredFileMover\soucre"
    
    # 设置要移动的文件类型
    file_extensions = ['.md']
    
    # 执行移动操作
    move_files_with_structure(source_directory, destination_directory, file_extensions) 