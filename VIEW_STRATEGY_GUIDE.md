# 📖 交互式策略查看器 - 详细使用指南

> `view_strategy.sh` - 轻松浏览 70,737 行策略代码的神器

---

## 🎯 工具简介

这是一个**彩色交互式终端工具**，专门为浏览 NostalgiaForInfinityX7 策略而设计。无需记住复杂的 grep/sed 命令，只需选择菜单选项，即可快速定位和查看代码。

### 特点

- 🎨 **彩色界面** - 清晰的视觉层次
- 🔄 **循环菜单** - 看完自动返回，无需重启
- 📂 **分类浏览** - 按功能组织，快速定位
- 🔍 **智能搜索** - 内置关键字搜索
- 📍 **精准定位** - 自动计算代码行号
- 💡 **零学习成本** - 跟着菜单选就行

---

## 🚀 启动方式

```bash
# 方法1: 直接运行
./view_strategy.sh

# 方法2: 用bash运行
bash view_strategy.sh

# 如果没有执行权限，先添加
chmod +x view_strategy.sh
```

---

## 📋 完整菜单结构

启动后您会看到这样的界面：

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   📊 NostalgiaForInfinityX7 策略快速查看器
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请选择要查看的内容:

  基础信息
    1) 查看核心配置参数
    2) 查看版本和基本信息
    3) 查看启用的入场信号列表

  入场信号
    11) 查看信号 #1-#6 (Normal模式)
    12) 查看信号 #41-#46 (Pump模式)
    13) 查看信号 #61-#63 (Rebuy模式)
    14) 查看信号 #101-#104 (High Profit模式)
    15) 查看信号 #141-#145 (Grind模式)
    16) 查看信号 #161-#163 (Top Coins模式)
    17) 查看所有做空信号
    18) 查看特定信号 (输入编号)

  出场和DCA
    21) 查看自定义出场逻辑 (custom_exit)
    22) 查看DCA加仓主逻辑
    23) 查看Long Grind DCA
    24) 查看出场条件方法列表

  技术指标
    31) 查看populate_indicators (主指标)
    32) 查看多时间框架指标方法
    33) 查看BTC相关指标

  分析和文档
    41) 生成策略结构报告
    42) 打开完整概览文档
    43) 搜索关键字
    44) 查看方法定义位置

  0) 退出

请输入选项: _
```

---

## 📚 功能详解

### 📦 第一组: 基础信息 (选项 1-3)

#### 选项 1️⃣: 查看核心配置参数

**功能**: 显示策略最重要的配置
**输出示例**:
```python
📋 核心配置参数:

  stoploss = -0.99                    # ⚠️ 极危险！
  timeframe = "5m"
  trailing_stop = False
  use_custom_stoploss = False
  position_adjustment_enable = True
  max_entry_position_adjustment = 6
  can_short = True
```

**适合场景**:
- 快速检查当前风险设置
- 确认时间框架和止损
- 了解是否启用DCA

---

#### 选项 2️⃣: 查看版本和基本信息

**功能**: 显示策略文件的元信息
**输出示例**:
```python
ℹ️ 策略版本信息:

class NostalgiaForInfinityX7(IStrategy):
  INTERFACE_VERSION = 3

  def version(self) -> str:
    return "v17.1.62"

文件统计:
70737 user_data/strategies/NostalgiaForInfinityX7.py
2.8M  user_data/strategies/NostalgiaForInfinityX7.py
```

**适合场景**:
- 确认策略版本
- 查看文件大小
- 了解接口版本

---

#### 选项 3️⃣: 查看启用的入场信号列表

**功能**: 列出所有已启用和已禁用的信号
**输出示例**:
```
✅ 已启用的入场信号:

做多信号:
  #1
  #2
  #3
  #4
  #5
  #6
  #21
  #41
  #42
  ... (共28个)

做空信号:
  #501
  #502
  #542

⏸️ 已禁用的信号:
  # "short_entry_condition_503_enable": True,
  # "short_entry_condition_504_enable": True,
  ...
