"""Controle negativo do lastro: cada regra tem de reprovar o caso ruim e aprovar o bom.

Rodar: python3 -I -m unittest discover -s plugins/lastro/tests -v
"""
import json
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

LASTRO = Path(__file__).resolve().parent.parent / "bin" / "lastro"


def fm(**campos):
    linhas = ["---"]
    for k, v in campos.items():
        linhas.append(f"{k}: {json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v}")
    return "\n".join(linhas + ["---", ""])


BASE = dict(title="Título", description="Uma frase.", dono="process:memoria")


class Projeto(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        self.run_ok("init")
        perfil = self.root / ".claude" / "memoria.yaml"
        perfil.write_text(perfil.read_text().replace("human:SEU_ID", "human:teste")
                          .replace("modulos: []", "modulos: [certificados]"))
        self.kb = self.root / "knowledge"

    def tearDown(self):
        self.tmp.cleanup()

    def cli(self, *args, stdin=None):
        return subprocess.run([str(LASTRO), *args], cwd=self.root, env=self.env, input=stdin,
                              capture_output=True, text=True)

    def run_ok(self, *args):
        r = self.cli(*args)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        return r

    def escrever(self, rel, texto, indices=True):
        p = self.kb / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto, encoding="utf-8")
        if indices:
            self.run_ok("indices")
        return p

    def codigos(self):
        r = self.cli("lint", "--json")
        d = json.loads(r.stdout)
        return {c for _, c, _ in d["erros"]}, {c for _, c, _ in d["avisos"]}

    def hook(self, nome, ev):
        return self.cli(nome, stdin=json.dumps(ev))


