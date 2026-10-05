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

def discovery_questions(research,industry):
    q=["What business outcome must this strategy influence?",
       "Which services, products, locations or profit centers are highest priority?",
       "What markets should PMC prioritize or avoid?",
       "What investment range is realistic?",
       "Which channels are active today and what performance is known?",
       "What counts as a qualified conversion?",
       "What capacity, compliance, seasonality or operational constraints matter?"]
    if not research.get("ok"): q.insert(0,"What are the client's core offerings and differentiators?")
    if industry=="Healthcare": q.append("Which clinical/provider content requires client or clinical approval?")
    if industry=="Restaurant / Hospitality": q.append("Which locations, dayparts, concepts and private-event opportunities are highest priority?")
    return q
