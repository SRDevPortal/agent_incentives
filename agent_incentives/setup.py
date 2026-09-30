import frappe

def install():
    ensure_workspace()
    from frappe.custom.doctype.custom_field.custom_field import create_custom_fields
    # Attribution is explicit before submission; never infer or backfill historical owners.
    create_custom_fields({"Sales Invoice": [
        dict(fieldname="incentive_agent",label="Incentive Agent",fieldtype="Link",options="User",
             insert_after="sales_partner",description="Agent credited for threshold incentives. Set before submission; no historical auto-attribution."),
        dict(fieldname="incentive_agent_name",label="Incentive Agent Name",fieldtype="Data",
             fetch_from="incentive_agent.full_name",read_only=1,insert_after="incentive_agent")
    ]}, update=False)
    # Preserve legacy duplicates for review instead of deleting financial history.
    duplicates=frappe.db.sql("""select incentive_run,agent_user,count(*) n
        from `tabAgent Incentive Ledger` group by incentive_run,agent_user having count(*)>1""")
    if not duplicates:
        frappe.db.add_unique("Agent Incentive Ledger",["incentive_run","agent_user"],constraint_name="unique_incentive_agent_run")
    frappe.db.add_index("Agent Incentive Source",["payment_entry","invoice"])
    frappe.db.add_index("Agent Incentive Settlement",["journal_entry","journal_row"])
    frappe.db.add_index("Agent Incentive Enrollment",["user","active"])


def ensure_workspace():
    """Keep existing navigation; install the app shortcut without developer exports."""
    import json
    from pathlib import Path
    if not frappe.db.exists("Workspace","Incentives"):
        path=Path(frappe.get_app_path("agent_incentives","workspace","incentives","incentives.json"))
        workspace=frappe.get_doc(json.loads(path.read_text()))
    else:
        workspace=frappe.get_doc("Workspace","Incentives")
    if not workspace.is_new() and any(r.link_to=="agent-incentive-workbench" for r in workspace.shortcuts):
        return
    if not any(r.link_to=="agent-incentive-workbench" for r in workspace.shortcuts):
        workspace.append("shortcuts",dict(type="Page",label="Incentive Workbench",link_to="agent-incentive-workbench",color="Blue"))
        content=json.loads(workspace.content or "[]")
        content.insert(0,dict(id="incentive_workbench",type="shortcut",data=dict(shortcut_name="Incentive Workbench",col=3)))
        workspace.content=json.dumps(content)
    previous=frappe.conf.developer_mode
    try:
        frappe.conf.developer_mode=0
        workspace.save(ignore_permissions=True)
    finally:
        frappe.conf.developer_mode=previous
