import frappe
from frappe.model.document import Document
from frappe.utils import getdate


class AgentIncentivePlan(Document):
	def validate(self):
		self._normalize_fields()
		self._populate_agent_name()
		self._validate_dates()
		self._validate_numbers()
		self._validate_threshold_mode()
		self._validate_status_consistency()
		self._validate_overlap()

	def _normalize_fields(self):
		self.agent_name = (self.agent_name or "").strip()
		self.salary_amount = float(self.salary_amount or 0)
		self.threshold_multiplier = float(self.threshold_multiplier or 0)
		self.threshold_amount = float(self.threshold_amount or 0)
		self.incentive_percentage = float(self.incentive_percentage or 0)

	def _populate_agent_name(self):
		if not self.agent_name and self.agent_user:
			self.agent_name = (
				frappe.db.get_value("User", self.agent_user, "full_name")
				or self.agent_user
			)
		self.agent_name = (self.agent_name or "").strip()
		if not self.agent_name:
			frappe.throw("Agent Name is required.")

	def _validate_dates(self):
		if self.effective_to and self.effective_from and self.effective_to < self.effective_from:
			frappe.throw("Effective To cannot be earlier than Effective From.")

	def _validate_numbers(self):
		for label, value in {
			"Salary Amount": self.salary_amount,
			"Threshold Multiplier": self.threshold_multiplier,
			"Threshold Amount": self.threshold_amount,
			"Incentive %": self.incentive_percentage,
		}.items():
			if value < 0:
				frappe.throw(f"{label} cannot be negative.")
		if self.incentive_percentage > 100:
			frappe.throw("Incentive % cannot exceed 100 in Phase 1 hardening.")

	def _validate_threshold_mode(self):
		if self.threshold_mode == "Salary Multiple":
			if not self.salary_amount:
				frappe.throw("Salary Amount is required when Threshold Mode is Salary Multiple.")
			if self.threshold_multiplier < 0:
				frappe.throw("Threshold Multiplier cannot be negative.")
		elif self.threshold_mode == "Fixed Amount":
			if self.threshold_amount <= 0:
				frappe.throw("Threshold Amount must be greater than zero when Threshold Mode is Fixed Amount.")

	def _validate_status_consistency(self):
		if not self.active and self.plan_status == "Active":
			frappe.throw("Inactive plans cannot have Plan Status set to Active.")
		if self.plan_status == "Expired" and not self.effective_to:
			frappe.throw("Expired plans should have an Effective To date.")

	def _validate_overlap(self):
		if not self.agent_user or not self.effective_from:
			return
		filters = {
			"name": ["!=", self.name or ""],
			"agent_user": self.agent_user,
			"docstatus": ["<", 2],
			"plan_status": ["in", ["Draft", "Active"]],
		}
		if self.company:
			filters["company"] = self.company
		plans = frappe.get_all(
			"Agent Incentive Plan",
			filters=filters,
			fields=["name", "effective_from", "effective_to"],
		)
		this_start = self.effective_from
		this_end = self.effective_to
		for plan in plans:
			other_start = plan.effective_from
			other_end = plan.effective_to
			if self._date_ranges_overlap(this_start, this_end, other_start, other_end):
				frappe.throw(
					f"Plan overlaps with existing plan {plan.name} for this agent in the selected date range."
				)

	@staticmethod
	def _date_ranges_overlap(start1, end1, start2, end2):
		start1 = getdate(start1) if start1 else getdate("1000-01-01")
		start2 = getdate(start2) if start2 else getdate("1000-01-01")
		end1 = getdate(end1) if end1 else getdate("9999-12-31")
		end2 = getdate(end2) if end2 else getdate("9999-12-31")
		return start1 <= end2 and start2 <= end1
