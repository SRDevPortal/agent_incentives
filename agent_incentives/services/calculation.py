import frappe
from frappe.utils import today, getdate
from agent_incentives.access import eligible, settings
from agent_incentives.domain import calculate, threshold, money
from agent_incentives.services.plans import get_applicable_plan
from agent_incentives.services.queries import collect, digest

def build_snapshot(company, start, end):
    s = settings()
    users = sorted({r.user for r in s.enrollments if r.active})
    cutoff = min(getdate(end), getdate(today()))
    sources, errors = collect(company, start, cutoff, users)
    results = []
    for user in users:
        try:
            eligible(user, company)
            plan = get_applicable_plan(user, company, start, end)
            evidence = sorted([r for r in sources if r["agent_user"] == user], key=lambda r:r["source_key"])
            received = sum((money(r["received_amount"]) for r in evidence), money(0))
            target = threshold(plan)
            calc = calculate(received, target, plan.incentive_percentage, s.rounding_rule or "No Rounding")
            results.append(dict(agent_user=user, agent_name=frappe.db.get_value("User",user,"full_name") or user,
                payment_entry_received=float(received), threshold_amount=float(target),
                eligible_amount=float(calc["eligible_amount"]), payout_amount=float(calc["payout_amount"]),
                incentive_percentage=float(plan.incentive_percentage), plan_reference=plan.name,
                plan_snapshot=frappe.as_json(dict(plan)), sources=evidence))
        except (frappe.ValidationError, ValueError) as exc:
            errors.append(dict(user=user, reference="Enrollment / Plan", error=str(exc)))
    snapshot = dict(company=company, start=str(start), end=str(end), cutoff=str(cutoff),
                    rounding=s.rounding_rule or "No Rounding", settings_modified=str(s.modified), rows=results, errors=errors)
    return snapshot, digest(snapshot)

def build_run_rows(company, period_start, period_end):
    snapshot, _ = build_snapshot(company, period_start, period_end)
    if snapshot["errors"]:
        frappe.throw("Resolve receipt and enrollment exceptions in the Incentive Workbench")
    return snapshot["rows"]
