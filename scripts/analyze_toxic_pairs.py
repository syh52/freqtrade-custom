#!/usr/bin/env python3
"""
毒瘤币种自动识别脚本

功能：
1. 分析回测结果，识别高风险币种
2. 自动生成黑名单配置
3. 支持三级风险评估

使用：
    python3 scripts/analyze_toxic_pairs.py
    python3 scripts/analyze_toxic_pairs.py --input backtest-result.json
"""

import json
import zipfile
import argparse
from pathlib import Path
from datetime import datetime
import pandas as pd


def is_deadly_toxic(stats):
    """
    Level 1: 致命信号检测

    满足任一条件立即拉黑：
    1. 总亏损超过1500U
    2. 长期深套（持仓>7天且Grind亏损>3000U）
    3. 极端单笔亏损（>5000U）
    4. Grind模式巨额亏损（>2000U）
    """
    # 信号1: 总亏损严重
    if stats.get('total_profit', 0) < -1500:
        return True, f"总亏损{stats['total_profit']:.0f}U"

    # 信号2: 长期深套
    if (stats.get('grind_avg_duration', 0) > 168 and
        stats.get('grind_profit', 0) < -3000):
        return True, f"长期深套（{stats['grind_avg_duration']/24:.1f}天，亏损{stats['grind_profit']:.0f}U）"

    # 信号3: 极端单笔亏损
    if stats.get('max_single_loss', 0) < -5000:
        return True, f"极端亏损（{stats['max_single_loss']:.0f}U）"

    # 信号4: Grind模式巨额亏损（即使总盈利也要警惕）
    if stats.get('grind_profit', 0) < -2000:
        return True, f"Grind巨亏{stats['grind_profit']:.0f}U"

    return False, None


def is_warning_toxic(stats):
    """
    Level 2: 警告信号检测

    满足2+条件为中等风险：
    1. 整体胜率<70%
    2. Grind胜率<70%（≥2笔）
    3. 单笔亏损<-1000U
    4. 长期持仓但亏损（>5天且亏损）
    """
    signals = []

    # 信号1: 整体胜率低
    if stats.get('win_rate', 100) < 70:
        signals.append(f"整体胜率{stats['win_rate']:.1f}%")

    # 信号2: Grind表现差
    if (stats.get('grind_trades', 0) >= 2 and
        stats.get('grind_win_rate', 100) < 70):
        signals.append(f"Grind胜率{stats['grind_win_rate']:.1f}%")

    # 信号3: 大额单笔亏损
    if stats.get('max_single_loss', 0) < -1000:
        signals.append(f"单笔亏损{stats['max_single_loss']:.0f}U")

    # 信号4: 长期持仓但亏损
    if (stats.get('grind_avg_duration', 0) > 120 and
        stats.get('grind_profit', 0) < 0):
        signals.append(f"长期持仓亏损（{stats['grind_avg_duration']/24:.1f}天）")

    # 信号5: Grind净亏损（单笔也算，因为可能是大额亏损）
    if stats.get('grind_profit', 0) < -1000:
        signals.append(f"Grind累计亏损{stats['grind_profit']:.0f}U")

    return len(signals) >= 2, signals


def analyze_backtest_file(filepath):
    """分析单个回测文件"""
    print(f"\n分析文件: {filepath}")

    # 处理zip文件
    if str(filepath).endswith('.zip'):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            json_files = [f for f in zip_ref.namelist()
                         if f.endswith('.json') and 'config' not in f]
            if not json_files:
                print("❌ ZIP文件中没有找到回测结果JSON")
                return None

            with zip_ref.open(json_files[0]) as f:
                data = json.load(f)
    else:
        with open(filepath) as f:
            data = json.load(f)

    # 提取交易数据
    if 'strategy' not in data:
        print("❌ 文件格式错误：缺少strategy字段")
        return None

    strategy_name = list(data['strategy'].keys())[0]
    trades = pd.DataFrame(data['strategy'][strategy_name]['trades'])

    if len(trades) == 0:
        print("❌ 没有交易记录")
        return None

    # 计算持仓时间
    trades['open_date'] = pd.to_datetime(trades['open_date'])
    trades['close_date'] = pd.to_datetime(trades['close_date'])
    trades['duration_hours'] = (trades['close_date'] - trades['open_date']).dt.total_seconds() / 3600

    # 识别Grind交易
    trades['is_grind'] = trades['enter_tag'].astype(str).str.contains('120', na=False)

    print(f"✅ 加载{len(trades)}笔交易记录")

    return trades


