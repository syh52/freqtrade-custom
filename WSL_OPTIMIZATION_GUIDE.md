# WSL 优化指南 - 解决回测崩溃问题

## 问题诊断

您的 WSL 在回测时崩溃的根本原因是：

1. **回测规模过大**：80 个交易对 × 6 个时间框架 = 480 个数据集
2. **内存限制不足**：WSL 配置的 12GB 内存对于大规模回测不够
3. **策略复杂度高**：NostalgiaForInfinityX7 计算大量技术指标

## 解决方案

### 方案 1：使用优化的配置（立即见效）

我已经为您创建了优化的配置文件：

```bash
# 使用安全的回测脚本（40 个交易对）
./start_backtest_safe.sh 20241001-20241101

# 或者直接使用优化配置
freqtrade backtesting \
  --config user_data/config-backtest-optimized.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20241001-20241101
```

**优势**：
- ✅ 交易对数量从 80 减少到 40
- ✅ 内存使用减少约 50%
- ✅ 回测速度更快
- ✅ 不会导致 WSL 崩溃

### 方案 2：增加 WSL 内存限制（如果主机内存充足）

如果您的 Windows 主机有 **32GB 或更多内存**，可以增加 WSL 的内存限制：

#### 步骤：

1. **找到您的 Windows 用户目录**（通常是 `C:\Users\您的用户名`）

2. **编辑或创建 `.wslconfig` 文件**

   在 Windows 资源管理器中，导航到用户目录并编辑 `.wslconfig` 文件（您已经有这个文件）。

3. **修改内存设置**

   将内存从 12GB 增加到 20GB 或更多：

   ```ini
   [wsl2]
   # 增加内存限制（确保主机有足够 RAM）
   memory=20GB  # 从 12GB 增加到 20GB

   # 增加 CPU 核心数
   processors=8  # 从 6 增加到 8

   # 增加交换空间
   swap=16GB    # 从 8GB 增加到 16GB

   # 交换文件位置
   swapfile=C:\\temp\\wsl-swap.vhdx

   # 启用本地主机转发
   localhostForwarding=true
   ```

4. **重启 WSL**

   在 Windows PowerShell（管理员）中执行：

   ```powershell
   wsl --shutdown
   ```

   然后重新打开 WSL 终端。

5. **验证新配置**

   在 WSL 中运行：

   ```bash
   free -h
   ```

   应该看到接近 20GB 的总内存。

### 方案 3：分批回测

如果您需要回测 80 个交易对，可以分批进行：

```bash
# 第一批：前 40 个交易对
freqtrade backtesting \
  --config user_data/config-backtest-optimized.json \
  --strategy NostalgiaForInfinityX7 \
  --timerange 20241001-20241101

# 第二批：后 40 个交易对（修改配置文件中的 pairlist）
# ... 然后再次运行回测
```

### 方案 4：减少回测时间范围

```bash
# 只回测 1 个月而不是 1 年
./start_backtest_safe.sh 20241001-20241101

# 或者只回测最近 30 天
./start_backtest_safe.sh
```

## 监控内存使用

在回测期间，您可以在另一个终端监控内存使用：

```bash
# 实时监控内存
watch -n 2 free -h

# 或者使用 htop
htop
```

## 推荐的回测工作流程

1. **首次测试**：使用 `config-backtest-optimized.json`（40 个交易对）
2. **验证策略**：确保策略在小规模数据上工作正常
3. **扩展测试**：如果需要更多交易对，先增加 WSL 内存限制
4. **全规模回测**：在确保有足够内存后，再使用完整的 80 个交易对

## 文件清单

已创建的优化文件：

- ✅ `user_data/configs/pairlist-volume-binance-usdt-40pairs.json` - 40 个交易对的 pairlist
- ✅ `user_data/config-backtest-optimized.json` - 优化的回测配置
- ✅ `start_backtest_safe.sh` - 安全回测启动脚本

## 常见问题

**Q: 40 个交易对够用吗？**
A: 根据 NostalgiaForInfinityX7 的官方建议，40-80 个交易对都是合理的。40 个交易对已经足够进行有效的回测和实盘交易。

**Q: 我的主机有多少内存才能运行 80 个交易对？**
A: 建议主机至少有 32GB RAM，为 WSL 分配 20GB 内存。

**Q: 如何检查我的主机内存？**
A: 在 Windows PowerShell 中运行：
```powershell
systeminfo | findstr /C:"Total Physical Memory"
```

**Q: 回测速度会受影响吗？**
A: 使用 40 个交易对反而会**更快**，因为减少了数据处理量。

## 下一步

1. 尝试运行安全回测脚本：
   ```bash
   ./start_backtest_safe.sh 20241001-20241101
   ```

2. 如果成功，您可以逐步增加交易对数量或增加 WSL 内存限制。

3. 如果仍然遇到问题，请检查：
   - Windows 事件查看器中的 WSL 错误日志
   - 主机的磁盘空间是否充足
   - 是否有其他占用大量内存的程序在运行

## 技术支持

如果问题持续存在，请提供以下信息：

```bash
# 系统信息
free -h
df -h
cat /proc/meminfo | grep -E 'MemTotal|MemFree|MemAvailable'

# WSL 版本
wsl --version  # 在 Windows PowerShell 中运行
```
