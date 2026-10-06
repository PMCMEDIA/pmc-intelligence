from flask import Flask,request,jsonify,render_template,session
from research_engine import research_url,discovery_questions
from strategy_engine import build_strategy
from storage import init_db,save,all_for,get
import os, uuid

app=Flask(__name__)
app.secret_key=os.getenv("SECRET_KEY","pmc-intelligence-development-key")
init_db()

def owner(): return session.get("owner")

@app.get("/")
def home(): return render_template("index.html")

@app.get("/api/session")
def session_info(): return jsonify({"owner":owner()})

@app.post("/api/login")
def login():
    data=request.json or {}
    email=(data.get("email") or "").strip().lower()
    if not email: return jsonify({"error":"Enter your PMC email address."}),400
    if not email.endswith("@pmcne.com"):
        return jsonify({"error":"PMC Intelligence is currently limited to @pmcne.com accounts."}),403
    session["owner"]=email
    return jsonify({"owner":email})

@app.post("/api/logout")
def logout(): session.clear(); return jsonify({"ok":True})

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
    p=request.json or {}; research=research_url(p.get("url",""))
    result={"id":str(uuid.uuid4())[:8],**p,"research":research,
      "questions":discovery_questions(research,p.get("industry","Other")),
      "strategy":build_strategy(p,research),"status":"Strategy Draft"}
    save(owner(),result); return jsonify(result)

@app.post("/api/projects/refine")
def refine():
    if not owner(): return jsonify({"error":"Login required"}),401
    p=request.json or {}; research=p.get("research") or {}
    p["strategy"]=build_strategy(p,research); p["status"]="Strategy Updated"
    save(owner(),p); return jsonify({"project":p,"strategy":p["strategy"],"status":p["status"]})

@app.post("/api/projects/save")
def save_current():
    if not owner(): return jsonify({"error":"Login required"}),401
    p=request.json or {}; save(owner(),p); return jsonify({"ok":True,"project":p})

@app.get("/health")
def health(): return {"ok":True,"version":"github-v4-pmc-login"}

if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=True)
