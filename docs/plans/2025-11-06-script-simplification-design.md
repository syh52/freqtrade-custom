# Freqtrade 启动脚本简化设计文档

**日期**: 2025-11-06
**作者**: Claude Code
**状态**: 设计阶段

## 1. 概述

本设计文档描述了 Freqtrade 项目启动脚本的简化重构方案。通过模块化设计和统一入口，解决当前脚本中存在的端口冲突处理暴力、职责混合、代码重复等问题。

## 2. 问题分析

### 2.1 现有脚本问题

#### 问题 1: 端口冲突处理过于暴力
- **start_all.sh**: 扫描 3000-3010 全部端口（第 46-52 行）
- 使用 `kill -9` 强制杀进程，可能导致数据不一致
- 多次循环等待端口释放，效率低下

#### 问题 2: 脚本职责不清
- **start_all.sh**: 混合了 Freqtrade Bot 和 FreqUI 两个独立服务的启动逻辑
- 无法独立启动/停止某个服务
- 增加了维护难度

#### 问题 3: 代码重复
- 端口检查逻辑在多个脚本中重复实现
- 打印函数（print_info、print_success 等）重复定义
- 进程管理逻辑分散在各个脚本中

### 2.2 使用场景分析

根据用户需求，主要有两种使用场景：

1. **实盘交易模式**: Freqtrade Bot (实盘策略) + FreqUI 前端 → 一起启动
2. **分析模式**: 只启动 FreqUI → 用于 Dry Run / Backtesting / 分析

## 3. 设计目标

### 3.1 核心目标

1. **职责分离**: 每个脚本只负责一个服务的管理
2. **代码复用**: 提取共享逻辑到函数库
3. **智能端口管理**: 精确识别进程，优雅停止
4. **友好接口**: 提供统一的命令行入口
5. **向后兼容**: 保留旧脚本作为备份

### 3.2 非目标

- 不涉及服务配置文件的修改
- 不改变 Freqtrade / FreqUI 本身的运行方式
- 不引入第三方依赖（如 systemd / supervisor）

## 4. 架构设计

### 4.1 设计方案: 独立脚本 + 统一入口

```
┌─────────────────────────────────────────────────────┐
│                   ft (主控脚本)                      │
│  命令: start/stop/status/restart                     │
│  参数: --bot/--ui/--all/--config                    │
└────────────┬────────────────────────────────────────┘
             │
             ├──────────────┬──────────────┬───────────────┐
             │              │              │               │
     ┌───────▼─────┐  ┌─────▼──────┐  ┌───▼───────┐  ┌───▼────────┐
     │ start-bot.sh│  │start-ui.sh │  │  stop.sh  │  │ status.sh  │
     └───────┬─────┘  └─────┬──────┘  └───┬───────┘  └───┬────────┘
             │              │              │              │
             └──────────────┴──────────────┴──────────────┘
                            │
                     ┌──────▼───────┐
                     │ lib/common.sh│
                     │ 共享函数库    │
                     └──────────────┘
```

### 4.2 核心组件

#### 4.2.1 共享函数库 (lib/common.sh)

提供以下功能：

**打印函数**:
- `print_info()` - [INFO] 蓝色
- `print_success()` - [SUCCESS] 绿色
- `print_warning()` - [WARNING] 黄色
- `print_error()` - [ERROR] 红色

**端口管理**:
- `check_port(port)` - 检查端口是否被占用（只检查 LISTEN 状态）
- `kill_port_process(port, process_pattern)` - 停止占用端口的进程
- `wait_port_ready(port, timeout)` - 等待端口释放

**进程管理**:
- `find_bot_process()` - 查找 freqtrade trade 进程
- `find_ui_process()` - 查找 FreqUI (vite/npm) 进程
- `stop_process_gracefully(pid)` - 优雅停止进程（TERM → KILL）

**健康检查**:
- `check_bot_health()` - 检查 Bot API 是否响应
- `check_ui_health()` - 检查 FreqUI 是否响应

#### 4.2.2 独立启动脚本

**scripts/start-bot.sh**:
- 负责启动 Freqtrade Bot
- 支持参数: `--config FILE`, `--strategy NAME`, `--daemon`
- 端口: 8082 (Bot API)

**scripts/start-ui.sh**:
- 负责启动 FreqUI 前端
- 自动检测 `/home/dministrator/Newproject/frequi` 目录
- 端口: 3000 (FreqUI)

**scripts/stop.sh**:
- 支持参数: `--bot`, `--ui`, `--all`
- 优雅停止进程（TERM → KILL）

**scripts/status.sh**:
- 显示所有服务运行状态
- 显示监听的端口和进程 ID

#### 4.2.3 主控脚本 (ft)

提供统一的命令行接口：

```bash
ft start [--bot] [--ui] [--config FILE]
ft stop [--bot] [--ui] [--all]
ft status
ft restart [--bot] [--ui] [--all]
```

## 5. 文件结构

```
freqtrade/
├── lib/
│   └── common.sh                    # 共享函数库
├── scripts/
│   ├── start-bot.sh                 # 启动 Freqtrade Bot
│   ├── start-ui.sh                  # 启动 FreqUI 前端
│   ├── stop.sh                      # 停止服务
│   └── status.sh                    # 查看运行状态
├── ft                               # 主控脚本（统一入口）
└── [旧脚本备份]
    ├── start_all.sh.bak             # 原 start_all.sh
    ├── start_frequi.sh.bak          # 原 start_frequi.sh
    └── start_dryrun.sh.bak          # 原 start_dryrun.sh
```

