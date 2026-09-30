frappe.ui.form.on("User", {
 refresh(frm) {
  if (!frappe.user_roles.includes("System Manager") || frm.is_new()) return;
  frm.add_custom_button(__("Incentive Settings"), () => frappe.set_route("Form", "Agent Incentive Settings"));
  frm.add_custom_button(__("Incentive Plans"), () => frappe.set_route("List", "Agent Incentive Plan", {agent_user: frm.doc.name}));
 }
});