class TestLint(Projeto):
    def test_init_limpo(self):
        erros, _ = self.codigos()
        self.assertEqual(erros, set())

    def test_conceitos_bons_passam(self):
        self.escrever("decisoes/2026-10-22-algo.md", fm(type="Decisao", **BASE) + "# Decisão\n")
        self.escrever("atividades/mudar-ilm.md", fm(type="Atividade", **BASE, mem_status="concluido", mem_escopo="mudanca",
                                                    mem_autorizacao="/decisoes/2026-10-22-algo.md") + "corpo\n")
        self.escrever("baselines/ingestao.md", fm(type="Baseline", **BASE, sources=[{"resource": "GET _nodes/stats"}],
                                                  stale_after="2099-01-01T00:00:00-03:00",
                                                  mem_janela={"de": "2026-10-01T00:00:00-03:00", "ate": "2026-10-08T00:00:00-03:00"},
                                                  generated={"by": "claude-code/claude-opus-5-5", "at": "2026-10-22T10:00:00-03:00"})
                      + "Ver [a decisão](/decisoes/2026-10-22-algo.md).\n")
        erros, _ = self.codigos()
        self.assertEqual(erros, set())

    def caso(self, rel, texto, codigo):
        self.escrever(rel, texto)
        erros, _ = self.codigos()
        self.assertIn(codigo, erros)

    def test_sem_frontmatter(self):
        self.caso("runbooks/x.md", "# sem cabeçalho\n", "E-FM")

    def test_tipo_fora_do_perfil(self):
        self.caso("runbooks/x.md", fm(type="Conceito", **BASE), "E-TYPE")

    def test_tipo_na_pasta_errada(self):
        self.caso("runbooks/x.md", fm(type="Resolucao", **BASE), "E-PASTA")

    def test_campo_base_ausente(self):
        self.caso("runbooks/x.md", fm(type="Runbook", title="t", dono="process:memoria"), "E-CAMPO")

    def test_exige_do_tipo(self):
        self.caso("analises/x.md", fm(type="Analise", **BASE), "E-CAMPO")

    def test_dono_fora_da_lista(self):
        self.caso("runbooks/x.md", fm(type="Runbook", title="t", description="d", dono="human:outro"), "E-DONO")

    def test_instante_so_data(self):
        self.caso("ambiente/x.md", fm(type="Componente", **BASE, sources=[{"resource": "r"}], stale_after="2027-01-01"), "E-INSTANTE")

    def test_ator_invalido(self):
        self.caso("runbooks/x.md", fm(type="Runbook", **BASE, generated={"by": "claude", "at": "2026-10-22T10:00:00Z"}), "E-ATOR")

    def test_verified_por_maquina(self):
        self.caso("runbooks/x.md", fm(type="Runbook", **BASE, verified=[{"by": "claude-code/x", "at": "2026-10-22T10:00:00Z"}]), "E-VERIFIED")

    def test_status_okf(self):
        self.caso("runbooks/x.md", fm(type="Runbook", **BASE, status="fazendo"), "E-STATUS")

    def test_status_da_atividade(self):
        self.caso("atividades/x.md", fm(type="Atividade", **BASE, mem_status="feito", mem_escopo="leitura"), "E-MEMSTATUS")

    def test_mudanca_sem_autorizacao(self):
        self.caso("atividades/x.md", fm(type="Atividade", **BASE, mem_status="fazendo", mem_escopo="mudanca"), "E-AUTORIZACAO")

    def test_autorizacao_em_prosa(self):
        self.caso("atividades/x.md", fm(type="Atividade", **BASE, mem_status="backlog", mem_escopo="mudanca",
                                        mem_autorizacao="o usuário disse que pode"), "E-AUTORIZACAO")

    def test_autorizacao_que_nao_e_decisao(self):
        self.escrever("runbooks/r.md", fm(type="Runbook", **BASE))
        self.caso("atividades/x.md", fm(type="Atividade", **BASE, mem_status="concluido", mem_escopo="mudanca",
                                        mem_autorizacao="/runbooks/r.md"), "E-AUTORIZACAO")

    def test_bloqueado_sem_motivo(self):
        self.caso("atividades/x.md", fm(type="Atividade", **BASE, mem_status="bloqueado", mem_escopo="leitura"), "E-CAMPO")

    def test_substituido_sem_deprecated(self):
        self.escrever("runbooks/novo.md", fm(type="Runbook", **BASE))
        self.caso("runbooks/velho.md", fm(type="Runbook", **BASE, mem_substituido_por="/runbooks/novo.md"), "E-SUBST")

    def test_link_quebrado(self):
        self.caso("runbooks/x.md", fm(type="Runbook", **BASE) + "Ver [algo](/runbooks/nao-existe.md).\n", "E-LINK")

    def test_link_em_codigo_nao_conta(self):
        self.escrever("runbooks/x.md", fm(type="Runbook", **BASE) + "Exemplo: `[x](/nao-existe.md)`\n")
        erros, _ = self.codigos()
        self.assertNotIn("E-LINK", erros)

    def test_indice_de_pasta_com_frontmatter(self):
        self.escrever("runbooks/index.md", "---\ntitle: x\n---\n# Runbooks\n", indices=False)
        erros, _ = self.codigos()
        self.assertIn("E-INDEX", erros)

    def test_indice_desatualizado(self):
        self.escrever("runbooks/x.md", fm(type="Runbook", **BASE), indices=False)
        erros, _ = self.codigos()
        self.assertIn("E-INDICE", erros)

    def test_log_fora_de_ordem(self):
        (self.kb / "log.md").write_text("# Log\n\n## 2026-10-01\n* **Criação**: a\n\n## 2026-10-05\n* **Criação**: b\n")
        erros, _ = self.codigos()
        self.assertIn("E-LOG", erros)

    def test_estado_acima_do_teto(self):
        p = self.kb / "estado.md"
        p.write_text(p.read_text() + "linha\n" * 80)
        erros, _ = self.codigos()
        self.assertIn("E-ESTADO", erros)

    def test_segredo(self):
        self.caso("runbooks/x.md", fm(type="Runbook", **BASE) + "curl -u elastic:Senha123 https://es:9200\n", "E-SEGREDO")

    def test_prosa_sobre_senha_nao_e_segredo(self):
        self.escrever("runbooks/x.md", fm(type="Runbook", **BASE) + "A senha: armazenada no cofre. token: `~/.env`\n")
        erros, _ = self.codigos()
        self.assertNotIn("E-SEGREDO", erros)

    def test_decisao_sem_data(self):
        self.caso("decisoes/algo.md", fm(type="Decisao", **BASE), "E-NOME")

    def test_janela_invertida(self):
        self.caso("baselines/x.md", fm(type="Baseline", **BASE, sources=[{"resource": "r"}], stale_after="2099-01-01T00:00:00Z",
                                       mem_janela={"de": "2026-10-08T00:00:00Z", "ate": "2026-10-01T00:00:00Z"}), "E-JANELA")

    def test_certificado_divergente(self):
        self.run_ok("certificar", "shards", "total", "--", "echo 42")
        self.escrever("baselines/x.md", fm(type="Baseline", **BASE, sources=[{"resource": "r"}], stale_after="2099-01-01T00:00:00Z",
                                           mem_janela={"de": "2026-10-01T00:00:00Z", "ate": "2026-10-08T00:00:00Z"},
                                           mem_certificados=[{"chave": "shards", "rotulo": "total", "valor": 42}]))
        erros, _ = self.codigos()
        self.assertNotIn("E-CERT", erros)
        self.run_ok("certificar", "shards", "total", "--", "echo 57")
        erros, _ = self.codigos()
        self.assertIn("E-CERT", erros)

    def test_stale_vencido_e_aviso(self):
        self.escrever("ambiente/x.md", fm(type="Componente", **BASE, sources=[{"resource": "r"}], stale_after="2020-01-01T00:00:00Z"))
        erros, avisos = self.codigos()
        self.assertEqual(erros, set())
        self.assertIn("A-STALE", avisos)


