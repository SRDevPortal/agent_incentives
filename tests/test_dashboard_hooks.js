const fs=require("fs"),vm=require("vm"),assert=require("assert");
const paths=[
 "apps/wfh_commission/wfh_commission/public/js/agent_commission_cards.js",
 "apps/agent_incentives/agent_incentives/public/js/agent_incentive_cards.js"
];
(async()=>{
 for(const order of [paths,[...paths].reverse()]){
  let loads=0,shows=0,calls=[];
  const page={on_page_load(){loads++;},on_page_show(){shows++;}};
  const jq={off(){return this;},on(){return this;},find(){return this;},remove(){return this;}};
  const context=vm.createContext({frappe:{pages:{"vobiz-agent-analytics":page},session:{user:"agent"},call:async options=>{calls.push(options.method);return {message:{visible:false}};}},$:()=>jq,console});
  for(const path of order)vm.runInContext(fs.readFileSync(path,"utf8"),context);
  // Running both scripts again must not wrap handlers twice.
  for(const path of order)vm.runInContext(fs.readFileSync(path,"utf8"),context);
  const wrapper={};page.on_page_load(wrapper);page.on_page_show(wrapper);
  await Promise.resolve();await Promise.resolve();
  assert.equal(loads,1);assert.equal(shows,1);assert.equal(calls.length,2);
  assert(calls.includes("agent_incentives.agent_dashboard.my_incentive_cards"));
  assert(calls.includes("wfh_commission.agent_dashboard.my_commission_cards"));
 }
 console.log("Dashboard hooks coexist in either load order; repeated installation does not duplicate calls");
})().catch(e=>{console.error(e);process.exitCode=1;});
