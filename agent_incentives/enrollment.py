import frappe
from agent_incentives.access import finance, settings
from agent_incentives.participation import assert_exclusive
from agent_incentives.domain import month_period

@frappe.whitelist(methods=["POST"])
def add_user(user, effective_from, threshold_mode, incentive_percentage, salary_amount=0,
             threshold_multiplier=1, threshold_amount=0):
    finance();assert_exclusive("incentives",[user])
    s=settings()
    if not s.company:
        frappe.throw("Configure the incentive company first")
    if not frappe.db.get_value("User",user,"enabled"):
        frappe.throw("Select an enabled User")
    if any(r.user==user and r.active for r in s.enrollments):
        frappe.throw("User is already enrolled; edit their plan instead")
    s.append("enrollments",dict(user=user,active=1))
    s.save()
    plan=frappe.get_doc(dict(doctype="Agent Incentive Plan",company=s.company,agent_user=user,
        agent_name=frappe.db.get_value("User",user,"full_name") or user,plan_status="Active",active=1,
        effective_from=effective_from,threshold_mode=threshold_mode,incentive_percentage=incentive_percentage,
        salary_amount=salary_amount,threshold_multiplier=threshold_multiplier,threshold_amount=threshold_amount))
    plan.insert()
    return dict(plan=plan.name)


@frappe.whitelist()
def defaults():
    finance()
    s=settings()
    return dict(threshold_mode=s.default_threshold_mode or "Salary Multiple",
        threshold_multiplier=s.default_threshold_multiplier or 0,
        incentive_percentage=s.default_incentive_percentage or 0)
