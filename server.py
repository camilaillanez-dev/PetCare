"""PetCare local backend: SQLite + JSON API, standard library only."""
from __future__ import annotations
import json
import hashlib
import hmac
import os
import re
import secrets
import sqlite3
import unicodedata
from contextlib import contextmanager
from datetime import date, datetime, timedelta
from http.cookies import SimpleCookie
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DB = DATA / "petcare.sqlite3"
HOST = "127.0.0.1"
PORT = int(os.environ.get("PETCARE_PORT", "8765"))
MAX_BODY = 64 * 1024


def connect():
    db = sqlite3.connect(DB, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys=ON")
    return db


def ensure_column(db, table, column, definition):
    existing = {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
    if column not in existing:
        db.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def password_digest(password, salt=None):
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return f"{salt.hex()}${digest.hex()}"


def password_matches(password, stored):
    try:
        salt_hex, expected = stored.split("$", 1)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 260_000).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def ensure_demo_accounts(db):
    now = datetime.now().isoformat(timespec="seconds")
    for patient in db.execute("SELECT DISTINCT owner,phone FROM patients WHERE phone!=''").fetchall():
        owner = db.execute("SELECT id FROM owners WHERE phone=?", (patient["phone"],)).fetchone()
        if not owner:
            slug = unicodedata.normalize("NFKD", patient["owner"]).encode("ascii", "ignore").decode().lower()
            slug = re.sub(r"[^a-z0-9]+", ".", slug).strip(".")
            email = f"{slug}@petcare.demo"
            db.execute("INSERT OR IGNORE INTO owners(full_name,email,phone,password_hash,created_at) VALUES(?,?,?,?,?)", (patient["owner"],email,patient["phone"],password_digest("bienvenida2026"),now))
            owner = db.execute("SELECT id FROM owners WHERE phone=?", (patient["phone"],)).fetchone()
        db.execute("UPDATE patients SET owner_id=? WHERE phone=? AND owner_id IS NULL", (owner["id"],patient["phone"]))
    if db.execute("SELECT COUNT(*) FROM medical_records").fetchone()[0] == 0:
        for row in db.execute("SELECT id,name FROM patients ORDER BY id").fetchall():
            visit = (date.today() - timedelta(days=18 + row["id"] * 3)).isoformat()
            db.execute("INSERT INTO medical_records(patient_id,visit_date,title,professional,summary,record_type,visible_to_owner) VALUES(?,?,?,?,?,?,1)", (row["id"],visit,"Consulta de seguimiento","Equipo veterinario","Registro de demostración. La clínica puede incorporar aquí notas revisadas y resultados compartidos con el tutor.","Consulta"))
    db.execute("DELETE FROM auth_sessions WHERE expires_at < ?", (datetime.now().isoformat(timespec="seconds"),))


@contextmanager
def database():
    db = connect()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    DATA.mkdir(exist_ok=True)
    with database() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.executescript("""
        CREATE TABLE IF NOT EXISTS owners (
          id INTEGER PRIMARY KEY, full_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE,
          phone TEXT NOT NULL UNIQUE, password_hash TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS patients (
          id INTEGER PRIMARY KEY, name TEXT NOT NULL, species TEXT NOT NULL,
          owner TEXT NOT NULL, phone TEXT NOT NULL DEFAULT '', age TEXT NOT NULL DEFAULT '',
          last_visit TEXT NOT NULL DEFAULT '', next_event TEXT NOT NULL DEFAULT 'Sin turnos',
          icon TEXT NOT NULL DEFAULT '🐾', color TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'Al día', created_at TEXT NOT NULL,
          owner_id INTEGER REFERENCES owners(id) ON DELETE SET NULL
        );
        CREATE TABLE IF NOT EXISTS appointments (
          id INTEGER PRIMARY KEY, appt_date TEXT NOT NULL, time TEXT NOT NULL,
          patient_id INTEGER REFERENCES patients(id) ON DELETE SET NULL,
          patient_name TEXT NOT NULL, kind TEXT NOT NULL, doctor TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'Por confirmar', icon TEXT NOT NULL DEFAULT '🐾',
          color TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
          duration_min INTEGER NOT NULL DEFAULT 30, priority TEXT NOT NULL DEFAULT 'Normal',
          source TEXT NOT NULL DEFAULT 'Clínica'
        );
        CREATE TABLE IF NOT EXISTS conversations (
          id INTEGER PRIMARY KEY, owner TEXT NOT NULL, pet_label TEXT NOT NULL,
          icon TEXT NOT NULL DEFAULT '👤', preview TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'Consulta', created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS messages (
          id INTEGER PRIMARY KEY, conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
          text TEXT NOT NULL, time TEXT NOT NULL, is_mine INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS reminders (
          id INTEGER PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
          sent INTEGER NOT NULL DEFAULT 0, response_rate TEXT NOT NULL DEFAULT '0%', active INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS soap_notes (
          id INTEGER PRIMARY KEY, patient_name TEXT NOT NULL, subjective TEXT NOT NULL DEFAULT '',
          objective TEXT NOT NULL DEFAULT '', assessment TEXT NOT NULL DEFAULT '', plan TEXT NOT NULL DEFAULT '',
          status TEXT NOT NULL DEFAULT 'Borrador', updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS medical_records (
          id INTEGER PRIMARY KEY, patient_id INTEGER NOT NULL REFERENCES patients(id) ON DELETE CASCADE,
          visit_date TEXT NOT NULL, title TEXT NOT NULL, professional TEXT NOT NULL,
          summary TEXT NOT NULL, record_type TEXT NOT NULL DEFAULT 'Consulta', visible_to_owner INTEGER NOT NULL DEFAULT 1
        );
        CREATE TABLE IF NOT EXISTS auth_sessions (
          token TEXT PRIMARY KEY, owner_id INTEGER NOT NULL REFERENCES owners(id) ON DELETE CASCADE,
          expires_at TEXT NOT NULL, created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appt_date, time);
        CREATE INDEX IF NOT EXISTS idx_messages_conversation ON messages(conversation_id, id);
        CREATE INDEX IF NOT EXISTS idx_medical_records_patient ON medical_records(patient_id, visit_date DESC);
        """)
        ensure_column(db, "patients", "owner_id", "INTEGER REFERENCES owners(id) ON DELETE SET NULL")
        ensure_column(db, "appointments", "duration_min", "INTEGER NOT NULL DEFAULT 30")
        ensure_column(db, "appointments", "priority", "TEXT NOT NULL DEFAULT 'Normal'")
        ensure_column(db, "appointments", "source", "TEXT NOT NULL DEFAULT 'Clínica'")
        db.execute("CREATE INDEX IF NOT EXISTS idx_patients_owner ON patients(owner_id)")
        db.execute("UPDATE appointments SET duration_min=15 WHERE kind LIKE 'Vacun%' AND duration_min=30")
        db.execute("UPDATE appointments SET duration_min=20 WHERE kind LIKE 'Control%' AND duration_min=30")
        if db.execute("SELECT COUNT(*) FROM patients").fetchone()[0] == 0:
            seed(db)
        ensure_demo_accounts(db)


def seed(db):
    today = date.today()
    now = datetime.now().isoformat(timespec="seconds")
    pets = [
      ("Mia", "Gata · Europea", "Carlos Ruiz", "11 5555-0134", "3 años", "20 nov", "Vacuna triple · 28 nov", "🐱", "c2", "Al día"),
      ("Toto", "Perro · Caniche", "Lucía Gómez", "11 5555-0198", "7 años", "22 nov", "Control · 26 nov", "🐶", "", "Control próximo"),
      ("Nube", "Gata · Mestiza", "Marina Díaz", "11 5555-0122", "2 años", "18 nov", "Sin turnos", "🐈", "c3", "Al día"),
      ("Simón", "Perro · Labrador", "Pablo Costa", "11 5555-0165", "5 años", "15 nov", "Vacuna · 3 dic", "🐕", "c4", "Al día"),
      ("Lola", "Coneja · Enana", "Sofía Rey", "11 5555-0146", "1 año", "10 nov", "Control · 2 dic", "🐰", "c2", "Al día"),
    ]
    db.executemany("INSERT INTO patients(name,species,owner,phone,age,last_visit,next_event,icon,color,status,created_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)", [(*p, now) for p in pets])
    ids = {r["name"]: r["id"] for r in db.execute("SELECT id,name FROM patients")}
    appointments = [("09:00","Toto","Control anual","Dra. Martínez","Confirmado"),("10:30","Mia","Vacunación triple","Dr. Acosta","En recepción"),("11:15","Nube","Consulta general","Dra. Martínez","Confirmado"),("12:00","Simón","Control postoperatorio","Dr. Acosta","Por confirmar")]
    db.executemany("INSERT INTO appointments(appt_date,time,patient_id,patient_name,kind,doctor,status,icon,color,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)", [(today.isoformat(),t,ids[n],n,k,d,s,db.execute("SELECT icon FROM patients WHERE id=?",(ids[n],)).fetchone()[0],db.execute("SELECT color FROM patients WHERE id=?",(ids[n],)).fetchone()[0],now) for t,n,k,d,s in appointments])
    conversations = [
      ("Lucía Gómez","Toto · Caniche","👩🏻","Está un poco decaído desde ayer","Urgente"),
      ("Carlos Ruiz","Mia · Gata","👨🏻","Quería consultar por la vacuna anual","Consulta"),
      ("Marina Díaz","Nube · Gata","👩🏼","¿Me confirman el turno del jueves?","Turno"),
    ]
    db.executemany("INSERT INTO conversations(owner,pet_label,icon,preview,status,created_at) VALUES(?,?,?,?,?,?)", [(*c,now) for c in conversations])
    ids_chat = [r["id"] for r in db.execute("SELECT id FROM conversations ORDER BY id")]
    messages = [
      [("Hola, Toto está un poco decaído desde ayer.","09:34",0),("Gracias por contarnos, Lucía. ¿Notaste dificultad para respirar, desmayo o vómitos repetidos?","09:36",1),("No, solo está más quieto y comió menos.","09:38",0)],
      [("Hola, quería consultar por la vacuna anual de Mia.","09:12",0),("¡Hola Carlos! Podemos ayudarte a coordinar un turno para su refuerzo.","09:14",1)],
      [("¿Me confirman el turno del jueves?","08:20",0),("Sí, Marina. Nube tiene turno el jueves a las 16:30.","08:23",1)],
    ]
    for cid, msgs in zip(ids_chat, messages):
        db.executemany("INSERT INTO messages(conversation_id,text,time,is_mine,created_at) VALUES(?,?,?,?,?)", [(cid,*m,now) for m in msgs])
    db.executemany("INSERT INTO reminders(title,description,sent,response_rate,active) VALUES(?,?,?,?,?)", [
      ("Confirmación de turnos","Enviar recordatorio 48 h y 24 h antes del turno.",94,"86%",1),
      ("Vacunas y medicina preventiva","Aviso al tutor cuando se acerca una fecha de refuerzo.",38,"71%",1),
      ("Seguimiento postconsulta","Consulta breve de bienestar después de una visita.",22,"68%",0),
    ])
    db.execute("INSERT INTO soap_notes(patient_name,subjective,objective,assessment,plan,status,updated_at) VALUES(?,?,?,?,?,?,?)", ("Toto","Menor apetito desde hace 2 días. Ingesta de agua conservada. Sin vómitos. Actividad habitual.","Temperatura: 38.7 °C. Mucosas rosadas. Hidratación adecuada. Auscultación sin hallazgos relevantes.","Disminución del apetito reportada. Requiere valoración clínica por el profesional tratante.","Completar evaluación, definir conducta y controles según criterio veterinario.","Borrador",now))


def as_pet(r):
    return dict(r)


def bootstrap():
    with database() as db:
        pets = [{**as_pet(r), "last": r["last_visit"], "next": r["next_event"]} for r in db.execute("SELECT * FROM patients ORDER BY name COLLATE NOCASE")]
        appts = [[r["id"],r["appt_date"],r["time"],r["patient_name"],r["kind"],r["doctor"],r["status"],r["icon"],r["color"],r["duration_min"],r["priority"],r["source"]] for r in db.execute("SELECT * FROM appointments WHERE appt_date>=? AND appt_date<=? ORDER BY CASE WHEN priority='Emergencia' THEN 0 ELSE 1 END,appt_date,time",(date.today().isoformat(),(date.today()+timedelta(days=30)).isoformat()))]
        today_appts = [[r["time"],r["patient_name"],r["kind"],r["doctor"],r["status"],r["icon"],r["color"],r["duration_min"],r["priority"]] for r in db.execute("SELECT * FROM appointments WHERE appt_date=? ORDER BY CASE WHEN priority='Emergencia' THEN 0 ELSE 1 END,time",(date.today().isoformat(),))]
        chats = []
        for c in db.execute("SELECT * FROM conversations ORDER BY CASE WHEN status='Urgente' THEN 0 ELSE 1 END,id DESC"):
            msgs = [[m["text"],m["time"],bool(m["is_mine"])] for m in db.execute("SELECT * FROM messages WHERE conversation_id=? ORDER BY id",(c["id"],))]
            chats.append({"id":c["id"],"name":c["owner"],"pet":c["pet_label"],"icon":c["icon"],"preview":c["preview"],"time":"reciente","status":c["status"],"messages":msgs})
        reminders = [dict(r) for r in db.execute("SELECT * FROM reminders ORDER BY id")]
        notes = [dict(r) for r in db.execute("SELECT * FROM soap_notes ORDER BY updated_at DESC")]
        metrics = {
          "today_appointments": db.execute("SELECT COUNT(*) FROM appointments WHERE appt_date=?",(date.today().isoformat(),)).fetchone()[0],
          "patients": db.execute("SELECT COUNT(*) FROM patients").fetchone()[0],
          "open_conversations": db.execute("SELECT COUNT(*) FROM conversations WHERE status!='Cerrada'").fetchone()[0],
          "vaccines_due": db.execute("SELECT COUNT(*) FROM patients WHERE next_event LIKE '%Vacuna%'").fetchone()[0],
        }
    return {"pets":pets,"appointments":appts,"today_appointments":today_appts,"chats":chats,"reminders":reminders,"notes":notes,"date":date.today().isoformat(),"metrics":metrics}


def clean_text(value, field, required=False, limit=160):
    if not isinstance(value,str):
        raise ValueError(f"{field} debe ser texto.")
    value = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", value).strip()
    value = value.replace("<", "").replace(">", "")
    if required and not value:
        raise ValueError(f"{field} es obligatorio.")
    if len(value)>limit:
        raise ValueError(f"{field} supera el máximo de {limit} caracteres.")
    return value


VISIT_DURATIONS = {
    "Consulta general": 30,
    "Vacunación": 15,
    "Control": 20,
    "Teleconsulta": 25,
    "Estudio diagnóstico": 45,
    "Procedimiento": 60,
    "Emergencia": 0,
}


def duration_for(kind):
    if kind not in VISIT_DURATIONS:
        raise ValueError("Seleccioná un tipo de consulta válido.")
    return VISIT_DURATIONS[kind]


def slot_available(db, appt_date, appt_time, duration):
    day = datetime.strptime(appt_date, "%Y-%m-%d").date()
    start = datetime.strptime(appt_time, "%H:%M")
    start_min = start.hour * 60 + start.minute
    if day.weekday() > 5 or start_min < 540 or start_min + duration > 1080:
        return False
    if day == date.today() and start_min <= datetime.now().hour * 60 + datetime.now().minute:
        return False
    for row in db.execute("SELECT time,duration_min,priority,status FROM appointments WHERE appt_date=? AND status NOT IN ('Cancelado','Rechazado')", (appt_date,)):
        if row["priority"] == "Emergencia" or row["time"] == "INMEDIATO":
            continue
        existing = datetime.strptime(row["time"], "%H:%M")
        a = existing.hour * 60 + existing.minute
        b = a + max(1, row["duration_min"])
        if start_min < b and a < start_min + duration:
            return False
    return True


def portal_data(owner_id):
    with database() as db:
        owner = db.execute("SELECT id,full_name,email,phone FROM owners WHERE id=?", (owner_id,)).fetchone()
        pets = [dict(r) for r in db.execute("SELECT id,name,species,age,icon,status FROM patients WHERE owner_id=? ORDER BY name", (owner_id,))]
        for pet in pets:
            pet["history"] = [dict(r) for r in db.execute("SELECT id,visit_date,title,professional,summary,record_type FROM medical_records WHERE patient_id=? AND visible_to_owner=1 ORDER BY visit_date DESC", (pet["id"],))]
            pet["appointments"] = [dict(r) for r in db.execute("SELECT id,appt_date,time,kind,status,duration_min,priority FROM appointments WHERE patient_id=? AND appt_date>=? AND status NOT IN ('Cancelado','Rechazado') ORDER BY appt_date,time LIMIT 8", (pet["id"],date.today().isoformat()))]
    return {"owner":dict(owner),"pets":pets}


class Handler(SimpleHTTPRequestHandler):
    server_version = "PetCare/1.0"
    sys_version = ""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,directory=str(BASE),**kwargs)

    def guess_type(self,path):
        if path.lower().endswith(".webmanifest"): return "application/manifest+json"
        return super().guess_type(path)

    def end_headers(self):
        self.send_header("X-Content-Type-Options","nosniff")
        self.send_header("Referrer-Policy","same-origin")
        self.send_header("X-Frame-Options","DENY")
        self.send_header("Content-Security-Policy","default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'; font-src 'self' data:")
        self.send_header("Cache-Control","no-store")
        super().end_headers()

    def log_message(self, fmt, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")

    def _json(self, code, payload, extra_headers=()):
        data=json.dumps(payload,ensure_ascii=False).encode("utf-8")
        self.send_response(code); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(data)))
        for key,value in extra_headers: self.send_header(key,value)
        self.end_headers(); self.wfile.write(data)

    def _session_owner(self):
        cookie=SimpleCookie(); cookie.load(self.headers.get("Cookie",""))
        morsel=cookie.get("petcare_session")
        if not morsel: return None
        with database() as db:
            row=db.execute("SELECT o.id,o.full_name,o.email,o.phone FROM auth_sessions s JOIN owners o ON o.id=s.owner_id WHERE s.token=? AND s.expires_at>?",(morsel.value,datetime.now().isoformat(timespec="seconds"))).fetchone()
        return dict(row) if row else None

    def _need_owner(self):
        owner=self._session_owner()
        if not owner: self._json(401,{"error":"Iniciá sesión para acceder al portal."})
        return owner

    def _body(self):
        n=int(self.headers.get("Content-Length","0"))
        if n<0 or n>MAX_BODY: raise ValueError("Solicitud demasiado grande.")
        raw=self.rfile.read(n)
        body=json.loads(raw.decode("utf-8")) if raw else {}
        if not isinstance(body,dict): raise ValueError("El cuerpo debe ser un objeto JSON.")
        origin=self.headers.get("Origin")
        host=self.headers.get("Host",f"{HOST}:{PORT}")
        if origin and urlparse(origin).netloc != host: raise PermissionError("Origen no permitido.")
        return body

    def do_GET(self):
        path=urlparse(self.path).path
        if path=="/api/health": return self._json(200,{"ok":True,"service":"PetCare","storage":"SQLite"})
        if path=="/api/bootstrap": return self._json(200,bootstrap())
        if path=="/api/auth/me":
            owner=self._session_owner()
            return self._json(200,{"authenticated":bool(owner),"owner":owner})
        if path=="/api/portal":
            owner=self._need_owner()
            if not owner: return
            return self._json(200,portal_data(owner["id"]))
        if path=="/api/availability":
            params=parse_qs(urlparse(self.path).query)
            appt_date=params.get("date",[""])[0]; kind=unquote(params.get("kind",["Consulta general"])[0])
            try:
                duration=duration_for(kind)
                if "duration" in params and kind!="Emergencia": duration=int(params["duration"][0])
                if kind!="Emergencia" and not 5<=duration<=180: raise ValueError("La duración debe estar entre 5 y 180 minutos.")
                datetime.strptime(appt_date,"%Y-%m-%d")
                with database() as db:
                    slots=[f"{hour:02d}:{minute:02d}" for hour in range(9,18) for minute in (0,15,30,45) if slot_available(db,appt_date,f"{hour:02d}:{minute:02d}",duration)]
                return self._json(200,{"date":appt_date,"duration_min":duration,"slots":slots})
            except ValueError as e: return self._json(400,{"error":str(e)})
        if path=="/api/patients":
            with database() as db: return self._json(200,[dict(r) for r in db.execute("SELECT * FROM patients ORDER BY name COLLATE NOCASE")])
        if path=="/api/appointments":
            with database() as db: return self._json(200,[dict(r) for r in db.execute("SELECT * FROM appointments ORDER BY appt_date,time")])
        if path=="/api/notes":
            with database() as db: return self._json(200,[dict(r) for r in db.execute("SELECT * FROM soap_notes ORDER BY updated_at DESC")])
        if path.startswith("/api/"): return self._json(404,{"error":"Ruta no encontrada."})
        return super().do_GET()

    def do_POST(self):
        path=urlparse(self.path).path
        try:
            body=self._body()
            if path=="/api/auth/login":
                email=clean_text(body.get("email",""),"Correo",True,180).lower()
                password=body.get("password","")
                if not isinstance(password,str) or len(password)>128: return self._json(400,{"error":"Revisá el correo y la contraseña."})
                with database() as db:
                    owner=db.execute("SELECT id,full_name,email,phone,password_hash FROM owners WHERE email=?",(email,)).fetchone()
                    if not owner or not password_matches(password,owner["password_hash"]): return self._json(401,{"error":"El correo o la contraseña no coinciden."})
                    token=secrets.token_urlsafe(32); now=datetime.now(); expires=(now+timedelta(hours=12)).isoformat(timespec="seconds")
                    db.execute("INSERT INTO auth_sessions(token,owner_id,expires_at,created_at) VALUES(?,?,?,?)",(token,owner["id"],expires,now.isoformat(timespec="seconds")))
                safe_owner={k:owner[k] for k in ("id","full_name","email","phone")}
                return self._json(200,{"owner":safe_owner},[("Set-Cookie",f"petcare_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200")])
            if path=="/api/auth/register":
                full_name=clean_text(body.get("full_name"),"Nombre",True,100); email=clean_text(body.get("email"),"Correo",True,180).lower(); phone=clean_text(body.get("phone"),"Teléfono",True,32); password=body.get("password","")
                if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+",email): return self._json(400,{"error":"Ingresá un correo válido."})
                if not isinstance(password,str) or len(password)<10 or len(password)>128: return self._json(400,{"error":"La contraseña debe tener entre 10 y 128 caracteres."})
                now=datetime.now()
                with database() as db:
                    cur=db.execute("INSERT INTO owners(full_name,email,phone,password_hash,created_at) VALUES(?,?,?,?,?)",(full_name,email,phone,password_digest(password),now.isoformat(timespec="seconds")))
                    db.execute("UPDATE patients SET owner_id=? WHERE phone=? AND owner_id IS NULL",(cur.lastrowid,phone))
                    token=secrets.token_urlsafe(32); expires=(now+timedelta(hours=12)).isoformat(timespec="seconds")
                    db.execute("INSERT INTO auth_sessions(token,owner_id,expires_at,created_at) VALUES(?,?,?,?)",(token,cur.lastrowid,expires,now.isoformat(timespec="seconds")))
                return self._json(201,{"owner":{"id":cur.lastrowid,"full_name":full_name,"email":email,"phone":phone}},[("Set-Cookie",f"petcare_session={token}; HttpOnly; SameSite=Strict; Path=/; Max-Age=43200")])
            if path=="/api/auth/logout":
                cookie=SimpleCookie(); cookie.load(self.headers.get("Cookie","")); morsel=cookie.get("petcare_session")
                if morsel:
                    with database() as db: db.execute("DELETE FROM auth_sessions WHERE token=?",(morsel.value,))
                return self._json(200,{"ok":True},[("Set-Cookie","petcare_session=; HttpOnly; SameSite=Strict; Path=/; Max-Age=0")])
            if path=="/api/portal/pets":
                owner=self._need_owner()
                if not owner: return
                name=clean_text(body.get("name"),"Nombre de la mascota",True,80); species=clean_text(body.get("species"),"Especie",True,80); age=clean_text(body.get("age",""),"Edad",False,40); icon=clean_text(body.get("icon","🐾"),"Ícono",False,8)
                with database() as db:
                    cur=db.execute("INSERT INTO patients(name,species,owner,phone,age,icon,status,created_at,owner_id) VALUES(?,?,?,?,?,?,?, ?,?)",(name,species,owner["full_name"],owner["phone"],age,icon,"Al día",datetime.now().isoformat(timespec="seconds"),owner["id"]))
                    pet=db.execute("SELECT id,name,species,age,icon,status FROM patients WHERE id=?",(cur.lastrowid,)).fetchone()
                return self._json(201,{**dict(pet),"history":[],"appointments":[]})
            if path=="/api/portal/appointments":
                owner=self._need_owner()
                if not owner: return
                patient_id=int(body.get("patient_id",0)); kind=clean_text(body.get("kind"),"Tipo de consulta",True,80); reason=clean_text(body.get("reason",""),"Motivo",False,500)
                duration=duration_for(kind)
                with database() as db:
                    patient=db.execute("SELECT * FROM patients WHERE id=? AND owner_id=?",(patient_id,owner["id"])).fetchone()
                    if not patient: return self._json(404,{"error":"No encontramos esa mascota en tu cuenta."})
                    if kind=="Emergencia":
                        now=datetime.now(); today=now.date().isoformat(); text=f"Solicitud de emergencia para {patient['name']}. {reason}".strip()
                        db.execute("BEGIN IMMEDIATE")
                        db.execute("INSERT INTO appointments(appt_date,time,patient_id,patient_name,kind,doctor,status,icon,color,created_at,duration_min,priority,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(today,"INMEDIATO",patient["id"],patient["name"],kind,"Equipo de guardia","Prioridad inmediata",patient["icon"],patient["color"],now.isoformat(timespec="seconds"),0,"Emergencia","Portal"))
                        cur=db.execute("INSERT INTO conversations(owner,pet_label,icon,preview,status,created_at) VALUES(?,?,?,?,?,?)",(owner["full_name"],f"{patient['name']} · {patient['species']}","👤",text[:180],"Urgente",now.isoformat(timespec="seconds")))
                        db.execute("INSERT INTO messages(conversation_id,text,time,is_mine,created_at) VALUES(?,?,?,?,?)",(cur.lastrowid,text,now.strftime("%H:%M"),0,now.isoformat(timespec="seconds")))
                        return self._json(202,{"priority":"Emergencia","message":"No esperes una confirmación de turno. Llamá ahora a la clínica o acudí a una guardia veterinaria."})
                    appt_date=clean_text(body.get("appt_date"),"Fecha",True,10); appt_time=clean_text(body.get("time"),"Horario",True,5)
                    datetime.strptime(appt_date,"%Y-%m-%d"); datetime.strptime(appt_time,"%H:%M")
                    db.execute("BEGIN IMMEDIATE")
                    if not slot_available(db,appt_date,appt_time,duration): return self._json(409,{"error":"Ese horario ya no está disponible. Elegí otro turno."})
                    cur=db.execute("INSERT INTO appointments(appt_date,time,patient_id,patient_name,kind,doctor,status,icon,color,created_at,duration_min,priority,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(appt_date,appt_time,patient["id"],patient["name"],kind,"A asignar","Solicitud recibida",patient["icon"],patient["color"],datetime.now().isoformat(timespec="seconds"),duration,"Normal","Portal"))
                    row=db.execute("SELECT id,appt_date,time,kind,status,duration_min FROM appointments WHERE id=?",(cur.lastrowid,)).fetchone()
                return self._json(201,dict(row))
            if path=="/api/patients":
                name=clean_text(body.get("name"),"Nombre",True,80); species=clean_text(body.get("species"),"Especie",True,80); owner=clean_text(body.get("owner"),"Tutor",True,100)
                phone=clean_text(body.get("phone",""),"Teléfono",False,32); age=clean_text(body.get("age",""),"Edad",False,40); icon=clean_text(body.get("icon","🐾"),"Ícono",False,8)
                now=datetime.now().isoformat(timespec="seconds")
                with database() as db:
                    linked=db.execute("SELECT id FROM owners WHERE phone=?",(phone,)).fetchone() if phone else None
                    cur=db.execute("INSERT INTO patients(name,species,owner,phone,age,icon,created_at,owner_id) VALUES(?,?,?,?,?,?,?,?)",(name,species,owner,phone,age,icon,now,linked["id"] if linked else None)); row=db.execute("SELECT * FROM patients WHERE id=?",(cur.lastrowid,)).fetchone()
                return self._json(201,dict(row))
            if path=="/api/appointments":
                kind=clean_text(body.get("kind"),"Tipo de turno",True,100); doctor=clean_text(body.get("doctor"),"Profesional",True,100)
                reason=clean_text(body.get("reason",""),"Motivo",False,500)
                patient_id=int(body.get("patient_id",0))
                duration=duration_for(kind); emergency=kind=="Emergencia"
                if not emergency and "duration_min" in body: duration=int(body["duration_min"])
                if not emergency and not 5<=duration<=180: raise ValueError("La duración debe estar entre 5 y 180 minutos.")
                appt_date=date.today().isoformat() if emergency else clean_text(body.get("appt_date"),"Fecha",True,10)
                time="INMEDIATO" if emergency else clean_text(body.get("time"),"Horario",True,5)
                datetime.strptime(appt_date,"%Y-%m-%d")
                if not emergency: datetime.strptime(time,"%H:%M")
                with database() as db:
                    p=db.execute("SELECT * FROM patients WHERE id=?",(patient_id,)).fetchone()
                    if not p: raise ValueError("No se encontró el paciente seleccionado.")
                    pname=p["name"]
                    db.execute("BEGIN IMMEDIATE")
                    if not emergency and not slot_available(db,appt_date,time,duration): return self._json(409,{"error":"Ese horario se superpone con otro turno. Elegí otra hora."})
                    status="Prioridad inmediata" if emergency else "Por confirmar"
                    priority="Emergencia" if emergency else "Normal"
                    cur=db.execute("INSERT INTO appointments(appt_date,time,patient_id,patient_name,kind,doctor,status,icon,color,created_at,duration_min,priority,source) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)",(appt_date,time,p["id"],pname,kind,"Equipo de guardia" if emergency else doctor,status,p["icon"],p["color"],datetime.now().isoformat(timespec="seconds"),duration,priority,"Clínica"))
                    if emergency:
                        now=datetime.now(); convo=db.execute("INSERT INTO conversations(owner,pet_label,icon,preview,status,created_at) VALUES(?,?,?,?,?,?)",(p["owner"],f"{pname} · {p['species']}","⚠️",f"Emergencia ingresada desde recepción: {pname}","Urgente",now.isoformat(timespec="seconds")))
                        db.execute("INSERT INTO messages(conversation_id,text,time,is_mine,created_at) VALUES(?,?,?,?,?)",(convo.lastrowid,f"Emergencia. Atención inmediata solicitada por recepción para {pname}. {reason}".strip(),now.strftime("%H:%M"),0,now.isoformat(timespec="seconds")))
                    r=db.execute("SELECT * FROM appointments WHERE id=?",(cur.lastrowid,)).fetchone()
                return self._json(201,{"id":r["id"],"appt_date":r["appt_date"],"time":r["time"],"patient_name":r["patient_name"],"kind":r["kind"],"doctor":r["doctor"],"status":r["status"],"icon":r["icon"],"color":r["color"],"duration_min":r["duration_min"],"priority":r["priority"]})
            if path.startswith("/api/conversations/") and path.endswith("/messages"):
                parts=path.strip("/").split("/")
                if len(parts)!=4: return self._json(404,{"error":"Ruta no encontrada."})
                cid=int(parts[2]); message=clean_text(body.get("text"),"Mensaje",True,4000); now=datetime.now()
                with database() as db:
                    if not db.execute("SELECT 1 FROM conversations WHERE id=?",(cid,)).fetchone(): return self._json(404,{"error":"Conversación no encontrada."})
                    cur=db.execute("INSERT INTO messages(conversation_id,text,time,is_mine,created_at) VALUES(?,?,?,?,?)",(cid,message,now.strftime("%H:%M"),1,now.isoformat(timespec="seconds")))
                    db.execute("UPDATE conversations SET preview=? WHERE id=?",(message,cid)); r=db.execute("SELECT * FROM messages WHERE id=?",(cur.lastrowid,)).fetchone()
                return self._json(201,{"id":r["id"],"text":r["text"],"time":r["time"],"is_mine":True})
            if path=="/api/notes":
                patient=clean_text(body.get("patient_name","Toto"),"Paciente",True,80)
                fields=[clean_text(body.get(k,""),k,False,4000) for k in ("subjective","objective","assessment","plan")]
                now=datetime.now().isoformat(timespec="seconds")
                with database() as db:
                    cur=db.execute("INSERT INTO soap_notes(patient_name,subjective,objective,assessment,plan,status,updated_at) VALUES(?,?,?,?,?,'Borrador',?)",(patient,*fields,now)); r=db.execute("SELECT * FROM soap_notes WHERE id=?",(cur.lastrowid,)).fetchone()
                return self._json(201,dict(r))
            return self._json(404,{"error":"Ruta no encontrada."})
        except sqlite3.IntegrityError: return self._json(409,{"error":"Ese correo o teléfono ya está registrado."})
        except (ValueError, json.JSONDecodeError) as e: return self._json(400,{"error":str(e)})
        except PermissionError as e: return self._json(403,{"error":str(e)})
        except Exception: return self._json(500,{"error":"No se pudo completar la operación."})

    def do_PATCH(self):
        path=urlparse(self.path).path
        try:
            body=self._body()
            if path.startswith("/api/reminders/"):
                rid=int(path.rsplit("/",1)[1]); active=body.get("active")
                if not isinstance(active,bool): return self._json(400,{"error":"El estado debe ser verdadero o falso."})
                with database() as db:
                    cur=db.execute("UPDATE reminders SET active=? WHERE id=?",(int(active),rid))
                    if not cur.rowcount: return self._json(404,{"error":"Recordatorio no encontrado."})
                    row=db.execute("SELECT * FROM reminders WHERE id=?",(rid,)).fetchone()
                return self._json(200,dict(row))
            return self._json(404,{"error":"Ruta no encontrada."})
        except (ValueError, json.JSONDecodeError) as e: return self._json(400,{"error":str(e)})
        except PermissionError as e: return self._json(403,{"error":str(e)})
        except Exception: return self._json(500,{"error":"No se pudo completar la operación."})

    def do_OPTIONS(self):
        self._json(405,{"error":"Método no permitido."})

if __name__=="__main__":
    init_db()
    print(f"PetCare listo en http://{HOST}:{PORT}")
    print("Base local SQLite: data/petcare.sqlite3")
    ThreadingHTTPServer((HOST,PORT),Handler).serve_forever()