class TestOperacoes(Projeto):
    def test_log_e_rotacao(self):
        (self.kb / "log.md").write_text("# Log\n\n## 2020-01-05\n* **Criação**: antigo\n")
        self.run_ok("log", "Descoberta", "algo novo")
        texto = (self.kb / "log.md").read_text()
        self.assertLess(texto.index("Descoberta"), texto.index("2020-01-05"))
        self.run_ok("log", "--rotacionar")
        self.assertNotIn("2020-01-05", (self.kb / "log.md").read_text())
        self.assertIn("antigo", (self.kb / "historico" / "2020-01" / "log.md").read_text())
        erros, _ = self.codigos()
        self.assertEqual(erros, set())

    def test_rotulo_fora_do_perfil(self):
        self.assertNotEqual(self.cli("log", "Fofoca", "x").returncode, 0)

    def test_contrair_recusa_com_dependente_e_executa_sem(self):
        self.escrever("runbooks/alvo.md", fm(type="Runbook", **BASE))
        self.escrever("runbooks/fan.md", fm(type="Runbook", **BASE) + "[alvo](/runbooks/alvo.md)\n")
        self.assertEqual(self.cli("contrair", "runbooks/alvo.md", "--motivo", "m", "--executar").returncode, 1)
        (self.kb / "runbooks" / "fan.md").write_text(fm(type="Runbook", **BASE))
        self.run_ok("contrair", "runbooks/alvo.md", "--motivo", "superado", "--executar")
        self.assertFalse((self.kb / "runbooks" / "alvo.md").exists())
        self.assertIn("Remoção", (self.kb / "log.md").read_text())
        erros, _ = self.codigos()
        self.assertEqual(erros, set())

    def test_verificar_so_revisor(self):
        self.escrever("runbooks/x.md", fm(type="Runbook", **BASE))
        self.assertEqual(self.cli("verificar", "runbooks/x.md", "--por", "human:intruso").returncode, 1)
        self.run_ok("verificar", "runbooks/x.md", "--por", "human:teste")
        self.assertIn("human:teste", (self.kb / "runbooks" / "x.md").read_text())
        erros, _ = self.codigos()
        self.assertEqual(erros, set())

    def test_certificar_recusa_credencial(self):
        self.assertEqual(self.cli("certificar", "a", "b", "--", "curl -u elastic:Senha123 http://x").returncode, 1)


