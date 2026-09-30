(() => {
 const page=frappe.pages["vobiz-agent-analytics"];
 if(!page||page.incentive_cards_installed)return;
 page.incentive_cards_installed=true;
 const load=page.on_page_load,show=page.on_page_show,selector="[data-agent-incentive-cards]";
 function install(wrapper) {
  $(wrapper).off("click.agentIncentives",'[data-action="refresh"]').on("click.agentIncentives",'[data-action="refresh"]',()=>refresh(wrapper));
 }
 async function refresh(wrapper) {
  const id=(wrapper.agent_incentive_request||0)+1;wrapper.agent_incentive_request=id;
  const user=frappe.session.user;
  $(wrapper).find(selector).remove();
  try {
   const r=await frappe.call({method:"agent_incentives.agent_dashboard.my_incentive_cards"});
   if(id!==wrapper.agent_incentive_request||user!==frappe.session.user)return;
   const d=r.message;if(!d?.visible)return;
   const dashboard=$(wrapper).find(".vobiz-analytics-page");if(!dashboard.length)return;
   const section=$('<section class="vobiz-band" data-agent-incentive-cards></section>');
   $("<h3>").text(__("My Incentives")).appendTo(section);
   $("<p class='text-muted small'>").text(d.company+" · "+d.month+" · "+__("Your incentives; independent of call-date and selected-agent filters.")).appendTo(section);
   const grid=$("<div class='vobiz-kpi-grid'>").css("grid-template-columns","repeat(auto-fit,minmax(180px,1fr))").appendTo(section);
   const closed=d.run?.status==="Locked";
   const definitions=[["Payment Entry Received","received"],["Threshold Remaining","threshold_remaining"],[closed?"Finalized Period Incentive":"Provisional Period Incentive","incentive"],["Lifetime Finalized Incentive","earned"],["Incentive Paid","paid"],["Outstanding Finalized Incentive","outstanding"]];
   for(const [label,key] of definitions) {
    const card=$("<div class='vobiz-kpi'>").appendTo(grid);
    $("<span>").text(__(label)).appendTo(card);
    const value=d.metrics[key];
    $("<strong>").text(value===null||value===undefined?__("Not available"):new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:2}).format(Number(value))).appendTo(card);
   }
   if(d.metrics.received!==null&&d.metrics.threshold!==null) {
    const percent=d.metrics.threshold>0?Math.min(100,Math.max(0,d.metrics.received/d.metrics.threshold*100)):100;
    $("<progress max='100'>").attr("value",percent).attr("aria-label",__("Monthly threshold progress")).css("width","100%").appendTo(section);
   }
   if(!d.complete)$("<p class='text-warning small'>").text(__("Period calculation is incomplete or has exceptions. Amounts are provisional; finance must review.")).appendTo(section);
   if(d.legacy_count)$("<p class='text-warning small'>").text(__("Legacy history awaits reconciliation and is excluded from finalized totals.")).appendTo(section);
   $("<p class='text-muted small'>").text(d.run?__("Calculated through {0}; last refreshed {1}",[d.run.calculated_through,d.run.run_on]):__("Calculations have not been refreshed yet.")).appendTo(section);
   const wfh=dashboard.children("[data-wfh-commission-cards]").first();
   const anchor=wfh.length?wfh:dashboard.children(".vobiz-summary").first();
   if(anchor.length)section.insertAfter(anchor);else section.prependTo(dashboard);
  } catch(e) {if(id===wrapper.agent_incentive_request)$(wrapper).find(selector).remove();}
 }
 page.on_page_load=function(wrapper){if(load)load.apply(this,arguments);install(wrapper);};
 page.on_page_show=function(wrapper){if(show)show.apply(this,arguments);install(wrapper);refresh(wrapper);};
})();
