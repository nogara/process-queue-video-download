# Fila de download → Telegram (envio como usuário)

**Data:** 2026-07-23
**Status:** Aprovado (design)

## Objetivo

Monitorar uma pasta de fila. Cada arquivo `*.txt` colocado ali contém um link.
Esse link deve ser enviado como **mensagem de usuário** (não bot) para
`@SEU_BOT` no Telegram, para que o bot de destino possa
processá-lo. Após envio bem-sucedido, o arquivo é movido para `processed/`.

Motivo de enviar como usuário: um bot não recebe mensagens de outro bot; um
usuário pode mandar mensagem a um bot e ele a recebe.

## Decisões

| Tema | Decisão |
|------|---------|
| Método de envio | Telethon (API de usuário / MTProto) |
| Autenticação | Login interativo único → arquivo de sessão reutilizável |
| Alvo | DM com `@SEU_BOT` |
| Conteúdo | Primeira linha não-vazia do `.txt`, enviada como link puro |
| Disparo | Cron do usuário a cada 1 minuto |
| Sucesso | Mover arquivo para `processed/` |
| Falha | Mover arquivo para `failed/` + log (sem re-tentar) |
| Concorrência | `flock` para evitar execuções sobrepostas |

## Layout de arquivos

Código e sessão ficam **fora de pastas sincronizadas** (ex: Dropbox), no
diretório do projeto:

```
process-queue-video-download/
├── venv/                     # virtualenv com telethon
├── config.env               # API_ID, API_HASH, TARGET, QUEUE_DIR (chmod 600)
├── login.py                 # login interativo único → queue.session
├── process_queue.py         # rodado pelo cron
├── queue.session            # sessão Telethon (chmod 600, NÃO versionar)
├── process_queue.log        # log de execução
└── docs/superpowers/specs/  # este spec
```

Fila (QUEUE_DIR, pode ser numa pasta sincronizada):
```
$QUEUE_DIR/
├── *.txt          # arquivos novos a processar
├── processed/     # movidos após sucesso
└── failed/        # movidos após falha (criado se não existir)
```

## Componentes

### config.env
Obrigatórios: `API_ID`, `API_HASH`, `TARGET`, `QUEUE_DIR`.
Opcionais (com default): `SESSION_NAME` (`queue`), `PROCESSED_SUBDIR`
(`processed`), `FAILED_SUBDIR` (`failed`), `LOCK_FILE` (`/tmp/vdq.lock`).
Nada específico do setup fica no código. Carregado por `login.py` e
`process_queue.py`. Permissão 600.

### login.py
- Roda uma única vez, interativamente (telefone + código SMS + senha 2FA se houver).
- Cria `TelegramClient(SESSION_NAME, API_ID, API_HASH)` → gera o `.session`.
- Valida o alvo: resolve `TARGET` e imprime o nome, confirmando que a sessão
  consegue enviar. Não envia nada.

### process_queue.py (fluxo)
1. Carrega `config.env`.
2. Conecta com a sessão existente. Se não autorizado, loga erro e sai (código ≠ 0).
3. Garante que `processed/` e `failed/` existem.
4. Lista `*.txt` **apenas na raiz** de `QUEUE_DIR` (ordena por nome), ignora subpastas.
5. Para cada arquivo:
   - Lê a primeira linha não-vazia (strip). Sem link → falha.
   - Envia como mensagem pura ao `TARGET`.
   - Sucesso → move para `processed/`.
   - Exceção/sem link → move para `failed/`, loga o motivo.
6. Loga resumo (quantos enviados / falharam).

Idempotência: mover o arquivo após envio impede reenvio. `flock` impede
concorrência entre ciclos do cron.

### Cron
Roda a cada minuto; `$PROJECT` é o caminho absoluto do projeto e o lockfile
bate com `LOCK_FILE`:
```
* * * * * flock -n /tmp/vdq.lock "$PROJECT/venv/bin/python" "$PROJECT/process_queue.py" >> "$PROJECT/process_queue.log" 2>&1
```

## Tratamento de erro
- Arquivo vazio / sem linha não-vazia → `failed/`.
- Erro de rede/autorização no envio → arquivo vai para `failed/`, log detalha.
- Colisão de nome ao mover (arquivo já existe no destino) → acrescenta sufixo numérico.

## Fora de escopo (YAGNI)
- Múltiplos links por arquivo.
- Retry automático da pasta `failed/`.
- Notificações de status.
- Validação/normalização de URL.

## Testes / verificação
- `login.py` conclui e resolve o alvo com sucesso.
- Colocar um `.txt` de teste com um link → após um ciclo, mensagem chega no bot
  e arquivo aparece em `processed/`.
- Colocar um `.txt` vazio → vai para `failed/` e nada é enviado.
- Rodar dois ciclos concorrentes → `flock` bloqueia o segundo.
