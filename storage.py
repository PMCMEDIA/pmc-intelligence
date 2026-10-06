import os, sqlite3, json, uuid
from datetime import datetime, timezone
DB_PATH=os.getenv("DATABASE_PATH","/var/data/pmc_intelligence.db" if os.path.isdir("/var/data") else "pmc_intelligence.db")
def db():
    conn=sqlite3.connect(DB_PATH,timeout=20); conn.row_factory=sqlite3.Row; conn.execute("PRAGMA journal_mode=WAL"); conn.execute("PRAGMA busy_timeout=20000"); return conn
def init_db():
    with db() as c: c.execute("CREATE TABLE IF NOT EXISTS projects (id TEXT PRIMARY KEY, owner TEXT NOT NULL, client TEXT NOT NULL, data TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
def save(owner,p):
    now=datetime.now(timezone.utc).isoformat(); pid=p.get("id") or str(uuid.uuid4())[:8]; p["id"]=pid
    with db() as c:
        row=c.execute("SELECT owner FROM projects WHERE id=?",(pid,)).fetchone()
        if row:
            creator=row["owner"]; p["created_by"]=p.get("created_by") or creator
            c.execute("UPDATE projects SET client=?,data=?,status=?,updated_at=? WHERE id=?",(p.get("client") or "Untitled Client",json.dumps(p),p.get("status") or "Strategy Draft",now,pid))
        else:
            p["created_by"]=p.get("created_by") or owner
            c.execute("INSERT INTO projects VALUES (?,?,?,?,?,?,?)",(pid,owner,p.get("client") or "Untitled Client",json.dumps(p),p.get("status") or "Strategy Draft",now,now))
    return p
def all_for(owner=None):
    with db() as c: rows=c.execute("SELECT id,owner,client,status,updated_at FROM projects ORDER BY updated_at DESC").fetchall()
    return [dict(x) for x in rows]
def get(owner,pid):
    with db() as c: row=c.execute("SELECT data,owner FROM projects WHERE id=?",(pid,)).fetchone()
    if not row:return None
    p=json.loads(row["data"]);p["created_by"]=p.get("created_by") or row["owner"];return p
