#!/usr/bin/env python3
"""
诊断 balance 问题 - 追踪数据流
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from freqtrade.configuration import Configuration
from freqtrade.resolvers import ExchangeResolver
from freqtrade.wallets import Wallets
import json


def diagnose():
    print("=" * 60)
    print("诊断 Balance 问题")
    print("=" * 60)

    # 加载配置
    config_files = [
        "user_data/config-custom.json",
        "user_data/config-private.json"
    ]

    configuration = Configuration({
        "config": config_files,
        "strategy": "NostalgiaForInfinityX7"
    })
    config = configuration.get_config()

    print(f"\n配置信息:")
    print(f"  dry_run: {config.get('dry_run')}")
    print(f"  dry_run_wallet: {config.get('dry_run_wallet', 'NOT SET')}")
    print(f"  available_capital: {config.get('available_capital', 'NOT SET')}")
    print(f"  trading_mode: {config.get('trading_mode')}")
    print(f"  stake_currency: {config.get('stake_currency')}")

    # 创建交易所实例
    print(f"\n创建交易所实例...")
    exchange = ExchangeResolver.load_exchange(config)
    print(f"✓ 交易所: {exchange.name}")

    # 创建 Wallets 实例
    print(f"\n创建 Wallets 实例...")
    try:
        wallets = Wallets(config, exchange, is_backtest=False)
        print(f"✓ Wallets 实例创建成功")
    except Exception as e:
        print(f"❌ Wallets 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return

    # 检查 wallets 内部状态
    print(f"\n" + "=" * 60)
    print("Wallets 内部状态:")
    print("=" * 60)
    print(f"  _stake_currency: {wallets._stake_currency}")
    print(f"  _start_cap: {wallets._start_cap}")
    print(f"  _is_backtest: {wallets._is_backtest}")

    # 获取 balances
    print(f"\n" + "=" * 60)
    print("调用 get_all_balances():")
    print("=" * 60)
    all_balances = wallets.get_all_balances()
    print(f"  返回的币种数量: {len(all_balances)}")

    for currency, wallet in all_balances.items():
        print(f"\n  {currency}:")
        print(f"    free: {wallet.free}")
        print(f"    used: {wallet.used}")
        print(f"    total: {wallet.total}")

    # 获取 positions
    print(f"\n" + "=" * 60)
    print("调用 get_all_positions():")
    print("=" * 60)
    all_positions = wallets.get_all_positions()
    print(f"  返回的持仓数量: {len(all_positions)}")

    for symbol, position in all_positions.items():
        print(f"\n  {symbol}:")
        print(f"    position: {position.position}")
        print(f"    collateral: {position.collateral}")
        print(f"    side: {position.side}")

    # 模拟 RPC _rpc_balance 的逻辑
    print(f"\n" + "=" * 60)
    print("模拟 RPC _rpc_balance 逻辑:")
    print("=" * 60)

    currencies_list = []
    for coin, balance in all_balances.items():
        print(f"\n检查 {coin}:")
        print(f"  balance.total = {balance.total}")
        print(f"  balance.free = {balance.free}")
        print(f"  条件: not balance.total and not balance.free = {not balance.total and not balance.free}")

        if not balance.total and not balance.free:
            print(f"  ❌ 跳过（total 和 free 都为 0）")
            continue
        else:
            print(f"  ✓ 将添加到 currencies 列表")
            currencies_list.append(coin)

    print(f"\n最终 currencies 列表包含: {currencies_list}")
    print(f"currencies 数量: {len(currencies_list)}")

    if len(currencies_list) == 0:
        print(f"\n⚠️  问题确认：currencies 列表为空！")
        print(f"\n可能原因:")
        print(f"  1. get_all_balances() 返回空字典")
        print(f"  2. 所有币种的 total 和 free 都为 0")
        print(f"  3. wallets 初始化或更新时出错")

    print(f"\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)


if __name__ == "__main__":
    diagnose()
