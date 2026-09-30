import frappe
from frappe.model.document import Document

class AgentIncentiveEnrollment(Document):
    def validate(self):
        frappe.throw("Edit enrollment through Agent Incentive Settings so cross-program checks are applied")

    def on_trash(self):
        frappe.throw("Preserve enrollment history; deactivate through program Settings")
