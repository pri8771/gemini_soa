from sqlalchemy.orm import Session
from . import models
def get_global_prompt(db: Session) -> str:
    row = db.query(models.Prompt).filter(models.Prompt.scope=="global").first()
    return row.prompt_text if row else ""
def set_global_prompt(db: Session, text: str) -> None:
    row = db.query(models.Prompt).filter(models.Prompt.scope=="global").first()
    if not row:
        row = models.Prompt(scope="global", customer_key=None, prompt_text=text or ""); db.add(row)
    else:
        row.prompt_text = text or ""; db.add(row)
    db.commit()
def get_customer_prompt(db: Session, key: str) -> str:
    if not key: return ""
    row = db.query(models.Prompt).filter(models.Prompt.scope=="customer", models.Prompt.customer_key==key).first()
    return row.prompt_text if row else ""
def set_customer_prompt(db: Session, key: str, text: str) -> None:
    if not key: return
    row = db.query(models.Prompt).filter(models.Prompt.scope=="customer", models.Prompt.customer_key==key).first()
    if not row:
        row = models.Prompt(scope="customer", customer_key=key, prompt_text=text or ""); db.add(row)
    else:
        row.prompt_text = text or ""; db.add(row)
    db.commit()
def list_customer_prompts(db: Session) -> list[dict]:
    rows = db.query(models.Prompt).filter(models.Prompt.scope=="customer").all()
    return [{"customer_key": r.customer_key, "prompt_text": r.prompt_text} for r in rows]