def calculate_pair_stats(trades):
    """计算每个币种的统计数据"""
    pair_stats_list = []

    for pair in trades['pair'].unique():
        pair_trades = trades[trades['pair'] == pair]
        grind_trades = pair_trades[pair_trades['is_grind']]

        stats = {
            'pair': pair,
            'total_trades': len(pair_trades),
            'total_profit': pair_trades['profit_abs'].sum(),
            'win_rate': len(pair_trades[pair_trades['profit_abs'] > 0]) / len(pair_trades) * 100,
            'max_single_loss': pair_trades['profit_abs'].min(),
            'has_liquidation': 'liquidation' in pair_trades['exit_reason'].values,
            'has_force_exit': 'force_exit' in pair_trades['exit_reason'].values,
        }

        # Grind专项统计
        if len(grind_trades) > 0:
            stats.update({
                'grind_trades': len(grind_trades),
                'grind_profit': grind_trades['profit_abs'].sum(),
                'grind_avg_duration': grind_trades['duration_hours'].mean(),
                'grind_win_rate': len(grind_trades[grind_trades['profit_abs'] > 0]) / len(grind_trades) * 100,
            })
        else:
            stats.update({
                'grind_trades': 0,
                'grind_profit': 0,
                'grind_avg_duration': 0,
                'grind_win_rate': 100,
            })

        pair_stats_list.append(stats)

    return pair_stats_list


def classify_pairs(pair_stats_list):
    """对币种进行风险分类"""
    toxic_pairs = []
    warning_pairs = []
    safe_pairs = []

    for stats in pair_stats_list:
        # Level 1: 致命检测
        is_deadly, reason = is_deadly_toxic(stats)
        if is_deadly:
            toxic_pairs.append({
                'pair': stats['pair'],
                'reason': reason,
                'stats': stats
            })
            continue

        # Level 2: 警告检测
        is_warning, signals = is_warning_toxic(stats)
        if is_warning:
            warning_pairs.append({
                'pair': stats['pair'],
                'signals': signals,
                'stats': stats
            })
            continue

        # Level 3: 安全
        safe_pairs.append({
            'pair': stats['pair'],
            'stats': stats
        })

    return toxic_pairs, warning_pairs, safe_pairs


def generate_blacklist(toxic_pairs, warning_pairs):
    """生成黑名单配置"""
    blacklist = {
        'generated_at': datetime.now().isoformat(),
        'pair_blacklist': [p['pair'] for p in toxic_pairs],
        'grind_blacklist': [p['pair'] for p in warning_pairs],
        'details': {
            'toxic_pairs': toxic_pairs,
            'warning_pairs': warning_pairs
        }
    }

    return blacklist


def print_analysis_report(toxic_pairs, warning_pairs, safe_pairs):
    """打印分析报告"""
    print("\n" + "=" * 100)
    print("毒瘤币种识别报告")
    print("=" * 100)

    print(f"\n📊 总体统计：")
    print(f"  总币种数: {len(toxic_pairs) + len(warning_pairs) + len(safe_pairs)}个")
    print(f"  🔴 致命毒瘤: {len(toxic_pairs)}个")
    print(f"  ⚠️ 警告币种: {len(warning_pairs)}个")
    print(f"  ✅ 安全币种: {len(safe_pairs)}个")

    if toxic_pairs:
        print(f"\n🔴 致命毒瘤（建议永久拉黑）：")
        print("-" * 100)
        for item in toxic_pairs:
            stats = item['stats']
            print(f"\n  {item['pair']}")
            print(f"    原因: {item['reason']}")
            print(f"    总交易: {stats['total_trades']}笔 | 总盈亏: {stats['total_profit']:+,.0f}U | 胜率: {stats['win_rate']:.1f}%")
            print(f"    Grind: {stats['grind_trades']}笔 | Grind盈亏: {stats['grind_profit']:+,.0f}U")
            if stats['grind_avg_duration'] > 0:
                print(f"    Grind平均持仓: {stats['grind_avg_duration']/24:.1f}天")

    if warning_pairs:
        print(f"\n⚠️ 警告币种（建议禁用Grind）：")
        print("-" * 100)
        for item in warning_pairs[:10]:  # 只显示前10个
            stats = item['stats']
            print(f"\n  {item['pair']}")
            print(f"    风险信号: {', '.join(item['signals'])}")
            print(f"    总交易: {stats['total_trades']}笔 | 总盈亏: {stats['total_profit']:+,.0f}U")
            print(f"    Grind: {stats['grind_trades']}笔 | Grind盈亏: {stats['grind_profit']:+,.0f}U")

        if len(warning_pairs) > 10:
            print(f"\n  ... 还有{len(warning_pairs)-10}个警告币种")

    if safe_pairs:
        print(f"\n✅ 安全币种：{len(safe_pairs)}个")
        # 显示Grind盈利最高的前5个
        grind_profitable = [p for p in safe_pairs if p['stats']['grind_profit'] > 0]
        if grind_profitable:
            grind_profitable.sort(key=lambda x: x['stats']['grind_profit'], reverse=True)
            print("\n  Grind盈利Top 5:")
            for item in grind_profitable[:5]:
                stats = item['stats']
                print(f"    {item['pair']:<20} Grind盈利: {stats['grind_profit']:+,.0f}U | "
                      f"{stats['grind_trades']}笔 | 胜率{stats['grind_win_rate']:.1f}%")


