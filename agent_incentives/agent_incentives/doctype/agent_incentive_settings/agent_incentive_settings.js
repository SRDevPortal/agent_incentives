frappe.ui.form.on("Agent Incentive Settings", {
 refresh(frm) {
  frm.add_custom_button(__("Incentive Workbench"), () => frappe.set_route("agent-incentive-workbench"));
  frm.add_custom_button(__("Incentive Plans"), () => frappe.set_route("List", "Agent Incentive Plan"));
  frm.set_query("user", "enrollments", () => ({filters: {enabled: 1}}));
  frm.set_query("settlement_account", () => ({filters: {company: frm.doc.company, account_type: "Payable", is_group: 0}}));
 }
});
