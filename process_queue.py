#!/usr/bin/env python3
"""Processa a fila: envia o link de cada *.txt ao alvo e arquiva o arquivo.

Rodado pelo cron a cada 1 minuto (via flock). Não interage.
Sucesso -> subpasta processed/ ; falha -> subpasta failed/.
"""
import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from telethon import TelegramClient

from common import load_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
log = logging.getLogger("process_queue")


def first_link(path: Path) -> str | None:
    """Primeira linha não-vazia do arquivo, ou None."""
    try:
        for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = raw.strip()
            if line:
                return line
    except OSError as exc:
        log.error("Não consegui ler %s: %s", path.name, exc)
    return None


def move_to(path: Path, dest_dir: Path) -> Path:
    """Move path para dest_dir, evitando sobrescrever nome existente."""
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / path.name
    if dest.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        dest = dest_dir / f"{path.stem}.{stamp}{path.suffix}"
    path.rename(dest)
    return dest


async def main() -> int:
    cfg = load_config()
    queue_dir: Path = cfg["queue_dir"]
    if not queue_dir.is_dir():
        log.error("QUEUE_DIR não existe: %s", queue_dir)
        return 1

    processed_dir = cfg["processed_dir"]
    failed_dir = cfg["failed_dir"]

    files = sorted(p for p in queue_dir.glob("*.txt") if p.is_file())
    if not files:
        return 0  # nada a fazer; silencioso para não poluir o log a cada minuto

    client = TelegramClient(cfg["session"], cfg["api_id"], cfg["api_hash"])
    await client.connect()
    if not await client.is_user_authorized():
        log.error("Sessão não autorizada. Rode login.py primeiro.")
        await client.disconnect()
        return 1

    sent = failed = 0
    try:
        for path in files:
            link = first_link(path)
            if not link:
                move_to(path, failed_dir)
                log.warning("Sem link em %s -> failed/", path.name)
                failed += 1
                continue
            try:
                await client.send_message(cfg["target"], link)
            except Exception as exc:  # noqa: BLE001
                move_to(path, failed_dir)
                log.error("Falha ao enviar %s (%s) -> failed/", path.name, exc)
                failed += 1
                continue
            move_to(path, processed_dir)
            log.info("Enviado %s: %s -> processed/", path.name, link)
            sent += 1
    finally:
        await client.disconnect()

    log.info("Resumo: %d enviado(s), %d falha(s).", sent, failed)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
