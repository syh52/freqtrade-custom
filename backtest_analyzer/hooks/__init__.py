"""
Decision logging hooks for strategy execution.

This module provides hooks to capture decision-making data during backtesting,
enabling 100% accurate decision replay without manual condition reconstruction.
"""

from .decision_logger import DecisionLogger
from .strategy_decorator import (
    log_entry_decisions,
    log_exit_decisions,
    log_entry_decisions_v2,
    log_exit_decisions_v2,
)
from .tracked_dataframe import TrackedDataFrame, TrackedSeries, ConditionTracker
from .exit_path_tracker import ExitPathTracker, track_exit_path

__all__ = [
    'DecisionLogger',
    'log_entry_decisions',
    'log_exit_decisions',
    'log_entry_decisions_v2',
    'log_exit_decisions_v2',
    'TrackedDataFrame',
    'TrackedSeries',
    'ConditionTracker',
    'ExitPathTracker',
    'track_exit_path',
]
