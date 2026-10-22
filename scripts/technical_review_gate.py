"""Read-only check of normalized technical_review data; never grants development authority."""
import json
import sys


def evaluate(review):
    if review.get('proposal_status') == 'not-applicable':
        return {'next': 'handoff-check' if review.get('reason') else 'assess-technical-scope',
                'implementation_ready': False}
    decisions = review.get('decisions')
    if not isinstance(decisions, list) or not decisions:
        return {'next': 'assess-technical-scope', 'implementation_ready': False}
    pending = [d.get('id') for d in decisions if
               d.get('status') != 'approved' or not d.get('selected') or not d.get('approval')]
    inconsistent = set(review.get('open_decisions', [])) != set(pending)
    result = {'next': 'technical-proposal-review', 'open_decisions': pending,
              'state_inconsistent': inconsistent, 'implementation_ready': False}
    if review.get('proposal_status') == 'needs-recheck' or any(d.get('status') == 'needs-recheck' for d in decisions):
        result['next'] = 'technical-proposal-recheck'
    elif inconsistent and not pending:
        result['next'] = 'technical-state-inconsistent'
    elif not pending and review.get('proposal_status') == 'approved':
        result['next'] = 'handoff-check'
    result['validation_status'] = review.get('validation_status', 'not-run')
    result['validation_skipped'] = bool(review.get('validation_skip'))
    return result


if __name__ == '__main__':
    print(json.dumps(evaluate(json.load(sys.stdin)), ensure_ascii=False, indent=2))


def evaluate_project(root, state):
    """Full task readiness; legacy technical proposal routing never grants it."""
    from runtime import evaluate
    return evaluate(root, state)
