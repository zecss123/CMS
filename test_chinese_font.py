#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import numpy as np
import os

# 设置字体环境
os.environ['MPLCONFIGDIR'] = '/tmp/matplotlib'

# 检查可用的中文字体
print("检查系统中可用的中文字体:")
available_fonts = [f.name for f in fm.fontManager.ttflist if 'WenQuanYi' in f.name or 'Noto' in f.name]
print(f"找到的中文字体: {available_fonts}")

# 配置matplotlib使用中文字体
chinese_fonts = ['WenQuanYi Zen Hei', 'WenQuanYi Micro Hei', 'Noto Sans CJK SC']
plt.rcParams['font.sans-serif'] = chinese_fonts + ['DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

# 创建测试图表
fig, ax = plt.subplots(figsize=(8, 6))
x = np.linspace(0, 10, 100)
y = np.sin(x)

ax.plot(x, y, label='正弦波')
ax.set_xlabel('时间 (秒)')
ax.set_ylabel('振幅 (mm/s)')
ax.set_title('中文字体测试图表')
ax.legend()
ax.grid(True)

# 保存图表
plt.savefig('/root/autodl-tmp/cms_vibration_rag/chinese_font_test.png', dpi=150, bbox_inches='tight')
print("测试图表已保存为: chinese_font_test.png")

# 显示当前使用的字体
current_font = plt.rcParams['font.sans-serif'][0]
print(f"当前使用的字体: {current_font}")

plt.close()
print("字体测试完成！")