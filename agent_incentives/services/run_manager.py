import json
import uuid
import frappe
from frappe.utils import getdate, today, now_datetime
from agent_incentives.access import finance, settings, stamp
from agent_incentives.participation import lock_participation
from agent_incentives.domain import VERSION, month_period
from agent_incentives.services.calculation import build_snapshot

CALCULATION_VERSION = VERSION

def find_run(company, start, end):
    names = frappe.get_all("Agent Incentive Run", filters=dict(company=company,
        period_start=["<=",end], period_end=[">=",start], status=["!=", "Cancelled"]), pluck="name")
    if len(names)>1:
        frappe.throw("Overlapping historical runs require review")
    if not names:
        return None
    run = frappe.get_doc("Agent Incentive Run", names[0])
    if getdate(run.period_start) != start or getdate(run.period_end) != end:
        frappe.throw("An existing overlapping period requires review")
    return run

@frappe.whitelist(methods=["POST"])
def refresh(month=None):
    finance(); lock_participation()
    s=settings()
    if not s.enabled or not s.company:
        frappe.throw("Enable and configure Agent Incentive Settings first")
    start,end=month_period(month or today())
    if start>getdate(today()):
        frappe.throw("Future months cannot be calculated")
    run=find_run(s.company,start,end)
    if run and run.status=="Locked":
        frappe.throw("This month is finalized; preserve its evidence and use reviewed corrections")
    if run and run.calculation_version != VERSION:
        frappe.throw("Legacy run requires explicit reconciliation; it cannot be rebuilt automatically")
    snapshot, fingerprint=build_snapshot(s.company,start,end)
    if not run:
        run=stamp(frappe.get_doc(dict(doctype="Agent Incentive Run",company=s.company,
            period_start=start,period_end=end,status="Draft",calculation_version=VERSION)))
        run.insert()
    existing=frappe.get_all("Agent Incentive Ledger",filters=dict(incentive_run=run.name),pluck="name")
    for name in existing:
        doc=frappe.get_doc("Agent Incentive Ledger",name)
        if doc.approval_status != "Draft" or doc.payment_status != "Unpaid" or doc.adjustment_amount:
            frappe.throw("Reviewed/adjusted ledger cannot be rebuilt")
    # Delete and replace within the same transaction; no explicit commit.
    frappe.local.incentive_rebuild=True
    try:
        for name in existing:
            frappe.delete_doc("Agent Incentive Ledger",name)
    finally:
        frappe.local.incentive_rebuild=False
    total=0
    for row in snapshot["rows"]:
        values=dict(row)
        values.update(doctype="Agent Incentive Ledger",incentive_run=run.name,company=s.company,
            period_start=start,period_end=end,calculation_version=VERSION,rounding_rule=snapshot["rounding"],
            gross_collected=row["payment_entry_received"],net_collected=row["payment_entry_received"],credit_note_amount=0,
            adjustment_amount=0,approval_status="Draft",payment_status="Unpaid")
        stamp(frappe.get_doc(values)).insert()
        total+=row["payout_amount"]
    run.update(dict(status="Calculated",run_on=now_datetime(),triggered_by=frappe.session.user,
        calculated_through=snapshot["cutoff"],snapshot_hash=fingerprint,rounding_rule=snapshot["rounding"],
        exceptions_json=frappe.as_json(snapshot["errors"]),exception_count=len(snapshot["errors"]),
        row_count=len(snapshot["rows"]),total_payout_amount=total))
    stamp(run).save()
    return dict(run=run.name,exceptions=snapshot["errors"],rows=len(snapshot["rows"]))

@frappe.whitelist(methods=["POST"])
def calculate_run(run_name, force_rebuild=False):
    finance()
    run=frappe.get_doc("Agent Incentive Run",run_name)
    if run.company != settings().company:
        frappe.throw("Run company differs from configured company")
    return refresh(str(run.period_start))

@frappe.whitelist(methods=["POST"])
def preview_finalize(run_name):
    finance();lock_participation()
    run=frappe.get_doc("Agent Incentive Run",run_name)
    if run.status != "Calculated" or run.calculation_version != VERSION:
        frappe.throw("Refresh a supported draft period first")
    if getdate(run.period_end)>=getdate(today()):
        frappe.throw("Finalize only after the month has ended")
    snapshot,fingerprint=build_snapshot(run.company,run.period_start,run.period_end)
    if not snapshot["rows"]:
        frappe.throw("No enrolled users to finalize")
    if snapshot["errors"] or run.exception_count:
        frappe.throw("Resolve all exceptions and refresh before finalization")
    if fingerprint != run.snapshot_hash:
        frappe.throw("Sources or settings changed; refresh calculations before finalization")
    token=uuid.uuid4().hex
    frappe.cache().set_value("incentive-finalize:"+token,
        dict(user=frappe.session.user,run=run.name,fingerprint=fingerprint),expires_in_sec=900)
    return dict(token=token,run=run.name,users=len(snapshot["rows"]),
                total=sum(r["payout_amount"] for r in snapshot["rows"]))

@frappe.whitelist(methods=["POST"])
def finalize(token):
    finance();lock_participation()
    data=frappe.cache().get_value("incentive-finalize:"+str(token))
    if not data or data["user"]!=frappe.session.user:
        frappe.throw("Preview expired; preview again")
    run=frappe.get_doc("Agent Incentive Run",data["run"])
    if run.status=="Locked" and run.snapshot_hash==data["fingerprint"]:
        return dict(run=run.name,status=run.status)
    if run.status!="Calculated" or getdate(run.period_end)>=getdate(today()):
        frappe.throw("Only a completed calculated month can be finalized")
    snapshot,fingerprint=build_snapshot(run.company,run.period_start,run.period_end)
    if snapshot["errors"] or fingerprint!=data["fingerprint"] or run.snapshot_hash!=fingerprint:
        frappe.throw("Preview is stale; refresh and preview again")
    for name in frappe.get_all("Agent Incentive Ledger",filters=dict(incentive_run=run.name),pluck="name"):
        ledger=frappe.get_doc("Agent Incentive Ledger",name)
        ledger.approval_status="Approved"
        stamp(ledger).save()
    run.status="Locked"
    stamp(run).save()
    return dict(run=run.name,status=run.status)
