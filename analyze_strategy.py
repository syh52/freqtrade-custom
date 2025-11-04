#!/usr/bin/env python3
"""
NostalgiaForInfinityX7 策略结构分析工具
生成策略概览、方法列表、信号分析等
"""

import re
import sys
from pathlib import Path
from collections import defaultdict


class StrategyAnalyzer:
    def __init__(self, strategy_file):
        self.file_path = Path(strategy_file)
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.content = f.read()
            self.lines = self.content.split('\n')

        self.methods = []
        self.class_attrs = {}
        self.entry_conditions = []
        self.exit_conditions = []
        self.protection_params = {}

    def analyze(self):
        """执行完整分析"""
        print("🔍 正在分析策略文件...")
        self.extract_class_attributes()
        self.extract_methods()
        self.extract_conditions()
        self.extract_protection_params()

    def extract_class_attributes(self):
        """提取类属性（配置参数）"""
        in_class = False
        for i, line in enumerate(self.lines):
            if 'class NostalgiaForInfinityX7' in line:
                in_class = True
                continue

            if in_class:
                # 遇到第一个方法定义就停止
                if re.match(r'^\s{2}def ', line):
                    break

                # 匹配类属性 (例如: stoploss = -0.99)
                match = re.match(r'^\s{2}([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+?)(?:\s*#.*)?$', line)
                if match:
                    attr_name = match.group(1)
                    attr_value = match.group(2).strip()
                    self.class_attrs[attr_name] = attr_value

    def extract_methods(self):
        """提取所有方法定义"""
        pattern = r'^\s{2,4}def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\('

        for i, line in enumerate(self.lines):
            match = re.match(pattern, line)
            if match:
                method_name = match.group(1)
                # 统计方法代码行数（简单估算到下一个方法定义）
                lines_count = 0
                for j in range(i + 1, min(i + 500, len(self.lines))):
                    if re.match(pattern, self.lines[j]):
                        break
                    lines_count += 1

                self.methods.append({
                    'name': method_name,
                    'line': i + 1,
                    'approx_lines': lines_count
                })

    def extract_conditions(self):
        """提取入场和出场条件"""
        # 查找所有的 buy_condition 和 entry 相关
        entry_pattern = r'(buy_condition_\d+|entry_\d+|long_entry_\d+|short_entry_\d+)'
        exit_pattern = r'(exit_\w+|sell_\w+)'

        for method in self.methods:
            if re.search(entry_pattern, method['name']):
                # 提取数字编号
                num_match = re.search(r'\d+', method['name'])
                num = num_match.group() if num_match else 'N/A'
                self.entry_conditions.append({
                    'name': method['name'],
                    'number': num,
                    'line': method['line']
                })
            elif re.search(exit_pattern, method['name']):
                self.exit_conditions.append({
                    'name': method['name'],
                    'line': method['line']
                })

    def extract_protection_params(self):
        """提取保护参数"""
        # 搜索保护参数相关的字典定义
        in_protection = False
        current_param = None

        for line in self.lines:
            if 'buy_protection_params' in line or 'entry_protection_params' in line:
                in_protection = True
                current_param = 'entry'
            elif 'sell_protection_params' in line or 'exit_protection_params' in line:
                in_protection = True
                current_param = 'exit'
            elif in_protection and '}' in line and not line.strip().startswith('#'):
                in_protection = False

    def generate_report(self):
        """生成分析报告"""
        report = []
        report.append("=" * 80)
        report.append("📊 NostalgiaForInfinityX7 策略结构分析报告")
        report.append("=" * 80)
        report.append("")

        # 基础信息
        report.append("## 📁 文件信息")
        report.append(f"文件路径: {self.file_path}")
        report.append(f"总行数: {len(self.lines):,}")
        report.append(f"文件大小: {self.file_path.stat().st_size / 1024 / 1024:.2f} MB")
        report.append("")

        # 核心配置参数
        report.append("## ⚙️ 核心配置参数")
        report.append("-" * 80)
        important_params = [
            'stoploss', 'timeframe', 'minimal_roi',
            'position_adjustment_enable', 'max_entry_position_adjustment',
            'can_short', 'use_custom_stoploss'
        ]

        for param in important_params:
            if param in self.class_attrs:
                value = self.class_attrs[param]
                report.append(f"{param:.<40} {value}")
        report.append("")

        # 方法统计
        report.append("## 📋 方法统计")
        report.append("-" * 80)
        report.append(f"总方法数: {len(self.methods)}")
        report.append(f"入场条件方法: {len(self.entry_conditions)}")
        report.append(f"出场条件方法: {len(self.exit_conditions)}")
        report.append("")

        # 方法分类统计
        method_categories = defaultdict(list)
        for method in self.methods:
            name = method['name']
            if name.startswith('populate_'):
                method_categories['主要流程方法'].append(method)
            elif 'entry' in name or 'buy' in name:
                method_categories['入场相关'].append(method)
            elif 'exit' in name or 'sell' in name:
                method_categories['出场相关'].append(method)
            elif 'protection' in name:
                method_categories['保护机制'].append(method)
            elif 'informative' in name:
                method_categories['多时间框架'].append(method)
            elif 'custom_stake' in name or 'adjust_trade' in name:
                method_categories['仓位管理'].append(method)
            else:
                method_categories['其他工具方法'].append(method)

        report.append("## 🗂️ 方法分类")
        report.append("-" * 80)
        for category, methods in sorted(method_categories.items()):
            report.append(f"\n### {category} ({len(methods)}个)")
            for method in methods[:10]:  # 只显示前10个
                report.append(f"  • {method['name']:.<50} 行 {method['line']}")
            if len(methods) > 10:
                report.append(f"  ... 还有 {len(methods) - 10} 个方法")
        report.append("")

        # 入场信号详细列表
        report.append("## 🎯 入场信号编号列表")
        report.append("-" * 80)
        entry_numbers = sorted(set(int(e['number']) for e in self.entry_conditions if e['number'].isdigit()))

        # 按10个一组显示
        for i in range(0, len(entry_numbers), 10):
            batch = entry_numbers[i:i+10]
            report.append("  " + ", ".join(f"#{num:03d}" for num in batch))
        report.append(f"\n总计: {len(entry_numbers)} 个入场信号")
        report.append("")

        # 关键方法列表
        report.append("## 🔑 关键方法列表")
        report.append("-" * 80)

        key_methods = [
            'populate_indicators',
            'populate_entry_trend',
            'populate_exit_trend',
            'custom_stake_amount',
            'adjust_trade_position',
            'custom_exit',
            'confirm_trade_entry',
            'confirm_trade_exit'
        ]

        for key_method in key_methods:
            found = next((m for m in self.methods if m['name'] == key_method), None)
            if found:
                report.append(f"{found['name']:.<50} 行 {found['line']:>6}  (~{found['approx_lines']} 行)")
            else:
                report.append(f"{key_method:.<50} [未找到]")

        report.append("")
        report.append("=" * 80)
        report.append("📝 提示: 使用以下命令查看具体方法内容:")
        report.append("   sed -n '<起始行>,<结束行>p' user_data/strategies/NostalgiaForInfinityX7.py")
        report.append("=" * 80)

        return "\n".join(report)

    def generate_markdown_overview(self):
        """生成Markdown格式的概览文档"""
        md = []
        md.append("# NostalgiaForInfinityX7 策略概览")
        md.append("")
        md.append("> 自动生成于策略分析工具")
        md.append("")

        # 快速导航
        md.append("## 📑 快速导航")
        md.append("")
        md.append("| 章节 | 描述 |")
        md.append("|------|------|")
        md.append("| [核心配置](#核心配置) | 止损、时间框架、ROI等关键参数 |")
        md.append("| [方法统计](#方法统计) | 策略包含的所有方法分类统计 |")
        md.append("| [入场信号](#入场信号) | 所有入场信号编号和位置 |")
        md.append("| [出场机制](#出场机制) | 退出条件和保护措施 |")
        md.append("| [关键方法](#关键方法) | 核心交易逻辑方法详情 |")
        md.append("")

        # 核心配置
        md.append("## 🔧 核心配置")
        md.append("")
        md.append("```python")
        for key, value in sorted(self.class_attrs.items())[:20]:
            md.append(f"{key} = {value}")
        md.append("```")
        md.append("")

        # 方法统计
        md.append("## 📊 方法统计")
        md.append("")
        md.append(f"- **总方法数**: {len(self.methods)}")
        md.append(f"- **入场条件**: {len(self.entry_conditions)} 个")
        md.append(f"- **出场条件**: {len(self.exit_conditions)} 个")
        md.append("")

        # 入场信号
        md.append("## 🎯 入场信号")
        md.append("")
        md.append("| 信号编号 | 方法名 | 代码行 |")
        md.append("|---------|--------|-------|")

        sorted_entries = sorted(self.entry_conditions, key=lambda x: int(x['number']) if x['number'].isdigit() else 9999)
        for entry in sorted_entries[:50]:  # 限制显示前50个
            md.append(f"| #{entry['number']} | `{entry['name']}` | {entry['line']} |")

        if len(sorted_entries) > 50:
            md.append(f"| ... | ... | ... |")
            md.append(f"| | *还有 {len(sorted_entries) - 50} 个信号* | |")
        md.append("")

        # 关键方法
        md.append("## 🔑 关键方法")
        md.append("")

        key_methods_desc = {
            'populate_indicators': '添加技术指标到数据框',
            'populate_entry_trend': '标记入场信号',
            'populate_exit_trend': '标记出场信号',
            'custom_stake_amount': '自定义每笔交易的投入金额',
            'adjust_trade_position': 'DCA/加仓逻辑',
            'custom_exit': '自定义退出条件',
            'confirm_trade_entry': '入场前的最终确认',
            'confirm_trade_exit': '出场前的最终确认'
        }

        md.append("| 方法名 | 描述 | 代码行 |")
        md.append("|--------|------|--------|")

        for method_name, desc in key_methods_desc.items():
            found = next((m for m in self.methods if m['name'] == method_name), None)
            if found:
                md.append(f"| `{method_name}` | {desc} | {found['line']} |")

        md.append("")
        md.append("---")
        md.append("")
        md.append("### 💡 使用建议")
        md.append("")
        md.append("1. **查看特定方法**: `sed -n '<行号>,+100p' user_data/strategies/NostalgiaForInfinityX7.py`")
        md.append("2. **搜索关键字**: `grep -n '关键字' user_data/strategies/NostalgiaForInfinityX7.py`")
        md.append("3. **使用代码编辑器**: VS Code, PyCharm 等可以提供更好的导航")
        md.append("")

        return "\n".join(md)

    def generate_interactive_menu(self):
        """生成交互式菜单"""
        print("\n" + "=" * 80)
        print("🎯 策略分析交互菜单")
        print("=" * 80)
        print("\n选择您想要查看的内容:\n")
        print("  1. 完整结构报告")
        print("  2. 查看所有入场信号")
        print("  3. 查看所有出场条件")
        print("  4. 查看关键方法位置")
        print("  5. 搜索特定方法")
        print("  6. 生成Markdown概览文档")
        print("  7. 查看具体信号代码")
        print("  0. 退出")
        print("\n" + "-" * 80)


