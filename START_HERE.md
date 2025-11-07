# 👋 欢迎使用 Freqtrade 交易Bot

> 如果这是你第一次使用这个项目，请从这里开始！

---

## 🚀 30秒快速启动

```bash
# 一键启动Bot + Web界面（后台运行）
./ft start --bot --ui -d

# 查看运行状态
./ft status

# 浏览器访问 http://127.0.0.1:3000
# 登录信息：
#   API地址: http://127.0.0.1:8082
#   用户名: freqtrade_user
#   密码: freqtrade_pass123
```

**就这么简单！** 🎉

---

## 📚 完整文档导航

### 新手必读

1. **[PROJECT_README.md](./PROJECT_README.md)**
   - 📖 项目总览
   - 🏗️ 架构说明
   - 🔧 常用命令速查

2. **[QUICK_START.md](./QUICK_START.md)**
   - 🎯 详细的启动指南
   - 🔄 多种启动方式对比
   - 🧪 回测使用方法

### 进阶配置

3. **[CONFIG_USAGE_GUIDE.md](./CONFIG_USAGE_GUIDE.md)**
   - ⚙️ 配置文件详解
   - 🔐 API密钥配置
   - 📊 策略参数调整

4. **[BACKTEST_GUIDE.md](./BACKTEST_GUIDE.md)**
   - 📈 回测方法
   - 🎲 策略优化
   - 📉 性能分析

### 开发者

5. **[CLAUDE.md](./CLAUDE.md)**
   - 💻 开发环境设置
   - 🧪 测试方法
   - 🔨 代码规范

---

## ⚡ 常用命令

```bash
# 启动服务
./ft start --bot --ui -d    # Bot + UI（后台）
./ft start --bot -d         # 只启动Bot
./ft start --ui             # 只启动UI

# 查看状态
./ft status                 # 查看所有服务

# 停止服务
./ft stop --all             # 停止所有
./ft stop --bot             # 只停止Bot
./ft stop --ui              # 只停止UI

# 帮助
./ft help                   # 查看完整帮助
```

---

## 🎓 推荐学习路径

### 第一天：了解基础

1. ✅ 运行 `./ft start --bot --ui -d` 启动系统
2. ✅ 访问 Web UI 查看界面
3. ✅ 运行 `./ft status` 了解服务状态
4. ✅ 阅读 [QUICK_START.md](./QUICK_START.md) 了解基础操作

### 第二天：深入配置

1. ✅ 阅读 [PROJECT_README.md](./PROJECT_README.md) 了解架构
2. ✅ 阅读 [CONFIG_USAGE_GUIDE.md](./CONFIG_USAGE_GUIDE.md) 了解配置
3. ✅ 查看日志：`tail -f user_data/logs/freqtrade.log`
4. ✅ 测试API：`curl http://127.0.0.1:8082/api/v1/status`

### 第三天：回测优化

1. ✅ 阅读 [BACKTEST_GUIDE.md](./BACKTEST_GUIDE.md)
2. ✅ 运行第一次回测
3. ✅ 分析回测结果
4. ✅ 尝试调整参数

---

## 🆘 遇到问题？

### 快速检查清单

- [ ] 虚拟环境是否激活？`source .venv/bin/activate`
- [ ] 端口是否被占用？`./ft status`
- [ ] 配置文件是否存在？`ls user_data/config-*.json`
- [ ] 查看日志有无错误？`tail -100 user_data/logs/freqtrade.log`

### 常见问题

**Q: Bot启动失败？**
```bash
# 查看详细日志
tail -100 user_data/logs/freqtrade.log

# 验证配置
freqtrade show-config --config user_data/config-custom.json
```

**Q: Web UI无法连接？**
```bash
# 检查Bot是否运行
./ft status

# 测试API
curl http://127.0.0.1:8082/api/v1/ping
```

**Q: 端口冲突？**
```bash
# ft脚本会自动处理端口冲突
./ft start --bot --ui -d
```

### 获取帮助

1. 📖 查看文档：[QUICK_START.md](./QUICK_START.md)
2. 🔍 查看故障排查：[PROJECT_README.md](./PROJECT_README.md#-故障排查)
3. 💬 官方Discord：https://discord.gg/p7nuUNVfP7
4. 📚 官方文档：https://www.freqtrade.io

---

## ⚠️ 重要提醒

### 安全第一

- ⚠️ **从Dry-run模式开始**（默认配置）
- ⚠️ **先回测，再实盘**
- ⚠️ **使用小额测试**
- ⚠️ **保护好API密钥**（`config-private.json`）
- ⚠️ **启用交易所2FA**

### 风险提示

> ⚠️ **加密货币交易存在风险**
>
> - 本软件仅供学习和研究
> - 不对任何交易结果负责
> - 请只用你能承受损失的资金
> - 建议从小额开始

---

## 🎯 下一步

现在你已经准备好了！

1. 🚀 运行 `./ft start --bot --ui -d` 启动系统
2. 📖 阅读 [PROJECT_README.md](./PROJECT_README.md) 了解更多
3. 🎓 按推荐学习路径逐步深入
4. 💪 享受自动化交易的乐趣！

---

**祝交易顺利！** 📈💰

_最后更新: 2025-01-06_
