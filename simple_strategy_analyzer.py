#!/usr/bin/env python3
"""
Simple Strategy File Analyzer
使用文本分析的方式来理解大型策略文件
"""

import re
from pathlib import Path
from collections import defaultdict


def analyze_strategy_simple(filepath):
    """使用文本分析方式分析策略文件"""

    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total_lines = len(lines)

    # 基本统计
    code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    blank_lines = total_lines - code_lines - comment_lines

    # 查找类定义
    class_pattern = re.compile(r'^class\s+(\w+)(\([^)]*\))?:', re.MULTILINE)
    classes = []
    for i, line in enumerate(lines):
        match = class_pattern.match(line)
        if match:
            classes.append({'name': match.group(1), 'line': i + 1})

    # 查找方法定义
    method_pattern = re.compile(r'^\s+def\s+(\w+)\s*\(')
    methods = defaultdict(list)
    current_indent = 0

    for i, line in enumerate(lines):
        match = method_pattern.match(line)
        if match:
            method_name = match.group(1)
            methods[method_name].append(i + 1)

    # 查找重要的配置
    config_patterns = {
        'timeframe': re.compile(r'timeframe\s*=\s*["\']([^"\']+)["\']'),
        'stoploss': re.compile(r'stoploss\s*=\s*([0-9.-]+)'),
        'roi': re.compile(r'minimal_roi\s*='),
        'leverage': re.compile(r'leverage.*=\s*([0-9.]+)'),
        'version': re.compile(r'def\s+version.*return\s+["\']([^"\']+)["\']'),
    }

    configs = {}
    for key, pattern in config_patterns.items():
        for line in lines:
            match = pattern.search(line)
            if match:
                if key == 'roi':
                    configs[key] = 'defined'
                else:
                    configs[key] = match.group(1) if match.groups() else 'found'
                break

    # 分析交易模式
    mode_patterns = {
        'long_normal': re.compile(r'long_normal'),
        'long_pump': re.compile(r'long_pump'),
        'long_quick': re.compile(r'long_quick'),
        'long_rebuy': re.compile(r'long_rebuy'),
        'long_rapid': re.compile(r'long_rapid'),
        'short_normal': re.compile(r'short_normal'),
        'short_pump': re.compile(r'short_pump'),
        'short_quick': re.compile(r'short_quick'),
    }

    modes_found = defaultdict(int)
    for mode_name, pattern in mode_patterns.items():
        for line in lines:
            if pattern.search(line):
                modes_found[mode_name] += 1

    # 查找关键方法并计数
    key_method_groups = {
        'populate': [],
        'entry': [],
        'exit': [],
        'grind': [],
        'custom': [],
        'indicator': [],
    }

    for method_name in methods.keys():
        if 'populate' in method_name:
            key_method_groups['populate'].append(method_name)
        elif 'entry' in method_name or 'buy' in method_name:
            key_method_groups['entry'].append(method_name)
        elif 'exit' in method_name or 'sell' in method_name:
            key_method_groups['exit'].append(method_name)
        elif 'grind' in method_name:
            key_method_groups['grind'].append(method_name)
        elif 'custom' in method_name:
            key_method_groups['custom'].append(method_name)
        elif 'indicator' in method_name or 'calc' in method_name:
            key_method_groups['indicator'].append(method_name)

    # 生成报告
    print("=" * 80)
    print("📊 NostalgiaForInfinityX7 策略分析报告")
    print("=" * 80)
    print(f"\n📁 文件: {filepath}")
    print(f"📏 文件大小: {Path(filepath).stat().st_size / 1024 / 1024:.2f} MB")

    print("\n" + "─" * 80)
    print("📈 基本统计")
    print("─" * 80)
    print(f"总行数:     {total_lines:>8,} 行")
    print(f"代码行:     {code_lines:>8,} 行")
    print(f"注释行:     {comment_lines:>8,} 行")
    print(f"空白行:     {blank_lines:>8,} 行")
    print(f"总方法数:   {len(methods):>8,} 个")

    print("\n" + "─" * 80)
    print("⚙️  核心配置")
    print("─" * 80)
    if 'version' in configs:
        print(f"策略版本:   {configs['version']}")
    if 'timeframe' in configs:
        print(f"时间周期:   {configs['timeframe']}")
    if 'stoploss' in configs:
        print(f"止损:       {configs['stoploss']}")
    if 'leverage' in configs:
        print(f"杠杆:       {configs['leverage']}x")
    if 'roi' in configs:
        print(f"最小ROI:    已定义")

    print("\n" + "─" * 80)
    print("🎯 交易模式")
    print("─" * 80)
    print("检测到的交易模式及其在代码中的出现次数:")
    for mode, count in sorted(modes_found.items(), key=lambda x: x[1], reverse=True):
        if count > 10:  # 只显示重要的模式
            print(f"  • {mode:20s}: {count:>5} 次")

    print("\n" + "─" * 80)
    print("🔍 方法分类统计")
    print("─" * 80)

    for group_name, method_list in key_method_groups.items():
        if method_list:
            print(f"\n{group_name.upper()} 相关方法 ({len(method_list)} 个):")
            # 显示前10个
            for method in sorted(method_list)[:10]:
                line_nums = methods[method]
                print(f"  • {method:50s} (line {line_nums[0]})")
            if len(method_list) > 10:
                print(f"  ... 还有 {len(method_list) - 10} 个方法")

    print("\n" + "=" * 80)
    print("💡 如何理解这个策略")
    print("=" * 80)
    print("""
这是一个**极其复杂**的多模式交易策略 (7万行代码!)。以下是系统化理解的方法:

┌─────────────────────────────────────────────────────────────────┐
│ 第一步: 理解策略的整体架构                                      │
└─────────────────────────────────────────────────────────────────┘

1. 这是 NostalgiaForInfinity 系列策略的 X7 版本
2. 支持多种交易模式:
   - Long (做多): normal, pump, quick, rebuy, rapid 等
   - Short (做空): normal, pump, quick 等
3. 使用 5分钟时间周期 (5m)，但会用到多个时间周期的数据

┌─────────────────────────────────────────────────────────────────┐
│ 第二步: 从核心方法入手                                          │
└─────────────────────────────────────────────────────────────────┘

推荐阅读顺序:

1. 先看配置部分 (前200行):
   命令: head -n 200 user_data/strategies/NostalgiaForInfinityX7.py

2. 查看 populate_indicators() 方法:
   命令: grep -n "def populate_indicators" user_data/strategies/NostalgiaForInfinityX7.py

3. 查看入场条件 populate_entry_trend():
   命令: grep -n "def populate_entry_trend" user_data/strategies/NostalgiaForInfinityX7.py

4. 查看出场条件 populate_exit_trend():
   命令: grep -n "def populate_exit_trend" user_data/strategies/NostalgiaForInfinityX7.py

┌─────────────────────────────────────────────────────────────────┐
│ 第三步: 理解特定交易模式                                        │
└─────────────────────────────────────────────────────────────────┘

每个模式都有自己的入场条件，你可以搜索特定模式:

例如，理解 "long_normal" 模式:
  grep -n "long_normal" user_data/strategies/NostalgiaForInfinityX7.py | head -20

┌─────────────────────────────────────────────────────────────────┐
│ 第四步: 使用工具辅助                                            │
└─────────────────────────────────────────────────────────────────┘

建议的工具:
  • VS Code / PyCharm: 使用大纲视图和代码折叠
  • ctags: 生成代码索引
  • grep/ripgrep: 快速搜索特定内容

  生成方法索引:
    grep -n "def " user_data/strategies/NostalgiaForInfinityX7.py > methods_index.txt

┌─────────────────────────────────────────────────────────────────┐
│ 第五步: 专注于你关心的部分                                      │
└─────────────────────────────────────────────────────────────────┘

不要试图理解所有代码! 这是不现实的。相反:

1. 如果你想优化参数: 关注类属性和配置部分
2. 如果你想理解入场时机: 关注 entry 相关方法
3. 如果你想理解出场时机: 关注 exit 和 grind 相关方法
4. 如果你想理解指标: 关注 populate_indicators

┌─────────────────────────────────────────────────────────────────┐
│ 实用命令速查                                                    │
└─────────────────────────────────────────────────────────────────┘

# 查看所有方法定义
grep -n "^\s*def " user_data/strategies/NostalgiaForInfinityX7.py

# 查看特定行范围 (例如 1000-1100行)
sed -n '1000,1100p' user_data/strategies/NostalgiaForInfinityX7.py

# 搜索特定关键词
grep -n "关键词" user_data/strategies/NostalgiaForInfinityX7.py

# 统计包含某关键词的行数
grep -c "关键词" user_data/strategies/NostalgiaForInfinityX7.py
""")

    print("\n" + "=" * 80)
    print("🚀 下一步建议")
    print("=" * 80)
    print("""
想要深入了解？试试这些命令:

1. 生成方法索引文件:
   python3 simple_strategy_analyzer.py > strategy_analysis.txt

2. 创建你自己的简化版本:
   • 选择一个交易模式 (如 long_normal)
   • 提取相关的代码到新文件
   • 逐步理解和测试

3. 咨询作者:
   • GitHub: https://github.com/iterativv/NostalgiaForInfinity
   • 查看文档和 issues
""")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        strategy_file = sys.argv[1]
    else:
        strategy_file = "user_data/strategies/NostalgiaForInfinityX7.py"

    analyze_strategy_simple(strategy_file)
