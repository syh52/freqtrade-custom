#!/usr/bin/env python3
"""
直接检查 balance API 的响应
"""
import requests
import json

# API 配置
api_url = "http://127.0.0.1:8082"
username = "freqtrade_user"
password = "freqtrade_pass123"

print("=" * 60)
print("检查 /api/v1/balance API 响应")
print("=" * 60)

# 步骤 1: 登录获取 token
print("\n步骤 1: 登录...")
try:
    login_resp = requests.post(
        f"{api_url}/api/v1/token/login",
        data={"username": username, "password": password},
        timeout=10
    )
    login_resp.raise_for_status()
    token = login_resp.json().get("access_token")
    print(f"✓ 登录成功，获取到 token")
except Exception as e:
    print(f"❌ 登录失败: {e}")
    exit(1)

# 步骤 2: 获取 balance 数据
print("\n步骤 2: 调用 /api/v1/balance...")
try:
    headers = {"Authorization": f"Bearer {token}"}
    balance_resp = requests.get(
        f"{api_url}/api/v1/balance",
        headers=headers,
        timeout=10
    )
    balance_resp.raise_for_status()
    balance_data = balance_resp.json()

    print(f"✓ 成功获取 balance 数据")
    print(f"\n" + "=" * 60)
    print("完整的 API 响应:")
    print("=" * 60)
    print(json.dumps(balance_data, indent=2, ensure_ascii=False))

    # 分析数据
    print(f"\n" + "=" * 60)
    print("数据分析:")
    print("=" * 60)

    if "currencies" in balance_data:
        print(f"\n币种数量: {len(balance_data['currencies'])}")
        print(f"总余额 (total): {balance_data.get('total', 'N/A')}")
        print(f"机器人管理余额 (total_bot): {balance_data.get('total_bot', 'N/A')}")
        print(f"起始资本: {balance_data.get('starting_capital', 'N/A')}")
        print(f"起始资本法币: {balance_data.get('starting_capital_fiat', 'N/A')}")

        print(f"\n所有币种信息:")
        for curr in balance_data['currencies']:
            print(f"\n  币种: {curr.get('currency', 'N/A')}")
            print(f"    free: {curr.get('free', 'N/A')}")
            print(f"    balance: {curr.get('balance', 'N/A')}")
            print(f"    used: {curr.get('used', 'N/A')}")
            print(f"    est_stake: {curr.get('est_stake', 'N/A')}")
            print(f"    est_stake_bot: {curr.get('est_stake_bot', 'N/A')}")
            print(f"    is_position: {curr.get('is_position', 'N/A')}")
            print(f"    is_bot_managed: {curr.get('is_bot_managed', 'N/A')}")

            # 检查关键字段
            if curr.get('is_position'):
                print(f"    position: {curr.get('position', 'N/A')}")
                print(f"    side: {curr.get('side', 'N/A')}")

    print(f"\n" + "=" * 60)

except Exception as e:
    print(f"❌ 调用失败: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("检查完成")
print("=" * 60)
