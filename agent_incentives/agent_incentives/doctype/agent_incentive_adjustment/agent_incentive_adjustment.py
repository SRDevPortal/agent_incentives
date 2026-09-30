import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime
from agent_incentives.access import finance
from agent_incentives.domain import money,VERSION
from agent_incentives.participation import lock_participation

class AgentIncentiveAdjustment(Document):
    def validate(self):
        finance();lock_participation()
        if not self.is_new():
            frappe.throw("Approved corrections are immutable; add a reversing correction with its reason")
        ledger=frappe.get_doc("Agent Incentive Ledger",self.ledger)
        if ledger.calculation_version!=VERSION or frappe.db.get_value("Agent Incentive Run",ledger.incentive_run,"status")!="Locked":
            frappe.throw("Corrections require a finalized Payment Entry-based ledger")
        if not money(self.amount) or not (self.reason or "").strip():
            frappe.throw("A nonzero correction and review reason are required")
        self.company=ledger.company;self.agent_user=ledger.agent_user
        self.amount=money(self.amount)
        self.approved_by=frappe.session.user;self.approved_on=now_datetime()
    def on_trash(self):
        frappe.throw("Preserve approved correction history")
