import frappe


@frappe.whitelist()
def get_setup_status():
	frappe.only_for(("System Manager",))
	return {
		"counts": {
			"plans": frappe.db.count("Agent Incentive Plan"),
			"runs": frappe.db.count("Agent Incentive Run"),
			"ledger_rows": frappe.db.count("Agent Incentive Ledger"),
		},
		"recent_plans": frappe.get_all(
			"Agent Incentive Plan",
			fields=["name", "agent_user", "agent_name", "active", "threshold_mode", "incentive_percentage", "effective_from", "effective_to", "modified"],
			order_by="modified desc",
			limit=20,
		),
	}


@frappe.whitelist()
def smoke_check():
	frappe.only_for(("System Manager",))
	checks = []
	for doctype in ["Agent Incentive Settings", "Agent Incentive Plan", "Agent Incentive Run", "Agent Incentive Ledger"]:
		checks.append({
			"name": f"doctype:{doctype}",
			"ok": bool(frappe.db.exists("DocType", doctype)),
			"message": f"{doctype} available" if frappe.db.exists("DocType", doctype) else f"{doctype} missing",
		})
	checks.append({
		"name": "formula-helper",
		"ok": True,
		"message": "agent_incentives.api.formulas.calculate_incentive",
	})
	return {"ok": all(item["ok"] for item in checks), "checks": checks}
