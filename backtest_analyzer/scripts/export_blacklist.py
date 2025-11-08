#!/usr/bin/env python3
"""
黑名单导出脚本

从分析结果中提取并导出黑名单配置
"""

import argparse
import json
import sys
from pathlib import Path

# 添加项目根目录
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backtest_analyzer.core.loader import BacktestResultLoader
from backtest_analyzer.core.cleaner import DataCleaner
from backtest_analyzer.analyzers.toxic_pair_detector import ToxicPairDetector


def export_blacklist(backtest_file: str, output_file: str = None, format_type: str = 'freqtrade'):
    """
    导出黑名单配置

    Args:
        backtest_file: 回测文件路径
        output_file: 输出文件路径（默认为configs/blacklist-dynamic.json）
        format_type: 格式类型（freqtrade/simple）
    """
    print(f"\n{'='*80}")
    print("黑名单导出工具")
    print(f"{'='*80}\n")

    # 加载数据
    print(f"正在加载回测结果: {backtest_file}")
    loader = BacktestResultLoader(backtest_file)
    data = loader.load_all()

    # 数据增强
    print("正在增强数据...")
    trades_df = DataCleaner.clean_and_enhance_trades(data['trades'])

    # 执行毒瘤币检测
    print("正在分析毒瘤币...")
    detector = ToxicPairDetector(trades_df)
    analysis = detector.analyze()

    summary = analysis['summary']
    print(f"\n分析结果:")
    print(f"  总币种数: {summary['total_pairs']}")
    print(f"  🔴 Level 1 (致命风险): {summary['level1_count']}")
    print(f"  🟠 Level 2 (警告风险): {summary['level2_count']}")
    print(f"  🟡 Level 3 (需监控): {summary['level3_count']}")
    print(f"  ✅ 安全币种: {summary['safe_count']}")

    # 生成黑名单
    blacklist_config = analysis['blacklist_config']

    if format_type == 'freqtrade':
        # Freqtrade配置格式
        output_config = blacklist_config['freqtrade_format']
    elif format_type == 'simple':
        # 简单列表格式
        output_config = {
            'full_blacklist': blacklist_config['full_blacklist'],
            'grind_restricted': blacklist_config['grind_restricted'],
            'monitor_list': blacklist_config['monitor_list']
        }
    else:
        raise ValueError(f"不支持的格式类型: {format_type}")

    # 确定输出路径
    if output_file is None:
        output_file = project_root / 'configs' / 'blacklist-dynamic.json'
    else:
        output_file = Path(output_file)

    # 创建目录
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 黑名单配置已导出到: {output_file}")

    # 打印详细信息
    if blacklist_config['full_blacklist']:
        print(f"\n🔴 完全拉黑列表 ({len(blacklist_config['full_blacklist'])}个):")
        for pair in blacklist_config['full_blacklist']:
            print(f"  - {pair}")

    if blacklist_config['grind_restricted']:
        print(f"\n🟠 限制Grind列表 ({len(blacklist_config['grind_restricted'])}个):")
        for pair in blacklist_config['grind_restricted']:
            print(f"  - {pair}")

    # 打印使用说明
    print(f"\n{'='*80}")
    print("使用说明:")
    print(f"{'='*80}")
    print(f"1. 将生成的配置添加到您的主配置文件:")
    print(f"   在 config-custom.json 的 add_config_files 中添加:")
    print(f'   "configs/blacklist-dynamic.json"')
    print(f"\n2. 或者直接合并到现有的黑名单配置中")
    print(f"\n3. 重启Bot以应用新的黑名单")
    print(f"{'='*80}\n")

    return output_config


def main():
    parser = argparse.ArgumentParser(
        description='从回测结果导出黑名单配置',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 导出黑名单到默认位置
  python scripts/export_blacklist.py --input user_data/backtest_results/backtest-result.json

  # 指定输出文件
  python scripts/export_blacklist.py --input backtest-result.json --output my-blacklist.json

  # 导出简单格式
  python scripts/export_blacklist.py --input backtest-result.json --format simple
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=str,
        default='user_data/backtest_results/backtest-result-2025-11-07_16-36-54.json',
        help='回测结果文件路径（支持.json或.zip）'
    )

    parser.add_argument(
        '--output', '-o',
        type=str,
        default=None,
        help='输出文件路径（默认：configs/blacklist-dynamic.json）'
    )

    parser.add_argument(
        '--format', '-f',
        type=str,
        choices=['freqtrade', 'simple'],
        default='freqtrade',
        help='输出格式（freqtrade: 完整配置格式, simple: 简单列表）'
    )

    args = parser.parse_args()

    try:
        export_blacklist(
            backtest_file=args.input,
            output_file=args.output,
            format_type=args.format
        )
    except Exception as e:
        print(f"\n❌ 导出失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
