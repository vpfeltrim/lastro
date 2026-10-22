---
paths:
  - "{{BUNDLE}}/**"
---

# Gravando no bundle `{{BUNDLE}}/`

Formato OKF v0.2 com o perfil de `.claude/memoria.yaml` (`lastro perfil` resume). Grave pela skill
`lastro:memoria`. O que o `lastro lint` reprova, o hook recusa na hora e o fim do turno cobra:

- frontmatter com `type`, `title`, `description`, `dono`; tipo na pasta dele; nome em kebab-case;
- instantes ISO 8601 **com fuso** (`2026-10-22T14:00:00-03:00`), nunca só a data;
- `verified` só o revisor humano aplica (`lastro verificar`), nunca o agente;
- `index.md` de pasta é gerado (`lastro indices`); o log recebe linha por `lastro log`;
- dado bruto e credencial não entram — só conclusão, com `sources` para refazer.
