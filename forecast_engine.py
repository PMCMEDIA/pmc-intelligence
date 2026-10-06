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
 industry=project.get("industry","Other"); b=DEFAULTS.get(industry,DEFAULTS["Other"]); total=_num(project.get("budget")) or 100000
 inv=project.get("investment") or {}; search=float(inv.get("Digital Media",total*.45))*.40
 scenarios=[]
 labels=["Conservative","Expected","Upside"]
 # conservative uses high CPC + low CVR; expected midpoint; upside low CPC + high CVR
 combos=[(b["search_cpc"][2],b["search_cvr"][0]),(b["search_cpc"][1],b["search_cvr"][1]),(b["search_cpc"][0],b["search_cvr"][2])]
 for label,(cpc,cvr) in zip(labels,combos):
  clicks=search/cpc; conv=clicks*cvr; cpa=search/conv if conv else 0
  scenarios.append({"scenario":label,"search_budget":round(search),"cpc":round(cpc,2),"clicks":round(clicks),"conversion_rate":round(cvr*100,1),"conversions":round(conv),"cpa":round(cpa)})
 return {"source_type":"Modeled Assumption","confidence":"Low until client/PMC benchmarks are supplied","scenarios":scenarios,
 "assumptions":["Illustrative planning defaults only","Replace with client historical performance first","Then PMC comparable campaign benchmarks","External benchmarks only when stronger evidence is unavailable"],
 "roi_ready":False,"roi_note":"ROAS/ROI requires a defensible customer value or revenue input and close-rate assumptions."}
