"""
自动数据加载工具

在所有页面中使用，实现数据的自动恢复和加载
"""

import streamlit as st
from pathlib import Path
from typing import Optional


def get_latest_backtest_file() -> Optional[str]:
    """
    获取最新的回测文件路径

    Returns:
        最新回测文件的相对路径，如果没有找到则返回None
    """
    project_root = Path(__file__).parent.parent.parent.parent
    backtest_dir = project_root / "user_data" / "backtest_results"

    if not backtest_dir.exists():
        return None

    # 查找所有回测文件
    files = []
    for ext in ['*.json', '*.zip']:
        files.extend(backtest_dir.glob(ext))

    # 过滤掉不需要的文件
    filtered_files = []
    for f in files:
        if f.name.startswith('.') or f.name.endswith('.meta.json'):
            continue
        filtered_files.append(f)

    if not filtered_files:
        return None

    # 按修改时间排序，返回最新的
    filtered_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return str(filtered_files[0].relative_to(project_root))


def ensure_data_loaded(force_reload: bool = False) -> bool:
    """
    确保数据已加载到session_state中

    优先级：
    1. 如果已经有数据且不强制重新加载，直接返回
    2. 尝试从session_state中保存的文件路径恢复
    3. 自动加载最新的回测文件

    Args:
        force_reload: 是否强制重新加载数据

    Returns:
        是否成功加载数据
    """
    from backtest_analyzer.core.loader import BacktestResultLoader
    from backtest_analyzer.core.cleaner import DataCleaner

    # 如果已有数据且不强制重新加载，直接返回
    if 'data' in st.session_state and not force_reload:
        return True

    # 确定要加载的文件路径
    file_to_load = None

    if 'backtest_file' in st.session_state:
        # 优先使用保存的文件路径
        file_to_load = st.session_state['backtest_file']
    else:
        # 自动查找最新的回测文件
        file_to_load = get_latest_backtest_file()
        if file_to_load:
            st.session_state['backtest_file'] = file_to_load

    # 如果没有找到文件，返回False
    if not file_to_load:
        return False

    # 加载数据
    try:
        # 使用Streamlit缓存加载数据
        @st.cache_data
        def load_data(path):
            loader = BacktestResultLoader(path)
            data = loader.load_all()
            return {
                'trades': DataCleaner.clean_and_enhance_trades(data['trades']),
                'stats': data['stats'],
                'config': data['config'],
                'summary': loader.get_summary(),
                'strategy_name': loader.get_strategy_name()
            }

        with st.spinner("正在自动加载回测数据..."):
            data = load_data(file_to_load)
            if data:
                st.session_state['data'] = data
                return True
    except Exception as e:
        st.error(f"自动加载失败: {e}")
        return False

    return False
