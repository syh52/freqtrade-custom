#!/usr/bin/env python3
"""
Strategy File Analyzer
分析大型策略文件的结构和组成
"""

import ast
import sys
from collections import defaultdict
from pathlib import Path


class StrategyAnalyzer(ast.NodeVisitor):
    def __init__(self):
        self.classes = []
        self.functions = defaultdict(list)
        self.class_methods = defaultdict(list)
        self.class_attributes = defaultdict(list)
        self.imports = []
        self.current_class = None
        self.constants = []

    def visit_Import(self, node):
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module:
            for alias in node.names:
                self.imports.append(f"{node.module}.{alias.name}")
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.current_class = node.name
        self.classes.append({
            'name': node.name,
            'lineno': node.lineno,
            'bases': [self._get_name(base) for base in node.bases],
            'docstring': ast.get_docstring(node)
        })
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node):
        func_info = {
            'name': node.name,
            'lineno': node.lineno,
            'args': [arg.arg for arg in node.args.args],
            'docstring': ast.get_docstring(node)
        }

        if self.current_class:
            self.class_methods[self.current_class].append(func_info)
        else:
            self.functions['global'].append(func_info)

        self.generic_visit(node)

    def visit_Assign(self, node):
        if self.current_class and isinstance(node.targets[0], ast.Name):
            attr_name = node.targets[0].id
            # 只记录类级别的属性（不在方法内的）
            if hasattr(node, 'lineno'):
                self.class_attributes[self.current_class].append({
                    'name': attr_name,
                    'lineno': node.lineno
                })
        self.generic_visit(node)

    def _get_name(self, node):
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        return str(node)


