import frappe
from frappe.model.document import Document
from frappe.utils import today
from agent_incentives.access import finance
from agent_incentives.domain import amount
from agent_incentives.participation import assert_exclusive

class AgentIncentiveSettings(Document):
    def on_trash(self):
        frappe.throw("Preserve incentive enrollment history")

    def validate(self):
        finance()
        rows = self.get("enrollments") or []
        assert_exclusive("incentives", [r.user for r in rows if r.active])
        previous = self.get_doc_before_save()
        old = {r.name:r for r in previous.enrollments} if previous else {}
        current = {r.name:r for r in rows}
        for name, row in old.items():
            if name not in current or current[name].user != row.user:
                frappe.throw("Preserve enrollment history; deactivate a row instead of deleting or changing its User")
        seen = set()
        for row in rows:
            row.enrolled_on = old[row.name].enrolled_on if row.name in old else today()
            row.agent_name = frappe.db.get_value("User", row.user, "full_name") or row.user
            row.profile = frappe.db.get_value("User", row.user, "role_profile_name")
            if row.active:
                if row.user in seen:
                    frappe.throw("Only one active incentive enrollment is allowed per User")
                seen.add(row.user)
        if previous and previous.company and previous.company != self.company and previous.enrollments:
            frappe.throw("Company cannot change after enrollment; preserve financial history")
        if self.enabled and (not self.company or frappe.db.get_value("Company", self.company, "default_currency") != "INR"):
            frappe.throw("Select an INR company")
        if amount(self.default_threshold_multiplier) < 0 or not 0 <= amount(self.default_incentive_percentage) <= 100:
            frappe.throw("Invalid default multiplier or incentive percentage")
        self.incentive_basis = "Payment Entry Posting Date"
        self.deduct_credit_notes = 0

def ensure_single():
    # Singles are materialized on first save; do not insert duplicate singleton documents.
    return
