import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, getdate
from agent_incentives.access import internal
from agent_incentives.domain import VERSION, month_period

class AgentIncentiveRun(Document):
    def validate(self):
        internal(self)
        start,end=month_period(self.period_start)
        if getdate(self.period_start)!=start or getdate(self.period_end)!=end:
            frappe.throw("Incentive runs must cover one complete calendar month")
        old=self.get_doc_before_save()
        if old and old.status=="Locked":
            frappe.throw("Finalized runs are immutable")
        duplicates=frappe.get_all("Agent Incentive Run",filters=dict(
            name=["!=",self.name],company=self.company,status=["!=","Cancelled"],
            period_start=["<=",self.period_end],period_end=[">=",self.period_start]),pluck="name")
        if duplicates:
            frappe.throw("An overlapping incentive run already exists")
        if self.status=="Locked":
            self.locked_by=frappe.session.user
            self.locked_on=now_datetime()

    def on_trash(self):
        frappe.throw("Preserve incentive run history")
