"""Configuração compartilhada entre login.py e process_queue.py."""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.env"

# Defaults para campos opcionais (sobrescrevíveis pelo config.env).
DEFAULTS = {
    "SESSION_NAME": "queue",
    "PROCESSED_SUBDIR": "processed",
    "FAILED_SUBDIR": "failed",
    "LOCK_FILE": "/tmp/vdq.lock",
}


def load_config():
    """Lê config.env (KEY=VALUE por linha) e valida os campos obrigatórios."""
    if not CONFIG_PATH.exists():
        sys.exit(f"Faltando {CONFIG_PATH}. Copie config.env.example e preencha.")

    cfg = {}
    for raw in CONFIG_PATH.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        cfg[key.strip()] = value.strip()

    api_id = cfg.get("API_ID", "")
    api_hash = cfg.get("API_HASH", "")
    target = cfg.get("TARGET", "")
    queue_dir = cfg.get("QUEUE_DIR", "")

    missing = [k for k, v in
               {"API_ID": api_id, "API_HASH": api_hash,
                "TARGET": target, "QUEUE_DIR": queue_dir}.items() if not v]
    if missing:
        sys.exit(f"config.env incompleto. Faltando: {', '.join(missing)}")

    try:
        api_id = int(api_id)
    except ValueError:
        sys.exit("API_ID deve ser um número inteiro.")

    # Opcionais com default.
    session_name = cfg.get("SESSION_NAME") or DEFAULTS["SESSION_NAME"]
    processed_subdir = cfg.get("PROCESSED_SUBDIR") or DEFAULTS["PROCESSED_SUBDIR"]
    failed_subdir = cfg.get("FAILED_SUBDIR") or DEFAULTS["FAILED_SUBDIR"]
    lock_file = cfg.get("LOCK_FILE") or DEFAULTS["LOCK_FILE"]

    queue_path = Path(os.path.expanduser(queue_dir)).resolve()

    return {
        "api_id": api_id,
        "api_hash": api_hash,
        "target": target,
        "queue_dir": queue_path,
        # Nome da sessão relativo ao diretório do projeto (gera <nome>.session).
        "session": str(BASE_DIR / session_name),
        "processed_dir": queue_path / processed_subdir,
        "failed_dir": queue_path / failed_subdir,
        "lock_file": lock_file,
    }
