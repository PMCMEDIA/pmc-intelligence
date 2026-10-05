from flask import Flask,request,jsonify,render_template
from research_engine import research_url,discovery_questions
from strategy_engine import build_strategy
import uuid

app=Flask(__name__)

@app.get("/")
def home(): return render_template("index.html")

@app.post("/api/projects")
def create():
    p=request.json or {}; research=research_url(p.get("url",""))
    return jsonify({"id":str(uuid.uuid4())[:8],**p,"research":research,
      "questions":discovery_questions(research,p.get("industry","Other")),
      "strategy":build_strategy(p,research),"status":"Strategy Draft"})

@app.post("/api/projects/refine")
def refine():
    p=request.json or {}
    research=p.get("research") or {}
    strategy=build_strategy(p,research)
    return jsonify({"strategy":strategy,"status":"Strategy Updated"})

@app.get("/health")
def health(): return {"ok":True,"version":"github-v2"}

if __name__=="__main__": app.run(host="0.0.0.0",port=5000,debug=True)
