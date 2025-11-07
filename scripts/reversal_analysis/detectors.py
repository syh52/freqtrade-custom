"""
Reversal Detection Algorithms

This module implements three different methods for identifying price reversals:
1. Fixed Threshold: Simple percentage-based reversal detection
2. Adaptive Threshold: Volatility-adjusted threshold
3. Local Extreme: Technical analysis swing high/low detection

⚠️ FORWARD-LOOKING BIAS WARNING ⚠️
All methods use future data to identify historical reversals.
Only use for training data creation and historical analysis!
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np
from pandas import DataFrame


class BaseReversalDetector(ABC):
    """
    Abstract base class for all reversal detection algorithms.

    All detectors must implement the detect() method and return a DataFrame
    with standardized columns for reversal information.
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        """
        Initialize the detector with parameters.

        Args:
            params: Dictionary of detector-specific parameters
        """
        self.params = params or {}
        self.name = self.__class__.__name__
        # Minimum time gap between reversals (in number of periods)
        self.min_gap_periods = self.params.get('min_gap_hours', 4) * 60 // self.params.get('timeframe_minutes', 5)

    @abstractmethod
    def detect(self, dataframe: DataFrame) -> DataFrame:
        """
        Detect reversal points in the given dataframe.

        Args:
            dataframe: OHLCV data with columns: date, open, high, low, close, volume

        Returns:
            DataFrame with additional columns:
                - is_reversal: bool, True if this point is a reversal
                - reversal_type: str, 'top' or 'bottom' or None
                - reversal_magnitude: float, percentage change (absolute value)
                - forward_return: float, actual return in the forward window
                - confidence: float, optional confidence score (0-1)
        """
        pass

    def _validate_dataframe(self, df: DataFrame) -> None:
        """Validate that the dataframe has required columns."""
        required_cols = ['date', 'open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"DataFrame missing required columns: {missing_cols}")

    def _initialize_reversal_columns(self, df: DataFrame) -> DataFrame:
        """Initialize empty reversal columns in the dataframe."""
        df = df.copy()
        df['is_reversal'] = False
        df['reversal_type'] = None
        df['reversal_magnitude'] = 0.0
        df['forward_return'] = 0.0
        df['confidence'] = 0.0
        df['detector_name'] = self.name
        return df

    def _deduplicate_reversals(self, df: DataFrame) -> DataFrame:
        """
        Remove duplicate reversals that are too close together.

        For reversals within min_gap_periods, keep only the one with largest magnitude.
        """
        reversals = df[df['is_reversal'] == True].copy()

        if len(reversals) == 0:
            return df

        # Sort by date
        reversals = reversals.sort_values('date')

        # Track which reversals to keep
        keep_indices = []
        last_kept_idx = None
        last_kept_date = None

        for idx, row in reversals.iterrows():
            current_date = row['date']

            # If this is the first reversal or far enough from the last kept one
            if last_kept_date is None:
                keep_indices.append(idx)
                last_kept_idx = idx
                last_kept_date = current_date
            else:
                time_diff = current_date - last_kept_date
                periods_diff = time_diff.total_seconds() / 60 / self.params.get('timeframe_minutes', 5)

                if periods_diff >= self.min_gap_periods:
                    # Far enough, keep this one
                    keep_indices.append(idx)
                    last_kept_idx = idx
                    last_kept_date = current_date
                else:
                    # Too close, compare magnitudes
                    if row['reversal_magnitude'] > df.loc[last_kept_idx, 'reversal_magnitude']:
                        # This one is better, replace
                        keep_indices.remove(last_kept_idx)
                        keep_indices.append(idx)
                        last_kept_idx = idx
                        last_kept_date = current_date

        # Reset all reversals
        df.loc[df['is_reversal'] == True, 'is_reversal'] = False
        df.loc[df['is_reversal'] == False, 'reversal_type'] = None
        df.loc[df['is_reversal'] == False, 'reversal_magnitude'] = 0.0
        df.loc[df['is_reversal'] == False, 'forward_return'] = 0.0
        df.loc[df['is_reversal'] == False, 'confidence'] = 0.0

        # Mark only the kept ones
        for idx in keep_indices:
            df.loc[idx, 'is_reversal'] = True
            df.loc[idx, 'reversal_type'] = reversals.loc[idx, 'reversal_type']
            df.loc[idx, 'reversal_magnitude'] = reversals.loc[idx, 'reversal_magnitude']
            df.loc[idx, 'forward_return'] = reversals.loc[idx, 'forward_return']
            df.loc[idx, 'confidence'] = reversals.loc[idx, 'confidence']

        return df


class FixedThresholdDetector(BaseReversalDetector):
    """
    Fixed Threshold Reversal Detector

    Identifies reversals by looking forward a fixed time window and checking
    if the price moves by more than a fixed percentage threshold.

    Parameters:
        forward_window_hours (int): Hours to look ahead (default: 6)
        threshold_pct (float): Minimum percentage change to qualify as reversal (default: 3.0)
        timeframe_minutes (int): Candle timeframe in minutes (default: 5)
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.forward_window_hours = self.params.get('forward_window_hours', 6)
        self.threshold_pct = self.params.get('threshold_pct', 3.0)
        self.timeframe_minutes = self.params.get('timeframe_minutes', 5)

        # Calculate number of periods for the forward window
        self.forward_periods = int(self.forward_window_hours * 60 / self.timeframe_minutes)

    def detect(self, dataframe: DataFrame) -> DataFrame:
        """
        Detect reversals using fixed threshold method.

        Logic:
        1. Look forward N periods
        2. Calculate maximum gain and maximum loss from current price
        3. If future gain > threshold: mark as bottom reversal (buy opportunity)
        4. If future loss > threshold: mark as top reversal (sell opportunity)
        """
        self._validate_dataframe(dataframe)
        df = self._initialize_reversal_columns(dataframe)

        close = df['close'].values

        # ⚠️ FORWARD-LOOKING: Calculate future price extremes
        # For each point, find the highest and lowest price in the next N periods
        future_high = pd.Series(close).shift(-1).rolling(
            window=self.forward_periods,
            min_periods=1
        ).max().values

        future_low = pd.Series(close).shift(-1).rolling(
            window=self.forward_periods,
            min_periods=1
        ).min().values

        # Calculate potential gains and losses from current price
        future_gain_pct = ((future_high - close) / close) * 100
        future_loss_pct = ((close - future_low) / close) * 100

        # Identify bottom reversals (future will go UP significantly)
        bottom_mask = future_gain_pct >= self.threshold_pct
        df.loc[bottom_mask, 'is_reversal'] = True
        df.loc[bottom_mask, 'reversal_type'] = 'bottom'
        df.loc[bottom_mask, 'reversal_magnitude'] = future_gain_pct[bottom_mask]
        df.loc[bottom_mask, 'forward_return'] = future_gain_pct[bottom_mask]
        df.loc[bottom_mask, 'confidence'] = np.minimum(
            future_gain_pct[bottom_mask] / (self.threshold_pct * 3), 1.0
        )

        # Identify top reversals (future will go DOWN significantly)
        top_mask = future_loss_pct >= self.threshold_pct
        df.loc[top_mask, 'is_reversal'] = True
        df.loc[top_mask, 'reversal_type'] = 'top'
        df.loc[top_mask, 'reversal_magnitude'] = future_loss_pct[top_mask]
        df.loc[top_mask, 'forward_return'] = -future_loss_pct[top_mask]
        df.loc[top_mask, 'confidence'] = np.minimum(
            future_loss_pct[top_mask] / (self.threshold_pct * 3), 1.0
        )

        # Handle boundary: Mark last N periods as invalid (no future data)
        invalid_range = len(df) - self.forward_periods
        if invalid_range > 0:
            df.iloc[invalid_range:, df.columns.get_loc('is_reversal')] = False
            df.iloc[invalid_range:, df.columns.get_loc('reversal_type')] = None

        # Apply deduplication to prevent clustered reversals
        df = self._deduplicate_reversals(df)

        return df


class AdaptiveThresholdDetector(BaseReversalDetector):
    """
    Adaptive Threshold Reversal Detector

    Uses historical volatility to dynamically adjust the threshold for each point.
    More volatile periods require larger moves to qualify as reversals.

    Parameters:
        forward_window_hours (int): Hours to look ahead (default: 6)
        volatility_window_days (int): Days to calculate volatility (default: 30)
        threshold_multiplier (float): Multiplier for ATR-based threshold (default: 2.0)
        timeframe_minutes (int): Candle timeframe in minutes (default: 5)
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.forward_window_hours = self.params.get('forward_window_hours', 6)
        self.volatility_window_days = self.params.get('volatility_window_days', 30)
        self.threshold_multiplier = self.params.get('threshold_multiplier', 2.0)
        self.timeframe_minutes = self.params.get('timeframe_minutes', 5)

        self.forward_periods = int(self.forward_window_hours * 60 / self.timeframe_minutes)
        self.volatility_periods = int(self.volatility_window_days * 24 * 60 / self.timeframe_minutes)

    def _calculate_atr(self, df: DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range (ATR) for volatility measurement."""
        high = df['high']
        low = df['low']
        close = df['close'].shift(1)

        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)

        true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = true_range.rolling(window=period, min_periods=1).mean()

        return atr

    def detect(self, dataframe: DataFrame) -> DataFrame:
        """
        Detect reversals using adaptive threshold based on volatility.

        Logic:
        1. Calculate ATR (Average True Range) as volatility measure
        2. For each point, threshold = ATR * multiplier / price (as percentage)
        3. Use this adaptive threshold instead of fixed percentage
        """
        self._validate_dataframe(dataframe)
        df = self._initialize_reversal_columns(dataframe)

        # Calculate volatility (ATR)
        atr = self._calculate_atr(df, self.volatility_periods)

        # Convert ATR to percentage threshold
        adaptive_threshold_pct = (atr / df['close']) * self.threshold_multiplier * 100

        # Calculate future price movements (same as fixed threshold)
        close = df['close'].values
        future_high = pd.Series(close).shift(-1).rolling(
            window=self.forward_periods,
            min_periods=1
        ).max().values

        future_low = pd.Series(close).shift(-1).rolling(
            window=self.forward_periods,
            min_periods=1
        ).min().values

        future_gain_pct = ((future_high - close) / close) * 100
        future_loss_pct = ((close - future_low) / close) * 100

        # Use adaptive threshold for each point
        adaptive_threshold = adaptive_threshold_pct.values

        # Bottom reversals: future gain exceeds adaptive threshold
        bottom_mask = future_gain_pct >= adaptive_threshold
        df.loc[bottom_mask, 'is_reversal'] = True
        df.loc[bottom_mask, 'reversal_type'] = 'bottom'
        df.loc[bottom_mask, 'reversal_magnitude'] = future_gain_pct[bottom_mask]
        df.loc[bottom_mask, 'forward_return'] = future_gain_pct[bottom_mask]
        df.loc[bottom_mask, 'confidence'] = np.minimum(
            future_gain_pct[bottom_mask] / (adaptive_threshold[bottom_mask] * 2), 1.0
        )

        # Top reversals: future loss exceeds adaptive threshold
        top_mask = future_loss_pct >= adaptive_threshold
        df.loc[top_mask, 'is_reversal'] = True
        df.loc[top_mask, 'reversal_type'] = 'top'
        df.loc[top_mask, 'reversal_magnitude'] = future_loss_pct[top_mask]
        df.loc[top_mask, 'forward_return'] = -future_loss_pct[top_mask]
        df.loc[top_mask, 'confidence'] = np.minimum(
            future_loss_pct[top_mask] / (adaptive_threshold[top_mask] * 2), 1.0
        )

        # Store the adaptive threshold used for each point (for debugging)
        df['adaptive_threshold'] = adaptive_threshold_pct

        # Mark boundary as invalid
        invalid_range = len(df) - self.forward_periods
        if invalid_range > 0:
            df.iloc[invalid_range:, df.columns.get_loc('is_reversal')] = False
            df.iloc[invalid_range:, df.columns.get_loc('reversal_type')] = None

        # Apply deduplication to prevent clustered reversals
        df = self._deduplicate_reversals(df)

        return df


class LocalExtremeDetector(BaseReversalDetector):
    """
    Local Extreme Reversal Detector

    Identifies swing highs and swing lows (local extremes) and verifies
    that they are followed by actual reversals.

    Parameters:
        swing_window (int): Number of candles before/after for swing identification (default: 5)
        confirmation_threshold_pct (float): Minimum reversal percentage for confirmation (default: 3.0)
        forward_window_hours (int): Hours to look ahead for confirmation (default: 6)
        timeframe_minutes (int): Candle timeframe in minutes (default: 5)
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None):
        super().__init__(params)
        self.swing_window = self.params.get('swing_window', 5)
        self.confirmation_threshold_pct = self.params.get('confirmation_threshold_pct', 3.0)
        self.forward_window_hours = self.params.get('forward_window_hours', 6)
        self.timeframe_minutes = self.params.get('timeframe_minutes', 5)

        self.forward_periods = int(self.forward_window_hours * 60 / self.timeframe_minutes)

    def _identify_swing_highs(self, df: DataFrame) -> pd.Series:
        """
        Identify swing highs (local maxima).

        A swing high is a high that is higher than N candles before and after it.
        """
        high = df['high']
        window = self.swing_window

        # For each point, check if it's the highest in the window
        is_swing_high = pd.Series(False, index=df.index)

        for i in range(window, len(df) - window):
            current_high = high.iloc[i]
            before_highs = high.iloc[i-window:i]
            after_highs = high.iloc[i+1:i+window+1]

            if current_high > before_highs.max() and current_high > after_highs.max():
                is_swing_high.iloc[i] = True

        return is_swing_high

    def _identify_swing_lows(self, df: DataFrame) -> pd.Series:
        """
        Identify swing lows (local minima).

        A swing low is a low that is lower than N candles before and after it.
        """
        low = df['low']
        window = self.swing_window

        is_swing_low = pd.Series(False, index=df.index)

        for i in range(window, len(df) - window):
            current_low = low.iloc[i]
            before_lows = low.iloc[i-window:i]
            after_lows = low.iloc[i+1:i+window+1]

            if current_low < before_lows.min() and current_low < after_lows.min():
                is_swing_low.iloc[i] = True

        return is_swing_low

    def detect(self, dataframe: DataFrame) -> DataFrame:
        """
        Detect reversals using local extreme identification.

        Logic:
        1. Identify swing highs (local peaks) and swing lows (local valleys)
        2. For swing highs: check if price drops significantly afterwards (top reversal)
        3. For swing lows: check if price rises significantly afterwards (bottom reversal)
        """
        self._validate_dataframe(dataframe)
        df = self._initialize_reversal_columns(dataframe)

        # Step 1: Identify swing points
        is_swing_high = self._identify_swing_highs(df)
        is_swing_low = self._identify_swing_lows(df)

        # Step 2: Calculate future price movements for confirmation
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values

        future_high = pd.Series(close).shift(-1).rolling(
            window=self.forward_periods,
            min_periods=1
        ).max().values

        future_low = pd.Series(close).shift(-1).rolling(
            window=self.forward_periods,
            min_periods=1
        ).min().values

        # For swing highs, calculate how much price dropped
        drop_from_high_pct = ((high - future_low) / high) * 100

        # For swing lows, calculate how much price rose
        rise_from_low_pct = ((future_high - low) / low) * 100

        # Step 3: Confirm top reversals (swing high + significant drop)
        top_mask = (is_swing_high) & (drop_from_high_pct >= self.confirmation_threshold_pct)
        df.loc[top_mask, 'is_reversal'] = True
        df.loc[top_mask, 'reversal_type'] = 'top'
        df.loc[top_mask, 'reversal_magnitude'] = drop_from_high_pct[top_mask]
        df.loc[top_mask, 'forward_return'] = -drop_from_high_pct[top_mask]
        df.loc[top_mask, 'confidence'] = np.minimum(
            drop_from_high_pct[top_mask] / (self.confirmation_threshold_pct * 3), 1.0
        )

        # Step 4: Confirm bottom reversals (swing low + significant rise)
        bottom_mask = (is_swing_low) & (rise_from_low_pct >= self.confirmation_threshold_pct)
        df.loc[bottom_mask, 'is_reversal'] = True
        df.loc[bottom_mask, 'reversal_type'] = 'bottom'
        df.loc[bottom_mask, 'reversal_magnitude'] = rise_from_low_pct[bottom_mask]
        df.loc[bottom_mask, 'forward_return'] = rise_from_low_pct[bottom_mask]
        df.loc[bottom_mask, 'confidence'] = np.minimum(
            rise_from_low_pct[bottom_mask] / (self.confirmation_threshold_pct * 3), 1.0
        )

        # Store swing point information for analysis
        df['is_swing_high'] = is_swing_high
        df['is_swing_low'] = is_swing_low

        # Mark boundaries as invalid
        boundary_size = max(self.swing_window, self.forward_periods)
        if boundary_size < len(df):
            # Beginning boundary
            df.iloc[:self.swing_window, df.columns.get_loc('is_reversal')] = False
            df.iloc[:self.swing_window, df.columns.get_loc('reversal_type')] = None

            # End boundary
            df.iloc[-boundary_size:, df.columns.get_loc('is_reversal')] = False
            df.iloc[-boundary_size:, df.columns.get_loc('reversal_type')] = None

        # Apply deduplication to prevent clustered reversals
        df = self._deduplicate_reversals(df)

        return df


def create_detector(method: str, params: Optional[Dict[str, Any]] = None) -> BaseReversalDetector:
    """
    Factory function to create detector instances.

    Args:
        method: Detector type ('fixed', 'adaptive', or 'extreme')
        params: Parameters for the detector

    Returns:
        Detector instance

    Raises:
        ValueError: If method is not recognized
    """
    detectors = {
        'fixed': FixedThresholdDetector,
        'adaptive': AdaptiveThresholdDetector,
        'extreme': LocalExtremeDetector,
    }

    method = method.lower()
    if method not in detectors:
        raise ValueError(f"Unknown detector method: {method}. Choose from: {list(detectors.keys())}")

    return detectors[method](params)
