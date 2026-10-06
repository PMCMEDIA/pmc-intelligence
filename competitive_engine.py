from urllib.parse import quote_plus
import urllib.request, json, re
from bs4 import BeautifulSoup

def _search(query, limit=5):
    url="https://www.google.com/search?q="+quote_plus(query)
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req,timeout=10) as r: html=r.read(500000).decode("utf-8","ignore")
        soup=BeautifulSoup(html,"html.parser"); out=[]
        for a in soup.select("a"):
            href=a.get("href",""); text=a.get_text(" ",strip=True)
            m=re.search(r"/url\?q=([^&]+)",href)
            if m and text and len(text)>10:
                link=m.group(1)
                if "google." not in link: out.append({"title":text[:180],"url":link})
            if len(out)>=limit: break
        return out
    except Exception: return []

def competitive_intelligence(project):
    client=project.get("client",""); industry=project.get("industry",""); research=project.get("research") or {}
    domain=research.get("domain",""); goal=project.get("goal","")
    queries=[
      f'{client} competitors {industry}',
      f'{industry} competitors near {client}',
      f'{client} alternatives services'
    ]
    results=[]; seen=set()
    for q in queries:
        for item in _search(q,4):
            if item["url"] in seen or domain and domain in item["url"]: continue
            seen.add(item["url"]); results.append(item)
            if len(results)>=8: break
        if len(results)>=8: break
    return {
      "status":"Research Draft",
      "research_date":"generated at request time",
      "queries":queries,
      "candidates":results,
      "notes":"Candidate competitors require PMC review before being treated as confirmed competitors.",
      "evidence_rules":["Observed public information","Source URL retained","PMC review required","No unsupported market-share claims"]
    }