def analyze_strategy_file(filepath):
    """分析策略文件并生成报告"""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 基本统计
    lines = content.split('\n')
    total_lines = len(lines)
    code_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
    comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
    blank_lines = total_lines - code_lines - comment_lines

    # AST 分析
    try:
        tree = ast.parse(content)
        analyzer = StrategyAnalyzer()
        analyzer.visit(tree)
    except SyntaxError as e:
        print(f"❌ 语法错误: {e}")
        return

    # 生成报告
    print("=" * 80)
    print("📊 策略文件分析报告")
    print("=" * 80)
    print(f"\n📁 文件: {filepath}")
    print(f"📏 文件大小: {Path(filepath).stat().st_size / 1024 / 1024:.2f} MB")

    print("\n" + "─" * 80)
    print("📈 基本统计")
    print("─" * 80)
    print(f"总行数:     {total_lines:>8,}")
    print(f"代码行:     {code_lines:>8,}")
    print(f"注释行:     {comment_lines:>8,}")
    print(f"空白行:     {blank_lines:>8,}")

    print("\n" + "─" * 80)
    print("📦 导入的模块")
    print("─" * 80)
    unique_imports = sorted(set(analyzer.imports))
    for imp in unique_imports[:20]:  # 显示前20个
        print(f"  • {imp}")
    if len(unique_imports) > 20:
        print(f"  ... 还有 {len(unique_imports) - 20} 个")

    print("\n" + "─" * 80)
    print("🏛️ 类定义")
    print("─" * 80)
    for cls in analyzer.classes:
        print(f"\n类名: {cls['name']}")
        print(f"  行号: {cls['lineno']}")
        print(f"  继承: {', '.join(cls['bases']) if cls['bases'] else 'None'}")

        # 类属性
        attrs = analyzer.class_attributes.get(cls['name'], [])
        if attrs:
            print(f"  配置属性 ({len(attrs)}个):")
            # 按类型分组显示一些重要的属性
            for attr in attrs[:10]:
                print(f"    • {attr['name']} (line {attr['lineno']})")
            if len(attrs) > 10:
                print(f"    ... 还有 {len(attrs) - 10} 个属性")

        # 类方法
        methods = analyzer.class_methods.get(cls['name'], [])
        if methods:
            print(f"  方法 ({len(methods)}个):")

            # 分类显示方法
            entry_methods = [m for m in methods if 'entry' in m['name'] or 'buy' in m['name']]
            exit_methods = [m for m in methods if 'exit' in m['name'] or 'sell' in m['name']]
            populate_methods = [m for m in methods if 'populate' in m['name']]
            custom_methods = [m for m in methods if 'custom' in m['name']]
            grind_methods = [m for m in methods if 'grind' in m['name']]

            if populate_methods:
                print(f"\n    📊 数据填充方法 ({len(populate_methods)}个):")
                for m in populate_methods[:5]:
                    print(f"      • {m['name']}() - line {m['lineno']}")

            if entry_methods:
                print(f"\n    📈 入场方法 ({len(entry_methods)}个):")
                for m in entry_methods[:5]:
                    print(f"      • {m['name']}() - line {m['lineno']}")
                if len(entry_methods) > 5:
                    print(f"      ... 还有 {len(entry_methods) - 5} 个")

            if exit_methods:
                print(f"\n    📉 出场方法 ({len(exit_methods)}个):")
                for m in exit_methods[:5]:
                    print(f"      • {m['name']}() - line {m['lineno']}")
                if len(exit_methods) > 5:
                    print(f"      ... 还有 {len(exit_methods) - 5} 个")

            if grind_methods:
                print(f"\n    🔄 网格/加仓方法 ({len(grind_methods)}个):")
                for m in grind_methods[:5]:
                    print(f"      • {m['name']}() - line {m['lineno']}")
                if len(grind_methods) > 5:
                    print(f"      ... 还有 {len(grind_methods) - 5} 个")

            if custom_methods:
                print(f"\n    ⚙️  自定义方法 ({len(custom_methods)}个):")
                for m in custom_methods[:5]:
                    print(f"      • {m['name']}() - line {m['lineno']}")
                if len(custom_methods) > 5:
                    print(f"      ... 还有 {len(custom_methods) - 5} 个")

            # 其他方法
            other_methods = [m for m in methods
                           if m not in entry_methods + exit_methods + populate_methods + custom_methods + grind_methods]
            if other_methods:
                print(f"\n    🔧 其他方法 ({len(other_methods)}个):")
                for m in other_methods[:5]:
                    print(f"      • {m['name']}() - line {m['lineno']}")
                if len(other_methods) > 5:
                    print(f"      ... 还有 {len(other_methods) - 5} 个")

    # 全局函数
    global_funcs = analyzer.functions.get('global', [])
    if global_funcs:
        print("\n" + "─" * 80)
        print("🔧 全局函数")
        print("─" * 80)
        for func in global_funcs[:10]:
            print(f"  • {func['name']}() - line {func['lineno']}")
        if len(global_funcs) > 10:
            print(f"  ... 还有 {len(global_funcs) - 10} 个")

    print("\n" + "=" * 80)
    print("💡 理解策略的建议:")
    print("=" * 80)
    print("""
1. 从核心方法开始:
   • populate_indicators() - 了解使用了哪些技术指标
   • populate_entry_trend() - 了解入场条件
   • populate_exit_trend() - 了解出场条件

2. 查看配置参数:
   • 找到类属性部分，了解可调整的参数
   • 注意 minimal_roi, stoploss, timeframe 等关键参数

3. 理解交易模式:
   • 这个策略似乎有多个模式 (normal, pump, quick, rebuy等)
   • 每个模式可能有不同的入场/出场条件

4. 使用工具辅助:
   • 使用代码编辑器的大纲视图 (outline)
   • 使用搜索功能查找特定的方法
   • 考虑使用 ctags 或 LSP 进行代码导航

5. 分段阅读:
   • 不要试图一次理解全部代码
   • 专注于你感兴趣的交易模式
   • 从简单的条件开始，逐步深入
""")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        strategy_file = sys.argv[1]
    else:
        strategy_file = "user_data/strategies/NostalgiaForInfinityX7.py"

    analyze_strategy_file(strategy_file)
