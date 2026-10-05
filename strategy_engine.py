def build_strategy(project,research):
    client=project.get("client","Client"); goal=project.get("goal","Grow qualified demand")
    facts=[]
    if research.get("title"): facts.append({"source":"Verified Research","label":"Website title","value":research["title"]})
    if research.get("description"): facts.append({"source":"Verified Research","label":"Website description","value":research["description"]})
    for h in research.get("h1",[])[:4]: facts.append({"source":"Verified Research","label":"Website heading","value":h})
    if project.get("goal"): facts.append({"source":"Client-Provided","label":"Primary goal","value":goal})
    if project.get("budget"): facts.append({"source":"Client-Provided","label":"Budget","value":project["budget"]})
    departments={
      "Digital Media":["Google Search","Performance Max","Paid Social","Performance Media / CTV"],
      "SEO / AEO":["Technical + on-page audit","Priority-page optimization","Local SEO","Expert-reviewed content","AI-search visibility"],
      "Organic Social":["Platform roles","Content pillars","Short-form video","Community management"],
      "Production":["Hero brand story","Vertical video","Photography","Expert / leadership interviews"],
      "Creative / Website":["Conversion paths","Landing pages","Proof + differentiation","Tracking"],
      "PR / Communications":["Story lanes","Thought leadership","Media outreach"],
      "Measurement":["Qualified conversions","CPA / ROAS","Attribution views","CRM / revenue reconciliation"]}
    return {"executive":f"{client} should use an integrated strategy connecting awareness, intent capture, conversion and retention around the stated business goal: {goal}.","facts":facts,"departments":departments}
