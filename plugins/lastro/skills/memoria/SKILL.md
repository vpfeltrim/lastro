---
name: memoria
description: Gravar na memória do projeto (bundle OKF v0.2 do lastro, normalmente knowledge/). Use ao concluir ou mudar uma atividade, ao executar ação que muda o ambiente, ao descobrir um procedimento, resolver um problema, tirar uma conclusão de dados, medir uma baseline, mapear uma peça do ambiente ou registrar uma decisão do usuário — e sempre que o fim do turno cobrar ações não consolidadas ou erro de lint.
---

# Gravar na memória do projeto

O bundle é a memória entre sessões: o que vale agora, o que foi feito, como se faz, o que já quebrou.
O formato é OKF v0.2 com o perfil do projeto em `.claude/memoria.yaml`. **Gravar é sempre mais de um
arquivo**: conceito solto que ninguém alcança é o mesmo que não ter gravado.

## 1. Ler o perfil

Rode `lastro perfil`. Ele diz os tipos, a pasta de cada um, os campos obrigatórios, os donos, os
revisores e os rótulos do log **deste** projeto. Não presuma o vocabulário de outro projeto.

## 2. Escolher o tipo e o arquivo

- Já existe conceito sobre o assunto? **Atualize-o** (uma nota canônica por assunto). Procure antes:
  `grep -ril "<termo>" <bundle>/` e o `index.md` da pasta.
- Superou um conceito? O antigo ganha `status: deprecated` e `mem_substituido_por: /pasta/novo.md`,
  e o texto dele não é apagado à mão. Remover de vez é `lastro contrair <arquivo>`, que recusa
  enquanto alguém depender dele.
- Nome em kebab-case, sem acento. `Decisao` leva a data na frente: `2026-10-22-assunto.md`.

## 3. O frontmatter

```yaml
---
type: Componente                       # um tipo do perfil, na pasta dele
title: Título curto e específico
description: Uma frase dizendo o que este arquivo entrega (vira o item do índice).
dono: process:memoria                  # da lista de donos do perfil
tags: [ilm, retencao]
status: stable                         # draft | stable | deprecated — maturidade do TEXTO
generated:
  by: claude-code/claude-opus-5-5      # ator: <produtor>/<versão>, human:<id> ou process:<id>
  at: 2026-10-22T14:30:00-03:00        # instante ISO com fuso, sempre
sources:                               # de onde saiu — para alguém refazer
  - id: ilm-get
    resource: "GET _ilm/policy no cluster de produção, 2026-10-22"
stale_after: 2027-01-22T00:00:00-03:00 # quando reconferir (ambiente muda sem avisar)
---
```

- **Instante sempre com fuso.** Data simples é erro.
- **`verified` nunca.** É o carimbo do revisor humano (`lastro verificar`, rodado por ele). O hook
  recusa a escrita. Ao reescrever um conceito verificado, o carimbo pode sair, porque o texto mudou.
- **`sources` é obrigatório** nos tipos que o perfil marca (análise, componente, baseline). O
  `resource` pode ser URL, caminho do bundle (`/pasta/x.md`) ou descrição da consulta.

Campos do perfil (prefixo `mem_`):

| campo | onde | regra |
|---|---|---|
| `mem_status` | Atividade | `backlog \| fazendo \| bloqueado \| concluido \| cancelado` |
| `mem_escopo` | Atividade | `leitura` ou `mudanca` (altera o ambiente do cliente) |
| `mem_autorizacao` | Atividade | **link** para a `Decisao`. Mudança em `fazendo`/`concluido` sem ele é erro |
| `mem_bloqueado_por` | Atividade bloqueada | link ou texto livre |
| `mem_substituido_por` | conceito superado | link; exige `status: deprecated` |
| `mem_janela` | Baseline | `{de: <instante>, ate: <instante>}` da medição |
| `mem_certificados` | módulo `certificados` | `[{chave, rotulo, valor}]` conferido contra `certificados.tsv` |

## 4. O corpo

**Conclusão, não dado bruto.** Se o texto pode ser regenerado rodando um comando, o que pertence ao
bundle é o comando e a conclusão. JSON de coleta, saída de API e logs ficam fora; o `sources` diz de
onde saíram. **Credencial nunca**: referencie a variável ou o `.env`.

| tipo | estrutura que funciona |
|---|---|
| Atividade | origem → o que foi feito / o que falta → o que fica em aberto |
| Runbook | objetivo → pré-requisitos → passos numerados → como verificar que deu certo |
| Resolucao | `# Sintoma` → `# Causa` → `# Solução` → `# Como não cair de novo` |
| Analise | pergunta → dados (com `sources`) → conclusão → limites |
| Componente | tabela de campos → o que significa → **como reconferir** (o comando) |
| Baseline | métrica, valor, janela, método → como remedir → o que seria desvio |
| Decisao | a decisão → por quê → escopo → quem decidiu → como desfazer |

Ligue aos vizinhos com link absoluto do bundle: `[ILM de logs](/ambiente/ilm-logs.md)`. Ao criar,
veja quem deveria apontar para o novo arquivo.

## 5. Fechamento — sempre os quatro

1. **O conceito** criado ou atualizado (o índice da pasta é regenerado pelo hook).
2. **Uma linha no log**: `lastro log "<Rótulo>" "<fato em uma linha> — ver [título](/pasta/x.md)"`.
   A linha diz o fato e aponta para o conceito, e o detalhe fica no conceito.
3. **O que ficou velho**: a `Atividade` muda de `mem_status`, o conceito superado é marcado, e o
   `estado.md` é reescrito se a frente, o próximo passo ou os bloqueios mudaram. O estado é
   reescrito, nunca acumulado, e tem teto.
4. **Consolidar as ações capturadas**: `lastro consolidar`. Se nenhuma merece memória (um teste,
   um rollback já registrado), use `lastro consolidar --nada "<motivo>"`.

Depois: `lastro lint`. Erro precisa de correção. Aviso se lê e se julga: `stale_after` vencido é
normal em conceito antigo, mas pede reconferência antes de embasar mudança.

## Não faça

- Gravar dado bruto, saída de comando ou credencial.
- Preencher ou alterar `verified`.
- Duplicar o que está no `CLAUDE.md` ou em outro conceito. Duplicata diverge, então aponte para o original.
- Editar `index.md` de pasta (é gerado) ou apagar conceito à mão (`lastro contrair`).
- Deixar a `Atividade` desatualizada. Memória que mente sobre o próprio estado é pior que memória vazia.
