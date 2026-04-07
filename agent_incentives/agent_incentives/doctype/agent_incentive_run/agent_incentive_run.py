import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime


class AgentIncentiveRun(Document):
	def validate(self):
		self._validate_period()
		self._prevent_duplicate_runs()
		self._enforce_status_transition_rules()
		self._enforce_lock_immutability()
		self._apply_status_metadata()

	def _validate_period(self):
		if self.period_start and self.period_end and self.period_end < self.period_start:
			frappe.throw("Period End cannot be earlier than Period Start.")

	def _prevent_duplicate_runs(self):
		if not self.company or not self.period_start or not self.period_end:
			return
		existing = frappe.get_all(
			"Agent Incentive Run",
			filters={
				"name": ["!=", self.name or ""],
				"company": self.company,
				"period_start": self.period_start,
				"period_end": self.period_end,
				"status": ["in", ["Draft", "Calculated", "Locked"]],
			},
			fields=["name"],
			limit=1,
		)
		if existing:
			frappe.throw(f"A run already exists for this company and period: {existing[0].name}")

	def _enforce_status_transition_rules(self):
		if self.is_new():
			return
		previous_status = frappe.db.get_value("Agent Incentive Run", self.name, "status")
		allowed = {
			"Draft": {"Draft", "Calculated", "Cancelled"},
			"Calculated": {"Calculated", "Locked", "Cancelled"},
			"Locked": {"Locked"},
			"Cancelled": {"Cancelled"},
		}
		if previous_status and self.status not in allowed.get(previous_status, {previous_status}):
			frappe.throw(f"Illegal status transition from {previous_status} to {self.status}.")

	def _enforce_lock_immutability(self):
		if self.is_new():
			return
		previous = self.get_doc_before_save()
		if not previous or previous.status != "Locked":
			return
		for fieldname in ("company", "period_start", "period_end", "status"):
			if getattr(previous, fieldname) != getattr(self, fieldname):
				frappe.throw("Locked runs cannot be modified.")

	def _apply_status_metadata(self):
		if self.status == "Calculated" and not self.run_on:
			self.run_on = now_datetime()
		if self.status == "Calculated" and not self.triggered_by:
			self.triggered_by = frappe.session.user
		if self.status == "Locked":
			self.locked_on = self.locked_on or now_datetime()
			self.locked_by = self.locked_by or frappe.session.user