def save_blacklist(blacklist, output_path):
    """保存黑名单配置"""
    with open(output_path, 'w') as f:
        json.dump(blacklist, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 黑名单已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='毒瘤币种自动识别')
    parser.add_argument('--input', '-i', type=str,
                       help='回测结果文件路径（默认：最新的backtest-result）')
    parser.add_argument('--output', '-o', type=str,
                       default='user_data/blacklist_auto_generated.json',
                       help='输出文件路径')

    args = parser.parse_args()

    # 确定输入文件
    if args.input:
        input_file = Path(args.input)
    else:
        # 自动查找最新的回测结果
        results_dir = Path('user_data/backtest_results')
        if not results_dir.exists():
            print(f"❌ 回测结果目录不存在: {results_dir}")
            return

        # 查找所有回测文件（包括.json和.zip）
        json_files = list(results_dir.glob('backtest-result-*.json'))
        zip_files = list(results_dir.glob('backtest-result-*.zip'))
        all_files = json_files + zip_files

        if not all_files:
            print(f"❌ 未找到回测结果文件")
            print(f"   请先运行回测: freqtrade backtesting --config ...")
            return

        # 选择最新的文件
        input_file = max(all_files, key=lambda p: p.stat().st_mtime)

    if not input_file.exists():
        print(f"❌ 文件不存在: {input_file}")
        return

    # 分析回测文件
    trades = analyze_backtest_file(input_file)
    if trades is None:
        return

    # 计算币种统计
    print("\n计算币种统计数据...")
    pair_stats_list = calculate_pair_stats(trades)

    # 分类币种
    print("应用识别规则...")
    toxic_pairs, warning_pairs, safe_pairs = classify_pairs(pair_stats_list)

    # 打印报告
    print_analysis_report(toxic_pairs, warning_pairs, safe_pairs)

    # 生成黑名单
    blacklist = generate_blacklist(toxic_pairs, warning_pairs)

    # 保存结果
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    save_blacklist(blacklist, output_path)

    # 打印使用建议
    print("\n" + "=" * 100)
    print("📋 使用建议：")
    print("=" * 100)
    print("\n1. 查看生成的黑名单:")
    print(f"   cat {output_path}")

    print("\n2. 手动合并到主配置:")
    print(f"   vim user_data/config-custom.json")
    print(f"   # 将以下币种添加到 pair_blacklist:")
    for pair in blacklist['pair_blacklist']:
        print(f"   #   \"{pair}\",")

    print("\n3. 或使用Python自动合并:")
    print("""   python3 << EOF
import json

with open('user_data/blacklist_auto_generated.json') as f:
    auto_bl = json.load(f)

with open('user_data/config-custom.json') as f:
    config = json.load(f)

# 合并黑名单
manual = set(config.get('pair_blacklist', []))
auto = set(auto_bl['pair_blacklist'])
config['pair_blacklist'] = sorted(list(manual | auto))

# 合并Grind黑名单
if 'nfi_parameters' not in config:
    config['nfi_parameters'] = {}
manual_grind = set(config['nfi_parameters'].get('blacklist_120_pairs', []))
auto_grind = set(auto_bl['grind_blacklist'])
config['nfi_parameters']['blacklist_120_pairs'] = sorted(list(manual_grind | auto_grind))

with open('user_data/config-custom.json', 'w') as f:
    json.dump(config, f, indent=2, ensure_ascii=False)

print("✅ 配置已更新")
print(f"   永久黑名单: {len(config['pair_blacklist'])}个")
print(f"   Grind黑名单: {len(config['nfi_parameters']['blacklist_120_pairs'])}个")
EOF""")

    print("\n4. 重启Bot（如果在运行）:")
    print("   ./ft stop --bot && ./ft start --bot -d")


if __name__ == '__main__':
    main()