class TestHooks(Projeto):
    def bash(self, cmd, evento="PostToolUse"):
        return {"hook_event_name": evento, "session_id": "abc12345", "tool_name": "Bash",
                "tool_input": {"command": cmd, "description": "descrição"}, "tool_response": {}}

    def test_captura_escrita_ignora_leitura_e_mascara(self):
        self.hook("hook-captura", self.bash("curl -s https://es:9200/_cluster/health"))
        self.assertEqual(self.cli("pendentes").stdout.strip(), "nenhuma ação pendente de consolidação.")
        self.hook("hook-captura", self.bash("curl -XPUT -u elastic:Senha123 https://es:9200/_ilm/policy/x -d '{}'"))
        linhas = (self.root / ".claude" / "memoria" / "pendente.jsonl").read_text().splitlines()
        self.assertEqual(len(linhas), 1)
        self.assertNotIn("Senha123", linhas[0])

    def test_fim_bloqueia_com_pendente_e_respeita_stop_hook_active(self):
        self.hook("hook-captura", self.bash("systemctl restart elasticsearch"))
        r = self.hook("hook-fim", {"hook_event_name": "Stop"})
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        r = self.hook("hook-fim", {"hook_event_name": "Stop", "stop_hook_active": True})
        self.assertEqual(r.stdout.strip(), "")

    def test_consolidar_exige_log_novo(self):
        self.hook("hook-captura", self.bash("systemctl restart kibana"))
        time.sleep(1.1)
        self.assertEqual(self.cli("consolidar").returncode, 1)
        self.run_ok("log", "Mudança no ambiente", "kibana reiniciado")
        self.run_ok("consolidar")
        r = self.hook("hook-fim", {"hook_event_name": "Stop"})
        self.assertEqual(r.stdout.strip(), "")

    def test_consolidar_nada(self):
        self.hook("hook-captura", self.bash("systemctl restart kibana"))
        self.run_ok("consolidar", "--nada", "teste de laboratório")
        self.assertIn("teste de laboratório", next((self.root / ".claude" / "memoria" / "diario").glob("*.jsonl")).read_text())

    def test_fim_bloqueia_com_erro_de_lint(self):
        (self.kb / "runbooks" / "x.md").write_text("# sem cabeçalho\n")
        r = self.hook("hook-fim", {"hook_event_name": "Stop"})
        self.assertIn("E-FM", json.loads(r.stdout)["reason"])

    def test_guarda_verified(self):
        p = self.escrever("runbooks/x.md", fm(type="Runbook", **BASE))
        novo = p.read_text().replace("\n---\n", "\nverified:\n  - by: human:teste\n    at: 2026-10-22T10:00:00Z\n---\n", 1)
        self.assertIn("verified", novo)
        r = self.hook("hook-guarda", {"tool_name": "Write", "tool_input": {"file_path": str(p), "content": novo}})
        self.assertEqual(json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"], "deny")
        r = self.hook("hook-guarda", {"tool_name": "Edit", "tool_input": {"file_path": str(p), "old_string": "Uma frase.", "new_string": "Outra frase."}})
        self.assertEqual(r.stdout.strip(), "")

    def test_guarda_indice_gerado_e_segredo(self):
        idx = self.kb / "runbooks" / "index.md"
        r = self.hook("hook-guarda", {"tool_name": "Write", "tool_input": {"file_path": str(idx), "content": "x"}})
        self.assertIn("deny", r.stdout)
        p = self.kb / "runbooks" / "y.md"
        r = self.hook("hook-guarda", {"tool_name": "Write", "tool_input": {"file_path": str(p), "content": "password=Abc12345"}})
        self.assertIn("deny", r.stdout)

    def test_guarda_bash_verificar(self):
        r = self.hook("hook-guarda-bash", {"tool_name": "Bash", "tool_input": {"command": "lastro verificar runbooks/x.md --por human:teste"}})
        self.assertIn("deny", r.stdout)
        r = self.hook("hook-guarda-bash", {"tool_name": "Bash", "tool_input": {"command": "lastro lint"}})
        self.assertEqual(r.stdout.strip(), "")

    def test_formato_recusa_e_regenera_indice(self):
        p = self.escrever("runbooks/ruim.md", "# sem cabeçalho\n", indices=False)
        r = self.hook("hook-formato", {"tool_name": "Write", "tool_input": {"file_path": str(p)}})
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        p.write_text(fm(type="Runbook", **BASE))
        r = self.hook("hook-formato", {"tool_name": "Write", "tool_input": {"file_path": str(p)}})
        self.assertEqual(r.stdout.strip(), "")
        self.assertIn("/runbooks/ruim.md", (self.kb / "runbooks" / "index.md").read_text())

    def test_inicio_traz_briefing(self):
        self.hook("hook-captura", self.bash("systemctl restart kibana"))
        r = self.hook("hook-inicio", {"hook_event_name": "SessionStart", "source": "startup"})
        self.assertIn("ainda não estão na memória", r.stdout)

    def test_inerte_fora_de_projeto(self):
        with tempfile.TemporaryDirectory() as vazio:
            r = subprocess.run([str(LASTRO), "hook-fim"], cwd=vazio, env={**os.environ, "CLAUDE_PROJECT_DIR": vazio},
                               input="{}", capture_output=True, text=True)
            self.assertEqual((r.returncode, r.stdout.strip()), (0, ""))


class TestSigilo(Projeto):
    """A credencial nunca chega ao modelo: nem por acesso direto, nem por saída de ferramenta."""

    def setUp(self):
        super().setUp()
        import base64
        self.cofre = self.root / "cofre-teste"
        self.cofre.mkdir()
        self.decod = "idFalso123:segredoSuperSecreto987"
        self.chave = base64.b64encode(self.decod.encode()).decode()
        (self.cofre / "npr.env").write_text(f"ES_URL=https://exemplo.invalid\nES_API_KEY_LEITURA={self.chave}\n")
        perfil = self.root / ".claude" / "memoria.yaml"
        perfil.write_text(perfil.read_text().replace("arquivos: []", f"arquivos: ['{self.cofre}/*.env']"))

    def pre(self, ferramenta, **ti):
        r = self.hook("hook-sigilo-pre", {"hook_event_name": "PreToolUse", "tool_name": ferramenta, "tool_input": ti})
        return json.loads(r.stdout)["hookSpecificOutput"]["permissionDecision"] if r.stdout.strip() else "permitido"

    def pos(self, resposta, ferramenta="Bash"):
        r = self.hook("hook-sigilo-pos", {"hook_event_name": "PostToolUse", "tool_name": ferramenta,
                                          "tool_input": {}, "tool_response": resposta})
        return json.loads(r.stdout)["hookSpecificOutput"] if r.stdout.strip() else None

    def test_bash_no_arquivo_de_credencial_e_negado(self):
        self.assertEqual(self.pre("Bash", command=f". {self.cofre}/npr.env; echo ok"), "deny")
        self.assertEqual(self.pre("Bash", command="cat ~/cofre-teste/npr.env"), "deny")

    def test_bash_com_variavel_secreta_e_negado(self):
        self.assertEqual(self.pre("Bash", command='curl -H "Authorization: ApiKey $ES_API_KEY_LEITURA" x'), "deny")
        self.assertEqual(self.pre("Bash", command='echo ${ES_API_KEY_LEITURA}'), "deny")

    def test_bash_com_credencial_por_extenso_e_negado(self):
        self.assertEqual(self.pre("Bash", command=f"curl -H 'Authorization: ApiKey {self.chave}' x"), "deny")

    def test_bash_normal_passa(self):
        self.assertEqual(self.pre("Bash", command="bin/es npr GET /_cluster/health"), "permitido")
        self.assertEqual(self.pre("Bash", command="echo $ES_URL_QUALQUER; ls"), "permitido")

    def test_read_grep_edit_no_cofre_sao_negados(self):
        self.assertEqual(self.pre("Read", file_path=str(self.cofre / "npr.env")), "deny")
        self.assertEqual(self.pre("Grep", pattern="KEY", path=str(self.cofre)), "deny")
        self.assertEqual(self.pre("Edit", file_path=str(self.cofre / "npr.env"), old_string="a", new_string="b"), "deny")
        self.assertEqual(self.pre("Read", file_path=str(self.root / "CLAUDE.md")), "permitido")

    def test_saida_com_chave_e_redigida_preservando_a_forma(self):
        resp = {"stdout": f"ES_API_KEY_LEITURA={self.chave}\nfim", "stderr": "", "interrupted": False, "isImage": False}
        out = self.pos(resp)
        novo = out["updatedToolOutput"]
        self.assertEqual(set(novo), set(resp))
        self.assertNotIn(self.chave, json.dumps(novo))
        self.assertIn("[SEGREDO REMOVIDO: npr.env:ES_API_KEY_LEITURA]", novo["stdout"])
        self.assertIn("fim", novo["stdout"])

    def test_forma_decodificada_tambem_e_redigida(self):
        segredo = self.decod.split(":", 1)[1]
        out = self.pos({"stdout": f"id e chave: {self.decod} | so a chave: {segredo}", "stderr": "",
                        "interrupted": False, "isImage": False})
        self.assertNotIn(segredo, json.dumps(out["updatedToolOutput"]))

    def test_estrutura_aninhada_de_outra_ferramenta(self):
        out = self.pos({"file": {"content": f"x {self.chave} y", "numLines": 1}}, ferramenta="Read")
        self.assertNotIn(self.chave, json.dumps(out["updatedToolOutput"]))
        self.assertEqual(out["updatedToolOutput"]["file"]["numLines"], 1)

    def test_saida_sem_segredo_nao_muda(self):
        self.assertIsNone(self.pos({"stdout": "cluster yellow", "stderr": "", "interrupted": False, "isImage": False}))

    def test_registro_de_auditoria_sem_o_valor(self):
        self.pos({"stdout": self.chave, "stderr": "", "interrupted": False, "isImage": False})
        log = (self.root / ".claude" / "memoria" / "diario" / "sigilo.jsonl").read_text()
        self.assertIn("npr.env:ES_API_KEY_LEITURA", log)
        self.assertNotIn(self.chave, log)

    def test_inerte_sem_segredos_no_perfil(self):
        perfil = self.root / ".claude" / "memoria.yaml"
        perfil.write_text(perfil.read_text().replace(f"arquivos: ['{self.cofre}/*.env']", "arquivos: []"))
        self.assertIsNone(self.pos({"stdout": self.chave, "stderr": "", "interrupted": False, "isImage": False}))


class TestCommitAutomatico(Projeto):
    def setUp(self):
        super().setUp()
        g = lambda *a, cwd=None: subprocess.run(["git", *a], cwd=cwd or self.root, capture_output=True, text=True, check=True)
        self.git = g
        self.remoto = Path(self.tmp.name + "-remoto.git")
        g("init", "-q", "--bare", str(self.remoto), cwd="/")
        g("init", "-q", "-b", "main")
        g("config", "user.email", "teste@exemplo.invalid"); g("config", "user.name", "Teste")
        g("remote", "add", "origin", str(self.remoto))
        perfil = self.root / ".claude" / "memoria.yaml"
        perfil.write_text(perfil.read_text().replace("commit_automatico: false", "commit_automatico: true")
                          .replace("push: false", "push: true"))
        g("add", "-A"); g("commit", "-q", "-m", "inicial"); g("push", "-q", "-u", "origin", "main")

    def tearDown(self):
        import shutil
        shutil.rmtree(self.remoto, ignore_errors=True)
        super().tearDown()

    def fim(self):
        return self.hook("hook-fim", {"hook_event_name": "Stop"})

    def test_commita_e_envia_com_titulo_do_log(self):
        self.escrever("runbooks/x.md", fm(type="Runbook", **BASE))
        self.cli("log", "Criação", "runbook x — ver [x](/runbooks/x.md)")
        self.assertEqual(self.fim().stdout.strip(), "")
        titulo = self.git("log", "-1", "--format=%s").stdout.strip()
        self.assertEqual(titulo, "memória: Criação: runbook x — ver x")
        self.assertEqual(self.git("status", "--porcelain").stdout.strip(), "")
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, self.git("rev-parse", "main", cwd=str(self.remoto)).stdout)

    def test_credencial_recusa_o_commit_inteiro(self):
        antes = self.git("rev-parse", "HEAD").stdout
        # fora do bundle (o lint não vê), mas dentro de git.caminhos: a varredura do commit tem de pegar
        (self.root / "CLAUDE.md").write_text("acesso: curl -u elastic:Senha123 https://x\n")
        out = json.loads(self.hook("hook-fim", {"hook_event_name": "Stop", "stop_hook_active": True}).stdout)
        self.assertIn("RECUSADO", out.get("systemMessage", ""))
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, antes)

    def test_erro_de_lint_nao_commita(self):
        antes = self.git("rev-parse", "HEAD").stdout
        (self.kb / "runbooks" / "ruim.md").write_text("# sem cabeçalho\n")
        r = self.fim()
        self.assertEqual(json.loads(r.stdout)["decision"], "block")
        self.hook("hook-fim", {"hook_event_name": "Stop", "stop_hook_active": True})
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, antes)

    def test_fora_dos_caminhos_nao_entra(self):
        (self.root / "coleta-bruta.json").write_text('{"dado": 1}')
        self.cli("log", "Descoberta", "algo")
        self.fim()
        self.assertIn("coleta-bruta.json", self.git("status", "--porcelain").stdout)
        self.assertNotIn("coleta-bruta.json", self.git("show", "--name-only", "--format=").stdout)

    def test_desligado_nao_commita(self):
        perfil = self.root / ".claude" / "memoria.yaml"
        perfil.write_text(perfil.read_text().replace("commit_automatico: true", "commit_automatico: false"))
        antes = self.git("rev-parse", "HEAD").stdout
        self.cli("log", "Descoberta", "algo")
        self.fim()
        self.assertEqual(self.git("rev-parse", "HEAD").stdout, antes)


if __name__ == "__main__":
    unittest.main()
