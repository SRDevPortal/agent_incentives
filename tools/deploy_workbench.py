"""Targeted application metadata update; no enrollment or accounting changes."""
import os
import json
import frappe
os.chdir("/home/srdev/frappe-bench-v15/sites")
frappe.init(site="sriaas.local",sites_path=".")
frappe.connect()
frappe.set_user("Administrator")
try:
    def counts():
        return {d:frappe.db.count(d) for d in ["Journal Entry","GL Entry","Payment Entry","WFH Enrollment","WFH Commission Calculation"]}
    before=counts()
    for name in ["agent_incentive_enrollment","agent_incentive_source","agent_incentive_settings",
                 "agent_incentive_plan","agent_incentive_run","agent_incentive_ledger","agent_incentive_settlement","agent_incentive_adjustment"]:
        frappe.reload_doc("agent_incentives","doctype",name,force=True)
    frappe.reload_doc("agent_incentives","page","agent_incentive_workbench",force=True)
    from agent_incentives.setup import install
    install()
    assert counts()==before,"Business record counts changed"
    frappe.db.commit()
    frappe.clear_cache()
    print(json.dumps(dict(updated=True,accounting_unchanged=True,counts=before)))
except Exception:
    frappe.db.rollback()
    raise
finally:
    frappe.destroy()
