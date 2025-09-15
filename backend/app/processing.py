import os, json, traceback
from sqlalchemy.orm import Session
from .database import SessionLocal
from . import models
from .ocr import pdf_to_images, ocr_images
from .llm import extract_structured
from .utils import new_id
from .logger import logger

def _update_progress(db: Session, po: models.PO, status: str = None, progress: float = None, avg_conf: float = None):
    if status is not None: po.status = status
    if progress is not None: po.progress = progress
    if avg_conf is not None: po.avg_confidence = avg_conf
    db.add(po); db.commit(); db.refresh(po)

def run_extraction(po_id: str, global_prompt: str, customer_prompt: str):
    logger.info(f"START extraction | po_id={po_id}")
    db: Session = SessionLocal()
    try:
        po = db.query(models.PO).filter(models.PO.id == po_id).first()
        if not po:
            logger.error(f"Missing PO {po_id}")
            return
        _update_progress(db, po, status="processing", progress=5.0); logger.info(f"status=processing progress=5% | po_id={po_id}")
        logger.info(f"pdf_to_images start | path={po.pdf_path}")
        images = pdf_to_images(po.pdf_path, dpi=300)
        logger.info(f"pdf_to_images done | pages={len(images)}")
        _update_progress(db, po, progress=20.0)

        logger.info("ocr start")
        text = ocr_images(images)
        logger.info(f"ocr done | chars={len(text)}")
        try:
            os.makedirs('/app/data/raw', exist_ok=True)
            with open(f"/app/data/raw/{po.id}.txt","w") as f: f.write(text)
        except Exception as e:
            logger.warning(f"raw save failed: {e}")
        _update_progress(db, po, progress=40.0)

        logger.info("gemini call start")
        result = extract_structured(text, global_prompt, customer_prompt)
        logger.info("gemini call done")
        try:
            os.makedirs('/app/data/labeled', exist_ok=True)
            with open(f"/app/data/labeled/{po.id}.json","w") as f: json.dump(result,f,indent=2)
        except Exception as e:
            logger.warning(f"labeled save failed: {e}")
        _update_progress(db, po, progress=70.0)

        # reset old line items
        for li in list(po.line_items):
            db.delete(li)
        db.commit()

        buyer = (result or {}).get("buyer", {}) or {}
        ship = (result or {}).get("ship_to", {}) or {}

        po.buyer_name = buyer.get("name","") or ""
        po.buyer_street = buyer.get("street","") or ""
        po.buyer_city = buyer.get("city","") or ""
        po.buyer_postal = buyer.get("postal","") or ""

        po.shipto_name = ship.get("name","") or ""
        po.shipto_street = ship.get("street","") or ""
        po.shipto_city = ship.get("city","") or ""
        po.shipto_postal = ship.get("postal","") or ""
        po.shipto_id = ship.get("ship_to_id","") or ""

        items = (result or {}).get("line_items", []) or []
        confidences = []
        for r in items:
            li = models.LineItem(
                id=new_id(),
                po_id=po.id,
                description=str(r.get("description","") or ""),
                quantity=float(r.get("quantity",0) or 0),
                unit_price=float(r.get("unit_price",0) or 0),
                total_price=float(r.get("total_price",0) or 0),
                confidence=float(r.get("confidence",0) or 0),
            )
            confidences.append(li.confidence or 0.0)
            db.add(li)
        avg_conf = sum(confidences)/len(confidences) if confidences else 0.0
        db.commit()
        _update_progress(db, po, status="complete", progress=100.0, avg_conf=avg_conf); logger.info(f"COMPLETE | po_id={po_id} avg_conf={avg_conf:.3f}")
    except Exception as e:
        logger.error(f"FAILED | po_id={po_id} error={e}")
        logger.error(traceback.format_exc())
        try:
            po = db.query(models.PO).filter(models.PO.id == po_id).first()
            if po:
                _update_progress(db, po, status="failed", progress=100.0)
        except Exception:
            pass
    finally:
        db.close()
