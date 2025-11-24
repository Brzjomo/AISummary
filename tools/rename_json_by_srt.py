#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interactive script to rename JSON files based on SRT files order.
Scans SRT files in source directory and JSON files in target directory,
then renames JSON files to match the SRT file naming order.
"""

import os
import sys
from pathlib import Path


def get_user_input(prompt):
    """Get user input with validation."""
    while True:
        path = input(prompt).strip()
        if not path:
            print("错误：路径不能为空，请重试。")
            continue
        
        # Handle Windows quotes and expand user home directory
        path = path.strip('"\'')
        path = os.path.expanduser(path)
        
        if not os.path.isdir(path):
            print(f"错误：'{path}' 不是有效的目录，请重试。")
            continue
        
        return path


def get_srt_files(source_dir):
    """Scan source directory for SRT files and return sorted list."""
    srt_files = sorted([f for f in os.listdir(source_dir) if f.lower().endswith('.srt')])
    return srt_files


def get_json_files(target_dir):
    """Scan target directory for JSON files and return sorted list."""
    json_files = sorted([f for f in os.listdir(target_dir) if f.lower().endswith('.json')])
    return json_files


def get_base_name(filename):
    """Get the base name without extension."""
    return os.path.splitext(filename)[0]


def rename_files(source_dir, target_dir, srt_files, json_files):
    """Rename JSON files based on SRT file order."""
    print("\n" + "="*60)
    print("正在重命名 JSON 文件...")
    print("="*60)
    
    renamed_count = 0
    
    for i, srt_file in enumerate(srt_files):
        if i >= len(json_files):
            break
        
        json_file = json_files[i]
        srt_base_name = get_base_name(srt_file)
        json_base_name = get_base_name(json_file)
        json_extension = os.path.splitext(json_file)[1]
        
        # Create new JSON filename based on SRT name
        new_json_name = srt_base_name + json_extension
        
        old_path = os.path.join(target_dir, json_file)
        new_path = os.path.join(target_dir, new_json_name)
        
        # Avoid overwriting if the new name is the same as old
        if old_path == new_path:
            print(f"[{i+1}/{len(srt_files)}] {json_file} (无需重命名)")
            continue
        
        # Check if target file already exists (shouldn't happen in normal cases)
        if os.path.exists(new_path) and old_path != new_path:
            print(f"[{i+1}/{len(srt_files)}] 警告：{new_json_name} 已存在，已跳过")
            continue
        
        try:
            os.rename(old_path, new_path)
            print(f"[{i+1}/{len(srt_files)}] {json_file} -> {new_json_name}")
            renamed_count += 1
        except Exception as e:
            print(f"[{i+1}/{len(srt_files)}] 重命名 {json_file} 出错: {str(e)}")
    
    return renamed_count


def main():
    """Main function."""
    print("="*60)
    print("交互式 JSON 文件重命名工具")
    print("="*60)
    print()
    
    # Get user input
    print("请提供目录信息：")
    source_dir = get_user_input("请输入源目录（包含 SRT 文件）: ")
    target_dir = get_user_input("请输入目标目录（包含 JSON 文件）: ")
    
    print("\n扫描目录中...")
    
    # Get file lists
    srt_files = get_srt_files(source_dir)
    json_files = get_json_files(target_dir)
    
    # Display results
    print("\n" + "="*60)
    print(f"源目录: {source_dir}")
    print(f"找到的 SRT 文件: {len(srt_files)} 个")
    if srt_files:
        for i, f in enumerate(srt_files, 1):
            print(f"  {i}. {f}")
    
    print("\n" + "-"*60)
    print(f"目标目录: {target_dir}")
    print(f"找到的 JSON 文件: {len(json_files)} 个")
    if json_files:
        for i, f in enumerate(json_files, 1):
            print(f"  {i}. {f}")
    
    # Check if file counts match
    print("\n" + "="*60)
    if len(srt_files) != len(json_files):
        print(f"错误：文件数目不匹配！")
        print(f"  SRT 文件: {len(srt_files)} 个")
        print(f"  JSON 文件: {len(json_files)} 个")
        print("\n操作已中止。请确保两个目录中的文件数目相同。")
        return 1
    
    if len(srt_files) == 0:
        print("两个目录中都没有找到文件。操作已中止。")
        return 1
    
    print(f"✓ 文件数目匹配: {len(srt_files)} 个文件")
    
    # Confirm before renaming
    print("\n" + "="*60)
    confirm = input("是否继续执行重命名操作？(直接按回车确认，输入任意字符后回车取消): ").strip().lower()
    if confirm:
        print("操作已取消。")
        return 0
    
    # Rename files
    renamed_count = rename_files(source_dir, target_dir, srt_files, json_files)
    
    # Summary
    print("\n" + "="*60)
    print(f"操作完成！成功重命名 {renamed_count} 个文件。")
    print("="*60)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
