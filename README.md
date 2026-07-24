# process-queue-video-download

Monitora uma pasta de fila. Cada `*.txt` colocado ali contém um link, que é
enviado **como você** (usuário, via Telethon/MTProto) para o alvo configurado no
Telegram. Depois de enviado, o arquivo vai para a subpasta de processados; se
falhar, vai para a de falhas.

Enviar como usuário (não bot) é necessário porque um bot não recebe mensagens de
outro bot — mas um usuário pode mandar mensagem a um bot.

Tudo que é específico do seu setup (alvo, pastas, nome de sessão, lockfile) fica
no `config.env`, não no código.

## Setup (uma vez)

Nos comandos abaixo, `$PROJECT` é o diretório onde você clonou este projeto.

1. **Pacote do venv** (precisa de sudo):
   ```
   sudo apt install -y python3.12-venv
   ```

2. **Ambiente + dependência:**
   ```
   cd "$PROJECT"
   python3 -m venv venv
   ./venv/bin/pip install -U pip telethon
   ```

3. **Config** — crie um app em <https://my.telegram.org>
   (Login > API development tools) para obter `api_id` e `api_hash`. Então:
   ```
   cp config.env.example config.env
   chmod 600 config.env
   # edite config.env: preencha API_ID, API_HASH, TARGET e QUEUE_DIR
   ```

4. **Login no Telegram** (interativo, uma vez — pede telefone, código e 2FA):
   ```
   ./venv/bin/python login.py
   ```
   Gera o arquivo de sessão. Se o alvo for um bot e não resolver, abra o Telegram
   e mande `/start` para ele uma vez, depois rode `login.py` de novo.

5. **Cron** (a cada 1 minuto, com trava anti-concorrência):
   ```
   crontab -e
   ```
   Adicione (troque `$PROJECT` pelo caminho absoluto do projeto; o lockfile deve
   bater com `LOCK_FILE` do config.env):
   ```
   * * * * * flock -n /tmp/vdq.lock "$PROJECT/venv/bin/python" "$PROJECT/process_queue.py" >> "$PROJECT/process_queue.log" 2>&1
   ```

## Uso

Largue um `.txt` com um link na pasta da fila (`QUEUE_DIR`). Em até 1 min o link
chega no alvo e o arquivo aparece na subpasta de processados. Logs em
`process_queue.log`.

## Teste rápido

```
echo "https://example.com/video" > "$QUEUE_DIR/teste.txt"
# rodar manualmente sem esperar o cron:
./venv/bin/python process_queue.py
```

## Configuração (config.env)

| Chave | Obrigatório | Default | Descrição |
|-------|-------------|---------|-----------|
| `API_ID` / `API_HASH` | sim | — | Credenciais de my.telegram.org |
| `TARGET` | sim | — | Username do bot/canal de destino |
| `QUEUE_DIR` | sim | — | Pasta da fila (`~` é expandido) |
| `SESSION_NAME` | não | `queue` | Nome do arquivo de sessão |
| `PROCESSED_SUBDIR` | não | `processed` | Subpasta de sucesso |
| `FAILED_SUBDIR` | não | `failed` | Subpasta de falha |
| `LOCK_FILE` | não | `/tmp/vdq.lock` | Lockfile do cron (referência) |

## Arquivos

- `common.py` — carrega/valida `config.env`.
- `login.py` — login interativo único → arquivo de sessão.
- `process_queue.py` — rodado pelo cron; envia e arquiva.
- `config.env` — configuração e segredos (não versionado).
- `<SESSION_NAME>.session` — sessão do Telegram (não versionado; mantenha fora de pastas sincronizadas como Dropbox).
