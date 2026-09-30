import json
import frappe
from frappe.utils import today, getdate
from agent_incentives.access import finance, settings
from agent_incentives.domain import VERSION, money, month_period, threshold
from agent_incentives.services.plans import get_applicable_plan
from agent_incentives.settlements import paid_by_user

def summaries(company, user=None):
    scope=" and l.agent_user=%s" if user else ""
    args=[company]+([user] if user else [])
    rows=frappe.db.sql("""select l.agent_user,
        sum(case when r.status='Locked' and l.calculation_version='payment-entry-v1'
                 then l.final_payout_amount else 0 end) earned,
        sum(case when coalesce(l.calculation_version,'')!='payment-entry-v1' then 1 else 0 end) legacy_count,
        sum(case when coalesce(l.calculation_version,'')!='payment-entry-v1'
                 and l.payment_status!='Unpaid' then 1 else 0 end) legacy_payments
        from `tabAgent Incentive Ledger` l join `tabAgent Incentive Run` r on r.name=l.incentive_run
        where l.company=%s and r.status!='Cancelled'""" + scope + " group by l.agent_user",args,as_dict=True)
    return {r.agent_user:r for r in rows}

def other_enrollments(user=None):
    if not frappe.db.exists("DocType","WFH Enrollment"):
        return set()
    filters=dict(parent="WFH Commission Settings",parenttype="WFH Commission Settings",active=1)
    if user:filters["user"]=user
    return set(frappe.get_all("WFH Enrollment",filters=filters,pluck="user"))

def data(month=None, only_user=None):
    s=settings();start,end=month_period(month or today())
    if not s.company:
        return dict(rows=[],company=None,month=str(start),run=None,exceptions=[],enabled=s.enabled)
    filters=dict(company=s.company,period_start=start,period_end=end,status=["!=","Cancelled"])
    run_names=frappe.get_all("Agent Incentive Run",filters=filters,pluck="name")
    if len(run_names)>1:
        frappe.throw("Duplicate historical runs require reconciliation")
    run=frappe.get_doc("Agent Incentive Run",run_names[0]) if run_names else None
    lf=dict(incentive_run=run.name) if run else {}
    if only_user:lf["agent_user"]=only_user
    ledgers=frappe.get_all("Agent Incentive Ledger",filters=lf,
        fields=["name","agent_user","payment_entry_received","threshold_amount","eligible_amount","payout_amount","plan_reference","incentive_percentage","calculation_version"]) if run else []
    by_user={r.agent_user:r for r in ledgers}
    lifetime=summaries(s.company,only_user);paid=paid_by_user(s.company,only_user)
    from agent_incentives.adjustments import amounts
    corrections=amounts(s.company,only_user)
    enrollments=[r for r in s.enrollments if not only_user or r.user==only_user]
    names=sorted({r.user for r in enrollments}|set(lifetime))
    others=other_enrollments(only_user)
    exceptions=json.loads(run.exceptions_json or "[]") if run else []
    result=[]
    for name in names:
        u=frappe.db.get_value("User",name,["full_name","enabled","role_profile_name"],as_dict=True)
        if not u:continue
        active=any(r.user==name and r.active for r in enrollments)
        status="Disabled" if not u.enabled else ("Active" if active else "Inactive")
        if name in others and active:status="Needs review"
        ledger=by_user.get(name)
        life=lifetime.get(name,{})
        warnings=[e["error"] for e in exceptions if not e.get("user") or e.get("user")==name]
        if status=="Needs review":warnings.append("Conflicting active WFH enrollment; deactivate one program")
        target=rate=plan_name=None
        supported=bool(ledger and ledger.calculation_version==VERSION)
        try:
            if supported:
                plan=frappe._dict(name=ledger.plan_reference,incentive_percentage=ledger.incentive_percentage,threshold_mode="Fixed Amount",threshold_amount=ledger.threshold_amount)
            else:
                plan=get_applicable_plan(name,s.company,start,end,required=False)
                if plan is None:
                    raise frappe.ValidationError("Missing plan")
            target=float(threshold(plan));rate=float(plan.incentive_percentage);plan_name=plan.name
        except frappe.ValidationError:
            warnings.append("No unique active plan covers this month")
        supported=bool(ledger and ledger.calculation_version==VERSION)
        complete=bool(supported and not warnings)
        if supported:
            target=ledger.threshold_amount;rate=ledger.incentive_percentage;plan_name=ledger.plan_reference
        earned=money(life.get("earned"))+corrections.get(name,money(0))
        paid_amount=paid.get(name,money(0))
        if life.get("legacy_count"):warnings.append("Legacy history excluded until evidence is reconciled")
        payment_unknown=bool(life.get("legacy_payments"))
        received=float(ledger.payment_entry_received) if supported else None
        result.append(dict(user=name,full_name=u.full_name or name,profile=u.role_profile_name,
            status=status,plan=plan_name,threshold=target,rate=rate,received=received,
            threshold_remaining=max(float(target or 0)-received,0) if received is not None and target is not None else None,
            eligible=float(ledger.eligible_amount) if supported else None,
            incentive=float(ledger.payout_amount) if supported else None,
            complete=complete,earned=float(earned),paid=None if payment_unknown else float(paid_amount),
            outstanding=None if payment_unknown else float(earned-paid_amount),
            legacy_count=int(life.get("legacy_count") or 0),corrections=float(corrections.get(name,money(0))),warnings=warnings,
            ledger=ledger.name if ledger else None))
    return dict(rows=result,company=s.company,month=str(start),enabled=s.enabled,
        run=dict(name=run.name,status=run.status,calculated_through=str(run.calculated_through or ""),
                 run_on=str(run.run_on or ""),version=run.calculation_version) if run else None,
        exceptions=exceptions)

