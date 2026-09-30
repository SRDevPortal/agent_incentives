import frappe
from frappe.model.document import Document
from agent_incentives.settlements import verify

class AgentIncentiveSettlement(Document):
    def validate(self):
        verify(self)
    def on_trash(self):
        frappe.throw("Preserve settlement evidence; cancel the accounting voucher to reverse payment")