def main():
    strategy_file = Path(__file__).parent / "user_data" / "strategies" / "NostalgiaForInfinityX7.py"

    if not strategy_file.exists():
        print(f"❌ 错误: 找不到策略文件 {strategy_file}")
        sys.exit(1)

    analyzer = StrategyAnalyzer(strategy_file)
    analyzer.analyze()

    # 如果有命令行参数
    if len(sys.argv) > 1:
        arg = sys.argv[1]

        if arg == "report":
            print(analyzer.generate_report())
        elif arg == "markdown":
            md_content = analyzer.generate_markdown_overview()
            output_file = Path(__file__).parent / "STRATEGY_OVERVIEW.md"
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(md_content)
            print(f"✅ Markdown概览已保存到: {output_file}")
        elif arg == "entries":
            print("\n📊 所有入场信号:")
            for entry in sorted(analyzer.entry_conditions, key=lambda x: int(x['number']) if x['number'].isdigit() else 9999):
                print(f"  信号 #{entry['number']:>3} - {entry['name']:.<60} 行 {entry['line']}")
        else:
            print(f"❌ 未知参数: {arg}")
            print("用法: python analyze_strategy.py [report|markdown|entries]")
    else:
        # 默认显示报告
        print(analyzer.generate_report())


if __name__ == "__main__":
    main()
