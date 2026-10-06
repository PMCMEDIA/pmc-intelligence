DEFAULTS={
 "Healthcare":{"search_cpc":[3.5,7.5,12.0],"search_cvr":[0.04,0.07,0.11],"social_cpm":[9,15,24]},
 "Restaurant / Hospitality":{"search_cpc":[1.5,3.0,5.5],"search_cvr":[0.035,0.06,0.09],"social_cpm":[7,12,20]},
 "Insurance":{"search_cpc":[6,12,22],"search_cvr":[0.025,0.05,0.08],"social_cpm":[10,17,28]},
 "Financial Services":{"search_cpc":[4,9,16],"search_cvr":[0.025,0.05,0.08],"social_cpm":[10,17,28]},
 "Other":{"search_cpc":[2.5,5.0,9.0],"search_cvr":[0.03,0.055,0.09],"social_cpm":[8,14,23]}
}
def _num(v):
 import re
 try:return float(re.sub(r"[^0-9.]","",str(v)))
 except:return 0

def forecast(project):
 industry=project.get("industry","Other"); b=DEFAULTS.get(industry,DEFAULTS["Other"]); total=_num(project.get("budget")) or 0
 allocations=project.get("investment_allocations") or []
 digital=next((float(x.get("amount",0)) for x in allocations if x.get("department")=="Digital Media"),total*.45)
 tactics=(project.get("tactic_allocations") or {}).get("Digital Media",[])
 search_pct=sum(float(x.get("percent",0)) for x in tactics if any(k in str(x.get("name","")).lower() for k in ["search","performance max","pmax"]))
 search=digital*(search_pct/100 if search_pct else .40)
 scenarios=[]; labels=["Conservative","Expected","Upside"]
 combos=[(b["search_cpc"][2],b["search_cvr"][0]),(b["search_cpc"][1],b["search_cvr"][1]),(b["search_cpc"][0],b["search_cvr"][2])]
 econ=project.get("forecast_inputs") or {}; lead_value=_num(econ.get("lead_value")); close_rate=_num(econ.get("close_rate"))/100; customer_value=_num(econ.get("customer_value")); margin=_num(econ.get("margin"))/100
 roi_ready=bool((lead_value>0) or (close_rate>0 and customer_value>0))
 for label,(cpc,cvr) in zip(labels,combos):
  clicks=search/cpc if cpc else 0; conv=clicks*cvr; cpa=search/conv if conv else 0
  revenue=conv*lead_value if lead_value else conv*close_rate*customer_value if roi_ready else 0
  roas=revenue/search if search and revenue else None; profit=revenue*margin if margin else revenue; roi=(profit-search)/search if search and revenue else None
  scenarios.append({"scenario":label,"search_budget":round(search),"cpc":round(cpc,2),"clicks":round(clicks),"conversion_rate":round(cvr*100,1),"conversions":round(conv),"cpa":round(cpa),"projected_revenue":round(revenue) if revenue else None,"roas":round(roas,2) if roas is not None else None,"roi_percent":round(roi*100,1) if roi is not None else None})
 return {"source_type":"Modeled Assumption","confidence":"Planning range, not a performance guarantee","benchmark_set":industry,"scenarios":scenarios,
 "assumptions":["Industry planning defaults are placeholders until PMC enters sourced/current benchmarks","Search/PMax share is derived from the approved Digital Media tactic mix when available","Scenario outputs are modeled estimates, not guaranteed results"],
 "roi_ready":roi_ready,"roi_note":"ROI/ROAS shown only when lead value or customer value + close rate is supplied." if roi_ready else "Add lead value or customer value + close rate to model ROAS/ROI."}
