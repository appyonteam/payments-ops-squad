# Instalação

O payments-ops-squad pode ser instalado de três formas. Escolha uma por máquina: o plugin e o script de instalação entregam os
mesmos agentes e skills, então instalar os dois gera duplicidade.

## 1. Plugin do Claude Code (recomendado)

Requisitos: Claude Code e Python 3 (para o buscador de documentação).

```bash
claude plugin marketplace add appyonteam/payments-ops-squad
claude plugin install payments-ops-squad@payments-ops-marketplace
```

Reinicie o Claude Code. Confira com `/agents` (21 especialistas) e digitando `/payments-ops-squad:` para listar os comandos:

| Comando | Skill |
|---|---|
| `/payments-ops-squad:pay-export` | `analyze-export` |
| `/payments-ops-squad:pay-incident` | `investigate-incident` |
| `/payments-ops-squad:pay-decline` | `explain-decline` |
| `/payments-ops-squad:pay-workflow` | `review-workflow` |
| `/payments-ops-squad:pay-ask` | `ask-payments` |
| `/payments-ops-squad:pay-docs` | `fetch-docs` |

Atualizar: `claude plugin marketplace update payments-ops-marketplace` e depois `claude plugin update payments-ops-squad@payments-ops-marketplace`.
Remover: `claude plugin uninstall payments-ops-squad`.

## 2. Script de instalação no Claude Code (sem namespace)

```bash
git clone https://github.com/appyonteam/payments-ops-squad.git
cd payments-ops-squad
bash install/install.sh                    # escopo de usuário, em ~/.claude
bash install/install.sh --scope project    # escopo de projeto, em ./.claude da pasta atual
```

Windows (PowerShell):

```powershell
.\install\install.ps1
.\install\install.ps1 -Scope project
```

O que o script copia:

- `agents/*.md` para `<destino>/agents/` (21 arquivos)
- cada skill para `<destino>/skills/<nome>/` (43 pastas; as skills da Stripe saem de `skills/stripe/` para o mesmo nível)
- `commands/*.md` para `<destino>/commands/` (6 arquivos; os comandos ficam sem namespace, por exemplo `/pay-export`)
- `tools/fetch_doc.py`, `knowledge/INDEX.md` e `knowledge/sources.json` para `<destino>/payments-ops-squad/`
- um cache de documentação vazio em `<destino>/payments-ops-squad/knowledge/`

Se algum destino já existir, o script lista os conflitos, não grava nada e sai com código 2. Rode de novo com `--force`
(`-Force` no Windows) para sobrescrever. Para remover, apague os arquivos listados acima.

No Windows, se `python3` não estiver no PATH, rode o buscador com `python` ou `py -3`.

## 3. Claude web e aplicativo desktop

1. Abra a Release mais recente de `appyonteam/payments-ops-squad` no GitHub e baixe os zips desejados (um por skill; 64 no total:
   21 especialistas, 35 skills da Stripe e 8 skills de uso).
2. No Claude, vá em **Settings > Capabilities > Skills** e envie cada zip.
3. Skills exigem plano Pro, Max, Team ou Enterprise com execução de código habilitada. Em Team e Enterprise, um owner pode
   precisar habilitar skills para a organização antes.

Limitações no web e no aplicativo: não há subagentes (cada especialista é uma skill cujo checklist o Claude aplica diretamente),
não há comandos com barra e o buscador de documentação não roda. As skills então leem a documentação oficial online e registram
isso nas fontes.

Para gerar os zips você mesmo: `python3 tools/build_dist.py . dist`.

## Cache de documentação

O `tools/fetch_doc.py` guarda as páginas de documentação oficial na primeira destas pastas: `$PAYMENTS_OPS_KNOWLEDGE`,
`${CLAUDE_PLUGIN_DATA}/knowledge/`, a pasta da instalação por script `<destino>/payments-ops-squad/knowledge/` ou
`~/.claude/payments-ops-squad/knowledge/`. Cada página vale por 14 dias. Para limpar o cache, apague a pasta. Veja
[knowledge/INDEX.md](../knowledge/INDEX.md).

## Segurança

Os agentes são instruídos a operar somente em leitura; isso não é imposto tecnicamente (eles podem rodar Bash). Conecte apenas
chaves de API restritas e somente leitura. Três skills da Stripe (`checkout-implementation`, `webhook-implementation`,
`stripe-billing-context`) geram código ou arquivos quando solicitadas.
