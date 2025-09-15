import os, json
import google.generativeai as genai

DEFAULT_SCHEMA = {
  "buyer": {"name":"","street":"","city":"","postal":""},
  "ship_to": {"name":"","street":"","city":"","postal":"","ship_to_id":""},
  "line_items": []
}
SYSTEM_PROMPT = ("You are an extraction engine. Given raw OCR text from a scanned Purchase Order, "
  "return a strict JSON object with keys: buyer{name,street,city,postal}, "
  "ship_to{name,street,city,postal,ship_to_id}, and line_items[{description,quantity,unit_price,total_price,confidence}]. "
  "Use numeric types for quantity/prices. confidence is 0..1. If missing, fill with best guess or 0.")

def _coerce_float(x):
    try:
        return float(str(x).replace(',','').strip())
    except Exception:
        return 0.0

def extract_structured(ocr_text: str, global_prompt: str, customer_prompt: str):
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = "\n\n".join([SYSTEM_PROMPT, global_prompt or "", customer_prompt or "", "OCR:", ocr_text[:20000]])
    resp = model.generate_content(prompt)
    txt = getattr(resp, "text", "") or ""
    s = txt.find("{"); e = txt.rfind("}")
    js = txt[s:e+1] if s!=-1 and e!=-1 and e>s else txt
    try:
        data = json.loads(js)
    except Exception:
        return DEFAULT_SCHEMA
    out = {
        "buyer": {
            "name": data.get("buyer",{}).get("name",""),
            "street": data.get("buyer",{}).get("street",""),
            "city": data.get("buyer",{}).get("city",""),
            "postal": data.get("buyer",{}).get("postal",""),
        },
        "ship_to": {
            "name": data.get("ship_to",{}).get("name",""),
            "street": data.get("ship_to",{}).get("street",""),
            "city": data.get("ship_to",{}).get("city",""),
            "postal": data.get("ship_to",{}).get("postal",""),
            "ship_to_id": data.get("ship_to",{}).get("ship_to_id",""),
        },
        "line_items": []
    }
    for li in data.get("line_items",[]) or []:
        out["line_items"].append({
            "description": str(li.get("description","") or ""),
            "quantity": _coerce_float(li.get("quantity",0)),
            "unit_price": _coerce_float(li.get("unit_price",0)),
            "total_price": _coerce_float(li.get("total_price",0)),
            "confidence": _coerce_float(li.get("confidence",0)),
        })
    return out
