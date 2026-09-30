"""Rollback-only integration checks. No business vouchers are created/submitted."""
import os
import json
from unittest.mock import patch
import frappe
from frappe.utils import getdate
os.chdir("/home/srdev/frappe-bench-v15/sites")
frappe.init(site="sriaas.local",sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
checks=[]
def assert_blocked(fn,label):
    try:fn()
    except (frappe.ValidationError,frappe.PermissionError):checks.append(label)
    else:raise AssertionError("Expected rejection: "+label)
try:
    before={d:frappe.db.count(d) for d in ["Journal Entry","GL Entry","Payment Entry","Agent Incentive Plan","Agent Incentive Run","Agent Incentive Ledger","Agent Incentive Settlement","Agent Incentive Adjustment"]}
    wfh=frappe.get_single("WFH Commission Settings")
    active=next(r for r in wfh.enrollments if r.active)
    user=active.user
    settings=frappe.get_single("Agent Incentive Settings")
    settings.company=wfh.company;settings.enabled=1;settings.rounding_rule="No Rounding"
    settings.append("enrollments",dict(user=user,active=1))
    assert_blocked(settings.save,"WFH member rejected by incentive Settings")
    # Switching requires explicit deactivation first, even while disabled or app processing is off.
    wfh=frappe.get_single("WFH Commission Settings")
    for r in wfh.enrollments:
        if r.user==user:r.active=0
    wfh.save()
    settings=frappe.get_single("Agent Incentive Settings")
    settings.company=wfh.company;settings.enabled=1;settings.rounding_rule="No Rounding"
    settings.append("enrollments",dict(user=user,active=1))
    settings.save()
    checks.append("Deactivated WFH history allows exclusive switch")
    wfh=frappe.get_single("WFH Commission Settings")
    for r in wfh.enrollments:
        if r.user==user:r.active=1
    assert_blocked(wfh.save,"Incentive member rejected by WFH Settings")
    from wfh_commission.access import eligible as wfh_eligible
    assert_blocked(lambda:wfh_eligible(user),"WFH posting eligibility also rejects incentive member")

    plan=frappe.get_doc(dict(doctype="Agent Incentive Plan",agent_user=user,agent_name="Rollback Test",
        company=settings.company,plan_status="Active",active=1,effective_from="2026-08-01",
        threshold_mode="Fixed Amount",threshold_amount=50000,incentive_percentage=5))
    plan.insert()
    pe=frappe.get_all("Payment Entry",filters=dict(docstatus=1,payment_type="Receive"),pluck="name",limit=1)[0]
    inv=frappe.get_all("Sales Invoice",filters=dict(docstatus=1,is_return=0),pluck="name",limit=1)[0]
    source=dict(source_key="rollback-only",payment_entry=pe,invoice=inv,posting_date="2026-08-15",
        received_amount=200000,agent_user=user,fingerprint="rollback-only")
    from agent_incentives.services.run_manager import refresh,preview_finalize,finalize
    with patch("agent_incentives.services.calculation.collect",return_value=([source],[])):
        first=refresh("2026-08-01")
        second=refresh("2026-08-01")
        assert first["run"]==second["run"]
        assert frappe.db.count("Agent Incentive Ledger",dict(incentive_run=first["run"]))==1
        ledger=frappe.get_doc("Agent Incentive Ledger",dict(incentive_run=first["run"]))
        assert ledger.payout_amount==7500
        assert ledger.credit_note_amount==0 and ledger.payment_entry_received==200000
        checks.append("Repeated monthly refresh: one ledger, INR 7500, no credit-note deduction")
        ledger.payout_amount=9000
        assert_blocked(ledger.save,"Direct forged financial edit rejected")
        preview=preview_finalize(first["run"])
        with patch("agent_incentives.services.calculation.collect",return_value=([dict(source,received_amount=210000)],[])):
            assert_blocked(lambda:finalize(preview["token"]),"Changed receipt invalidates finalization preview")
        result=finalize(preview["token"])
        assert result["status"]=="Locked"
        assert finalize(preview["token"])==result
        checks.append("Finalization and repeated confirmation preserve one frozen snapshot")
        assert_blocked(lambda:refresh("2026-08-01"),"Locked period cannot be rebuilt")
        assert_blocked(lambda:frappe.delete_doc("Agent Incentive Ledger",ledger.name),"Locked ledger cannot be deleted")
    correction=frappe.get_doc(dict(doctype="Agent Incentive Adjustment",ledger=ledger.name,amount=-500,reason="Rollback-only correction test"))
    correction.insert()
    correction.amount=0
    assert_blocked(correction.save,"Reviewed correction immutable")
    from agent_incentives.workbench import list_users
    result=list_users("2026-08-01",status="All")
    row=next(r for r in result["rows"] if r["user"]==user)
    assert row["earned"]==7000 and row["paid"]==0 and row["outstanding"]==7000
    checks.append("Lifetime totals include immutable correction and verified paid only")
    from agent_incentives.agent_dashboard import my_incentive_cards
    frappe.set_user(user)
    cards=my_incentive_cards()
    assert cards["visible"] and cards["metrics"]["earned"]==7000
    assert "salary_amount" not in json.dumps(cards) and "sources" not in cards
    assert_blocked(lambda:list_users("2026-08-01"),"Agent cannot query finance workbench")
    checks.append("Agent self-only cards match corrected workbench totals")
    frappe.set_user("Administrator")
    assert not my_incentive_cards()["visible"]
    checks.append("Unenrolled administrator has no self-view bypass")
    assert frappe.get_hooks("page_js").get("vobiz-agent-analytics")
    from frappe.desk.desk_page import get as getpage
    page=getpage("agent-incentive-workbench")
    assert "IncentiveWorkbench" in page.script
    workspace=frappe.get_doc("Workspace","Incentives")
    assert any(r.link_to=="agent-incentive-workbench" for r in workspace.shortcuts)
    checks.append("Installed workbench Page and workspace shortcut available")
    analytics=getpage("vobiz-agent-analytics")
    assert "agent_incentives.agent_dashboard.my_incentive_cards" in analytics.script
    assert "wfh_commission.agent_dashboard.my_commission_cards" in analytics.script
    checks.append("Installed analytics serves both independent card extensions")
    frappe.db.rollback()
    after={d:frappe.db.count(d) for d in before}
    assert before==after,(before,after)
    print(json.dumps(dict(checks=checks,rolled_back=True,accounting_unchanged=True),indent=2))
finally:
    if "preview" in globals(): frappe.cache().delete_value("incentive-finalize:"+preview["token"])
    frappe.db.rollback()
    frappe.destroy()
