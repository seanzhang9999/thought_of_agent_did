#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SVG提取脚本
从Markdown文件中提取内嵌的SVG代码，保存为独立的SVG文件，并替换为链接引用
"""

import re
import os
import sys
from pathlib import Path

def extract_svgs_from_markdown(md_file_path, output_dir=None):
    """
    从Markdown文件中提取SVG代码并保存为独立文件
    
    Args:
        md_file_path (str): Markdown文件路径
        output_dir (str): SVG文件输出目录，默认为Markdown文件同目录
    
    Returns:
        tuple: (成功提取的SVG数量, 修改后的Markdown内容)
    """
    
    # 读取Markdown文件
    try:
        with open(md_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"错误: 找不到文件 {md_file_path}")
        return 0, None
    except Exception as e:
        print(f"错误: 读取文件失败 - {e}")
        return 0, None
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.dirname(md_file_path)
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 正则表达式匹配SVG标签
    svg_pattern = r'<svg[^>]*>.*?</svg>'
    svg_matches = re.findall(svg_pattern, content, re.DOTALL)
    
    if not svg_matches:
        print("未找到任何SVG代码")
        return 0, content
    
    print(f"找到 {len(svg_matches)} 个SVG图表")
    
    # 处理每个SVG
    modified_content = content
    svg_count = 0
    
    for i, svg_code in enumerate(svg_matches):
        # 尝试从SVG代码中提取标题信息
        title_match = re.search(r'<text[^>]*>([^<]*(?:战略|分析|模型|架构|演进|收入)[^<]*)</text>', svg_code)
        
        if title_match:
            title = title_match.group(1).strip()
            # 清理标题，移除特殊字符
            clean_title = re.sub(r'[^\w\u4e00-\u9fff]+', '_', title)
            svg_filename = f"{clean_title}.svg"
        else:
            # 如果没有找到标题，使用序号
            svg_filename = f"chart_{i+1}.svg"
        
        svg_file_path = os.path.join(output_dir, svg_filename)
        
        # 保存SVG文件
        try:
            with open(svg_file_path, 'w', encoding='utf-8') as f:
                f.write(svg_code)
            
            print(f"已保存: {svg_filename}")
            
            # 在Markdown中替换为链接引用
            # 计算相对路径
            md_dir = os.path.dirname(md_file_path)
            if os.path.samefile(output_dir, md_dir):
                # 同目录，直接使用文件名
                relative_path = svg_filename
            else:
                # 不同目录，计算相对路径
                relative_path = os.path.relpath(svg_file_path, md_dir)
            
            # 替换SVG代码为图片链接
            img_tag = f"![{title if title_match else f'图表{i+1}'}]({relative_path})"
            modified_content = modified_content.replace(svg_code, img_tag, 1)
            
            svg_count += 1
            
        except Exception as e:
            print(f"错误: 保存SVG文件失败 - {e}")
            continue
    
    return svg_count, modified_content

def backup_original_file(file_path):
    """备份原始文件"""
    backup_path = file_path + '.backup'
    try:
        with open(file_path, 'r', encoding='utf-8') as original:
            with open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
        print(f"已创建备份文件: {backup_path}")
        return True
    except Exception as e:
        print(f"错误: 创建备份失败 - {e}")
        return False

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python extract_svg_from_md.py <markdown_file> [output_directory]")
        print("示例: python extract_svg_from_md.py document.md ./svg_files/")
        sys.exit(1)
    
    md_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    # 检查文件是否存在
    if not os.path.exists(md_file):
        print(f"错误: 文件不存在 - {md_file}")
        sys.exit(1)
    
    print(f"处理文件: {md_file}")
    if output_dir:
        print(f"输出目录: {output_dir}")
    
    # 备份原始文件
    if not backup_original_file(md_file):
        print("警告: 无法创建备份文件，继续处理...")
    
    # 提取SVG
    svg_count, modified_content = extract_svgs_from_markdown(md_file, output_dir)
    
    if svg_count > 0 and modified_content:
        # 保存修改后的Markdown文件
        try:
            with open(md_file, 'w', encoding='utf-8') as f:
                f.write(modified_content)
            
            print(f"\n✅ 成功处理完成!")
            print(f"   - 提取了 {svg_count} 个SVG文件")
            print(f"   - 已更新Markdown文件中的引用")
            print(f"   - 原文件已备份为 {md_file}.backup")
            
        except Exception as e:
            print(f"错误: 保存修改后的Markdown文件失败 - {e}")
            sys.exit(1)
    else:
        print("没有找到SVG内容或处理失败")

if __name__ == "__main__":
    main()
