# Freqtrade Dry Run 使用指南

## 🚀 快速启动

### 1. 启动 Dry Run 模式

```bash
./start_dryrun.sh
```

**或者手动启动：**

```bash
source .venv/bin/activate
freqtrade trade --config user_data/config.json &
```

### 2. 访问 Web UI

打开浏览器访问：**http://127.0.0.1:8080**

**登录凭据：**
- 用户名: `freqtrade_user`
- 密码: `freqtrade_pass123`

### 3. 停止 Dry Run

```bash
./stop_dryrun.sh
```

**或者手动停止：**

```bash
pkill -f "freqtrade trade"
```

---

## 📋 配置说明

### 当前配置文件结构

```
user_data/
├── config.json                    # 主配置文件（策略选择）
├── config-custom.json             # 自定义配置（Dry Run 设置）
├── config-private.json            # 私密配置（API Keys）
└── configs/
    ├── pairlist-volume-binance-usdt.json    # 交易对配置
    └── blacklist-binance.json               # 黑名单配置
```

### 关键配置项

在 `user_data/config-custom.json` 中：

```json
{
  "dry_run": true,              // 必须为 true（模拟交易）
  "dry_run_wallet": 10000,      // 模拟钱包金额（USDT）
  "max_open_trades": 10,        // 最大同时持仓数
  "stake_amount": "unlimited",  // 每笔交易金额（unlimited=自动分配）
  "api_server": {
    "enabled": true,            // 必须启用 API（Web UI 需要）
    "listen_port": 8080         // API 端口
  }
}
```

在 `user_data/config.json` 中：

```json
{
  "strategy": "NostalgiaForInfinityX7_6x_limited_stoploss30"  // 使用的策略
}
```

---

## 🎯 Web UI 功能

### Dashboard（仪表板）
- 查看总资产、盈亏情况
- 今日交易统计
- 活跃交易数量

### Open Trades（持仓）
- 实时查看所有持仓
- 每个仓位的盈亏
- 手动平仓功能

### Trade History（历史）
- 所有已完成的交易
- 详细盈亏记录
- 交易时间线

### Whitelist（白名单）
- 当前监控的交易对列表
- 约 70 个主流币种

### Performance（性能）
- 每个币种的表现
- 胜率统计
- 平均收益率

### Charts（图表）
- 实时 K 线图
- 技术指标显示
- 买卖信号标记

---

## 🔍 监控和调试

### 实时查看日志

```bash
tail -f user_data/logs/freqtrade.log
```

### 检查进程状态

```bash
ps aux | grep freqtrade
```

### 检查 API 服务

```bash
curl http://127.0.0.1:8080/api/v1/ping
```

预期返回：`{"status":"pong"}`

---

## 🎮 常用命令

### 查看策略信息

```bash
source .venv/bin/activate
freqtrade show-config --config user_data/config.json
```

### 查看当前白名单

```bash
freqtrade list-pairs --config user_data/config.json
```

### 查看交易历史

```bash
freqtrade show-trades --config user_data/config.json
```

### 查看盈亏统计

```bash
freqtrade profit --config user_data/config.json
```

---

## ⚙️ 切换策略

编辑 `user_data/config.json`：

```json
{
  "strategy": "你的策略名称"
}
```

然后重启 Dry Run：

```bash
./stop_dryrun.sh
./start_dryrun.sh
```

---

## 📊 当前策略信息

**策略名称：** NostalgiaForInfinityX7_6x_limited_stoploss30

**策略特点：**
- 时间周期：5 分钟
- 止损：-30% （固定止损）
- 杠杆优化：6x
- 仓位调整：启用（DCA）
- 适用市场：币安 USDT 永续合约

**推荐设置：**
- 6-12 个开仓位
- 40-80 个交易对
- 使用稳定币对（USDT）

---

## 🚨 注意事项

### ✅ Dry Run 模式（当前）
- **不使用真实资金**
- 所有交易都是模拟的
- 用于测试策略和熟悉系统
- 数据保存在 `user_data/tradesv3.sqlite`

### ⚠️ 切换到实盘前
1. 充分测试策略（建议至少运行 1-2 周）
2. 理解策略的风险收益特征
3. 设置合理的止损和仓位管理
4. 将 `dry_run` 改为 `false`
5. **小资金开始，逐步增加**

---

## 🛠️ 故障排除

### Web UI 无法访问

**检查进程：**
```bash
ps aux | grep freqtrade
```

**检查端口：**
```bash
lsof -i :8080
```

**重启服务：**
```bash
./stop_dryrun.sh
./start_dryrun.sh
```

### 机器人没有交易

可能原因：
1. **市场条件不满足** - 策略有严格的入场条件
2. **白名单过滤** - 太多币被黑名单或年龄过滤器排除
3. **资金不足** - 检查 dry_run_wallet 设置
4. **策略加载失败** - 查看日志文件

### 查看详细错误

```bash
tail -100 user_data/logs/freqtrade.log
```

---

## 📚 更多资源

- **官方文档：** https://www.freqtrade.io
- **策略开发：** https://www.freqtrade.io/en/stable/strategy-customization/
- **Discord 支持：** https://discord.gg/p7nuUNVfP7

---

## 🔄 版本信息

- Freqtrade: 2025.11-dev
- 策略版本: v17.1.51-6x
- 配置日期: 2025-11-02
