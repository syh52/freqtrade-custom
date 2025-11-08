"""
Exit Path Tracker - Track execution path during exit decisions.

This module provides functionality to track which exit functions are called
and which conditions trigger the exit, enabling detailed exit decision analysis.
"""

import logging
from typing import Dict, List, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)


class ExitPathTracker:
    """
    Track the execution path during exit decision making.

    Records:
    - Which exit functions were called
    - Which function triggered the exit
    - The order of function calls
    - Any conditions evaluated
    """

    def __init__(self):
        """Initialize the exit path tracker."""
        self.call_stack: List[Dict[str, Any]] = []
        self.triggered_function: Optional[str] = None
        self.triggered_result: Optional[Any] = None

    def track_call(
        self,
        function_name: str,
        result: Optional[Any] = None,
        **metadata
    ):
        """
        Track a function call in the exit path.

        Args:
            function_name: Name of the function being called
            result: Return value of the function (None if not exited, or exit reason)
            **metadata: Additional metadata about the call
        """
        call_record = {
            'function': function_name,
            'result': result,
            'metadata': metadata
        }

        self.call_stack.append(call_record)

        # If result is not None/False, this function triggered the exit
        if result not in (None, False):
            self.triggered_function = function_name
            self.triggered_result = result

    def get_execution_path(self) -> Dict[str, Any]:
        """
        Get the complete execution path as a structured dict.

        Returns:
            Dictionary with execution path details
        """
        if not self.call_stack:
            return {}

        # Extract mode from first function call (e.g., "long_exit_normal" -> "long_normal")
        first_func = self.call_stack[0]['function']
        mode = self._extract_mode(first_func)

        # Build call chain summary
        call_chain = []
        for call in self.call_stack:
            call_info = {
                'function': call['function'],
                'result': call['result'] is not None and call['result'] not in (False,)
            }
            # Add metadata if present
            if call['metadata']:
                call_info['metadata'] = call['metadata']

            call_chain.append(call_info)

        # Build execution path
        execution_path = {
            'mode': mode,
            'call_chain': call_chain
        }

        # Add triggered function info if available
        if self.triggered_function:
            execution_path['triggered_by'] = self.triggered_function
            execution_path['triggered_result'] = self.triggered_result

        return execution_path

    def _extract_mode(self, function_name: str) -> str:
        """
        Extract mode from function name.

        Examples:
            "long_exit_normal" -> "long_normal"
            "long_exit_pump" -> "long_pump"
            "short_exit_stoploss" -> "short_stoploss"
        """
        # Remove "exit_" part
        if 'long_exit_' in function_name:
            return function_name.replace('long_exit_', 'long_')
        elif 'short_exit_' in function_name:
            return function_name.replace('short_exit_', 'short_')
        else:
            return "unknown"

    def clear(self):
        """Clear all tracked calls."""
        self.call_stack.clear()
        self.triggered_function = None
        self.triggered_result = None


def track_exit_path(func):
    """
    Decorator to automatically track exit function calls.

    Usage:
        @track_exit_path
        def long_exit_signals(self, ...):
            ...
            return sell_reason
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        # Execute the function
        result = func(self, *args, **kwargs)

        # Track the call if tracker is available
        if hasattr(self, 'exit_path_tracker'):
            function_name = func.__name__
            self.exit_path_tracker.track_call(function_name, result)

        return result

    return wrapper
