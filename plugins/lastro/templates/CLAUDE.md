# {{PROJETO}}

(Uma linha dizendo o que é o projeto.)

## Leia primeiro

@{{BUNDLE}}/{{ESTADO}}

A memória do projeto é o bundle `{{BUNDLE}}/` (OKF v0.2 + perfil em `.claude/memoria.yaml`), mantido
pelo plugin `lastro`. O mapa está em `{{BUNDLE}}/index.md`. Ao iniciar, o hook entrega o resumo:
atividades em andamento, ações não consolidadas, conceitos vencidos e as últimas entradas do log.

## Memória — o contrato

1. **Gravar pela skill `lastro:memoria`**, nunca de memória própria do formato.
2. **Ação que muda o ambiente é capturada pelo hook** e o turno não encerra sem consolidá-la:
   conceito afetado + `lastro log` + `lastro consolidar` (ou `--nada "<motivo>"`).
3. **`verified` é só do revisor humano.** Conceito sem `verified` serve para investigar, não para
   embasar mudança. `stale_after` vencido: reconferir contra o ambiente antes de agir.
4. **Atividade de `mudanca`** só sai de `backlog` com `mem_autorizacao` apontando para a `Decisao`.
5. **Dado bruto e credencial não entram.** Só conclusão, com `sources`.
6. **Nada se apaga à mão:** `lastro contrair` mede quem depende antes.
