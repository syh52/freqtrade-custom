"""
Reversal Analysis Module

A comprehensive toolkit for identifying and visualizing price reversal points
in cryptocurrency trading data.

This module provides:
- Multiple reversal detection algorithms (fixed threshold, adaptive, local extremes)
- Interactive visualization with Plotly
- Statistical analysis of reversal patterns

⚠️ FORWARD-LOOKING BIAS WARNING ⚠️
This analysis uses future data to label historical reversal points.
This is ONLY suitable for:
1. Creating training datasets for machine learning
2. Historical pattern analysis
3. Strategy backtesting with proper safeguards

DO NOT use these signals for live trading directly!
"""

__version__ = "1.0.0"
__author__ = "Freqtrade Community"

from .detectors import (
    BaseReversalDetector,
    FixedThresholdDetector,
    AdaptiveThresholdDetector,
    LocalExtremeDetector,
    create_detector,
)
from .visualizer import ReversalVisualizer
from .statistics import ReversalStatistics

__all__ = [
    "BaseReversalDetector",
    "FixedThresholdDetector",
    "AdaptiveThresholdDetector",
    "LocalExtremeDetector",
    "create_detector",
    "ReversalVisualizer",
    "ReversalStatistics",
]
