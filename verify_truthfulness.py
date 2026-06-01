"""Quick live verification of SAI truthfulness fixes."""
import asyncio, sys, tempfile
from pathlib import Path
from unittest.mock import AsyncMock, patch
sys.path.insert(0, 'src')

from core.super_intelligent_ai import SuperIntelligentAI

SYNTHESIS = '## Strategic Analysis\n\n' + 'A' * 500

async def main():
    results = {}
    with tempfile.TemporaryDirectory() as tmpdir:
        sai = SuperIntelligentAI(base_dir=Path(tmpdir), use_meta_controller=False)

        # SCENARIO A: forced exception → backup path
        with patch.object(sai.evaluator, 'strategic_task_planning',
                          new_callable=AsyncMock, side_effect=RuntimeError('network down')):
            r = await sai.execute_intelligent_task('failing task', use_meta_controller=False)
        results['backup'] = {'success': r.get('success'), 'partial': r.get('partial')}
        hist_backup = sai.execution_history[-1]['success']

        mock_plan = {
            'strategy': 'direct', 'complexity': 'low', 'confidence': 0.8,
            'use_cognitive_core': False, 'use_orchestration': True,
            'optimizations': [], 'recommendations': [], 'status': 'active',
            'success_prediction': 0.8,
        }
        mock_orch = {'final_output': {'summary': 'Done', 'detailed_results': []}, 'success': True}

        # SCENARIO B: evaluator returns replan (nested key)
        mock_eval_replan = {
            'success': False, 'confidence': 0.3, 'goal_achieved': True,
            'assessment': 'stub',
            'recommendations': {'action': 'replan', 'reason': 'stub output'},
        }
        with (patch.object(sai.evaluator, 'strategic_task_planning', new_callable=AsyncMock, return_value=mock_plan),
              patch.object(sai.tool_orchestrator, 'orchestrate_task', new_callable=AsyncMock, return_value=mock_orch),
              patch.object(sai.evaluator, 'evaluate_execution_result', new_callable=AsyncMock, return_value=mock_eval_replan)):
            r = await sai.execute_intelligent_task('web research task', use_meta_controller=False)
        results['replan'] = {'success': r.get('success'), 'partial': r.get('partial')}
        hist_replan = sai.execution_history[-1]['success']

        # SCENARIO C: real synthesis output
        mock_orch_ok = {
            'final_output': {
                'summary': 'Done',
                'detailed_results': [{'status': 'success', 'result': {'output': SYNTHESIS}}],
            },
            'success': True,
        }
        mock_eval_ok = {
            'success': True, 'confidence': 0.9, 'goal_achieved': True,
            'assessment': 'done', 'recommendations': {'action': 'continue', 'reason': 'done'},
        }
        with (patch.object(sai.evaluator, 'strategic_task_planning', new_callable=AsyncMock, return_value=mock_plan),
              patch.object(sai.tool_orchestrator, 'orchestrate_task', new_callable=AsyncMock, return_value=mock_orch_ok),
              patch.object(sai.evaluator, 'evaluate_execution_result', new_callable=AsyncMock, return_value=mock_eval_ok)):
            r = await sai.execute_intelligent_task('synthesis task', use_meta_controller=False)
        results['synth'] = {'success': r.get('success'), 'partial': r.get('partial')}
        hist_synth = sai.execution_history[-1]['success']

        # SCENARIO D: improve_tool → partial
        mock_eval_improve = {
            'success': True, 'confidence': 0.7, 'goal_achieved': True,
            'assessment': 'suboptimal',
            'recommendations': {'action': 'improve_tool', 'reason': 'suboptimal'},
        }
        with (patch.object(sai.evaluator, 'strategic_task_planning', new_callable=AsyncMock, return_value=mock_plan),
              patch.object(sai.tool_orchestrator, 'orchestrate_task', new_callable=AsyncMock, return_value=mock_orch_ok),
              patch.object(sai.evaluator, 'evaluate_execution_result', new_callable=AsyncMock, return_value=mock_eval_improve)):
            r = await sai.execute_intelligent_task('improve task', use_meta_controller=False)
        results['improve'] = {'success': r.get('success'), 'partial': r.get('partial')}
        hist_improve = sai.execution_history[-1]['success']

    print()
    print('=== SAI TRUTHFULNESS FIX VERIFICATION ===')
    print()
    a_ok = results['backup']['success'] is False and hist_backup is False
    b_ok = results['replan']['success'] is False and hist_replan is False
    c_ok = results['synth']['success'] is True and hist_synth is True
    d_ok = results['improve']['success'] is True and results['improve']['partial'] is True

    print(f"A. Backup exception   success={results['backup']['success']}  partial={results['backup']['partial']}  history={hist_backup}")
    print(f"   VERDICT: {'PASS' if a_ok else 'FAIL'} (want success=False, history=False)")
    print(f"B. Evaluator replan   success={results['replan']['success']}  partial={results['replan']['partial']}  history={hist_replan}")
    print(f"   VERDICT: {'PASS' if b_ok else 'FAIL'} (want success=False, history=False)")
    print(f"C. Real synthesis     success={results['synth']['success']}  partial={results['synth']['partial']}  history={hist_synth}")
    print(f"   VERDICT: {'PASS' if c_ok else 'FAIL'} (want success=True, history=True)")
    print(f"D. improve_tool       success={results['improve']['success']}  partial={results['improve']['partial']}  history={hist_improve}")
    print(f"   VERDICT: {'PASS' if d_ok else 'FAIL'} (want success=True, partial=True)")
    print()
    total = sum([a_ok, b_ok, c_ok, d_ok])
    print(f"ALL SCENARIOS: {'PASS' if total == 4 else 'FAIL'} ({total}/4)")
    return 0 if total == 4 else 1

import sys
sys.exit(asyncio.run(main()))