@frappe.whitelist()
def list_users(month=None, search="", status="Active", start=0, page_length=30):
    finance()
    result=data(month)
    rows=[r for r in result["rows"] if (not status or status=="All" or r["status"]==status)
          and (not search or search.lower() in (r["user"]+" "+r["full_name"]).lower())]
    totals={}
    for key in ("received","incentive","earned","paid","outstanding"):
        totals[key]=sum(r[key] or 0 for r in rows)
    totals["incomplete"]=sum(not r["complete"] for r in rows)
    totals["payment_unknown"]=any(r["paid"] is None for r in rows)
    result.update(rows=rows[max(0,int(start)):max(0,int(start))+min(100,max(1,int(page_length)))],
                  total=len(rows),totals=totals)
    return result

@frappe.whitelist()
def detail(user, month=None, start=0, page_length=50):
    finance()
    result=data(month, user)
    if not result["rows"]:
        frappe.throw("User is not part of this incentive history")
    row=result["rows"][0]
    sources=[]
    if row["ledger"]:
        ledger=frappe.get_doc("Agent Incentive Ledger",row["ledger"])
        sources=[dict(payment_entry=r.payment_entry,invoice=r.invoice,posting_date=r.posting_date,
                      received_amount=r.received_amount) for r in ledger.sources]
    offset=max(0,int(start));limit=min(100,max(1,int(page_length)))
    history=frappe.get_all("Agent Incentive Ledger",filters=dict(agent_user=user,company=result["company"]),
        fields=["name","incentive_run","period_start","period_end","final_payout_amount","calculation_version"],
        order_by="period_start desc",start=offset,page_length=limit)
    correction_rows=frappe.get_all("Agent Incentive Adjustment",filters=dict(agent_user=user,company=result["company"]),fields=["name","ledger","amount","reason","source_reference","approved_on"],order_by="creation desc",start=offset,page_length=limit)
    return dict(user=row,corrections=correction_rows,sources=sources[offset:offset+limit],source_count=len(sources),history=history)

@frappe.whitelist()
def export_statement(month=None):
    finance()
    import csv
    import io
    result=data(month)
    buf=io.StringIO()
    writer=csv.writer(buf)
    keys=("user","full_name","status","received","threshold","rate","incentive","earned","paid","outstanding")
    writer.writerow(keys)
    for row in result["rows"]:
        values=[]
        for key in keys:
            value=row.get(key)
            # Prevent spreadsheet formula injection in user-supplied labels.
            if isinstance(value,str) and value.startswith(("=","+","-","@")):value="'"+value
            values.append(value)
        writer.writerow(values)
    frappe.response["filename"]="incentives-"+result["month"]+".csv"
    frappe.response["filecontent"]=buf.getvalue()
    frappe.response["type"]="download"
