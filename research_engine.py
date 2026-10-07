from urllib.parse import urlparse
import urllib.request, re
from bs4 import BeautifulSoup

def research_url(url):
    if not url:
        return {"ok": False, "error": "No URL supplied"}
    if not url.startswith(("http://","https://")):
        url="https://"+url
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 PMC-Intelligence/1.0"})
        with urllib.request.urlopen(req,timeout=12) as r:
            html=r.read(750000).decode("utf-8","ignore")
        soup=BeautifulSoup(html,"html.parser")
        for x in soup(["script","style","noscript"]): x.decompose()
        title=soup.title.string.strip() if soup.title and soup.title.string else ""
        meta=soup.find("meta",attrs={"name":re.compile("^description$",re.I)})
        return {"ok":True,"url":url,"domain":urlparse(url).netloc,"title":title,
          "description":meta.get("content","").strip() if meta else "",
          "h1":[x.get_text(" ",strip=True) for x in soup.find_all("h1")][:8],
          "h2":[x.get_text(" ",strip=True) for x in soup.find_all("h2")][:20],
          "text_sample":" ".join(soup.stripped_strings)[:10000]}
    except Exception as e:
        return {"ok":False,"url":url,"error":str(e)}

def discovery_questions(research,industry,project=None):
    p=project or {}; context=" ".join([str(p.get("goal","")),str(p.get("budget","")),str(p.get("strategy_context",""))]).lower()
    gaps=[]
    def missing(terms): return not any(t in context for t in terms)
    if missing(["budget","investment","$"]) and str(p.get("budget","TBD")).upper()=="TBD":
        gaps.append({"question":"What investment range should the strategy plan around?","reason":"Needed to build an actionable investment model.","required":False})
    if missing(["priority","service line","product","location","profit center"]):
        gaps.append({"question":"Are there specific services, products, locations or profit centers that must be prioritized?","reason":"Only needed if priorities are not already clear from the supplied context or public research.","required":False})
    if missing(["capacity","availability","constraint","season"]):
        gaps.append({"question":"Are there capacity, seasonality or operational constraints that should limit demand generation?","reason":"This can materially change media intensity and timing and usually is not public.","required":False})
    gaps.append({"question":"Do we have a defensible lead/customer value or close rate for ROI modeling?","reason":"Optional. Needed only if the client wants revenue, ROAS or ROI projections.","required":False})
    return gaps[:4]
