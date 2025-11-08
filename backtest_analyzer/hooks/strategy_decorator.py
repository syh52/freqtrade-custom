"""
Strategy Decorators - Wrap strategy methods to log decisions.

These decorators intercept strategy execution to capture decision-making data
without modifying the original strategy code.
"""

import logging
from functools import wraps
from typing import Optional, Tuple, Dict, Any, List
import pandas as pd

logger = logging.getLogger(__name__)


def log_entry_decisions(func):
    """
    Decorator for populate_entry_trend() to log entry decisions.

    This decorator:
    1. Executes the original populate_entry_trend()
    2. Identifies all rows with entry signals (enter_long=1 or enter_short=1)
    3. Logs all technical indicators for each entry signal

    Usage:
        @log_entry_decisions
        def populate_entry_trend(self, dataframe, metadata):
            return super().populate_entry_trend(dataframe, metadata)
    """
    @wraps(func)
    def wrapper(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Execute original strategy logic
        result_df = func(self, dataframe, metadata)

        # Check if logger is available
        if not hasattr(self, 'decision_logger'):
            logger.warning("Decision logger not found in strategy instance. Skipping decision logging.")
            return result_df

        # Find all long entry signals
        if 'enter_long' in result_df.columns:
            long_entries = result_df[result_df['enter_long'] == 1]
            for idx, row in long_entries.iterrows():
                try:
                    self.decision_logger.log_entry(
                        timestamp=row.get('date', idx),
                        pair=metadata['pair'],
                        tag=row.get('enter_tag_long', row.get('enter_tag')),
                        indicators=row.to_dict(),
                        side='long'
                    )
                except Exception as e:
                    logger.error(f"Failed to log long entry for {metadata['pair']} at {idx}: {e}")

        # Find all short entry signals
        if 'enter_short' in result_df.columns:
            short_entries = result_df[result_df['enter_short'] == 1]
            for idx, row in short_entries.iterrows():
                try:
                    self.decision_logger.log_entry(
                        timestamp=row.get('date', idx),
                        pair=metadata['pair'],
                        tag=row.get('enter_tag_short', row.get('enter_tag')),
                        indicators=row.to_dict(),
                        side='short'
                    )
                except Exception as e:
                    logger.error(f"Failed to log short entry for {metadata['pair']} at {idx}: {e}")

        return result_df

    return wrapper


def log_exit_decisions(func):
    """
    Decorator for custom_exit() to log exit decisions.

    This decorator:
    1. Executes the original custom_exit()
    2. If the result is not None (i.e., exit triggered), logs the decision
    3. Captures current indicators, profit, and exit reason

    IMPORTANT: Only logs when custom_exit() returns a non-None value,
    because custom_exit() is called on every tick but only triggers occasionally.

    Usage:
        @log_exit_decisions
        def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
            return super().custom_exit(pair, trade, current_time, current_rate, current_profit, **kwargs)
    """
    @wraps(func)
    def wrapper(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        **kwargs
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        # Execute original strategy logic
        result = func(self, pair, trade, current_time, current_rate, current_profit, **kwargs)

        # Only log if exit is triggered (result is not None)
        if result is not None:
            # Check if logger is available
            if not hasattr(self, 'decision_logger'):
                logger.warning("Decision logger not found in strategy instance. Skipping decision logging.")
                return result

            try:
                # Extract exit reason and tag from result
                if isinstance(result, tuple):
                    exit_reason = result[0] if result[0] else 'custom_exit'
                    exit_tag = result[1] if len(result) > 1 and result[1] else None
                elif isinstance(result, str):
                    exit_reason = result
                    exit_tag = None
                else:
                    exit_reason = 'custom_exit'
                    exit_tag = None

                # Build indicators snapshot from kwargs
                # Note: We don't have the full dataframe here, only current values
                indicators = {
                    'current_rate': current_rate,
                    'current_profit': current_profit,
                    'current_time': str(current_time),
                }

                # Add dataframe row if available in kwargs
                if 'dataframe' in kwargs and kwargs['dataframe'] is not None:
                    df = kwargs['dataframe']
                    # Get the latest row (current_time)
                    if not df.empty:
                        if 'date' in df.columns:
                            current_row = df[df['date'] == current_time]
                            if not current_row.empty:
                                indicators.update(current_row.iloc[-1].to_dict())
                        else:
                            # Fallback: use last row
                            indicators.update(df.iloc[-1].to_dict())

                # Determine side from trade
                side = 'short' if trade.is_short else 'long'

                # Get entry tag from trade
                entry_tag = trade.enter_tag if hasattr(trade, 'enter_tag') else None

                # Log the exit decision
                self.decision_logger.log_exit(
                    timestamp=current_time,
                    pair=pair,
                    tag=entry_tag,
                    indicators=indicators,
                    exit_reason=exit_reason,
                    current_profit=current_profit,
                    side=side
                )

                logger.debug(f"Logged exit decision for {pair} at {current_time}: {exit_reason}")

            except Exception as e:
                logger.error(f"Failed to log exit for {pair} at {current_time}: {e}")

        return result

    return wrapper


def log_entry_decisions_v2(func):
    """
    Decorator for populate_entry_trend() to log entry decisions with condition tracking (v2).

    This decorator:
    1. Wraps the dataframe with TrackedDataFrame to capture condition evaluations
    2. Executes the original populate_entry_trend()
    3. Extracts all condition evaluations from the tracker
    4. Logs entry signals with full condition details

    Usage:
        @log_entry_decisions_v2
        def populate_entry_trend(self, dataframe, metadata):
            return super().populate_entry_trend(dataframe, metadata)
    """
    @wraps(func)
    def wrapper(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Check if logger and tracker are available
        if not hasattr(self, 'decision_logger'):
            logger.warning("Decision logger not found. Skipping condition tracking.")
            return func(self, dataframe, metadata)

        # Import here to avoid circular dependency
        from .tracked_dataframe import TrackedDataFrame, ConditionTracker

        # Create condition tracker
        condition_tracker = ConditionTracker()
        condition_tracker.current_pair = metadata['pair']

        # Wrap dataframe with tracker
        tracked_df = TrackedDataFrame(dataframe, condition_tracker=condition_tracker)
        logger.info(f"[DEBUG-V2] Created TrackedDataFrame for {metadata['pair']}, shape: {dataframe.shape}")

        # Execute original strategy logic with tracked dataframe
        try:
            result_df = func(self, tracked_df, metadata)
            logger.info(f"[DEBUG-V2] Strategy execution complete for {metadata['pair']}, tracker has {len(condition_tracker.conditions)} conditions")
        except Exception as e:
            # If tracking fails, fall back to untracked execution
            logger.warning(f"Condition tracking failed for {metadata['pair']}: {e}. Falling back to v1.")
            return func(self, dataframe, metadata)

        # Convert back to normal DataFrame if needed
        if not isinstance(result_df, pd.DataFrame):
            logger.warning(f"Result is not a DataFrame: {type(result_df)}")
            return result_df

        # Find all long entry signals
        if 'enter_long' in result_df.columns:
            long_entries = result_df[result_df['enter_long'] == 1]
            logger.info(f"[DEBUG-V2] Found {len(long_entries)} long entry signals for {metadata['pair']}")
            for idx, row in long_entries.iterrows():
                try:
                    tag = row.get('enter_tag_long', row.get('enter_tag'))
                    condition_tracker.current_tag = tag

                    # Get conditions for this entry
                    conditions = condition_tracker.get_conditions_for_entry(
                        timestamp=row.get('date', idx),
                        pair=metadata['pair'],
                        tag=tag,
                        dataframe=dataframe
                    )
                    logger.info(f"[DEBUG-V2] Extracted {len(conditions)} conditions for {metadata['pair']} long entry at {idx}, tag={tag}")

                    # Log with v2 format
                    self.decision_logger.log_entry_v2(
                        timestamp=row.get('date', idx),
                        pair=metadata['pair'],
                        tag=tag,
                        indicators=row.to_dict(),
                        conditions=conditions,
                        side='long'
                    )
                except Exception as e:
                    logger.error(f"Failed to log long entry (v2) for {metadata['pair']} at {idx}: {e}")

        # Find all short entry signals
        if 'enter_short' in result_df.columns:
            short_entries = result_df[result_df['enter_short'] == 1]
            for idx, row in short_entries.iterrows():
                try:
                    tag = row.get('enter_tag_short', row.get('enter_tag'))
                    condition_tracker.current_tag = tag

                    # Get conditions for this entry
                    conditions = condition_tracker.get_conditions_for_entry(
                        timestamp=row.get('date', idx),
                        pair=metadata['pair'],
                        tag=tag,
                        dataframe=dataframe
                    )

                    # Log with v2 format
                    self.decision_logger.log_entry_v2(
                        timestamp=row.get('date', idx),
                        pair=metadata['pair'],
                        tag=tag,
                        indicators=row.to_dict(),
                        conditions=conditions,
                        side='short'
                    )
                except Exception as e:
                    logger.error(f"Failed to log short entry (v2) for {metadata['pair']} at {idx}: {e}")

        return result_df

    return wrapper


def log_exit_decisions_v2(func):
    """
    Decorator for custom_exit() to log exit decisions with execution path (v2).

    This decorator:
    1. Executes the original custom_exit()
    2. If exit is triggered, reads the execution path from exit_path_tracker
    3. Logs exit with full execution path details

    Usage:
        @log_exit_decisions_v2
        def custom_exit(self, pair, trade, current_time, current_rate, current_profit, **kwargs):
            return super().custom_exit(pair, trade, current_time, current_rate, current_profit, **kwargs)
    """
    @wraps(func)
    def wrapper(
        self,
        pair: str,
        trade,
        current_time,
        current_rate: float,
        current_profit: float,
        **kwargs
    ) -> Optional[Tuple[Optional[str], Optional[str]]]:
        # Clear exit path tracker before execution (if available)
        if hasattr(self, 'exit_path_tracker'):
            self.exit_path_tracker.clear()

        # Execute original strategy logic
        result = func(self, pair, trade, current_time, current_rate, current_profit, **kwargs)

        # Only log if exit is triggered (result is not None)
        if result is not None:
            # Check if logger is available
            if not hasattr(self, 'decision_logger'):
                logger.warning("Decision logger not found. Skipping exit logging.")
                return result

            try:
                # Extract exit reason and tag from result
                if isinstance(result, tuple):
                    exit_reason = result[0] if result[0] else 'custom_exit'
                    exit_tag = result[1] if len(result) > 1 and result[1] else None
                elif isinstance(result, str):
                    exit_reason = result
                    exit_tag = None
                else:
                    exit_reason = 'custom_exit'
                    exit_tag = None

                # Build indicators snapshot from kwargs
                indicators = {
                    'current_rate': current_rate,
                    'current_profit': current_profit,
                    'current_time': str(current_time),
                }

                # Add dataframe row if available in kwargs
                if 'dataframe' in kwargs and kwargs['dataframe'] is not None:
                    df = kwargs['dataframe']
                    if not df.empty:
                        if 'date' in df.columns:
                            current_row = df[df['date'] == current_time]
                            if not current_row.empty:
                                indicators.update(current_row.iloc[-1].to_dict())
                        else:
                            indicators.update(df.iloc[-1].to_dict())

                # Determine side from trade
                side = 'short' if trade.is_short else 'long'

                # Get entry tag from trade
                entry_tag = trade.enter_tag if hasattr(trade, 'enter_tag') else None

                # Get execution path from tracker (if available)
                execution_path = {}
                if hasattr(self, 'exit_path_tracker'):
                    execution_path = self.exit_path_tracker.get_execution_path()

                # Log with v2 format
                self.decision_logger.log_exit_v2(
                    timestamp=current_time,
                    pair=pair,
                    tag=entry_tag,
                    indicators=indicators,
                    exit_reason=exit_reason,
                    current_profit=current_profit,
                    execution_path=execution_path,
                    side=side
                )

                logger.debug(f"Logged exit decision (v2) for {pair} at {current_time}: {exit_reason}")

            except Exception as e:
                logger.error(f"Failed to log exit (v2) for {pair} at {current_time}: {e}")

        return result

    return wrapper
