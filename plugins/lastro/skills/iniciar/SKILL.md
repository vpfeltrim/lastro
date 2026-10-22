---
name: iniciar
description: Montar a memória lastro (bundle OKF v0.2 em knowledge/) num projeto que ainda não a tem, ou adaptar o perfil de captura e os tipos ao domínio do projeto. Use quando o usuário pedir para configurar, iniciar ou adotar a memória do projeto.
disable-model-invocation: true
---

# Montar a memória num projeto

1. **Rode `lastro init`** na raiz do projeto. Ele cria, sem sobrescrever nada:
   `.claude/memoria.yaml`, o bundle com as pastas dos tipos, o `index.md` da raiz, `log.md`,
   `estado.md`, `.claude/rules/memoria.md` (carregada só ao mexer no bundle), o `CLAUDE.md` (se não
   existir) e as linhas do `.gitignore` para a captura bruta.
2. **Ajuste o perfil com o usuário**:
   - `revisores` e `donos`: o id humano de quem carimba (`human:<id>`).
   - `captura.bash`: os comandos que **mudam o ambiente** neste domínio (API de escrita, restart,
     deploy, o wrapper do projeto). Leitura não entra. O que parece escrita mas é leitura (por
     exemplo POST de busca) vai em `captura.ignorar`.
   - `tipos`: só acrescente tipo quando mudar quem lê ou que campos leva. Tipo novo é decisão.
3. **Se o projeto já tinha `CLAUDE.md`**, acrescente o bloco de memória do template: o import
   `@knowledge/estado.md` e o contrato. Mantenha o `CLAUDE.md` curto (abaixo de 150 linhas): o
   inventário do ambiente vai para `ambiente/`, não para ele.
4. **Registre a adoção**: uma `Decisao` com o formato e o perfil escolhidos, e a linha no log.
5. **Confira**: `lastro lint` precisa terminar com 0 erro(s). Se o projeto não é repositório git,
   pergunte ao usuário antes de rodar `git init`.

O plugin precisa estar habilitado no projeto para os hooks rodarem:
`claude plugin install lastro@lastro --scope project`.
