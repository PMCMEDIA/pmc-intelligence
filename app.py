from flask import Flask,request,jsonify,render_template,session,redirect,url_for
from research_engine import research_url,discovery_questions
from strategy_engine import build_strategy
from storage import init_db,save,all_for,get
from competitive_engine import competitive_intelligence
from forecast_engine import forecast
from deck_engine import default_outline,build_pptx
from flask import send_file
import os, uuid, re
from urllib.parse import urlparse

app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","pmc-intelligence-development-key")
app.config.update(SESSION_COOKIE_HTTPONLY=True,SESSION_COOKIE_SAMESITE="Lax",MAX_CONTENT_LENGTH=2*1024*1024)
init_db()

def owner(): return session.get("owner")

def valid_email(email):
    return bool(re.fullmatch(r"[A-Za-z0-9._%+-]+@pmcne\.com",email or ""))

def clean_project(p):
    p=dict(p or {})
    p["client"]=(p.get("client") or "").strip()[:160]
    p["industry"]=(p.get("industry") or "Other").strip()[:100]
    p["goal"]=(p.get("goal") or "").strip()[:3000]
    p["budget"]=(p.get("budget") or "TBD").strip()[:100]
    p["url"]=(p.get("url") or "").strip()[:1000]
    return p

@app.get("/")
def home(): return render_template("index.html", logged_in=bool(owner()), login_error=request.args.get("error",""))

@app.post("/enter")
def enter():
    email=(request.form.get("email") or "").strip().lower()
    if not valid_email(email):
        return redirect(url_for("home", error="Please use your @pmcne.com email address."))
    session["owner"]=email
    return redirect(url_for("home"))

@app.get("/api/session")
def session_info(): return jsonify({"owner":owner()})

@app.post("/api/login")
def login():
    data=request.json or {}
    email=(data.get("email") or "").strip().lower()
    if not email: return jsonify({"error":"Enter your PMC email address."}),400
    if not valid_email(email):
        return jsonify({"error":"PMC Intelligence is currently limited to @pmcne.com accounts."}),403
    session["owner"]=email
    return jsonify({"owner":email})

@app.post("/api/logout")
def logout(): session.clear(); return jsonify({"ok":True})

@app.get("/logout")
def logout_page():
    session.clear()
    return redirect(url_for("home"))

@app.get("/api/projects")
def projects():
    if not owner(): return jsonify({"error":"Login required"}),401
    return jsonify(all_for(owner()))

@app.get("/api/projects/<pid>")
def project(pid):
    if not owner(): return jsonify({"error":"Login required"}),401
    p=get(owner(),pid)
    return jsonify(p) if p else (jsonify({"error":"Project not found"}),404)

@app.post("/api/projects")
def create():
    if not owner(): return jsonify({"error":"Login required"}),401
    p=clean_project(request.json or {})
    if not p["client"]: return jsonify({"error":"Client name is required"}),400
    research=research_url(p.get("url",""))
    result={"id":str(uuid.uuid4())[:8],**p,"research":research,
      "questions":discovery_questions(research,p.get("industry","Other")),
      "strategy":build_strategy(p,research),"status":"Strategy Draft"}
    save(owner(),result); return jsonify(result)

@app.post("/api/projects/refine")
def refine():
    if not owner(): return jsonify({"error":"Login required"}),401
    p=request.json or {}
    if not p.get("id") or not get(owner(),p.get("id")): return jsonify({"error":"Project not found"}),404
    research=p.get("research") or {}
    p["strategy"]=build_strategy(p,research); p["status"]="Strategy Updated"
    save(owner(),p); return jsonify({"project":p,"strategy":p["strategy"],"status":p["status"]})

@app.post("/api/projects/save")
def save_current():
    if not owner(): return jsonify({"error":"Login required"}),401
    p=request.json or {}
    if not p.get("id"): return jsonify({"error":"Project id is required"}),400
    existing=get(owner(),p["id"])
    if not existing: return jsonify({"error":"Project not found"}),404
    save(owner(),p); return jsonify({"ok":True,"project":p})

@app.post("/api/projects/<pid>/competitive")
def competitive(pid):
    if not owner(): return jsonify({"error":"Login required"}),401
    p=get(owner(),pid)
    if not p: return jsonify({"error":"Project not found"}),404
    p["competitive_intelligence"]=competitive_intelligence(p)
    p["status"]="Competitive Research Draft"
    save(owner(),p)
    return jsonify(p["competitive_intelligence"])

@app.post("/api/projects/<pid>/forecast")
def campaign_forecast(pid):
    if not owner(): return jsonify({"error":"Login required"}),401
    p=get(owner(),pid)
    if not p: return jsonify({"error":"Project not found"}),404
    p["campaign_outlook"]=forecast(p)
    p["status"]="Campaign Outlook Draft"
    save(owner(),p)
    return jsonify(p["campaign_outlook"])

@app.get("/api/projects/<pid>/deck-outline")
def deck_outline(pid):
    if not owner(): return jsonify({"error":"Login required"}),401
    p=get(owner(),pid)
    if not p: return jsonify({"error":"Project not found"}),404
    if not p.get("deck_outline"): p["deck_outline"]=default_outline(p); save(owner(),p)
    return jsonify(p["deck_outline"])

@app.post("/api/projects/<pid>/deck-outline")
def save_deck_outline(pid):
    if not owner(): return jsonify({"error":"Login required"}),401
    p=get(owner(),pid)
    if not p: return jsonify({"error":"Project not found"}),404
    p["deck_outline"]=(request.json or {}).get("slides",[]); p["status"]="Deck Outline Ready"; save(owner(),p)
    return jsonify({"ok":True,"slides":p["deck_outline"]})

@app.get("/api/projects/<pid>/deck.pptx")
def export_deck(pid):
    if not owner(): return jsonify({"error":"Login required"}),401
    p=get(owner(),pid)
    if not p: return jsonify({"error":"Project not found"}),404
    if not p.get("measurement_approved"): return jsonify({"error":"Measurement and success framework must be approved before export"}),400
    if not p.get("deck_outline"): p["deck_outline"]=default_outline(p); save(owner(),p)
    if not any(x.get("include",True) for x in p.get("deck_outline",[])): return jsonify({"error":"Deck must include at least one slide"}),400
    try: stream=build_pptx(p)
    except Exception as e:
        app.logger.exception("Deck export failed for %s",pid)
        return jsonify({"error":"PowerPoint export failed. Please review the deck and try again."}),500
    name="".join(ch if ch.isalnum() or ch in " -_" else "" for ch in p.get("client","Client")).strip()+"_PMC_Strategy.pptx"
    return send_file(stream,as_attachment=True,download_name=name,mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")

@app.get("/health")
def health():
    try:
        from storage import db
        with db() as conn: conn.execute("SELECT 1").fetchone()
        return {"ok":True,"version":"github-v7-production","database":"ok"}
    except Exception:
        return {"ok":False,"version":"github-v7-production","database":"error"},503

if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=True)
