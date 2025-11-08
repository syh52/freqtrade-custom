"""
回测分析管线 - Streamlit主应用

启动命令：
streamlit run backtest_analyzer/app/main.py
"""

import streamlit as st
import sys
import re
import json
import zipfile
from pathlib import Path
from typing import Dict, Optional

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backtest_analyzer.core.loader import BacktestResultLoader
from backtest_analyzer.core.cleaner import DataCleaner

# 页面配置
st.set_page_config(
    page_title="回测结果深度分析",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 标题
st.title("📊 Freqtrade 回测结果深度分析管线")
st.markdown("---")

# 辅助函数：快速提取回测元数据
def extract_backtest_metadata(file_path: Path) -> Optional[Dict]:
    """
    快速提取回测文件的关键元数据（不完整加载文件）

    Args:
        file_path: 回测文件路径（.json 或 .zip）

    Returns:
        元数据字典，如果提取失败则返回 None
    """
    try:
        # 读取文件内容（读取开头和末尾）
        if file_path.suffix == '.zip':
            # ZIP 文件：提取内部的 JSON
            with zipfile.ZipFile(file_path, 'r') as zf:
                # 查找 backtest-result-*.json 文件
                json_files = [f for f in zf.namelist() if f.endswith('.json') and 'backtest-result' in f and not f.endswith('.meta.json')]
                if not json_files:
                    return None
                # 读取整个 JSON 文件（因为需要找到 TOTAL 统计）
                with zf.open(json_files[0]) as f:
                    content = f.read().decode('utf-8', errors='ignore')
        else:
            # JSON 文件：直接读取整个文件
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        # 使用正则表达式快速提取关键信息
        metadata = {}

        # 提取策略名称（从文件开头）
        strategy_match = re.search(r'"strategy":\s*{\s*"([^"]+)":', content[:10000])
        if strategy_match:
            metadata['strategy'] = strategy_match.group(1)

        # 查找 "TOTAL" 统计行（在文件中搜索）
        total_pos = content.find('"key":"TOTAL"')

        if total_pos >= 0:
            # 提取 TOTAL 行附近的内容（1000个字符应该足够了）
            total_snippet = content[total_pos:total_pos+1000]

            # 分别提取每个字段
            trades_match = re.search(r'"trades":(\d+)', total_snippet)
            wins_match = re.search(r'"wins":(\d+)', total_snippet)
            profit_match = re.search(r'"profit_total":([-\d.]+)', total_snippet)

            if trades_match:
                metadata['total_trades'] = int(trades_match.group(1))
            if wins_match:
                metadata['wins'] = int(wins_match.group(1))
            if profit_match:
                metadata['profit_total'] = float(profit_match.group(1))

            # 计算胜率
            if 'total_trades' in metadata and 'wins' in metadata:
                metadata['win_rate'] = (metadata['wins'] / metadata['total_trades'] * 100) if metadata['total_trades'] > 0 else 0
        else:
            # 如果找不到 TOTAL，尝试从文件末尾提取（兼容旧格式）
            trades_match = re.search(r'"total_trades":\s*(\d+)', content[-100000:])
            if trades_match:
                metadata['total_trades'] = int(trades_match.group(1))

            profit_match = re.search(r'"profit_total":\s*([-\d.]+)', content[-100000:])
            if profit_match:
                metadata['profit_total'] = float(profit_match.group(1))

        return metadata if metadata else None

    except Exception as e:
        # 静默失败，返回 None
        return None

# 辅助函数：格式化文件显示名称
def format_display_name(file_path: str) -> str:
    """
    将文件路径格式化为友好的显示名称

    Args:
        file_path: 相对文件路径

    Returns:
        格式化的显示字符串
    """
    path_obj = project_root / file_path

    # 提取文件名中的时间信息
    filename = path_obj.name
    # backtest-result-2025-11-07_16-36-54.json -> 11-07 16:36
    time_match = re.search(r'(\d{4})-(\d{2})-(\d{2})_(\d{2})-(\d{2})-(\d{2})', filename)
    if time_match:
        year, month, day, hour, minute, second = time_match.groups()
        time_str = f"{month}-{day} {hour}:{minute}"
    else:
        time_str = "未知时间"

    # 尝试提取元数据
    metadata = extract_backtest_metadata(path_obj)

    if metadata:
        strategy = metadata.get('strategy', '未知策略')
        trades = metadata.get('total_trades', 0)
        profit = metadata.get('profit_total', 0) * 100  # 转换为百分比
        win_rate = metadata.get('win_rate', 0)

        # 收益状态图标
        profit_icon = "✅" if profit > 0 else "❌"
        profit_str = f"+{profit:.1f}%" if profit > 0 else f"{profit:.1f}%"

        # 格式：11-07 16:36 | NostalgiaForInfinityX7 | 313笔 | +126.9% ✅ | 78%胜
        return f"{time_str} | {strategy} | {trades}笔 | {profit_str} {profit_icon} | {win_rate:.0f}%胜"
    else:
        # 如果无法提取元数据，只显示时间
        return f"{time_str} | {filename}"

# 辅助函数：扫描回测结果目录
def scan_backtest_files():
    """扫描并返回所有回测结果文件"""
    backtest_dir = project_root / "user_data" / "backtest_results"
    if not backtest_dir.exists():
        return []

    # 获取所有 .json 和 .zip 文件
    files = []
    for ext in ['*.json', '*.zip']:
        files.extend(backtest_dir.glob(ext))

    # 过滤掉不需要的文件
    filtered_files = []
    for f in files:
        # 排除隐藏文件（以.开头）
        if f.name.startswith('.'):
            continue
        # 排除元数据文件（.meta.json）
        if f.name.endswith('.meta.json'):
            continue
        # 保留有效的回测结果文件
        filtered_files.append(f)

    # 按修改时间排序（最新的在前）
    filtered_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

    # 返回相对路径
    return [str(f.relative_to(project_root)) for f in filtered_files]

# 侧边栏 - 数据加载
with st.sidebar:
    st.header("⚙️ 配置")

    # 文件选择
    st.subheader("📁 选择回测文件")

    # 方式1: 下拉列表选择（推荐）
    available_files = scan_backtest_files()
    if available_files:
        default_index = 0
        # 尝试找到最新的文件作为默认值
        if 'backtest_file' in st.session_state and st.session_state['backtest_file'] in available_files:
            default_index = available_files.index(st.session_state['backtest_file'])

        selected_file = st.selectbox(
            "从列表中选择",
            options=available_files,
            index=default_index,
            format_func=format_display_name,  # 使用自定义格式化函数
            help="显示：时间 | 策略 | 交易数 | 收益 | 胜率"
        )
        backtest_file = selected_file
    else:
        st.warning("⚠️ 未找到回测文件，请手动输入路径")
        backtest_file = "user_data/backtest_results/"

    # 方式2: 手动输入（高级选项）
    with st.expander("✏️ 手动输入路径"):
        custom_path = st.text_input(
            "自定义路径",
            value=backtest_file,
            help="支持.json或.zip格式"
        )
        if custom_path != backtest_file:
            backtest_file = custom_path

    load_button = st.button("🔄 加载数据", type="primary", use_container_width=True)

# 加载数据
@st.cache_data
def load_backtest_data(file_path: str):
    """加载回测数据（带缓存）"""
    try:
        loader = BacktestResultLoader(file_path)
        data = loader.load_all()

        # 数据增强
        trades_df = data['trades']
        enhanced_trades = DataCleaner.clean_and_enhance_trades(trades_df)

        return {
            'trades': enhanced_trades,
            'stats': data['stats'],
            'config': data['config'],
            'summary': loader.get_summary(),
            'strategy_name': loader.get_strategy_name()
        }
    except Exception as e:
        st.error(f"加载失败: {e}")
        return None

# 自动加载上次使用的数据（如果存在且当前未加载）
if 'backtest_file' in st.session_state and 'data' not in st.session_state:
    with st.spinner("正在恢复上次加载的数据..."):
        try:
            data = load_backtest_data(st.session_state['backtest_file'])
            if data:
                st.session_state['data'] = data
        except:
            pass  # 如果恢复失败，用户可以手动重新加载

# 主界面
if load_button or 'data' in st.session_state:
    if load_button:
        with st.spinner("正在加载和分析数据..."):
            data = load_backtest_data(backtest_file)
            if data:
                st.session_state['data'] = data
                st.session_state['backtest_file'] = backtest_file
                st.success("✅ 数据加载成功！")

    if 'data' in st.session_state:
        data = st.session_state['data']
        trades_df = data['trades']
        summary = data['summary']

        # 总览摘要
        st.header("📈 回测摘要")

        # 显示时间范围
        timerange = summary.get('timerange', ('Unknown', 'Unknown'))
        if timerange and timerange[0] != 'Unknown':
            start_date = timerange[0].split()[0]  # 提取日期部分（去掉时间）
            end_date = timerange[1].split()[0]
            st.info(f"📅 **回测时间范围**: {start_date} 至 {end_date}")
        else:
            st.warning("⚠️ 无法确定回测时间范围")

        st.markdown("")  # 添加一点间距

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            st.metric("策略", summary['strategy'])
            st.metric("总交易数", summary['total_trades'])

        with col2:
            st.metric("胜率", f"{summary['win_rate']:.2f}%")
            st.metric("盈利交易", summary['winning_trades'])

        with col3:
            st.metric(
                "总收益",
                f"{summary['total_profit_pct']:.2f}%",
                delta=f"{summary['total_profit_abs']:.2f} USDT"
            )

        with col4:
            st.metric("最大回撤", f"{summary['max_drawdown_pct']:.2f}%")
            st.metric("Sharpe比率", f"{summary['sharpe_ratio']:.2f}")

        with col5:
            st.metric("Sortino比率", f"{summary['sortino_ratio']:.2f}")
            st.metric("期望收益", f"{summary['expectancy']:.2f}")

        st.markdown("---")

        # 快速洞察
        st.header("🔍 快速洞察")

        col1, col2 = st.columns(2)

        with col1:
            # 爆仓统计
            liq_count = trades_df['is_liquidation'].sum() if 'is_liquidation' in trades_df.columns else 0
            if liq_count > 0:
                st.error(f"⚠️ 发现 {liq_count} 笔爆仓交易（{liq_count/len(trades_df)*100:.1f}%）")
                st.info("👉 前往 **爆仓分析** 页面查看详情")
            else:
                st.success("✅ 未发现爆仓交易")

            # Grind模式统计
            grind_count = trades_df['is_grind_entry'].sum() if 'is_grind_entry' in trades_df.columns else 0
            if grind_count > 0:
                grind_profit = trades_df[trades_df['is_grind_entry']]['profit_ratio'].mean() * 100
                st.info(f"💰 Grind模式：{grind_count}笔交易，平均收益 {grind_profit:.2f}%")

        with col2:
            # 需要复盘的交易
            needs_review = trades_df['needs_review'].sum() if 'needs_review' in trades_df.columns else 0
            st.warning(f"📋 {needs_review} 笔交易需要深度复盘（{needs_review/len(trades_df)*100:.1f}%）")
            st.info("👉 前往 **交易复盘** 页面进行分析")

            # Top币种
            if 'pair' in trades_df.columns:
                top_pair = trades_df.groupby('pair')['profit_abs'].sum().idxmax()
                top_profit = trades_df.groupby('pair')['profit_abs'].sum().max()
                st.success(f"🏆 最佳币种：{top_pair} (+{top_profit:.2f} USDT)")

        st.markdown("---")

        # 导航提示
        st.header("🧭 导航")
        st.info("""
        **功能页面**：
        - **1️⃣ 总览仪表盘**：全局绩效指标和图表
        - **2️⃣ 爆仓分析**：深度分析爆仓原因和预防措施
        - **3️⃣ 币种分析**：识别毒瘤币和优质币种
        - **4️⃣ 入场模式分析**：17种模式效果对比
        - **5️⃣ 交易复盘** ⭐：针对差交易的深度复盘（最核心功能）

        👈 请在左侧边栏选择页面
        """)

else:
    # 欢迎页面
    st.info("""
    ## 🎯 功能特性

    本分析管线专为NostalgiaForInfinityX7策略设计，提供：

    ### 🔴 爆仓问题诊断
    - 识别高风险币种和入场模式
    - 分析DCA加仓行为对爆仓的影响
    - 生成预防建议和黑名单

    ### 💎 核心创新：交易深度复盘
    - 结合K线和技术指标分析每笔交易
    - 自动找出最优入场/出场点
    - 分析被拒绝的信号（机会成本）
    - 生成反思报告和改进建议

    ### 📊 多维度分析
    - 17种入场模式效果对比
    - 币种表现排行和筛选
    - 时间维度分析（日/周/月/小时）
    - DCA/Grind模式专项分析

    ---

    **开始使用**：请在左侧输入回测文件路径并点击"加载数据"
    """)

    # 示例文件路径
    with st.expander("📁 示例文件路径"):
        st.code("""
# JSON格式（推荐）
user_data/backtest_results/backtest-result-2025-11-07_16-36-54.json

# ZIP格式（包含策略代码和市场数据）
user_data/backtest_results/backtest-result-2025-11-07_16-36-54.zip
        """)

# 页脚
st.markdown("---")
st.caption("Freqtrade回测分析管线 | 由Claude Code设计 | v1.0")
