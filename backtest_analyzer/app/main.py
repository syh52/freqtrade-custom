"""
回测分析管线 - Streamlit主应用

启动命令：
streamlit run backtest_analyzer/app/main.py
"""

import streamlit as st
import sys
from pathlib import Path

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

# 侧边栏 - 数据加载
with st.sidebar:
    st.header("⚙️ 配置")

    # 文件选择
    backtest_file = st.text_input(
        "回测文件路径",
        value="user_data/backtest_results/backtest-result-2025-11-07_16-36-54.json",
        help="支持.json或.zip格式"
    )

    load_button = st.button("🔄 加载数据", type="primary")

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
