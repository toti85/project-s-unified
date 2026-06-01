import json, sys

data = json.load(open('self_state.json', encoding='utf-8'))
gs = data['current_state']['gaps_summary']
mp = data['current_state']['model_policy']
gaps = data['identity']['known_gaps']
gap23 = next((g for g in gaps if g['gap_id'] == 'GAP_023'), None)

print('JSON valid: OK')
print('Gaps: total=%d resolved=%d active=%d accepted=%d' % (gs['total'], gs['resolved'], gs['active'], gs['accepted']))
print('GAP_023 status: %s' % (gap23['status'] if gap23 else 'NOT FOUND'))
print('synthesis_default: %s' % mp.get('synthesis_default', 'MISSING'))

assert gs['total'] == 25 and gs['resolved'] == 24 and gs['active'] == 0 and gs['accepted'] == 1, 'GAP COUNTS MISMATCH'
assert gap23 is not None and gap23['status'] == 'RESOLVED', 'GAP_023 not found or wrong status'
assert mp.get('synthesis_default') == 'qwen/qwen3.6-35b-a3b', 'synthesis_default wrong — expected qwen3.6'
print('All assertions PASS')
