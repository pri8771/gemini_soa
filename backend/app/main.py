import os, json
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from datetime import datetime
from .database import Base, engine, SessionLocal
from . import models
from .schemas import POOut, LineItemOut, StatsOut, PromptPayload, PromptBundleOut
from .utils import new_id
from .processing import run_extraction
from .prompts import get_global_prompt, set_global_prompt, get_customer_prompt, set_customer_prompt, list_customer_prompts
from .logger import logger

UPLOAD_DIR = "/app/uploads"
STATIC_DIR = "/app/static"
APP_LOG_PATH = os.getenv("APP_LOG_PATH", "/app/data/app.log")
os.makedirs(UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def log_requests(request, call_next):
    try:
        logger.info(f"REQUEST {request.method} {request.url.path}")
        resp = await call_next(request)
        logger.info(f"RESPONSE {request.method} {request.url.path} {resp.status_code}")
        return resp
    except Exception as e:
        logger.error(f"MIDDLEWARE ERROR {request.method} {request.url.path} err={e}")
        raise

logger.info("API ready")

def to_po_out(po: models.PO, ocr_text: str | None = None, llm_json: dict | None = None) -> POOut:
    buyer = {"name": po.buyer_name or "","street": po.buyer_street or "","city": po.buyer_city or "","postal": po.buyer_postal or ""}
    ship_to = {"name": po.shipto_name or "","street": po.shipto_street or "","city": po.shipto_city or "","postal": po.shipto_postal or "","ship_to_id": po.shipto_id or ""}
    line_items = [LineItemOut(id=li.id, description=li.description, quantity=li.quantity, unit_price=li.unit_price, total_price=li.total_price, confidence=li.confidence) for li in po.line_items]
    return POOut(id=po.id, filename=po.filename, pdf_url=po.pdf_url, created_at=po.created_at.isoformat(), status=po.status, progress=po.progress, avg_confidence=po.avg_confidence, buyer=buyer, ship_to=ship_to, line_items=line_items, ocr_text=ocr_text, llm_json=llm_json)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/upload")
async def upload_po(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    file_id = new_id()
    dest = os.path.join(UPLOAD_DIR, f"{file_id}.pdf")
    with open(dest, "wb") as f: f.write(await file.read())
    pdf_url = f"/files/{file_id}.pdf"
    db: Session = next(get_db())
    po = models.PO(id=file_id, filename=file.filename, pdf_path=dest, pdf_url=pdf_url, created_at=datetime.utcnow(), status="queued", progress=0.0, avg_confidence=0.0)
    db.add(po); db.commit()
    logger.info(f"UPLOAD received | filename={file.filename} id={file_id}")
    gprompt = get_global_prompt(db); cprompt = ""
    background_tasks.add_task(run_extraction, file_id, gprompt, cprompt)
    logger.info(f"QUEUED | po_id={file_id}")
    return {"id": file_id}

@app.get("/api/po")
def list_pos():
    db: Session = next(get_db())
    rows = db.query(models.PO).order_by(models.PO.created_at.desc()).all()
    out = []
    for po in rows:
        ocr_text = None; llm_json = None
        raw_path = f"/app/data/raw/{po.id}.txt"; lbl_path = f"/app/data/labeled/{po.id}.json"
        if os.path.exists(raw_path): 
            with open(raw_path, "r") as f: ocr_text = f.read()
        if os.path.exists(lbl_path):
            try: 
                with open(lbl_path, "r") as f: llm_json = json.load(f)
            except: llm_json = None
        out.append(to_po_out(po, ocr_text=ocr_text, llm_json=llm_json))
    return out

@app.get("/api/po/{po_id}")
def get_po(po_id: str):
    db: Session = next(get_db())
    po = db.query(models.PO).filter(models.PO.id == po_id).first()
    if not po: raise HTTPException(status_code=404, detail="PO not found")
    ocr_text = None; llm_json = None
    if os.path.exists(f"/app/data/raw/{po.id}.txt"):
        with open(f"/app/data/raw/{po.id}.txt", "r") as f: ocr_text = f.read()
    if os.path.exists(f"/app/data/labeled/{po.id}.json"):
        try: 
            with open(f"/app/data/labeled/{po.id}.json","r") as f: llm_json = json.load(f)
        except: llm_json=None
    return to_po_out(po, ocr_text=ocr_text, llm_json=llm_json)

@app.delete("/api/po/{po_id}/line-item/{li_id}")
def delete_line_item(po_id: str, li_id: str):
    db: Session = next(get_db())
    li = db.query(models.LineItem).filter(models.LineItem.id==li_id, models.LineItem.po_id==po_id).first()
    if not li: raise HTTPException(status_code=404, detail="Line item not found")
    db.delete(li); db.commit(); return {"ok": True}

@app.post("/api/po/{po_id}/reprocess")
def reprocess(po_id: str, background_tasks: BackgroundTasks):
    db: Session = next(get_db())
    po = db.query(models.PO).filter(models.PO.id == po_id).first()
    if not po: raise HTTPException(status_code=404, detail="PO not found")
    po.status = "queued"; po.progress=0.0; db.add(po); db.commit()
    gprompt = get_global_prompt(db); cprompt = ""
    background_tasks.add_task(run_extraction, po_id, gprompt, cprompt)
    logger.info(f"REPROCESS | po_id={po_id}")
    return {"ok": True}

@app.get("/api/stats")
def stats():
    db: Session = next(get_db())
    total = db.query(models.PO).count()
    complete = db.query(models.PO).filter(models.PO.status=="complete").count()
    processing = db.query(models.PO).filter(models.PO.status=="processing").count()
    failed = db.query(models.PO).filter(models.PO.status=="failed").count()
    avg_conf = 0.0
    rows = db.query(models.PO).filter(models.PO.status=="complete").all()
    if rows: avg_conf = sum([(r.avg_confidence or 0) for r in rows]) / len(rows)
    return {"total": total, "complete": complete, "processing": processing, "failed": failed, "avg_confidence": avg_conf}

@app.get("/api/prompts")
def get_prompts():
    db: Session = next(get_db()); 
    return {"global_prompt": get_global_prompt(db), "customer_prompts": list_customer_prompts(db)}

@app.post("/api/prompts")
def save_prompts(payload: PromptPayload):
    db: Session = next(get_db())
    if payload.global_prompt is not None: set_global_prompt(db, payload.global_prompt)
    if payload.customer_key and payload.customer_prompt is not None: set_customer_prompt(db, payload.customer_key, payload.customer_prompt)
    return {"ok": True}

@app.get("/api/logs")
def get_logs(tail: int = 400):
    try:
        tail = max(1, min(2000, tail))
        path = APP_LOG_PATH
        if not os.path.exists(path): return {"lines": []}
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END); size=f.tell(); block=8192; data=b""
            while size>0 and data.count(b"\n")<=tail:
                step=min(block,size); size-=step; f.seek(size); data=f.read(step)+data
        return {"lines": data.decode(errors="ignore").splitlines()[-tail:]}
    except Exception: return {"lines": []}

@app.get("/api/health")
def health(): return {"status":"ok"}

app.mount("/files", StaticFiles(directory=UPLOAD_DIR), name="files")
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="ui")