## 6. 端口冲突处理策略

### 6.1 改进前（现有实现）

```bash
# start_all.sh 第 46-52 行
# 问题: 扫描 3000-3010 全部端口
for port in {3000..3010}; do
    PORT_PID=$(lsof -t -i:$port 2>/dev/null)
    if [ -n "$PORT_PID" ]; then
        kill -9 $PORT_PID 2>/dev/null  # 强制杀死
    fi
done
```

### 6.2 改进后（新策略）

```bash
# 步骤 1: 精确识别
check_port 3000  # 只检查 FreqUI 端口
check_port 8082  # 只检查 Bot API 端口

# 步骤 2: 智能过滤
# 只停止属于 freqtrade/vite/npm 的进程
lsof -i :3000 -sTCP:LISTEN | grep -E 'vite|npm'
lsof -i :8082 -sTCP:LISTEN | grep freqtrade

# 步骤 3: 优雅停止
kill -TERM $PID    # 先发送 TERM 信号
sleep 5            # 等待进程保存状态
if still_running; then
    kill -KILL $PID  # 不响应才强制杀死
fi

# 步骤 4: 验证端口释放
wait_port_ready 3000 --timeout 10
```

**优势**:
- ✅ 不影响其他无关进程
- ✅ 给进程时间保存状态
- ✅ 清晰的错误提示

## 7. 使用示例

### 7.1 实盘交易模式（Bot + UI）

```bash
# 启动实盘 Bot + FreqUI
./ft start --bot --ui

# 指定配置文件
./ft start --bot --ui --config user_data/config-custom.json

# 查看状态
./ft status

# 停止所有服务
./ft stop --all
```

### 7.2 分析模式（仅 UI）

```bash
# 只启动 FreqUI（用于 Dry Run / Backtesting）
./ft start --ui

# 停止 UI
./ft stop --ui
```

### 7.3 独立调用脚本

```bash
# 直接调用脚本（不通过 ft）
./scripts/start-bot.sh --config user_data/config-custom.json
./scripts/start-ui.sh
./scripts/stop.sh --bot
./scripts/status.sh
```

## 8. 实施计划

### 8.1 阶段 1: 创建共享函数库

- [ ] 创建 `lib/common.sh`
- [ ] 实现打印函数
- [ ] 实现端口管理函数
- [ ] 实现进程管理函数
- [ ] 实现健康检查函数

### 8.2 阶段 2: 创建独立脚本

- [ ] 创建 `scripts/start-bot.sh`
- [ ] 创建 `scripts/start-ui.sh`
- [ ] 创建 `scripts/stop.sh`
- [ ] 创建 `scripts/status.sh`

### 8.3 阶段 3: 创建主控脚本

- [ ] 创建 `ft` 主控脚本
- [ ] 实现参数解析
- [ ] 实现命令路由

### 8.4 阶段 4: 备份旧脚本

- [ ] 备份 `start_all.sh` → `start_all.sh.bak`
- [ ] 备份 `start_frequi.sh` → `start_frequi.sh.bak`
- [ ] 备份 `start_dryrun.sh` → `start_dryrun.sh.bak`

### 8.5 阶段 5: 测试验证

- [ ] 测试独立启动 Bot
- [ ] 测试独立启动 UI
- [ ] 测试同时启动 Bot + UI
- [ ] 测试端口冲突处理
- [ ] 测试优雅停止

## 9. 向后兼容性

### 9.1 保留旧脚本

所有旧脚本将备份为 `.bak` 后缀：
- `start_all.sh.bak`
- `start_frequi.sh.bak`
- `start_dryrun.sh.bak`
- `start_webui.sh.bak`
- `stop_dryrun.sh.bak`

### 9.2 迁移路径

用户可以继续使用旧脚本（通过 `.bak` 后缀），也可以逐步迁移到新接口：

| 旧脚本 | 新命令 |
|--------|--------|
| `./start_all.sh` | `./ft start --bot --ui` |
| `./start_frequi.sh` | `./ft start --ui` |
| `./start_dryrun.sh` | `./ft start --bot --config user_data/config.json` |
| `./stop_dryrun.sh` | `./ft stop --bot` |

## 10. 风险评估

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 端口检测逻辑错误 | 中 | 借鉴 start_webui.sh 的成熟实现 |
| 进程停止失败 | 中 | 实现优雅停止 + 强制停止双重机制 |
| 破坏现有工作流 | 低 | 保留旧脚本备份 |
| FreqUI 路径不存在 | 低 | 启动前检查目录存在性 |

## 11. 后续优化

本次简化完成后，可考虑的后续优化：

1. **配置文件支持**: 提供 `config/ft.conf` 配置文件，支持默认参数
2. **日志管理**: 添加 `./ft logs --bot --tail` 命令查看日志
3. **systemd 集成**: 提供 systemd 服务文件，实现开机自启
4. **监控告警**: 添加健康检查定时任务，异常时发送通知

---

**设计完成日期**: 2025-11-06
**预计实施时间**: 1-2 小时
