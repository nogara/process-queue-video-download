#!/usr/bin/env python3
"""Login interativo único no Telegram como usuário.

Rode UMA vez num terminal interativo:
    ./venv/bin/python login.py

Vai pedir telefone (+55...), código enviado pelo Telegram e senha 2FA se houver.
Gera queue.session, que o process_queue.py reutiliza sem interação.
"""
import asyncio

from telethon import TelegramClient

from common import load_config


async def main():
    cfg = load_config()
    client = TelegramClient(cfg["session"], cfg["api_id"], cfg["api_hash"])
    await client.start()  # faz o login interativo se necessário

    me = await client.get_me()
    print(f"Autenticado como: {me.first_name} (@{me.username}) id={me.id}")

    try:
        target = await client.get_entity(cfg["target"])
        name = getattr(target, "title", None) or getattr(target, "first_name", "?")
        print(f"Alvo resolvido: {cfg['target']} -> {name} (id={target.id})")
    except Exception as exc:  # noqa: BLE001
        print(f"AVISO: não consegui resolver o alvo {cfg['target']}: {exc}")
        print("Verifique o TARGET no config.env (talvez precise iniciar o bot uma vez).")

    await client.disconnect()
    print("Sessão salva. Você já pode configurar o cron.")


if __name__ == "__main__":
    asyncio.run(main())
