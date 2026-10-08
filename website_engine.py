"""Bounded public website discovery for preliminary website proposals."""
from urllib.parse import urlparse, urljoin
from urllib.request import Request, build_opener, HTTPRedirectHandler
from urllib.error import URLError
import ipaddress, socket, re, xml.etree.ElementTree as ET
from datetime import datetime, timezone
from bs4 import BeautifulSoup

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs): return None

def safe_url(value):
    value=(value or "").strip()
    if not value.startswith(("http://","https://")): value="https://"+value
    p=urlparse(value)
    if p.scheme not in ("https","http") or not p.hostname or p.username or p.password or p.port not in (None,80,443):
        raise ValueError("Use a public HTTP(S) website URL.")
    host=p.hostname
    if host=="localhost" or host.endswith((".local",".internal")): raise ValueError("Private host is not allowed.")
    for entry in socket.getaddrinfo(host,None,type=socket.SOCK_STREAM):
        ip=ipaddress.ip_address(entry[4][0])
        if not ip.is_global: raise ValueError("Private or reserved address is not allowed.")
    return value

def fetch(url,limit=650000):
    url=safe_url(url)
    opener=build_opener(NoRedirect())
    with opener.open(Request(url,headers={"User-Agent":"PMC-Intelligence-Public-Site-Review/1.0","Accept":"text/html,application/xml,text/xml"}),timeout=9) as response:
        kind=response.headers.get("Content-Type","").lower()
        if not any(x in kind for x in ("html","xml","text/plain")): raise ValueError("Unsupported content type.")
        return response.read(limit).decode("utf-8","replace")

def sitemap_urls(site, max_urls=500):
    root=safe_url(site); parsed=urlparse(root); origin=parsed.scheme+"://"+parsed.netloc
    queue=[urljoin(origin,"/sitemap.xml"),urljoin(origin,"/sitemap_index.xml")]
    seen=set(); pages=[]; found=False
    while queue and len(seen)<12 and len(pages)<max_urls:
        loc=queue.pop(0)
        if loc in seen: continue
        seen.add(loc)
        try: raw=fetch(loc); xml=ET.fromstring(raw)
        except Exception: continue
        tag=xml.tag.rsplit("}",1)[-1].lower()
        if tag not in ("urlset","sitemapindex"): continue
        found=True
        for node in xml.iter():
            if node.tag.rsplit("}",1)[-1]!="loc" or not node.text: continue
            candidate=node.text.strip()
            try:
                p=urlparse(safe_url(candidate))
                if p.hostname!=parsed.hostname: continue
            except Exception: continue
            if tag=="sitemapindex":
                if len(queue)<24: queue.append(candidate)
            elif candidate not in pages: pages.append(candidate)
            if len(pages)>=max_urls: break
    return pages,found,len(pages)>=max_urls

FEATURES={
 "Appointment or booking":("appointment","book now","schedule online","book an appointment"),
 "Provider or team directory":("find a doctor","our providers","meet the team","provider directory"),
 "Location finder":("find a location","locations","get directions"),
 "Search":("search","site search"),
 "E-commerce":("add to cart","checkout","shop online"),
 "Careers":("careers","join our team","job openings"),
 "Forms and lead capture":("contact us","request a quote","request information"),
 "Events":("events","event calendar"),
 "Portfolio or case studies":("portfolio","case studies","our work"),
 "Customer portal":("patient portal","client portal","log in"),
}
INDUSTRY={
 "health": ["Provider or team directory","Location finder","Appointment or booking","Forms and lead capture"],
 "medical":["Provider or team directory","Location finder","Appointment or booking"],
 "restaurant":["Appointment or booking","Location finder","Events"],
 "construction":["Portfolio or case studies","Forms and lead capture","Careers"],
 "insurance":["Forms and lead capture","Provider or team directory"],
 "real estate":["Location finder","Forms and lead capture","Portfolio or case studies"],
 "education":["Events","Forms and lead capture","Search"],
}
def analyze(site,industry=""):
    site=safe_url(site)
    html=fetch(site)
    soup=BeautifulSoup(html,"html.parser")
    title=soup.title.get_text(" ",strip=True) if soup.title else ""
    links=[urljoin(site,a.get("href","")) for a in soup.select("a[href]")]
    own=urlparse(site).hostname
    internal=list(dict.fromkeys(u for u in links if urlparse(u).hostname==own and urlparse(u).scheme in ("http","https")))
    pages,found,truncated=sitemap_urls(site)
    if not pages: pages=internal[:100]
    sample=" ".join(soup.stripped_strings).lower()[:80000]
    observed=[{"feature":feature,"evidence":"Public homepage text","confidence":"possible"} for feature,terms in FEATURES.items() if any(t in sample for t in terms)]
    recommended=[]
    for key,features in INDUSTRY.items():
        if key in industry.lower(): recommended=features;break
    if not recommended: recommended=["Forms and lead capture","Search","Portfolio or case studies"]
    present={x["feature"] for x in observed}
    suggestions=[{"feature":f,"reason":"Common functionality to evaluate for this industry; validate against business goals.","priority":"Review","status":"Not confirmed on homepage"} for f in recommended if f not in present]
    return {"url":site,"scanned_at":datetime.now(timezone.utc).isoformat(),"title":title,
      "sitemap_found":found,"url_count":len(pages),"truncated":truncated,
      "page_count_note":"Sitemap URLs are not equivalent to billable development pages; review duplicates, posts, archives and retained pages.",
      "urls":pages[:200],"homepage_links":internal[:40],"observed_features":observed,
      "recommendations":suggestions,"limitations":["Homepage and public XML sitemaps only; not a full crawl.","Feature detection is indicative, not verified functionality.","Page counts require manual scope review."]}

def compare(client,competitor_urls,industry):
    rows=[]
    for url in competitor_urls[:5]:
        try:
            data=analyze(url,industry)
            rows.append({"url":data["url"],"title":data["title"],"url_count":data["url_count"],"observed_features":data["observed_features"],"status":"Public scan completed"})
        except Exception as exc: rows.append({"url":url,"status":"Scan unavailable","reason":str(exc)[:160]})
    return rows
