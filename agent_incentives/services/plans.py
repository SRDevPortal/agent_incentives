import frappe
from frappe.utils import getdate


def get_applicable_plan(agent_user, company, period_start, period_end):
    period_start = getdate(period_start)
    period_end = getdate(period_end)
    plans = frappe.get_all(
        "Agent Incentive Plan",
        filters={
            "agent_user": agent_user,
            "company": company,
            "plan_status": "Active",
            "docstatus": ["<", 2],
        },
        fields=[
            "name",
            "agent_user",
            "agent_name",
            "threshold_mode",
            "salary_amount",
            "threshold_multiplier",
            "threshold_amount",
            "incentive_percentage",
            "effective_from",
            "effective_to",
        ],
    )
    matches = []
    for plan in plans:
        start = getdate(plan.effective_from) if plan.effective_from else getdate("1000-01-01")
        end = getdate(plan.effective_to) if plan.effective_to else getdate("9999-12-31")
        if start <= period_start and end >= period_end:
            matches.append(plan)
    if not matches:
        frappe.throw(f"No active incentive plan found for agent {agent_user} in company {company} covering the run period.")
    if len(matches) > 1:
        frappe.throw(f"Multiple active incentive plans found for agent {agent_user} in company {company} covering the run period.")
    return matches[0]
