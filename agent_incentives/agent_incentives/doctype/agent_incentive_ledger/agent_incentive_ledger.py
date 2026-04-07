import frappe
from frappe.model.document import Document
from frappe.utils import flt, now_datetime, getdate


class AgentIncentiveLedger(Document):
	def validate(self):
		self._populate_defaults()
		self._validate_run_consistency()
		self._prevent_duplicate_agent_run_rows()
		self._validate_math()
		self._enforce_lock_immutability()

	def _populate_defaults(self):
		if not self.agent_name and self.agent_user:
			self.agent_name = frappe.db.get_value("User", self.agent_user, "full_name") or self.agent_user
		self.adjustment_amount = flt(self.adjustment_amount)
		self.gross_collected = flt(self.gross_collected)
		self.credit_note_amount = flt(self.credit_note_amount)
		self.net_collected = flt(self.net_collected)
		self.threshold_amount = flt(self.threshold_amount)
		self.eligible_amount = flt(self.eligible_amount)
		self.incentive_percentage = flt(self.incentive_percentage)
		self.payout_amount = flt(self.payout_amount)
		self.final_payout_amount = flt(self.payout_amount) + flt(self.adjustment_amount)
		self.generated_by = self.generated_by or frappe.session.user
		self.generated_on = self.generated_on or now_datetime()

	def _validate_run_consistency(self):
		run = frappe.get_doc("Agent Incentive Run", self.incentive_run)
		self.company = self.company or run.company
		if self.company != run.company:
			frappe.throw("Ledger company must match Incentive Run company.")
		ledger_start = getdate(self.period_start) if self.period_start else None
		ledger_end = getdate(self.period_end) if self.period_end else None
		run_start = getdate(run.period_start) if run.period_start else None
		run_end = getdate(run.period_end) if run.period_end else None
		if ledger_start != run_start or ledger_end != run_end:
			frappe.throw("Ledger period must match the linked Incentive Run period.")

	def _prevent_duplicate_agent_run_rows(self):
		existing = frappe.get_all(
			"Agent Incentive Ledger",
			filters={
				"name": ["!=", self.name or ""],
				"incentive_run": self.incentive_run,
				"agent_user": self.agent_user,
			},
			fields=["name"],
			limit=1,
		)
		if existing:
			frappe.throw(f"A ledger row already exists for this agent in run {self.incentive_run}: {existing[0].name}")

	def _validate_math(self):
		expected_net = flt(self.gross_collected) - flt(self.credit_note_amount)
		if abs(flt(self.net_collected) - expected_net) > 0.01:
			frappe.throw("Net Collected must equal Gross Collected minus Credit Note Amount.")
		expected_eligible = max(expected_net - flt(self.threshold_amount), 0)
		if abs(flt(self.eligible_amount) - expected_eligible) > 0.01:
			frappe.throw("Eligible Amount does not match the threshold-adjusted net collection.")
		expected_payout = expected_eligible * (flt(self.incentive_percentage) / 100.0)
		if abs(flt(self.payout_amount) - expected_payout) > 0.01:
			frappe.throw("Payout Amount does not match Eligible Amount × Incentive %.")
		expected_final = flt(self.payout_amount) + flt(self.adjustment_amount)
		if abs(flt(self.final_payout_amount) - expected_final) > 0.01:
			frappe.throw("Final Payout Amount must equal Payout Amount plus Adjustment Amount.")

	def _enforce_lock_immutability(self):
		run_status = frappe.db.get_value("Agent Incentive Run", self.incentive_run, "status")
		if run_status != "Locked" or self.is_new():
			return
		previous = self.get_doc_before_save()
		if not previous:
			return
		protected_fields = [
			"incentive_run", "company", "agent_user", "agent_name", "period_start", "period_end",
			"gross_collected", "credit_note_amount", "net_collected", "threshold_amount",
			"eligible_amount", "incentive_percentage", "payout_amount", "plan_reference"
		]
		for fieldname in protected_fields:
			if getattr(previous, fieldname) != getattr(self, fieldname):
				frappe.throw("Ledger rows linked to a locked run cannot be modified.")
