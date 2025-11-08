"""
Decision Logger - Records trading decisions during backtesting.

This module captures all technical indicators at the moment of entry/exit signals,
enabling accurate decision replay without manual condition reconstruction.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import pandas as pd

logger = logging.getLogger(__name__)


class DecisionLogger:
    """
    Records trading decisions to JSONL files during backtesting.

    This logger captures:
    - Entry decisions: All technical indicators at entry signal time
    - Exit decisions: All indicators and exit reasons at exit time

    The logs enable 100% accurate decision replay in the analyzer UI.
    """

    def __init__(self, log_dir: Optional[Path] = None):
        """
        Initialize the decision logger.

        Args:
            log_dir: Directory for decision logs. Defaults to user_data/decision_logs/
        """
        if log_dir is None:
            # Default to user_data/decision_logs/
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            log_dir = project_root / 'user_data' / 'decision_logs'

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Create log file with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.log_file = self.log_dir / f'decisions_{timestamp}.jsonl'

        # Open file handle (append mode)
        self._file_handle = None
        self._open_file()

        logger.info(f"Decision logger initialized: {self.log_file}")

    def _open_file(self):
        """Open the log file for writing."""
        if self._file_handle is None:
            self._file_handle = open(self.log_file, 'a', encoding='utf-8')

    def _close_file(self):
        """Close the log file."""
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def log_entry(
        self,
        timestamp: pd.Timestamp,
        pair: str,
        tag: Optional[str],
        indicators: Dict[str, Any],
        side: str = 'long'
    ):
        """
        Log an entry decision.

        Args:
            timestamp: Entry signal timestamp
            pair: Trading pair (e.g., 'BTC/USDT:USDT')
            tag: Entry tag (e.g., '142', 'quick_142')
            indicators: All technical indicators at this moment
            side: 'long' or 'short'
        """
        record = {
            'timestamp': str(timestamp),
            'pair': pair,
            'type': 'entry',
            'side': side,
            'tag': tag,
            'data': {
                'indicators': self._clean_indicators(indicators),
                'decision': 'enter'
            }
        }

        self._write_record(record)

    def log_exit(
        self,
        timestamp: pd.Timestamp,
        pair: str,
        tag: Optional[str],
        indicators: Dict[str, Any],
        exit_reason: str,
        current_profit: float,
        side: str = 'long'
    ):
        """
        Log an exit decision.

        Args:
            timestamp: Exit signal timestamp
            pair: Trading pair
            tag: Entry tag (for matching with entry)
            indicators: All technical indicators at this moment
            exit_reason: Reason for exit (e.g., 'profit_target', 'stoploss')
            current_profit: Profit percentage at exit
            side: 'long' or 'short'
        """
        record = {
            'timestamp': str(timestamp),
            'pair': pair,
            'type': 'exit',
            'side': side,
            'tag': tag,
            'data': {
                'indicators': self._clean_indicators(indicators),
                'exit_reason': exit_reason,
                'current_profit': current_profit,
                'decision': 'exit'
            }
        }

        self._write_record(record)

    def log_entry_v2(
        self,
        timestamp: pd.Timestamp,
        pair: str,
        tag: Optional[str],
        indicators: Dict[str, Any],
        conditions: List[Dict[str, Any]],
        side: str = 'long'
    ):
        """
        Log an entry decision with condition evaluations (v2 format).

        Args:
            timestamp: Entry signal timestamp
            pair: Trading pair (e.g., 'BTC/USDT:USDT')
            tag: Entry tag (e.g., '142', 'quick_142')
            indicators: All technical indicators at this moment
            conditions: List of condition evaluations with results
            side: 'long' or 'short'
        """
        record = {
            'timestamp': str(timestamp),
            'pair': pair,
            'type': 'entry',
            'side': side,
            'tag': tag,
            'data': {
                'indicators': self._clean_indicators(indicators),
                'decision': 'enter',
                'conditions': conditions  # 🆕 v2: Add condition evaluations
            }
        }

        self._write_record(record)

    def log_exit_v2(
        self,
        timestamp: pd.Timestamp,
        pair: str,
        tag: Optional[str],
        indicators: Dict[str, Any],
        exit_reason: str,
        current_profit: float,
        execution_path: Dict[str, Any],
        side: str = 'long'
    ):
        """
        Log an exit decision with execution path (v2 format).

        Args:
            timestamp: Exit signal timestamp
            pair: Trading pair
            tag: Entry tag (for matching with entry)
            indicators: All technical indicators at this moment
            exit_reason: Reason for exit (e.g., 'profit_target', 'stoploss')
            current_profit: Profit percentage at exit
            execution_path: Execution path with function calls and conditions
            side: 'long' or 'short'
        """
        record = {
            'timestamp': str(timestamp),
            'pair': pair,
            'type': 'exit',
            'side': side,
            'tag': tag,
            'data': {
                'indicators': self._clean_indicators(indicators),
                'exit_reason': exit_reason,
                'current_profit': current_profit,
                'decision': 'exit',
                'execution_path': execution_path  # 🆕 v2: Add execution path
            }
        }

        self._write_record(record)

    def _clean_indicators(self, indicators: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean indicators for JSON serialization.

        Handles:
        - NaN/Inf values (convert to None)
        - NumPy types (convert to Python types)
        - Non-serializable objects
        """
        cleaned = {}

        for key, value in indicators.items():
            # Skip non-numeric columns
            if key in ['date', 'open_date', 'close_date']:
                continue

            # Handle pandas/numpy types
            if pd.isna(value):
                cleaned[key] = None
            elif isinstance(value, (pd.Timestamp, datetime)):
                cleaned[key] = str(value)
            elif isinstance(value, (int, float, str, bool)):
                # Handle inf/-inf
                if isinstance(value, float):
                    if pd.isna(value) or value == float('inf') or value == float('-inf'):
                        cleaned[key] = None
                    else:
                        cleaned[key] = value
                else:
                    cleaned[key] = value
            else:
                # Try to convert to native Python type
                try:
                    cleaned[key] = float(value) if hasattr(value, '__float__') else str(value)
                except:
                    continue

        return cleaned

    def _write_record(self, record: Dict[str, Any]):
        """
        Write a record to the JSONL file.

        Each record is written as a single line of JSON.
        """
        try:
            self._file_handle.write(json.dumps(record, ensure_ascii=False) + '\n')
            self._file_handle.flush()  # Ensure immediate write
        except Exception as e:
            logger.error(f"Failed to write decision log: {e}")

    def __del__(self):
        """Cleanup: close file handle."""
        self._close_file()

    def __enter__(self):
        """Context manager support."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self._close_file()
