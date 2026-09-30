import json
import os
import frappe
os.chdir('/home/srdev/frappe-bench-v15/sites')
frappe.init(site="sriaas.local",sites_path="/home/srdev/frappe-bench-v15/sites")
frappe.connect()
try:
    result={"apps":frappe.get_installed_apps()}
    result["incentives"]={dt:frappe.db.count(dt) for dt in ["Agent Incentive Plan","Agent Incentive Run","Agent Incentive Ledger"]}
    result["attribution_fields"]=[f.fieldname for f in frappe.get_meta("Sales Invoice").fields if f.fieldname in ("incentive_agent","incentive_agent_name","source_encounter")]
    result["companies"]=frappe.get_all("Company",fields=["name","default_currency"])
    result["active_wfh"]=frappe.db.count("WFH Enrollment",{"active":1})
    result["workspace"] = frappe.get_all("Workspace", filters={"module":"Agent Incentives"},fields=["name","title","label"])
    result["journal_count"]=frappe.db.count("Journal Entry")
    result["gl_count"]=frappe.db.count("GL Entry")
    print(json.dumps(result,default=str))
finally:
    frappe.db.rollback()
    frappe.destroy()
