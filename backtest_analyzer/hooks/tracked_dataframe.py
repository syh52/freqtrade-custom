"""
Tracked DataFrame - Automatically track condition evaluations during strategy execution.

This module provides a wrapper around pandas DataFrame that intercepts all comparison
and boolean operations, allowing automatic logging of condition evaluations without
modifying the original strategy code.

Key components:
- TrackedSeries: Wraps pandas.Series, records all comparisons
- TrackedDataFrame: Wraps pandas.DataFrame, returns TrackedSeries on column access
- ConditionTracker: Centralized condition recording and management
"""

import pandas as pd
import numpy as np
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


class ConditionTracker:
    """
    Centralized tracker for condition evaluations.

    Records all condition expressions and their evaluation results,
    organized by pair and tag for later retrieval.
    """

    def __init__(self, max_expr_length: int = 100):
        """
        Initialize condition tracker.

        Args:
            max_expr_length: Maximum length for condition expressions (truncated if longer)
        """
        self.conditions: List[Dict[str, Any]] = []
        self.current_pair: Optional[str] = None
        self.current_tag: Optional[str] = None
        self.max_expr_length = max_expr_length
        self._expr_cache: Dict[str, int] = {}  # Cache for deduplication

    def record_condition(
        self,
        expression: str,
        result: Union[pd.Series, bool],
        values: Optional[Dict[str, Any]] = None
    ):
        """
        Record a condition evaluation.

        Args:
            expression: String representation of the condition (e.g., "RSI_14 > 84.0")
            result: Boolean series or single boolean value
            values: Optional dict of variable values used in the condition
        """
        # Simplify expression
        expr = self._simplify_expression(expression)

        # Check cache for deduplication
        if expr in self._expr_cache:
            return  # Already recorded

        # Convert result to serializable format
        if isinstance(result, pd.Series):
            result_values = result.tolist()
        elif isinstance(result, (bool, np.bool_)):
            result_values = bool(result)
        else:
            result_values = None

        # Record condition
        condition_record = {
            'expression': expr,
            'result': result_values,
            'pair': self.current_pair,
            'tag': self.current_tag,
            'values': values or {}
        }

        self.conditions.append(condition_record)
        self._expr_cache[expr] = len(self.conditions) - 1

    def _simplify_expression(self, expr: str) -> str:
        """
        Simplify expression for readability.

        Removes redundant parts and truncates if too long.
        """
        # Remove common prefixes
        expr = expr.replace("df['", "").replace("']", "")
        expr = expr.replace('df["', "").replace('"]', "")

        # Truncate if too long
        if len(expr) > self.max_expr_length:
            expr = expr[:self.max_expr_length - 3] + "..."

        return expr

    def get_conditions_for_entry(
        self,
        timestamp: pd.Timestamp,
        pair: str,
        tag: str,
        dataframe: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Get all conditions evaluated for a specific entry signal.

        Args:
            timestamp: Entry timestamp
            pair: Trading pair
            tag: Entry tag
            dataframe: Original dataframe (for looking up row index)

        Returns:
            List of condition records with their results at the specific timestamp
        """
        # Find row index for timestamp
        if 'date' not in dataframe.columns:
            return []

        matching_rows = dataframe[dataframe['date'] == timestamp]
        if matching_rows.empty:
            return []

        idx = matching_rows.index[0]

        # Extract conditions for this pair/tag
        # Note: conditions are recorded with tag=None during strategy execution,
        # so we match on pair only (tag is determined after strategy completes)
        entry_conditions = []
        for cond in self.conditions:
            if cond['pair'] == pair:
                # Get result for this specific row
                if isinstance(cond['result'], list):
                    try:
                        row_result = cond['result'][idx] if idx < len(cond['result']) else None
                    except (IndexError, TypeError):
                        row_result = None
                else:
                    row_result = cond['result']

                entry_conditions.append({
                    'expression': cond['expression'],
                    'result': row_result,
                    'values': cond['values']
                })

        return entry_conditions

    def clear(self):
        """Clear all recorded conditions."""
        self.conditions.clear()
        self._expr_cache.clear()


class TrackedSeries(pd.Series):
    """
    A pandas Series that tracks all comparison and boolean operations.

    When you perform operations like `series > 5` or `series & other_series`,
    the operation is recorded in the ConditionTracker for later analysis.
    """

    def __init__(
        self,
        data=None,
        condition_tracker: Optional[ConditionTracker] = None,
        expr_name: str = "unknown",
        **kwargs
    ):
        """
        Initialize TrackedSeries.

        Args:
            data: Series data
            condition_tracker: Tracker to record conditions to
            expr_name: Name/expression representing this series
        """
        super().__init__(data, **kwargs)
        self._tracker = condition_tracker
        self._expr_name = expr_name

    @property
    def _constructor(self):
        """Return constructor for maintaining TrackedSeries type."""
        def _make_tracked_series(data, **kwargs):
            return TrackedSeries(
                data,
                condition_tracker=self._tracker,
                expr_name=self._expr_name,
                **kwargs
            )
        return _make_tracked_series

    def _record_comparison(
        self,
        operator: str,
        other: Any,
        result: pd.Series
    ) -> 'TrackedSeries':
        """
        Record a comparison operation.

        Args:
            operator: Comparison operator (e.g., ">", "<=")
            other: Value being compared to
            result: Result of the comparison

        Returns:
            TrackedSeries wrapping the result
        """
        if self._tracker is None:
            return TrackedSeries(result)

        # Build expression
        if isinstance(other, TrackedSeries):
            other_expr = other._expr_name
        elif isinstance(other, pd.Series):
            other_expr = "Series"
        else:
            other_expr = str(other)

        expr = f"{self._expr_name} {operator} {other_expr}"

        # Record condition
        self._tracker.record_condition(expr, result)

        # Debug log
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[TRACK] Recorded condition: {expr}")

        # Return tracked result
        return TrackedSeries(
            result,
            condition_tracker=self._tracker,
            expr_name=f"({expr})"
        )

    def __gt__(self, other):
        """Greater than comparison."""
        result = super().__gt__(other)
        return self._record_comparison(">", other, result)

    def __lt__(self, other):
        """Less than comparison."""
        result = super().__lt__(other)
        return self._record_comparison("<", other, result)

    def __ge__(self, other):
        """Greater than or equal comparison."""
        result = super().__ge__(other)
        return self._record_comparison(">=", other, result)

    def __le__(self, other):
        """Less than or equal comparison."""
        result = super().__le__(other)
        return self._record_comparison("<=", other, result)

    def __eq__(self, other):
        """Equality comparison."""
        result = super().__eq__(other)
        return self._record_comparison("==", other, result)

    def __ne__(self, other):
        """Inequality comparison."""
        result = super().__ne__(other)
        return self._record_comparison("!=", other, result)

    def __and__(self, other):
        """Boolean AND operation."""
        result = super().__and__(other)

        if self._tracker is None:
            return TrackedSeries(result)

        # Build expression
        if isinstance(other, TrackedSeries):
            other_expr = other._expr_name
        else:
            other_expr = "Series"

        expr = f"{self._expr_name} & {other_expr}"

        # Record condition
        self._tracker.record_condition(expr, result)

        # Debug log
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[TRACK] Recorded condition: {expr}")

        # Return tracked result
        return TrackedSeries(
            result,
            condition_tracker=self._tracker,
            expr_name=f"({expr})"
        )

    def __or__(self, other):
        """Boolean OR operation."""
        result = super().__or__(other)

        if self._tracker is None:
            return TrackedSeries(result)

        # Build expression
        if isinstance(other, TrackedSeries):
            other_expr = other._expr_name
        else:
            other_expr = "Series"

        expr = f"{self._expr_name} | {other_expr}"

        # Record condition
        self._tracker.record_condition(expr, result)

        # Debug log
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[TRACK] Recorded condition: {expr}")

        # Return tracked result
        return TrackedSeries(
            result,
            condition_tracker=self._tracker,
            expr_name=f"({expr})"
        )

    def __invert__(self):
        """Boolean NOT operation."""
        result = super().__invert__()

        if self._tracker is None:
            return TrackedSeries(result)

        expr = f"~{self._expr_name}"

        # Record condition
        self._tracker.record_condition(expr, result)

        # Debug log
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"[TRACK] Recorded condition: {expr}")

        # Return tracked result
        return TrackedSeries(
            result,
            condition_tracker=self._tracker,
            expr_name=f"({expr})"
        )


class TrackedDataFrame(pd.DataFrame):
    """
    A pandas DataFrame that returns TrackedSeries on column access.

    This allows automatic tracking of all condition evaluations
    performed on the dataframe during strategy execution.
    """

    def __init__(
        self,
        data=None,
        condition_tracker: Optional[ConditionTracker] = None,
        **kwargs
    ):
        """
        Initialize TrackedDataFrame.

        Args:
            data: DataFrame data
            condition_tracker: Tracker to record conditions to
        """
        super().__init__(data, **kwargs)
        self._tracker = condition_tracker

    def __getitem__(self, key):
        """
        Get column(s) from dataframe.

        Returns TrackedSeries for single column access,
        allowing automatic condition tracking.
        """
        result = super().__getitem__(key)

        # Only track single column access
        if isinstance(result, pd.Series) and self._tracker is not None:
            return TrackedSeries(
                result,
                condition_tracker=self._tracker,
                expr_name=str(key)
            )

        return result

    @property
    def _constructor(self):
        """Return constructor for maintaining TrackedDataFrame type."""
        def _make_tracked_df(data, **kwargs):
            return TrackedDataFrame(
                data,
                condition_tracker=self._tracker,
                **kwargs
            )
        return _make_tracked_df

    @property
    def _constructor_sliced(self):
        """Return constructor for sliced results (Series)."""
        def _make_tracked_series(data, **kwargs):
            return TrackedSeries(
                data,
                condition_tracker=self._tracker,
                expr_name="slice",
                **kwargs
            )
        return _make_tracked_series
