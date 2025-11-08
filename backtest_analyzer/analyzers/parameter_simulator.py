"""
参数模拟器 (Parameter Simulator)

允许用户调整策略参数，模拟对入场/出场决策的影响:
- 调整指标阈值（如RSI < 36 → RSI < 40）
- 重新评估条件
- 对比原始 vs 模拟结果
- 计算参数敏感度
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from copy import deepcopy


class ParameterSimulator:
    """参数模拟器"""

    def __init__(self, entry_analyzer, exit_analyzer=None):
        """
        初始化参数模拟器

        Args:
            entry_analyzer: 入场决策分析器实例
            exit_analyzer: 出场决策分析器实例（可选）
        """
        self.entry_analyzer = entry_analyzer
        self.exit_analyzer = exit_analyzer

        # 原始分析结果（缓存）
        self.original_entry_analysis = None
        self.original_exit_analysis = None

    def simulate_entry_parameter_change(self, tag: int, parameter_changes: Dict[str, float]) -> Dict[str, Any]:
        """
        模拟入场参数变化的影响

        Args:
            tag: 要模拟的条件编号
            parameter_changes: 参数变化字典，如 {'RSI_14_threshold': 40.0, 'SMA_16_offset': 0.95}

        Returns:
            模拟结果
        """
        # 获取原始分析结果
        if self.original_entry_analysis is None:
            self.original_entry_analysis = self.entry_analyzer.analyze()

        # 获取原始条件逻辑
        original_logic = self.entry_analyzer._get_condition_logic(tag)
        if not original_logic:
            return {
                'success': False,
                'error': f'无法找到Tag {tag}的条件定义'
            }

        # 应用参数变化
        modified_logic = self._apply_parameter_changes(original_logic, parameter_changes)

        # 重新评估条件
        simulated_analysis = self._re_evaluate_condition(tag, modified_logic)

        # 对比结果
        comparison = self._compare_entry_results(tag, self.original_entry_analysis, simulated_analysis)

        # 计算参数敏感度
        sensitivity = self._calculate_sensitivity(tag, parameter_changes, comparison)

        return {
            'success': True,
            'tag': tag,
            'parameter_changes': parameter_changes,
            'original': {
                'triggered': tag in self.entry_analyzer.triggered_tags,
                'all_satisfied': self._get_original_condition_status(tag)
            },
            'simulated': {
                'would_trigger': simulated_analysis['all_satisfied'],
                'analysis': simulated_analysis
            },
            'comparison': comparison,
            'sensitivity': sensitivity
        }

    def _apply_parameter_changes(self, original_logic: Dict, changes: Dict[str, float]) -> Dict:
        """应用参数变化到条件逻辑"""
        modified_logic = deepcopy(original_logic)

        # 遍历所有层的条件，应用变化
        for layer_name in ['protection', 'mtf_filter', 'entry_logic']:
            if layer_name not in modified_logic:
                continue

            conditions = modified_logic[layer_name]

            for i, cond in enumerate(conditions):
                # 检查是否需要修改这个条件的参数
                for param_name, new_value in changes.items():
                    # 解析参数名称，如 'RSI_14_threshold' -> 指标='RSI_14', 参数='threshold'
                    if '_threshold' in param_name:
                        indicator_name = param_name.replace('_threshold', '')
                        if cond.get('indicator') == indicator_name:
                            cond['threshold'] = new_value

                    elif '_offset' in param_name:
                        indicator_base = param_name.replace('_offset', '')
                        if cond.get('comparison') and indicator_base in cond.get('comparison', ''):
                            cond['offset'] = new_value

                    # 可以添加更多参数类型的处理...

        return modified_logic

    def _re_evaluate_condition(self, tag: int, modified_logic: Dict) -> Dict:
        """使用修改后的逻辑重新评估条件"""
        # 评估三层结构（使用修改后的逻辑）
        protection_result = self.entry_analyzer._evaluate_protection_layer(tag, modified_logic)
        mtf_result = self.entry_analyzer._evaluate_mtf_layer(tag, modified_logic)
        entry_logic_result = self.entry_analyzer._evaluate_entry_logic_layer(tag, modified_logic)

        return {
            'tag': tag,
            'condition_name': modified_logic.get('name', f'Condition #{tag}'),
            'layer1_protection': protection_result,
            'layer2_mtf_filter': mtf_result,
            'layer3_entry_logic': entry_logic_result,
            'all_satisfied': (
                protection_result['all_satisfied'] and
                mtf_result['all_satisfied'] and
                entry_logic_result['all_satisfied']
            )
        }

    def _get_original_condition_status(self, tag: int) -> bool:
        """获取原始条件的满足状态"""
        if not self.original_entry_analysis:
            return False

        for triggered in self.original_entry_analysis['triggered_analysis']:
            if triggered['tag'] == tag:
                return triggered['all_satisfied']

        return False

    def _compare_entry_results(self, tag: int, original: Dict, simulated: Dict) -> Dict:
        """对比原始和模拟的入场结果"""
        original_triggered = tag in original['triggered_tags']
        simulated_would_trigger = simulated['all_satisfied']

        # 判断变化类型
        if original_triggered and simulated_would_trigger:
            change_type = 'no_change'
            description = '✅ 仍会触发入场'
        elif original_triggered and not simulated_would_trigger:
            change_type = 'would_not_trigger'
            description = '❌ 将不再触发入场'
        elif not original_triggered and simulated_would_trigger:
            change_type = 'would_trigger'
            description = '✅ 将会触发入场（原本不触发）'
        else:
            change_type = 'no_change'
            description = '❌ 仍不触发入场'

        # 找出哪些条件的状态发生了变化
        changed_conditions = self._find_changed_conditions(tag, original, simulated)

        return {
            'change_type': change_type,
            'description': description,
            'original_triggered': original_triggered,
            'simulated_triggered': simulated_would_trigger,
            'changed_conditions': changed_conditions
        }

    def _find_changed_conditions(self, tag: int, original_analysis: Dict, simulated_analysis: Dict) -> List[Dict]:
        """找出状态发生变化的条件"""
        changed = []

        # 获取原始条件状态
        original_cond = None
        for triggered in original_analysis.get('triggered_analysis', []):
            if triggered['tag'] == tag:
                original_cond = triggered
                break

        if not original_cond:
            # 如果原始分析中没有这个tag，说明原本不触发
            # 比较所有条件
            return []

        simulated_cond = simulated_analysis

        # 比较三层的每个条件
        for layer_num, layer_name in enumerate(['layer1_protection', 'layer2_mtf_filter', 'layer3_entry_logic'], 1):
            orig_layer = original_cond.get(layer_name, {})
            sim_layer = simulated_cond.get(layer_name, {})

            orig_conditions = orig_layer.get('conditions', [])
            sim_conditions = sim_layer.get('conditions', [])

            for i, (orig_c, sim_c) in enumerate(zip(orig_conditions, sim_conditions)):
                orig_sat = orig_c.get('satisfied', False)
                sim_sat = sim_c.get('satisfied', False)

                if orig_sat != sim_sat:
                    changed.append({
                        'layer': layer_num,
                        'layer_name': layer_name,
                        'condition_index': i,
                        'description': orig_c.get('description', ''),
                        'original_satisfied': orig_sat,
                        'simulated_satisfied': sim_sat,
                        'details': sim_c.get('details', '')
                    })

        return changed

    def _calculate_sensitivity(self, tag: int, parameter_changes: Dict, comparison: Dict) -> Dict:
        """
        计算参数敏感度

        Args:
            tag: 条件编号
            parameter_changes: 参数变化
            comparison: 对比结果

        Returns:
            敏感度分析结果
        """
        # 判断敏感度等级
        if comparison['change_type'] in ['would_trigger', 'would_not_trigger']:
            # 参数变化导致结果反转 -> 高敏感
            sensitivity_level = 'high'
            sensitivity_score = 1.0
        elif comparison['changed_conditions']:
            # 参数变化导致部分条件状态改变 -> 中敏感
            sensitivity_level = 'medium'
            sensitivity_score = 0.5
        else:
            # 参数变化不影响结果 -> 低敏感
            sensitivity_level = 'low'
            sensitivity_score = 0.0

        # 计算参数变化幅度
        change_magnitude = {}
        for param_name, new_value in parameter_changes.items():
            # 这里需要知道原始值才能计算变化幅度
            # 简化处理：只记录新值
            change_magnitude[param_name] = {
                'new_value': new_value,
                'change_pct': None  # 需要原始值才能计算
            }

        return {
            'level': sensitivity_level,
            'score': sensitivity_score,
            'description': self._get_sensitivity_description(sensitivity_level),
            'change_magnitude': change_magnitude,
            'affected_conditions': len(comparison.get('changed_conditions', []))
        }

    def _get_sensitivity_description(self, level: str) -> str:
        """获取敏感度描述"""
        descriptions = {
            'high': '🔴 高敏感 - 参数变化会改变入场决策',
            'medium': '🟡 中敏感 - 参数变化会影响部分条件',
            'low': '🟢 低敏感 - 参数变化不影响入场决策'
        }
        return descriptions.get(level, '未知')

    def batch_simulate(self, tag: int, parameter_ranges: Dict[str, List[float]]) -> Dict[str, Any]:
        """
        批量模拟多个参数值

        Args:
            tag: 条件编号
            parameter_ranges: 参数范围，如 {'RSI_14_threshold': [30, 35, 40, 45, 50]}

        Returns:
            批量模拟结果
        """
        results = []

        # 生成所有参数组合
        param_names = list(parameter_ranges.keys())
        if not param_names:
            return {'success': False, 'error': '没有提供参数范围'}

        # 简化版：只测试每个参数单独变化的情况
        for param_name in param_names:
            for value in parameter_ranges[param_name]:
                # 单个参数变化
                changes = {param_name: value}
                result = self.simulate_entry_parameter_change(tag, changes)
                results.append({
                    'parameter': param_name,
                    'value': value,
                    'result': result
                })

        # 汇总分析
        summary = self._summarize_batch_results(results)

        return {
            'success': True,
            'tag': tag,
            'total_simulations': len(results),
            'results': results,
            'summary': summary
        }

    def _summarize_batch_results(self, results: List[Dict]) -> Dict:
        """汇总批量模拟结果"""
        summary = {
            'trigger_change_count': 0,  # 导致触发状态改变的次数
            'high_sensitivity_params': [],  # 高敏感参数
            'optimal_values': {}  # 最优参数值
        }

        for r in results:
            param = r['parameter']
            value = r['value']
            result = r['result']

            if result.get('success'):
                comparison = result.get('comparison', {})
                if comparison.get('change_type') in ['would_trigger', 'would_not_trigger']:
                    summary['trigger_change_count'] += 1

                sensitivity = result.get('sensitivity', {})
                if sensitivity.get('level') == 'high':
                    if param not in summary['high_sensitivity_params']:
                        summary['high_sensitivity_params'].append(param)

        return summary


def format_simulation_report(simulation_result: Dict) -> str:
    """
    格式化参数模拟报告

    Args:
        simulation_result: 模拟结果字典

    Returns:
        格式化的报告文本
    """
    if not simulation_result.get('success'):
        return f"❌ 模拟失败: {simulation_result.get('error', '未知错误')}"

    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("🧪 参数模拟实验报告")
    report_lines.append("=" * 60)
    report_lines.append(f"条件: Tag {simulation_result['tag']}")
    report_lines.append(f"参数变化: {simulation_result['parameter_changes']}")
    report_lines.append("-" * 60)

    # 原始结果
    original = simulation_result['original']
    report_lines.append(f"\n📍 原始状态:")
    report_lines.append(f"   入场触发: {'✅ 是' if original['triggered'] else '❌ 否'}")

    # 模拟结果
    simulated = simulation_result['simulated']
    report_lines.append(f"\n🔮 模拟结果:")
    report_lines.append(f"   是否会触发: {'✅ 是' if simulated['would_trigger'] else '❌ 否'}")

    # 对比
    comparison = simulation_result['comparison']
    report_lines.append(f"\n📊 结果对比:")
    report_lines.append(f"   {comparison['description']}")

    if comparison['changed_conditions']:
        report_lines.append(f"\n   受影响的条件:")
        for cond in comparison['changed_conditions']:
            icon = '✅→❌' if cond['original_satisfied'] and not cond['simulated_satisfied'] else '❌→✅'
            report_lines.append(f"      {icon} 第{cond['layer']}层: {cond['description']}")

    # 敏感度分析
    sensitivity = simulation_result['sensitivity']
    report_lines.append(f"\n📈 参数敏感度:")
    report_lines.append(f"   {sensitivity['description']}")
    report_lines.append(f"   敏感度评分: {sensitivity['score']:.2f}")
    if sensitivity['affected_conditions'] > 0:
        report_lines.append(f"   影响条件数: {sensitivity['affected_conditions']}")

    report_lines.append(f"\n{'=' * 60}")

    return '\n'.join(report_lines)


def format_batch_simulation_report(batch_result: Dict) -> str:
    """
    格式化批量模拟报告

    Args:
        batch_result: 批量模拟结果字典

    Returns:
        格式化的报告文本
    """
    if not batch_result.get('success'):
        return f"❌ 批量模拟失败: {batch_result.get('error', '未知错误')}"

    report_lines = []

    report_lines.append("=" * 60)
    report_lines.append("🔬 批量参数模拟实验报告")
    report_lines.append("=" * 60)
    report_lines.append(f"条件: Tag {batch_result['tag']}")
    report_lines.append(f"模拟次数: {batch_result['total_simulations']}")
    report_lines.append("-" * 60)

    # 汇总
    summary = batch_result['summary']
    report_lines.append(f"\n📊 汇总分析:")
    report_lines.append(f"   导致触发状态改变的参数组合: {summary['trigger_change_count']}")
    report_lines.append(f"   高敏感参数: {', '.join(summary['high_sensitivity_params']) if summary['high_sensitivity_params'] else '无'}")

    # 详细结果（只显示前10个）
    report_lines.append(f"\n📋 详细结果 (前10个):")
    for i, r in enumerate(batch_result['results'][:10], 1):
        param = r['parameter']
        value = r['value']
        result = r['result']

        if result.get('success'):
            comparison = result.get('comparison', {})
            report_lines.append(f"\n   {i}. {param} = {value}")
            report_lines.append(f"      {comparison['description']}")

    report_lines.append(f"\n{'=' * 60}")

    return '\n'.join(report_lines)
