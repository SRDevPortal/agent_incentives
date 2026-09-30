frappe.pages["agent-incentive-workbench"].on_page_load = function(wrapper) {
 const page=frappe.ui.make_app_page({parent:wrapper,title:__("Agent Incentive Workbench"),single_column:true});
 wrapper.incentive_workbench=new IncentiveWorkbench(page);
};
frappe.pages["agent-incentive-workbench"].on_page_show=function(wrapper) {
 if(wrapper.incentive_workbench) wrapper.incentive_workbench.load();
};
class IncentiveWorkbench {
 constructor(page) {
  this.page=page; this.offset=0; this.request=0;
  this.month=page.add_field({fieldname:"month",fieldtype:"Date",label:__("Incentive Month"),default:frappe.datetime.month_start(),change:()=>{this.offset=0;this.load();}});
  this.search=page.add_field({fieldname:"search",fieldtype:"Data",label:__("User / Name"),change:()=>{this.offset=0;this.load();}});
  this.status=page.add_field({fieldname:"status",fieldtype:"Select",label:__("Participation"),options:["Active","All","Inactive","Disabled","Needs review"],default:"Active",change:()=>{this.offset=0;this.load();}});
  page.set_primary_action(__("Refresh Calculations"),()=>this.refresh());
  page.add_inner_button(__("Settings"),()=>frappe.set_route("Form","Agent Incentive Settings"));
  page.add_inner_button(__("Add User"),()=>this.addUser());
  page.add_inner_button(__("Finalize Period"),()=>this.finalize());
  page.add_inner_button(__("Record Reviewed Correction"),()=>frappe.new_doc("Agent Incentive Adjustment"));
  page.add_inner_button(__("Record Verified Payment"),()=>frappe.new_doc("Agent Incentive Settlement"));
  page.add_inner_button(__("Export Statement"),()=>window.open("/api/method/agent_incentives.workbench.export_statement?month="+encodeURIComponent(this.month.get_value()),"_blank"));
  this.body=$('<div class="incentive-workbench"></div>').appendTo(page.main);
 }
 async load() {
  if(!this.body) return;
  const id=++this.request;
  try {
   const r=await frappe.call({method:"agent_incentives.workbench.list_users",args:{month:this.month.get_value(),search:this.search.get_value(),status:this.status.get_value(),start:this.offset}});
   if(id!==this.request)return;
   this.data=r.message;this.render();
  } catch(e) {if(id===this.request)this.body.empty().append($("<p>").text(__("Unable to load incentives. Check permissions and settings.")));}
 }
 currency(value) {return value===null||value===undefined ? "—" : new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR"}).format(Number(value));}
 render() {
  const d=this.data,b=this.body.empty(),t=d.totals||{};
  $("<p class='text-muted'>").text((d.company||__("Configure a company in Settings"))+" · "+d.month+" · "+(d.run?d.run.status+" · "+__("Calculated through")+" "+d.run.calculated_through:__("Not calculated"))).appendTo(b);
  $("<p class='text-muted'>").text(__("Receipts earn incentive only above the monthly threshold. Finalize after month-end. Finalization does not pay the agent.")).appendTo(b);
  const cards=$("<div>").css({display:"grid",gridTemplateColumns:"repeat(auto-fit,minmax(180px,1fr))",gap:"12px",marginBottom:"18px"}).appendTo(b);
  [["Payment Entry Received",t.received],["Period Incentive",t.incentive],["Lifetime Finalized",t.earned],["Verified Paid",t.payment_unknown?null:t.paid],["Outstanding",t.payment_unknown?null:t.outstanding]].forEach(([label,value])=>{
   const c=$("<div class='frappe-card p-3'>").appendTo(cards);$("<small>").text(__(label)).appendTo(c);$("<h4>").text(this.currency(value)).appendTo(c);
  });
  if(t.incomplete)$("<p class='text-warning'>").text(__("{0} users have incomplete/unavailable period figures. Totals include only calculated evidence.",[t.incomplete])).appendTo(b);
  if(d.exceptions.length) {
   const details=$("<details class='text-warning mb-3'>").appendTo(b);
   $("<summary>").text(__("{0} calculation exceptions",[d.exceptions.length])).appendTo(details);
   for(const e of d.exceptions)$("<p>").text((e.user||__("Unattributed"))+" · "+e.reference+" · "+e.error).appendTo(details);
  }
  const table=$("<table class='table table-bordered table-hover'>").appendTo($("<div class='table-responsive'>").appendTo(b));
  const header=$("<tr>").appendTo($("<thead>").appendTo(table));
  ["User","Status","Received","Threshold","Rate","Eligible","Period Incentive","Earned","Paid","Outstanding","Actions"].forEach(x=>$("<th>").text(__(x)).appendTo(header));
  const tbody=$("<tbody>").appendTo(table);
  for(const row of d.rows) {
   const tr=$("<tr>").appendTo(tbody),user=$("<td>").appendTo(tr);
   $("<a href='#'>").text(row.full_name).on("click",e=>{e.preventDefault();this.detail(row);}).appendTo(user);
   $("<small class='d-block text-muted'>").text(row.user).appendTo(user);
   if(row.warnings.length)$("<small class='d-block text-warning'>").text(row.warnings.join("; ")).appendTo(user);
   $("<td>").text(row.status).appendTo(tr);
   [row.received,row.threshold].forEach(v=>$("<td>").text(this.currency(v)).appendTo(tr));
   $("<td>").text(row.rate===null?"—":row.rate+"%").appendTo(tr);
   [row.eligible,row.incentive,row.earned,row.paid,row.outstanding].forEach(v=>$("<td>").text(this.currency(v)).appendTo(tr));
   const action=$("<td>").appendTo(tr);
   $("<button class='btn btn-xs btn-default'>").text(__("Plan")).on("click",()=>row.plan?frappe.set_route("Form","Agent Incentive Plan",row.plan):frappe.new_doc("Agent Incentive Plan",{agent_user:row.user,company:d.company,effective_from:d.month})).appendTo(action);
  }
  if(!d.rows.length)$("<p>").text(__("No enrolled users match these filters. Use Add User to enroll an agent.")).appendTo(b);
  const nav=$("<div class='flex'>").appendTo(b);
  $("<button class='btn btn-default btn-sm'>").text(__("Previous")).prop("disabled",this.offset===0).on("click",()=>{this.offset=Math.max(0,this.offset-30);this.load();}).appendTo(nav);
  $("<span class='mx-3'>").text(__("{0} users",[d.total])).appendTo(nav);
  $("<button class='btn btn-default btn-sm'>").text(__("Next")).prop("disabled",this.offset+30>=d.total).on("click",()=>{this.offset+=30;this.load();}).appendTo(nav);
 }
 async refresh() {
  await frappe.call({method:"agent_incentives.services.run_manager.refresh",args:{month:this.month.get_value()},freeze:true,freeze_message:__("Validating receipts and plans…")});
  await this.load();
 }
 async finalize() {
  if(!this.data?.run){frappe.msgprint(__("Refresh calculations first."));return;}
  const r=await frappe.call({method:"agent_incentives.services.run_manager.preview_finalize",args:{run_name:this.data.run.name}});
  const p=r.message;
  frappe.confirm(__("Finalize {0} users with total incentive {1}? This freezes the period; no payment is made.",[p.users,this.currency(p.total)]),async()=>{
   await frappe.call({method:"agent_incentives.services.run_manager.finalize",args:{token:p.token},freeze:true});this.load();
  });
 }
 async addUser() {
  const response=await frappe.call({method:"agent_incentives.enrollment.defaults"});
  const defaults=response.message;
  const d=new frappe.ui.Dialog({title:__("Enroll User and Create Plan"),fields:[
   {fieldname:"user",fieldtype:"Link",options:"User",label:__("User"),reqd:1},
   {fieldname:"effective_from",fieldtype:"Date",label:__("Effective From (month start)"),default:frappe.datetime.month_start(),reqd:1},
   {fieldname:"threshold_mode",fieldtype:"Select",options:"Salary Multiple\nFixed Amount",label:__("Threshold Mode"),default:defaults.threshold_mode,reqd:1},
   {fieldname:"salary_amount",fieldtype:"Currency",label:__("Salary Amount")},
   {fieldname:"threshold_multiplier",fieldtype:"Float",label:__("Multiplier"),default:defaults.threshold_multiplier},
   {fieldname:"threshold_amount",fieldtype:"Currency",label:__("Fixed Threshold")},
   {fieldname:"incentive_percentage",fieldtype:"Percent",label:__("Incentive %"),default:defaults.incentive_percentage,reqd:1},
  ],primary_action_label:__("Enroll"),primary_action:async values=>{
   await frappe.call({method:"agent_incentives.enrollment.add_user",args:values,freeze:true});d.hide();this.load();
  }});
  d.show();
 }
 async detail(row) {
  const r=await frappe.call({method:"agent_incentives.workbench.detail",args:{user:row.user,month:this.month.get_value()}});
  const d=new frappe.ui.Dialog({title:row.full_name,fields:[{fieldname:"content",fieldtype:"HTML"}]});
  const root=d.fields_dict.content.$wrapper;
  $("<p>").text(__("Showing up to 50 receipts and periods. Open the ledger for complete source evidence.")).appendTo(root);
  for(const s of r.message.sources)$("<p>").text(s.posting_date+" · "+s.payment_entry+" · "+s.invoice+" · "+this.currency(s.received_amount)).appendTo(root);
  for(const c of r.message.corrections)$("<p>").text(__("Correction")+" · "+this.currency(c.amount)+" · "+c.reason).appendTo(root);
  for(const h of r.message.history)$("<a class='d-block'>").attr("href","/app/agent-incentive-ledger/"+encodeURIComponent(h.name)).text(h.period_start+" · "+this.currency(h.final_payout_amount)).appendTo(root);
  d.show();
 }
}
