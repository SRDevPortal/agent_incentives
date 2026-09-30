"""Self-only financial cards; never accept a user selector."""
import frappe
from agent_incentives.access import settings
from agent_incentives.workbench import data

@frappe.whitelist()
def my_incentive_cards():
    user=frappe.session.user
    if not user or user=="Guest" or not frappe.db.get_value("User",user,"enabled"):
        return dict(visible=False)
    s=settings()
    if not any(r.user==user for r in s.enrollments):
        return dict(visible=False)
    result=data(only_user=user)
    if not result["rows"]:return dict(visible=False)
    row=result["rows"][0]
    # Only aggregates needed for this user's progress; no salary/plan or source references.
    return dict(visible=True,company=result["company"],month=result["month"],run=result["run"],
        status=row["status"],complete=row["complete"],legacy_count=row["legacy_count"],
        metrics={k:row[k] for k in ("received","threshold","threshold_remaining","incentive","earned","paid","outstanding")})
