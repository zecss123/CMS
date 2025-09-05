#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试正则表达式调试
"""

import re

def test_wind_farm_regex():
    """测试风场提取正则表达式"""
    print("=== 风场提取正则表达式调试 ===")
    
    test_text = "生成华能风场A的A01风机振动分析报告"
    print(f"测试文本: {test_text}")
    
    patterns = [
        # 匹配"华能风场A"这样的模式，确保风场前面有边界
        r'(?:^|[^\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)风场',
        r'(?:^|[^\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)风电场',
        r'(?:^|[^\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)电站',
        # 备用模式：直接匹配常见风场名称格式
        r'(华能风场[A-Za-z0-9]*)',
        r'(大唐风场[A-Za-z0-9]*)',
        r'(国电风场[A-Za-z0-9]*)',
        r'([\u4e00-\u9fa5]{2,4}风场[A-Za-z0-9]*)'
    ]
    
    for i, pattern in enumerate(patterns, 1):
        print(f"\n模式 {i}: {pattern}")
        matches = re.findall(pattern, test_text)
        print(f"所有匹配: {matches}")
        if matches:
            longest_match = max(matches, key=len)
            print(f"最长匹配: {longest_match}")
    
    # 测试改进的正则表达式
    print("\n=== 改进的正则表达式 ===")
    improved_patterns = [
        r'([\u4e00-\u9fa5]+[A-Za-z0-9]*)风场(?![\u4e00-\u9fa5])',  # 使用负向前瞻
        r'(?<![\u4e00-\u9fa5])([\u4e00-\u9fa5]+[A-Za-z0-9]*)风场',  # 使用负向后瞻
    ]
    
    for i, pattern in enumerate(improved_patterns, 1):
        print(f"\n改进模式 {i}: {pattern}")
        matches = re.findall(pattern, test_text)
        print(f"所有匹配: {matches}")
        if matches:
            longest_match = max(matches, key=len)
            print(f"最长匹配: {longest_match}")

if __name__ == "__main__":
    test_wind_farm_regex()