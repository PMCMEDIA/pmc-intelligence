import os, sqlite3, json, uuid
from datetime import datetime, timezone

DB_PATH=os.getenv("DATABASE_PATH","/var/data/pmc_intelligence.db" if os.path.isdir("/var/data") else "pmc_intelligence.db")

def db():
    conn=sqlite3.connect(DB_PATH); conn.row_factory=sqlite3.Row; return conn

def init_db():
    with db() as c:
        c.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, owner TEXT NOT NULL, client TEXT NOT NULL, data TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")

def save(owner,p):
    now=datetime.now(timezone.utc).isoformat(); pid=p.get("id") or str(uuid.uuid4())[:8]; p["id"]=pid
    with db() as c:
        old=c.execute("SELECT id FROM projects WHERE id=? AND owner=?",(pid,owner)).fetchone()
        vals=(p.get("client") or "Untitled Client",json.dumps(p),p.get("status") or "Strategy Draft",now,pid,owner)
        if old: c.execute("UPDATE projects SET client=?,data=?,status=?,updated_at=? WHERE id=? AND owner=?",vals)
        else: c.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?)",(pid,owner,p.get("client") or "Untitled Client",json.dumps(p),p.get("status") or "Strategy Draft",now,now))
    return p

def all_for(owner):
    with db() as c: rows=c.execute("SELECT id,client,status,updated_at FROM projects WHERE owner=? ORDER BY updated_at DESC",(owner,)).fetchall()
    return [dict(x) for x in rows]

def get(owner,pid):
    with db() as c: row=c.execute("SELECT data FROM projects WHERE id=? AND owner=?",(pid,owner)).fetchone()
    return json.loads(row["data"]) if row else None
