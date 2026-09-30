"""Verify existing accounting payments; never create or submit a voucher."""
import frappe
from agent_incentives.access import finance, settings
from agent_incentives.domain import money, VERSION
from agent_incentives.participation import lock_participation

def paid_by_user(company, user=None):
    scope=" and s.agent_user=%s" if user else ""
    args=[company]+([user] if user else [])
    rows=frappe.db.sql("""select s.agent_user, sum(s.amount) amount
        from `tabAgent Incentive Settlement` s join `tabJournal Entry` j on j.name=s.journal_entry
        where s.company=%s and s.state='Verified' and j.docstatus=1""" + scope +
        " group by s.agent_user",args,as_dict=True)
    return {r.agent_user:money(r.amount) for r in rows}

def verify(doc):
    finance();lock_participation()
    if not doc.is_new():
        frappe.throw("Settlement evidence is immutable; voucher cancellation reverses its paid contribution")
    ledger=frappe.get_doc("Agent Incentive Ledger",doc.ledger)
    run=frappe.get_doc("Agent Incentive Run",ledger.incentive_run)
    if run.status!="Locked" or ledger.calculation_version!=VERSION:
        frappe.throw("Select a finalized Payment Entry-based incentive ledger")
    s=settings()
    if not s.settlement_account:
        frappe.throw("Configure a dedicated incentive payable account in Settings")
    account=frappe.get_doc("Account",s.settlement_account)
    if account.company!=ledger.company or account.account_type!="Payable" or account.disabled or account.is_group:
        frappe.throw("Invalid incentive payable account")
    if (account.account_currency or "INR")!="INR":
        frappe.throw("Settlement account must be INR")
    if frappe.db.exists("DocType","WFH Commission Settings"):
        other=frappe.get_single("WFH Commission Settings")
        if other.get("payable_account")==s.settlement_account:
            frappe.throw("Use a separate incentive payable account to keep WFH settlements independent")
    journal=frappe.get_doc("Journal Entry",doc.journal_entry)
    journal.check_permission("read")
    if journal.docstatus!=1 or journal.company!=ledger.company:
        frappe.throw("Select a submitted company payment Journal Entry")
    if journal.get("wfh_payout_batch") or journal.get("wfh_commission_posting_batch"):
        frappe.throw("WFH vouchers cannot settle agent incentives")
    bank_credit=money(0)
    for row in journal.accounts:
        if money(row.credit):
            kind=frappe.db.get_value("Account",row.account,"account_type")
            if kind not in ("Bank","Cash"):
                frappe.throw("Settlement must be a bank/cash payment journal, not an accrual or adjustment")
            bank_credit+=money(row.credit)
        if money(row.debit) and row.account!=s.settlement_account:
            frappe.throw("Use a dedicated incentive settlement journal")
    line=next((r for r in journal.accounts if r.name==doc.journal_row),None)
    if not line or line.account!=s.settlement_account or line.party_type!="User" or line.party!=ledger.agent_user:
        frappe.throw("Select the incentive payable debit row for this User")
    value=money(doc.amount)
    if value<=0 or money(line.debit)<=0 or money(line.credit) or bank_credit<=0:
        frappe.throw("A positive verified payment allocation is required")
    used=frappe.db.sql("""select coalesce(sum(s.amount),0) from `tabAgent Incentive Settlement` s
        join `tabJournal Entry` j on j.name=s.journal_entry
        where s.journal_entry=%s and s.journal_row=%s and s.state='Verified' and j.docstatus=1""",
        (journal.name,line.name))[0][0]
    ledger_paid=frappe.db.sql("""select coalesce(sum(s.amount),0) from `tabAgent Incentive Settlement` s
        join `tabJournal Entry` j on j.name=s.journal_entry
        where s.ledger=%s and s.state='Verified' and j.docstatus=1""",ledger.name)[0][0]
    from agent_incentives.adjustments import for_ledger
    if money(used)+value>money(line.debit) or money(ledger_paid)+value>money(ledger.final_payout_amount)+for_ledger(ledger.name):
        frappe.throw("Allocation exceeds unallocated payment or outstanding incentive")
    doc.company=ledger.company;doc.agent_user=ledger.agent_user
    doc.amount=value;doc.posting_date=journal.posting_date;doc.state="Verified"
