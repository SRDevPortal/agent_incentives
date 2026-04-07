from collections import defaultdict

from agent_incentives.agent_incentives.api.formulas import calculate_incentive, calculate_threshold
from agent_incentives.agent_incentives.services.plans import get_applicable_plan
from agent_incentives.agent_incentives.services.queries import get_collection_rows, get_credit_note_rows


def build_run_rows(company, period_start, period_end):
    collections = get_collection_rows(company, period_start, period_end)
    deductions = get_credit_note_rows(company, period_start, period_end)

    gross_by_agent = defaultdict(lambda: {"agent_name": None, "gross": 0.0})
    deduction_by_agent = defaultdict(float)

    for row in collections:
        gross_by_agent[row["agent_user"]]["agent_name"] = row["agent_name"]
        gross_by_agent[row["agent_user"]]["gross"] += float(row["allocated_amount"] or 0)

    for row in deductions:
        deduction_by_agent[row["agent_user"]] += float(row["deduction_amount"] or 0)
        if row["agent_user"] not in gross_by_agent:
            gross_by_agent[row["agent_user"]]["agent_name"] = row["agent_name"]

    rows = []
    for agent_user, payload in gross_by_agent.items():
        plan = get_applicable_plan(agent_user, company, period_start, period_end)
        threshold = calculate_threshold(plan)
        gross = float(payload["gross"] or 0)
        deduction = float(deduction_by_agent.get(agent_user, 0) or 0)
        net = gross - deduction
        calc = calculate_incentive(net, threshold, plan.incentive_percentage)
        rows.append({
            "agent_user": agent_user,
            "agent_name": payload["agent_name"] or agent_user,
            "gross_collected": gross,
            "credit_note_amount": deduction,
            "net_collected": net,
            "threshold_amount": threshold,
            "eligible_amount": calc["eligible_amount"],
            "incentive_percentage": float(plan.incentive_percentage or 0),
            "payout_amount": calc["payout_amount"],
            "plan_reference": plan.name,
        })
    return rows
