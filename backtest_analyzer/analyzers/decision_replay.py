"""
Decision Replay - Load and query decision logs.

This module provides functionality to load decision logs recorded during backtesting
and query them for specific trades. It enables accurate decision reconstruction
without manual condition analysis.
"""

import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

logger = logging.getLogger(__name__)


class DecisionReplay:
    """
    Load and query decision logs for trade analysis.

    This class reads JSONL decision log files and provides efficient querying
    for matching trades based on pair, timestamp, and tag.
    """

    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize the decision replay system.

        Args:
            log_file: Path to decision log file. If None, attempts auto-discovery.
        """
        self.log_file = log_file
        self.decisions: List[Dict[str, Any]] = []
        self.loaded = False

        if log_file and Path(log_file).exists():
            self._load_log_file(log_file)

    def _load_log_file(self, log_file: Path):
        """
        Load decisions from a JSONL file.

        Args:
            log_file: Path to JSONL decision log file
        """
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        decision = json.loads(line)
                        # Parse timestamp
                        decision['timestamp_dt'] = pd.to_datetime(decision['timestamp'])
                        self.decisions.append(decision)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON at line {line_num}: {e}")
                        continue

            self.loaded = True
            logger.info(f"Loaded {len(self.decisions)} decisions from {log_file}")

        except Exception as e:
            logger.error(f"Failed to load decision log {log_file}: {e}")
            self.loaded = False

    @staticmethod
    def find_log_for_backtest(backtest_file: Path, log_dir: Optional[Path] = None) -> Optional[Path]:
        """
        Auto-discover decision log file matching a backtest result file.

        Matches by timestamp in filename:
        - Backtest: backtest-result-2025-01-08_14-30-22.json
        - Decision log: decisions_20250108_143022.jsonl

        Args:
            backtest_file: Path to backtest result JSON file
            log_dir: Directory containing decision logs. Defaults to user_data/decision_logs/

        Returns:
            Path to matching decision log, or None if not found
        """
        if log_dir is None:
            # Default to user_data/decision_logs/
            current_dir = Path(__file__).resolve().parent
            project_root = current_dir.parent.parent
            log_dir = project_root / 'user_data' / 'decision_logs'

        log_dir = Path(log_dir)
        if not log_dir.exists():
            logger.debug(f"Decision log directory not found: {log_dir}")
            return None

        # Extract timestamp from backtest filename
        # Format: backtest-result-2025-01-08_14-30-22.json
        backtest_name = backtest_file.stem
        try:
            # Extract timestamp using regex to handle both .json and .zip extensions
            # Pattern: YYYY-MM-DD_HH-MM-SS
            import re
            match = re.search(r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', backtest_name)
            if match:
                timestamp_str = match.group(1)

                # Parse to datetime
                backtest_dt = datetime.strptime(timestamp_str, '%Y-%m-%d_%H-%M-%S')

                # Generate expected decision log filename
                # Format: decisions_20250108_143022.jsonl
                decision_filename = f"decisions_{backtest_dt.strftime('%Y%m%d_%H%M%S')}.jsonl"
                decision_path = log_dir / decision_filename

                if decision_path.exists():
                    logger.info(f"Found matching decision log: {decision_path}")
                    return decision_path

                # Fallback: search for logs within ±5 minutes
                logger.debug(f"Exact match not found, searching within ±5 minutes...")
                for log_file in sorted(log_dir.glob('decisions_*.jsonl'), reverse=True):
                    try:
                        # Extract timestamp from log filename
                        # Format: decisions_20250108_143022.jsonl
                        log_name = log_file.stem.replace('decisions_', '')
                        log_dt = datetime.strptime(log_name, '%Y%m%d_%H%M%S')

                        # Check if within ±5 minutes
                        time_diff = abs((log_dt - backtest_dt).total_seconds())
                        if time_diff <= 300:  # 5 minutes
                            logger.info(f"Found nearby decision log ({time_diff}s difference): {log_file}")
                            return log_file
                    except:
                        continue

        except Exception as e:
            logger.debug(f"Failed to parse backtest timestamp: {e}")

        logger.warning(f"No matching decision log found for {backtest_file}")
        return None

    def find_entry_decision(
        self,
        pair: str,
        timestamp: pd.Timestamp,
        tag: Optional[str] = None,
        tolerance_seconds: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Find entry decision for a specific trade.

        Args:
            pair: Trading pair (e.g., 'BTC/USDT:USDT')
            timestamp: Entry timestamp
            tag: Entry tag (optional, for disambiguation)
            tolerance_seconds: Time tolerance for matching (default: 5 seconds)

        Returns:
            Decision record if found, None otherwise
        """
        if not self.loaded:
            return None

        matches = []
        tolerance = timedelta(seconds=tolerance_seconds)

        for decision in self.decisions:
            # Filter by type
            if decision['type'] != 'entry':
                continue

            # Filter by pair
            if decision['pair'] != pair:
                continue

            # Filter by timestamp (with tolerance)
            time_diff = abs(decision['timestamp_dt'] - timestamp)
            if time_diff > tolerance:
                continue

            # Filter by tag (if provided)
            if tag is not None and decision.get('tag') != tag:
                continue

            matches.append(decision)

        if len(matches) == 0:
            logger.debug(f"No entry decision found for {pair} at {timestamp}")
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            # Multiple matches: return closest by timestamp
            matches.sort(key=lambda d: abs(d['timestamp_dt'] - timestamp))
            logger.debug(f"Multiple entry decisions found for {pair} at {timestamp}, returning closest")
            return matches[0]

    def find_exit_decision(
        self,
        pair: str,
        timestamp: pd.Timestamp,
        tag: Optional[str] = None,
        tolerance_seconds: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Find exit decision for a specific trade.

        Args:
            pair: Trading pair
            timestamp: Exit timestamp
            tag: Entry tag (for matching, optional)
            tolerance_seconds: Time tolerance for matching (default: 5 seconds)

        Returns:
            Decision record if found, None otherwise
        """
        if not self.loaded:
            return None

        matches = []
        tolerance = timedelta(seconds=tolerance_seconds)

        for decision in self.decisions:
            # Filter by type
            if decision['type'] != 'exit':
                continue

            # Filter by pair
            if decision['pair'] != pair:
                continue

            # Filter by timestamp (with tolerance)
            time_diff = abs(decision['timestamp_dt'] - timestamp)
            if time_diff > tolerance:
                continue

            # Filter by tag (if provided)
            if tag is not None and decision.get('tag') != tag:
                continue

            matches.append(decision)

        if len(matches) == 0:
            logger.debug(f"No exit decision found for {pair} at {timestamp}")
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            # Multiple matches: return closest by timestamp
            matches.sort(key=lambda d: abs(d['timestamp_dt'] - timestamp))
            logger.debug(f"Multiple exit decisions found for {pair} at {timestamp}, returning closest")
            return matches[0]

    def get_all_entries(self, pair: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all entry decisions, optionally filtered by pair.

        Args:
            pair: Trading pair filter (optional)

        Returns:
            List of entry decision records
        """
        if not self.loaded:
            return []

        entries = [d for d in self.decisions if d['type'] == 'entry']

        if pair:
            entries = [d for d in entries if d['pair'] == pair]

        return entries

    def get_all_exits(self, pair: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all exit decisions, optionally filtered by pair.

        Args:
            pair: Trading pair filter (optional)

        Returns:
            List of exit decision records
        """
        if not self.loaded:
            return []

        exits = [d for d in self.decisions if d['type'] == 'exit']

        if pair:
            exits = [d for d in exits if d['pair'] == pair]

        return exits

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about loaded decisions.

        Returns:
            Dictionary with counts and metadata
        """
        if not self.loaded:
            return {
                'loaded': False,
                'total_decisions': 0,
                'entry_count': 0,
                'exit_count': 0,
                'pairs': [],
                'tags': []
            }

        entries = [d for d in self.decisions if d['type'] == 'entry']
        exits = [d for d in self.decisions if d['type'] == 'exit']
        pairs = sorted(set(d['pair'] for d in self.decisions))
        tags = sorted(set(str(d.get('tag', '')) for d in self.decisions if d.get('tag')))

        return {
            'loaded': True,
            'log_file': str(self.log_file) if self.log_file else None,
            'total_decisions': len(self.decisions),
            'entry_count': len(entries),
            'exit_count': len(exits),
            'pairs': pairs,
            'tags': tags,
            'time_range': {
                'start': str(min(d['timestamp_dt'] for d in self.decisions)) if self.decisions else None,
                'end': str(max(d['timestamp_dt'] for d in self.decisions)) if self.decisions else None,
            }
        }

    def detect_log_version(self) -> str:
        """
        Detect the version of the log format.

        Returns:
            'v1' for basic indicator logging, 'v2' for condition tracking
        """
        if not self.loaded or not self.decisions:
            return 'unknown'

        # Check if any decision has conditions or execution_path
        for decision in self.decisions:
            data = decision.get('data', {})
            if 'conditions' in data or 'execution_path' in data:
                return 'v2'

        return 'v1'

    def get_entry_conditions(
        self,
        pair: str,
        timestamp: pd.Timestamp,
        tag: Optional[str] = None
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Get condition evaluations for a specific entry (v2 format only).

        Args:
            pair: Trading pair
            timestamp: Entry timestamp
            tag: Entry tag

        Returns:
            List of condition evaluations, or None if not available
        """
        decision = self.find_entry_decision(pair, timestamp, tag)

        if not decision:
            return None

        # Extract conditions from v2 format
        data = decision.get('data', {})
        conditions = data.get('conditions')

        return conditions

    def get_exit_execution_path(
        self,
        pair: str,
        timestamp: pd.Timestamp,
        tag: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get execution path for a specific exit (v2 format only).

        Args:
            pair: Trading pair
            timestamp: Exit timestamp
            tag: Entry tag

        Returns:
            Execution path dictionary, or None if not available
        """
        decision = self.find_exit_decision(pair, timestamp, tag)

        if not decision:
            return None

        # Extract execution path from v2 format
        data = decision.get('data', {})
        execution_path = data.get('execution_path')

        return execution_path
