import frappe
from frappe.model.document import Document


class AgentIncentiveSettings(Document):
	def validate(self):
		self.default_threshold_multiplier = float(self.default_threshold_multiplier or 1)
		self.default_incentive_percentage = float(self.default_incentive_percentage or 0)
		if self.default_threshold_multiplier < 0:
			self.default_threshold_multiplier = 0
		if self.default_incentive_percentage < 0:
			self.default_incentive_percentage = 0



def ensure_single():
	if frappe.db.exists("DocType", "Agent Incentive Settings") and not frappe.db.exists("Agent Incentive Settings", "Agent Incentive Settings"):
		doc = frappe.get_doc({"doctype": "Agent Incentive Settings"})
		doc.insert(ignore_permissions=True)
