def build_strategy(project,research):
    client=project.get("client","Client"); goal=project.get("goal","Grow qualified demand")
    answers=[x for x in project.get("discovery_answers",[]) if x.get("answer")]
    supplied=project.get("strategy_context","")
    facts=[]
    if research.get("title"): facts.append({"source":"Verified Research","label":"Website title","value":research["title"]})
    if research.get("description"): facts.append({"source":"Verified Research","label":"Website description","value":research["description"]})
    for h in research.get("h1",[])[:4]: facts.append({"source":"Verified Research","label":"Website heading","value":h})
    if project.get("goal"): facts.append({"source":"Client-Provided","label":"Primary goal","value":goal})
    if project.get("budget"): facts.append({"source":"Client-Provided","label":"Budget","value":project["budget"]})
    if supplied: facts.append({"source":"Account Manager / Client Context","label":"Strategy context supplied at intake","value":supplied[:4000]})
    for item in answers:
        facts.append({"source":"Discovery Answer","label":item.get("question","Discovery"),"value":item.get("answer","")})
    departments={
      "Digital Media":["Google Search","Performance Max","Paid Social","Performance Media / CTV"],
      "SEO / AEO":["Technical + on-page audit","Priority-page optimization","Local SEO","Expert-reviewed content","AI-search visibility"],
      "Organic Social":["Platform roles","Content pillars","Short-form video","Community management"],
      "Production":["Hero brand story","Vertical video","Photography","Expert / leadership interviews"],
      "Creative / Website":["Conversion paths","Landing pages","Proof + differentiation","Tracking"],
      "PR / Communications":["Story lanes","Thought leadership","Media outreach"]}
    context = (" Supplied account/client context has been incorporated into the strategy." if supplied else "")
    if answers:
        summary="; ".join([a.get("answer","") for a in answers[:3]])
        context+=f" Gap-check responses added {len(answers)} additional inputs, including: {summary}."
    return {"executive":f"{client} should use an integrated strategy connecting awareness, intent capture, conversion and retention around the stated business goal: {goal}.{context}","facts":facts,"departments":departments}
