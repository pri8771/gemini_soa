import os, logging
os.makedirs("/app/data", exist_ok=True)
LOG_PATH = os.getenv("APP_LOG_PATH", "/app/data/app.log")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logger = logging.getLogger("pipeline")
logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
if not logger.handlers:
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(name)s | %(message)s")
    fh = logging.FileHandler(LOG_PATH); fh.setFormatter(fmt)
    sh = logging.StreamHandler(); sh.setFormatter(fmt)
    logger.addHandler(fh); logger.addHandler(sh); logger.propagate = False
