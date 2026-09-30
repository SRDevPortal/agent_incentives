import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate
from agent_incentives.access import internal
from agent_incentives.domain import calculate, money, VERSION

class AgentIncentiveLedger(Document):
    def validate(self):
        internal(self)
        run=frappe.get_doc("Agent Incentive Run",self.incentive_run)
        if run.status=="Locked":
            frappe.throw("Finalized ledger evidence is immutable")
        if self.company!=run.company or getdate(self.period_start)!=getdate(run.period_start) or getdate(self.period_end)!=getdate(run.period_end):
            frappe.throw("Ledger company and period must match the run")
        if self.calculation_version!=VERSION:
            frappe.throw("Legacy calculation evidence cannot be rewritten")
        if frappe.db.exists("Agent Incentive Ledger",dict(incentive_run=self.incentive_run,agent_user=self.agent_user,name=["!=",self.name])):
            frappe.throw("Only one ledger per agent and run is allowed")
        if money(self.adjustment_amount):
            frappe.throw("Financial corrections require a separately reviewed record; generated evidence cannot be adjusted")
        expected=calculate(self.payment_entry_received,self.threshold_amount,self.incentive_percentage,self.rounding_rule)
        if money(self.eligible_amount)!=expected["eligible_amount"] or money(self.payout_amount)!=expected["payout_amount"]:
            frappe.throw("Incentive does not match the Payment Entry threshold formula")
        if sum((money(r.received_amount) for r in self.sources),money(0))!=money(self.payment_entry_received):
            frappe.throw("Receipt evidence does not match collected amount")
        keys=[r.source_key for r in self.sources]
        if len(keys)!=len(set(keys)):
            frappe.throw("Duplicate receipt evidence")
        if any(r.agent_user!=self.agent_user for r in self.sources):
            frappe.throw("Receipt evidence belongs to another agent")
        self.final_payout_amount=self.payout_amount
        self.generated_by=self.generated_by or frappe.session.user
        self.generated_on=self.generated_on or now_datetime()

    def on_trash(self):
        if not getattr(frappe.local,"incentive_rebuild",False):
            frappe.throw("Use Refresh Calculations to replace provisional evidence")
        run=frappe.get_doc("Agent Incentive Run",self.incentive_run)
        if run.status=="Locked" or self.approval_status!="Draft" or self.payment_status!="Unpaid" or self.adjustment_amount:
            frappe.throw("Reviewed or finalized evidence cannot be deleted")