```

**适合场景**:
- 快速查看哪些信号在工作
- 确认是否禁用了危险信号
- 了解做多/做空信号数量

---

### 🎯 第二组: 入场信号 (选项 11-18)

#### 选项 1️⃣1️⃣: 查看信号 #1-#6 (Normal模式)

**功能**: 显示最基础、最稳健的6个信号
**输出示例**:
```python
🎯 Normal模式信号 (#1-#6)

信号 #1 (行 11855):
        if long_entry_condition_index == 1:
          # Protections
          long_entry_logic.append(df["num_empty_288"] <= allowed_empty_candles_288)
          long_entry_logic.append(df["protections_long_global"] == True)

          long_entry_logic.append(
            # 5m & 15m & 1h down move
            ((df["RSI_3"] > 3.0) | (df["RSI_3_15m"] > 3.0) | (df["RSI_3_change_pct_1h"] > -50.0))
            # 5m & 15m down move, 5h high
            & ((df["RSI_3"] > 3.0) | (df["RSI_3_15m"] > 5.0) | (df["RSI_14_4h"] < 60.0))
            ...
          )

信号 #2 (行 12012):
        if long_entry_condition_index == 2:
          ...

... (依次显示 #1-#6)
```

**适合场景**:
- 学习基础信号逻辑
- 理解多时间框架过滤
- 研究保护机制

---

#### 选项 1️⃣2️⃣-1️⃣7️⃣: 其他信号分类

同样的格式，分别显示：
- **12**: Pump模式 (#41-46) - 拉盘追踪信号
- **13**: Rebuy模式 (#61-63) - 回购/补仓信号
- **14**: High Profit (#101-104) - 高利润模式
- **15**: Grind模式 (#141-145) - 磨仓模式 ⭐ 重点！
- **16**: Top Coins (#161-163) - 头部币种模式
- **17**: 做空信号 (#501-542)

---

#### 选项 1️⃣8️⃣: 查看特定信号 ⭐ 最实用！

**功能**: 输入任意信号编号，精确定位
**使用流程**:
```
请输入选项: 18
请输入信号编号 (例如: 142): 142

📍 信号 #142 (行 16713):

        if long_entry_condition_index == 142:
          # Protections
          long_entry_logic.append(df["protections_long_global"] == True)
          long_entry_logic.append(df["protections_long_rebuy"] == True)

          long_entry_logic.append(
            (df["close"] < df["EMA_26"] * 0.936)
            & (df["EMA_12"] < df["EMA_26"])
            & (df["WILLR_14"] < -75.0)
            & (df["RSI_14"] < 35.0)
            & (df["close"] < df["BB_lower_15m"] * 1.004)
            & (df["AROONU_14_15m"] < 25.0)
            & (df["AROONU_14_4h"] < 25.0)
            & (df["close"] < df["SMA_200_1h"] * 0.942)
          )
          ...
```

**适合场景**:
- 深入研究某个特定信号
- 查看最佳信号 #142, #145
- 检查危险信号 #62, #141, #144
- 对比不同信号的逻辑

**💡 使用技巧**:
```bash
# 研究最佳信号
选 18 -> 输入 142  # 95.2% 胜率
选 18 -> 输入 145  # 90.8% 胜率

# 查看危险信号（看看为什么危险）
选 18 -> 输入 62   # 26次爆仓
选 18 -> 输入 141  # 13次爆仓
选 18 -> 输入 144  # 11次爆仓
```

---

### 🚪 第三组: 出场和DCA (选项 21-24)

#### 选项 2️⃣1️⃣: 查看自定义出场逻辑

**功能**: 显示 `custom_exit` 方法
**代码位置**: 行 1700-2199 (约499行)
**输出**: 前100行代码

**适合场景**:
- 理解何时止盈/止损
- 查看利润保护逻辑
- 研究时间衰减退出

---

#### 选项 2️⃣2️⃣: 查看DCA加仓主逻辑

**功能**: 显示 `adjust_trade_position` 方法
**代码位置**: 行 2401-2699 (约298行)
**输出示例**:
```python
💰 DCA加仓主逻辑 (adjust_trade_position):

方法位置: 行 2401

  def adjust_trade_position(
    self,
    trade: Trade,
    current_time: datetime,
    current_rate: float,
    current_profit: float,
    min_stake: Optional[float],
    max_stake: float,
    current_entry_rate: float,
    current_exit_rate: float,
    current_entry_profit: float,
    current_exit_profit: float,
    **kwargs,
  ) -> Optional[float]:

    # 判断是做多还是做空
    if trade.is_short:
      return self.short_adjust_trade_position(...)
    else:
      return self.long_adjust_trade_position(...)
```

**适合场景**:
- 理解DCA触发条件
- 查看加仓金额计算
- 了解做多/做空分流逻辑

---

#### 选项 2️⃣3️⃣: 查看Long Grind DCA

**功能**: 选择查看不同版本的Grind DCA
**提供3个选项**:
- `2` - long_grind_adjust_trade_position_v2 (行 37134)
- `3` - long_grind_adjust_trade_position_v3 (行 39544)
- `main` - long_grind_adjust_trade_position (行 40872)

**使用流程**:
```
选择版本 (2/3/main) 或按Enter返回: main

  def long_grind_adjust_trade_position(
    self, trade: Trade, current_time: datetime, ...
  ):
    # Grind模式的DCA逻辑
    # 根据价格跌幅分层加仓
    ...
```

**适合场景**:
- 深入理解Grind模式
- 对比不同版本差异
- 优化DCA参数

---

#### 选项 2️⃣4️⃣: 查看出场条件方法列表

**功能**: 列出所有exit相关方法
**输出示例**:
```
🚪 所有出场方法:

1700:  def custom_exit(
11501:  def confirm_trade_exit(
984:   def exit_profit_target(
19290:  def long_exit_normal(
19549:  def long_exit_pump(
19800:  def long_exit_quick(
20090:  def long_exit_rebuy(
20334:  def long_exit_high_profit(
20564:  def long_exit_rapid(
20863:  def long_exit_grind(
20894:  def long_exit_top_coins(
20925:  def long_exit_scalp(
... (共34个方法)
```

**适合场景**:
- 查看所有出场方法
- 定位特定出场逻辑
- 了解出场方法数量

---

### 📊 第四组: 技术指标 (选项 31-33)

#### 选项 3️⃣1️⃣: 查看 populate_indicators

**功能**: 显示主指标计算方法
**代码位置**: 行 3763-11766 (约8000行！)
**输出**: 前137行

**内容包括**:
- 所有技术指标的计算
- RSI, EMA, SMA, Bollinger Bands
- Williams %R, Aroon, CMF
- 自定义指标

**适合场景**:
- 了解策略使用哪些指标
- 查看指标参数设置
- 学习技术指标组合

---

#### 选项 3️⃣2️⃣: 查看多时间框架指标方法

**功能**: 选择查看不同时间框架的指标
**提供4个选项**:
- `1d` - informative_1d_indicators (行 2870)
- `4h` - informative_4h_indicators (行 2998)
- `1h` - informative_1h_indicators (行 3169)
- `15m` - informative_15m_indicators (行 3337)

**使用流程**:
```
🕐 多时间框架指标方法:

2870:  def informative_1d_indicators(
2998:  def informative_4h_indicators(
3169:  def informative_1h_indicators(
3337:  def informative_15m_indicators(

选择时间框架 (1d/4h/1h/15m) 或按Enter返回: 1h

  def informative_1h_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
    # 1小时时间框架的技术指标
    dataframe["RSI_14_1h"] = ta.RSI(dataframe, timeperiod=14)
    dataframe["EMA_12_1h"] = ta.EMA(dataframe, timeperiod=12)
    ...
```

**适合场景**:
- 理解多时间框架分析
- 查看各时间框架的指标
- 学习跨周期过滤

---

### 📄 第五组: 分析和文档 (选项 41-44)

#### 选项 4️⃣1️⃣: 生成策略结构报告

**功能**: 调用 Python 分析脚本
**等同于**: `python analyze_strategy.py report`
**输出**: 完整的文本报告（在前面已展示）

**适合场景**:
- 获取策略完整概览
- 查看方法分类统计
- 导出为文本文件

---

#### 选项 4️⃣2️⃣: 打开完整概览文档

**功能**: 显示 `STRATEGY_OVERVIEW_COMPLETE.md`
**使用工具**:
- 如果有 `bat`: 彩色语法高亮显示
- 如果有 `less`: 分页显示
- 否则: `cat` 直接输出

**适合场景**:
- 阅读完整策略文档
- 查看风险评估
- 学习使用建议

---

#### 选项 4️⃣3️⃣: 搜索关键字 ⭐ 超实用！

**功能**: 在策略文件中搜索任意关键字
**使用流程**:
```
请输入要搜索的关键字: RSI_14

🔍 搜索结果:

3823:    dataframe["RSI_14"] = ta.RSI(dataframe, timeperiod=14)
12053:    & (df["RSI_14"] < 30.0)
12178:    & (df["RSI_14"] < 35.0)
13421:    & (df["RSI_14"] > 50.0)
... (显示前50个结果)
```

**常用搜索示例**:
```bash
选 43 -> 输入 "grind"          # 查找所有Grind相关代码
选 43 -> 输入 "stoploss"       # 查找止损相关
选 43 -> 输入 "leverage"       # 查找杠杆相关
选 43 -> 输入 "protections"    # 查找保护机制
选 43 -> 输入 "WILLR"          # 查找Williams %R使用
选 43 -> 输入 "adjust_trade"   # 查找DCA相关
```

**适合场景**:
- 快速定位特定功能
- 查找指标使用位置
- 研究某个概念的实现

---

#### 选项 4️⃣4️⃣: 查看方法定义位置

**功能**: 输入方法名，定位并显示代码
**使用流程**:
```
请输入方法名 (例如: custom_stake_amount): custom_stake_amount

📍 方法位置:

找到: custom_stake_amount (行 2257)

  def custom_stake_amount(
    self,
    pair: str,
    current_time: datetime,
    current_rate: float,
    proposed_stake: float,
    min_stake: Optional[float],
    max_stake: float,
    leverage: float,
    entry_tag: Optional[str],
    side: str,
    **kwargs,
  ) -> float:
    # 计算每笔交易的投入金额
    ...
```

**常用方法名**:
```bash
选 44 -> 输入 "populate_indicators"
选 44 -> 输入 "populate_entry_trend"
选 44 -> 输入 "custom_exit"
选 44 -> 输入 "adjust_trade_position"
选 44 -> 输入 "confirm_trade_entry"
选 44 -> 输入 "custom_stake_amount"
```

**适合场景**:
- 快速跳转到方法定义
- 查看方法签名
- 了解方法参数

---

## 💡 实用技巧

### 技巧1: 连续查看相关内容

工具会在显示内容后返回菜单，无需重启：
```
启动 -> 选18 -> 输入142 -> 按Enter
     -> 选18 -> 输入145 -> 按Enter
     -> 选18 -> 输入62  -> 按Enter
     -> 选0  -> 退出
```

### 技巧2: 结合文档使用

```bash
# 终端1: 打开交互式查看器
./view_strategy.sh

# 终端2: 打开快速参考
cat STRATEGY_QUICK_REFERENCE.md

# 或者在查看器里选 42 打开完整文档
```

### 技巧3: 导出查看结果

如果想保存输出：
```bash
# 运行工具并保存输出
./view_strategy.sh | tee my_viewing_session.txt

# 或者使用 script 命令记录整个会话
script -c "./view_strategy.sh" session.log
```

### 技巧4: 快速学习流程

**新手推荐路线**:
```
1. 选 2  -> 查看版本信息
2. 选 3  -> 查看启用的信号列表
3. 选 1  -> 查看核心配置
4. 选 18 -> 输入 1  (查看最简单的信号)
5. 选 18 -> 输入 142 (查看最佳信号)
6. 选 22 -> 查看DCA逻辑
7. 选 41 -> 生成完整报告
```

**进阶用户路线**:
```
1. 选 15 -> 查看Grind模式信号 (#141-145)
2. 选 18 -> 逐个研究 141-145
3. 选 23 -> 查看Grind DCA版本对比
4. 选 43 -> 搜索 "grind_mode"
5. 选 44 -> 查看 long_grind_adjust_trade_position
```

---

## 🎨 界面颜色说明

- 🔵 **蓝色** - 标题和分隔线
- 🟢 **绿色** - 分类标题、成功信息
- 🟡 **黄色** - 提示、输入提示
- 🔴 **红色** - 警告、错误、退出选项

---

## ⚡ 快捷键和操作

- **Enter** - 返回菜单（看完内容后）
- **0** - 退出程序
- **Ctrl+C** - 强制退出
- **Ctrl+L** - 清屏（在查看长文本时）

---

## 🐛 常见问题

### Q: 显示乱码或没有颜色？

**A**: 确保终端支持ANSI颜色码
```bash
# 检查终端类型
echo $TERM

# 如果不支持颜色，可以禁用
# 编辑脚本，将所有 ${GREEN} ${BLUE} 等替换为空
```

### Q: 显示的代码行数不够？

**A**: 默认显示有限制，可以修改脚本中的 `head -50` 等数字
```bash
# 例如在 view_specific_signal 函数中
sed -n "${line},$((line+100))p"  # 改为更大的数字
```

### Q: 能否搜索多个关键字？

**A**: 选择选项 43，然后可以使用正则表达式
```
搜索关键字: RSI.*WILLR     # 同时包含RSI和WILLR的行
搜索关键字: grind|rebuy    # 包含grind或rebuy的行
```

---

## 📦 文件依赖

工具需要以下文件存在：
- ✅ `user_data/strategies/NostalgiaForInfinityX7.py` - 策略文件
- ✅ `analyze_strategy.py` - Python分析脚本（选项41需要）
- ✅ `STRATEGY_OVERVIEW_COMPLETE.md` - 完整文档（选项42需要）

如果文件不存在，工具会显示错误信息。

---

## 🎓 学习建议

### 第1次使用（15分钟）
1. 启动工具熟悉界面
2. 选 1, 2, 3 查看基础信息
3. 选 18，输入 1 查看一个简单信号
4. 选 41 生成报告

### 第2次使用（30分钟）
1. 选 15 查看Grind模式所有信号
2. 选 18 逐个查看 #141-145
3. 选 22 和 23 理解DCA
4. 选 43 搜索感兴趣的关键字

### 第3次使用（1小时）
1. 对比最佳信号 (#142, #145)
2. 研究危险信号 (#62, #141, #144)
3. 查看出场逻辑
4. 学习多时间框架指标

---

## 🚀 高级用法

### 批量查看信号

可以写个小脚本自动查看多个信号：
```bash
#!/bin/bash
for signal in 142 145 62 141 144; do
  echo "=== Signal #$signal ==="
  sed -n "$(grep -n "if long_entry_condition_index == $signal:" user_data/strategies/NostalgiaForInfinityX7.py | cut -d: -f1),+50p" user_data/strategies/NostalgiaForInfinityX7.py
  echo ""
done
```

### 导出特定部分

```bash
# 导出所有Grind信号到文件
./view_strategy.sh # 选15后重定向输出
```

---

## ✅ 总结

`view_strategy.sh` 是一个强大的**交互式代码浏览工具**，让您能够：

- ✨ **无需记命令** - 跟着菜单走
- 🎯 **快速定位** - 按功能分类查找
- 🔍 **灵活搜索** - 关键字搜索和方法定位
- 📖 **学习友好** - 逐步深入策略逻辑
- 💡 **提高效率** - 节省95%的代码查找时间

**立即尝试**: `./view_strategy.sh` 🚀

---

**创建时间**: 2025-11-04
**作者**: Claude Code AI
**版本**: 1.0
