# -*- coding: utf-8 -*-
"""
LOF基金套利工具使用示例
"""

from main import LOFArbitrageTool

# 示例1：监控单个基金
print("=" * 60)
print("示例1：监控单个基金")
print("=" * 60)
tool = LOFArbitrageTool(use_mock_data=True)  # 使用模拟数据
tool.monitor_single_fund('161725', '招商中证白酒指数(LOF)A')

# 示例2：监控多个基金
print("\n" + "=" * 60)
print("示例2：监控多个基金")
print("=" * 60)
tool.monitor_multiple_funds(['161725', '161028', '160632'])

print("\n" + "=" * 60)
print("提示：使用真实数据时，请运行: python main.py")
print("=" * 60)
