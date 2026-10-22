#!/usr/bin/env python3
"""Gera os diagramas do README (docs/img/*.png) a partir de SVG escrito aqui.

Uso: python3 docs/diagramas/gerar.py      (precisa de rsvg-convert no PATH)
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.sax.saxutils import escape

SAIDA = Path(__file__).resolve().parent.parent / "img"
FONTE = "DejaVu Sans, Liberation Sans, sans-serif"
MONO = "DejaVu Sans Mono, Liberation Mono, monospace"

INK, MUTED, LINE, PAPER, BG = "#1f2937", "#6b7280", "#9ca3af", "#ffffff", "#f8fafc"
COR = {  # (traço, preenchimento)
    "gerado": ("#047857", "#d1fae5"),
    "julgado": ("#6d28d9", "#ede9fe"),
    "contexto": ("#1d4ed8", "#dbeafe"),
    "executado": ("#b45309", "#fef3c7"),
    "problema": ("#b91c1c", "#fee2e2"),
    "neutro": ("#475569", "#f1f5f9"),
}


class Svg:
    def __init__(self, w, h):
        self.w, self.h, self.p = w, h, []

    def add(self, s):
        self.p.append(s)

    def rect(self, x, y, w, h, fill=PAPER, stroke=LINE, r=14, sw=2, dash=None):
        d = f' stroke-dasharray="{dash}"' if dash else ""
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"{d}/>')

    def text(self, x, y, s, size=18, weight="normal", fill=INK, anchor="start", mono=False, italic=False):
        st = ' font-style="italic"' if italic else ""
        self.add(f'<text x="{x}" y="{y}" font-family="{MONO if mono else FONTE}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>{escape(s)}</text>')

    def lines(self, x, y, linhas, size=17, lh=None, **kw):
        lh = lh or int(size * 1.45)
        for i, l in enumerate(linhas):
            self.text(x, y + i * lh, l, size=size, **kw)
        return y + len(linhas) * lh

    def arrow(self, pts, color=MUTED, sw=2.5, dash=None, label=None, lpos=None, lsize=15):
        d = "M " + " L ".join(f"{x} {y}" for x, y in pts)
        da = f' stroke-dasharray="{dash}"' if dash else ""
        mid = f"m{color.strip('#')}"
        self.add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{sw}" marker-end="url(#{mid})"{da}/>')
        if label:
            lx, ly = lpos or pts[len(pts) // 2]
            self.text(lx, ly, label, size=lsize, fill=color, anchor="middle", weight="bold")

    def diamond(self, cx, cy, w, h, linhas, cor="neutro", size=16):
        s, f = COR[cor]
        self.add(f'<polygon points="{cx},{cy - h / 2} {cx + w / 2},{cy} {cx},{cy + h / 2} {cx - w / 2},{cy}" '
                 f'fill="{f}" stroke="{s}" stroke-width="2.5"/>')
        y0 = cy - (len(linhas) - 1) * size * 0.65 + size * 0.35
        self.lines(cx, y0, linhas, size=size, lh=int(size * 1.3), anchor="middle", weight="bold", fill=s)

    def card(self, x, y, w, h, titulo, linhas, cor="neutro", size=17, tsize=20, mono=False, sub=None):
        s, f = COR[cor]
        self.rect(x, y, w, h, fill=f, stroke=s, sw=2.5)
        self.text(x + 20, y + 36, titulo, size=tsize, weight="bold", fill=s)
        yy = y + 36
        if sub:
            self.text(x + 20, y + 62, sub, size=15, fill=s, italic=True)
            yy += 26
        self.lines(x + 20, yy + 32, linhas, size=size, mono=mono)

    def box(self, x, y, w, h, linhas, cor="neutro", size=17, bold_first=True, center=True, mono_rest=False):
        s, f = COR[cor]
        self.rect(x, y, w, h, fill=f, stroke=s, sw=2.5, r=12)
        lh = int(size * 1.4)
        y0 = y + h / 2 - (len(linhas) - 1) * lh / 2 + size * 0.35
        for i, l in enumerate(linhas):
            self.text(x + w / 2 if center else x + 18, y0 + i * lh, l, size=size,
                      weight="bold" if (bold_first and i == 0) else "normal",
                      fill=s if (bold_first and i == 0) else INK, anchor="middle" if center else "start",
                      mono=mono_rest and i > 0)

    def svg(self):
        cores = {c for c in [MUTED, INK, LINE] + [v[0] for v in COR.values()]}
        marcadores = "".join(
            f'<marker id="m{c.strip("#")}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
            f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>' for c in cores)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<defs>{marcadores}</defs><rect width="100%" height="100%" fill="{BG}"/>' + "".join(self.p) + "</svg>")


def titulo(s, t, sub):
    s.text(60, 64, t, size=34, weight="bold")
    s.text(60, 100, sub, size=18, fill=MUTED)


# ── 1. o problema ─────────────────────────────────────────────────────────────

def d1():
    s = Svg(1600, 990)
    titulo(s, "Por que a memória de um projeto apodrece",
           "Medido em dois projetos reais trabalhados com o Claude Code: um de desenvolvimento (194 mil linhas) e um de operação em produção.")
    s.rect(60, 130, 1480, 250, fill=PAPER)
    s.text(90, 172, "O que existe × o que chega ao modelo", size=20, weight="bold")
    linhas = [("Prosa escrita pelo projeto", 1.0, "7,97 MB · 247 documentos + 105 memórias", COR["neutro"][0]),
              ("Chega sozinho a uma sessão nova", 0.0031, "24 KB · 0,31%", COR["problema"][0]),
              ("Chega a um subagente", 0.0, "0 bytes", COR["problema"][0])]
    for i, (rot, frac, val, cor) in enumerate(linhas):
        y = 212 + i * 46
        s.text(90, y + 20, rot, size=17)
        larg = max(6, 1000 * frac) if frac else 0
        s.rect(430, y, 1000, 28, fill="#eef2f7", stroke="none", r=6, sw=0)
        if larg:
            s.rect(430, y, larg, 28, fill=cor, stroke="none", r=6, sw=0)
        s.text(430 + (larg + 14 if larg < 600 else 16), y + 20, val, size=16, weight="bold",
               fill=cor if larg < 600 else "#ffffff")
    s.text(90, 358, "O resto só chega se alguém souber qual arquivo abrir — e a sessão remede o que já foi medido.",
           size=16, fill=MUTED, italic=True)
    cards = [
        ("O índice virou o conteúdo", "95,6%", ["do teto de 25 KB que o harness carrega;", "9 linhas com mais de 500 caracteres —",
                                                 "a sessão lê o resumo e não abre o arquivo."]),
        ("Memória órfã, viva na busca", "50 de 104", ["arquivos fora do índice, nunca revisados;", "41 descrevem arquitetura extinta,",
                                                      "e nenhum está marcado como obsoleto."]),
        ("Estado fóssil", "0", ["documentos descreviam o sistema hoje;", "o de status dizia “não há código”",
                                "com 194 mil linhas na árvore."]),
        ("Só se acrescenta, nunca se poda", "472 KB", ["num único log.md; uma frente escrita", "3 a 4 vezes (1,1 MB) — e nenhuma",
                                                       "operação para matar um documento."]),
        ("A gravação depende de lembrar", "0 hooks", ["ligavam a ação à memória: o registro", "acontecia no fim da sessão longa,",
                                                      "justo quando o modelo mais erra."]),
        ("O formato deriva em silêncio", "61 campos", ["saíram da spec quando ela trocou data", "por instante com fuso — e nenhum",
                                                       "validador oficial avisou."]),
    ]
    for i, (t, num, ls) in enumerate(cards):
        x, y = 60 + (i % 3) * 505, 410 + (i // 3) * 280
        st, fi = COR["problema"]
        s.rect(x, y, 470, 250, fill=PAPER, stroke=st, sw=2.5)
        s.rect(x, y, 10, 250, fill=st, stroke="none", r=4, sw=0)
        s.text(x + 34, y + 44, t, size=21, weight="bold")
        s.text(x + 34, y + 104, num, size=42, weight="bold", fill=st)
        s.lines(x + 34, y + 150, ls, size=17)
    return s


# ── 2. arquitetura ────────────────────────────────────────────────────────────

def d2():
    s = Svg(1600, 990)
    titulo(s, "O OKF dá o vocabulário. O harness dá a execução.",
           "O lastro junta os dois num bundle versionado no git do próprio projeto.")
    topo = [
        (60, "OKF v0.2 — o formato", "contexto", ["um conceito por arquivo .md", "type obrigatório; title, description",
                                                   "sources: de onde saiu", "generated · verified (human:)",
                                                   "status · stale_after (instante)", "index.md e log.md reservados"]),
        (585, "Perfil do projeto", "julgado", ["os tipos e a pasta de cada um", "campos mem_: status, escopo,",
                                               "autorizacao, substituido_por, janela", "donos e revisores humanos",
                                               "padrões de captura do domínio", "tetos do estado e do log"]),
        (1110, "Claude Code — a execução", "executado", ["hooks: SessionStart, PreToolUse,", "PostToolUse e Stop",
                                                          "skill lastro:memoria", "CLAUDE.md + @estado.md",
                                                          ".claude/rules com paths:", "o comando lastro no PATH"]),
    ]
    subs = ["especificação aberta do Google Cloud", ".claude/memoria.yaml", "o harness do Claude Code"]
    for (x, t, c, ls), sb in zip(topo, subs):
        s.card(x, 130, 430, 260, t, ls, cor=c, sub=sb)
        s.arrow([(x + 215, 392), (x + 215, 442)], color=COR[c][0])
    st, fi = COR["neutro"]
    s.rect(60, 450, 1480, 210, fill=PAPER, stroke=st, sw=2.5)
    s.text(90, 494, "knowledge/", size=24, weight="bold", mono=True)
    s.text(258, 494, "— o bundle: Markdown com frontmatter, no git do projeto", size=18, fill=MUTED)
    chips = [("estado.md", "contexto"), ("log.md", "gerado"), ("index.md", "neutro"), ("atividades/", "neutro"),
             ("ambiente/", "neutro"), ("baselines/", "neutro"), ("analises/", "neutro"), ("decisoes/", "julgado"),
             ("runbooks/", "neutro"), ("resolucoes/", "neutro"), ("historico/", "gerado"), ("certificados.tsv", "julgado")]
    x, y = 90, 526
    for nome, c in chips:
        w = 26 + len(nome) * 12
        if x + w > 1510:
            x, y = 90, y + 58
        s.rect(x, y, w, 42, fill=COR[c][1], stroke=COR[c][0], r=21, sw=2)
        s.text(x + w / 2, y + 28, nome, size=17, mono=True, anchor="middle", fill=COR[c][0], weight="bold")
        x += w + 16
    camadas = [
        ("Gerado", "gerado", "derivado por script, nunca editado", ["index.md das pastas", "historico/AAAA-MM/log.md",
                                                                     "o resumo do início da sessão"]),
        ("Julgado", "julgado", "mão humana, mínima e assinada", ["verified (lastro verificar)", "a Decisao que autoriza",
                                                                 "certificados (só acréscimo)"]),
        ("Contexto", "contexto", "o modelo lê e tenta seguir", ["CLAUDE.md curto", "estado.md com teto,", "que chega aos subagentes"]),
        ("Executado", "executado", "o harness roda; o modelo não escolhe", ["captura das ações", "lint na hora e no fim do turno",
                                                                             "Stop que cobra a consolidação"]),
    ]
    for i, (t, c, sb, ls) in enumerate(camadas):
        s.card(60 + i * 377, 705, 351, 190, t, ls, cor=c, sub=sb, tsize=22)
    s.text(800, 948, "A regra que move algo de contexto para executado: se falhar uma vez custa mais do que o hook, vira hook.",
           size=18, anchor="middle", weight="bold", fill=COR["executado"][0])
    return s


# ── 3. uma sessão ─────────────────────────────────────────────────────────────

def d3():
    s = Svg(1600, 900)
    titulo(s, "Uma sessão com o lastro", "O modelo trabalha normalmente; os hooks garantem que nada do que mudou fique fora da memória.")
    faixas = [("Você e o modelo", "contexto", 190), ("Hooks do harness", "executado", 410), ("Bundle e captura", "gerado", 630)]
    for nome, c, y in faixas:
        s.rect(40, y - 20, 1520, 200, fill=COR[c][1], stroke="none", r=16, sw=0)
        s.add(f'<text x="70" y="{y + 80}" font-family="{FONTE}" font-size="18" font-weight="bold" fill="{COR[c][0]}" '
              f'transform="rotate(-90 70 {y + 80})" text-anchor="middle">{escape(nome)}</text>')
    cols = ["1 · Começar", "2 · Agir no ambiente", "3 · Gravar na memória", "4 · Encerrar o turno"]
    xs = [110, 470, 830, 1190]
    for x, c in zip(xs, cols):
        s.text(x + 170, 160, c, size=20, weight="bold", anchor="middle")
    W, H = 340, 160
    cel = {
        (0, 0): ["a sessão já sabe", "onde o projeto está", "antes da 1ª pergunta"],
        (0, 1): ["SessionStart", "monta o resumo", "(até 8 mil caracteres)"],
        (0, 2): ["lint · ações pendentes", "atividades em andamento", "vencidos · últimas do log"],
        (1, 0): ["roda um comando", "que muda o ambiente", "(ex.: PUT de uma política)"],
        (1, 1): ["PostToolUse", "casa com a captura?", "mascara a credencial"],
        (1, 2): ["pendente.jsonl", "uma linha por ação", "(fica fora do git)"],
        (2, 0): ["grava o conceito", "pela skill", "lastro:memoria"],
        (2, 1): ["PreToolUse nega índice,", "verified e segredo;", "PostToolUse: lint + índice"],
        (2, 2): ["conceito atualizado", "+ uma linha via", "lastro log"],
        (3, 0): ["tenta encerrar", "→ recebe o motivo", "e consolida"],
        (3, 1): ["Stop", "pendência ou erro?", "bloqueia uma vez"],
        (3, 2): ["lastro consolidar", "→ diário local", "Stop libera"],
    }
    for (ci, fi), ls in cel.items():
        cor = faixas[fi][1]
        s.box(xs[ci], faixas[fi][2], W, H, ls, cor=cor, size=17)
    cx = [x + W / 2 for x in xs]
    y0, y1, y2 = 190, 410, 630
    s.arrow([(cx[0], y2), (cx[0], y1 + H + 4)], color=COR["executado"][0])
    s.arrow([(cx[0], y1), (cx[0], y0 + H + 4)], color=COR["contexto"][0])
    s.arrow([(cx[1], y0 + H), (cx[1], y1 - 4)], color=COR["executado"][0])
    s.arrow([(cx[1], y1 + H), (cx[1], y2 - 4)], color=COR["gerado"][0])
    s.arrow([(cx[2], y0 + H), (cx[2], y1 - 4)], color=COR["executado"][0])
    s.arrow([(cx[2], y1 + H), (cx[2], y2 - 4)], color=COR["gerado"][0])
    s.arrow([(cx[3] - 60, y0 + H), (cx[3] - 60, y1 - 4)], color=COR["executado"][0])
    s.arrow([(cx[3] + 60, y1), (cx[3] + 60, y0 + H + 4)], color=COR["problema"][0])
    s.text(cx[3] + 72, y1 - 14, "continua o turno", size=14, weight="bold", fill=COR["problema"][0])
    s.arrow([(cx[3], y1 + H), (cx[3], y2 - 4)], color=COR["gerado"][0])
    s.arrow([(110, 842), (1526, 842)], color=LINE, sw=2)
    s.text(800, 875, "o tempo da sessão", size=15, fill=MUTED, anchor="middle", italic=True)
    return s


# ── 4. captura e consolidação ─────────────────────────────────────────────────

def d4():
    s = Svg(1600, 980)
    titulo(s, "Da ação à memória: captura e consolidação",
           "Leitura nunca é cobrada. O que muda o ambiente é registrado na hora e precisa de destino antes de o turno acabar.")
    s.text(60, 160, "Durante o turno", size=20, weight="bold", fill=COR["executado"][0])
    s.box(60, 190, 250, 120, ["Comando Bash", "ou ferramenta MCP"], cor="contexto", size=18)
    s.diamond(470, 250, 230, 150, ["casa com", "captura?"], cor="neutro")
    s.diamond(790, 250, 230, 150, ["casa com", "ignorar?"], cor="neutro")
    s.box(990, 190, 240, 120, ["mascara", "credencial"], cor="executado", size=18)
    s.box(1290, 190, 250, 120, ["pendente.jsonl", "fora do git"], cor="gerado", size=18)
    s.arrow([(310, 250), (353, 250)])
    s.arrow([(585, 250), (673, 250)], label="sim", lpos=(629, 240))
    s.arrow([(905, 250), (986, 250)], label="não", lpos=(945, 240))
    s.arrow([(1230, 250), (1286, 250)])
    s.box(370, 380, 200, 90, ["ignorado", "é leitura"], cor="neutro", size=16)
    s.box(670, 380, 240, 90, ["ignorado", "POST de busca etc."], cor="neutro", size=16)
    s.arrow([(470, 325), (470, 376)], label="não", lpos=(500, 357))
    s.arrow([(790, 325), (790, 376)], label="sim", lpos=(820, 357))
    s.add(f'<line x1="60" y1="520" x2="1540" y2="520" stroke="{LINE}" stroke-width="2" stroke-dasharray="8 8"/>')
    s.text(60, 570, "No fim do turno", size=20, weight="bold", fill=COR["executado"][0])
    s.box(60, 600, 250, 120, ["o modelo", "tenta encerrar"], cor="contexto", size=18)
    s.diamond(470, 660, 230, 150, ["Stop: há", "pendência?"], cor="executado")
    s.box(370, 800, 200, 90, ["encerra"], cor="neutro", size=18)
    s.box(670, 600, 260, 120, ["bloqueia uma vez", "“registre e consolide”"], cor="problema", size=17)
    s.box(990, 560, 300, 100, ["conceito + lastro log", "→ lastro consolidar"], cor="julgado", size=17)
    s.box(990, 690, 300, 100, ["nada merece memória", "→ consolidar --nada"], cor="julgado", size=17)
    s.box(1340, 600, 200, 120, ["diário local", "e o Stop libera"], cor="gerado", size=17)
    s.arrow([(310, 660), (353, 660)])
    s.arrow([(470, 735), (470, 796)], label="não", lpos=(500, 772))
    s.arrow([(585, 660), (666, 660)], label="sim", lpos=(625, 650))
    s.arrow([(930, 640), (986, 610)])
    s.arrow([(930, 680), (986, 740)])
    s.arrow([(1290, 610), (1336, 640)])
    s.arrow([(1290, 740), (1336, 690)])
    s.lines(990, 830, ["o consolidar recusa se o log.md não mudou", "desde a primeira ação pendente"], size=15, fill=MUTED, italic=True)
    s.text(800, 950, "A segunda tentativa de encerrar passa sempre (stop_hook_active): o hook cobra, não prende.",
           size=17, anchor="middle", fill=MUTED, italic=True)
    return s


# ── 5. ciclo de vida ──────────────────────────────────────────────────────────

def d5():
    s = Svg(1600, 1000)
    titulo(s, "O ciclo de vida: do conceito e da atividade",
           "O OKF dá status e prazo; o lastro acrescenta quem carimba, quem substitui, como se remove e o que autoriza.")
    s.text(60, 160, "Conceito", size=22, weight="bold")
    s.box(60, 190, 250, 130, ["nasce", "generated · sources", "type na pasta certa"], cor="neutro")
    s.box(400, 190, 250, 130, ["vigente", "status: stable", "serve para investigar"], cor="contexto")
    s.box(800, 190, 280, 130, ["verificado", "verified por human:…", "embasa mudança"], cor="julgado")
    s.box(400, 400, 250, 130, ["vencido", "stale_after passou", "reconferir antes de agir"], cor="executado")
    s.box(1170, 190, 230, 130, ["superado", "deprecated +", "mem_substituido_por"], cor="neutro")
    s.box(1170, 400, 230, 130, ["removido", "lastro contrair", "motivo no log"], cor="problema")
    s.arrow([(310, 255), (396, 255)])
    s.arrow([(650, 240), (796, 240)], label="lastro verificar", lpos=(723, 228), lsize=13)
    s.arrow([(796, 285), (654, 285)], label="texto mudou", lpos=(725, 307), lsize=13, color=COR["problema"][0])
    s.arrow([(500, 320), (500, 396)], label="o relógio", lpos=(450, 365), lsize=13, color=COR["executado"][0])
    s.arrow([(560, 396), (560, 324)], label="reconferido", lpos=(616, 365), lsize=13, color=COR["contexto"][0])
    s.arrow([(1080, 255), (1166, 255)], label="novo vale", lpos=(1123, 243), lsize=13)
    s.arrow([(1285, 320), (1285, 396)], label="ninguém depende", lpos=(1365, 365), lsize=13, color=COR["problema"][0])
    s.lines(1425, 215, ["só o revisor", "humano carimba;", "o hook nega", "o agente"], size=15, fill=COR["julgado"][0], italic=True)
    s.add(f'<line x1="60" y1="590" x2="1540" y2="590" stroke="{LINE}" stroke-width="2" stroke-dasharray="8 8"/>')
    s.text(60, 640, "Atividade", size=22, weight="bold")
    s.box(60, 680, 220, 110, ["backlog", "mem_status"], cor="neutro")
    s.box(560, 680, 220, 110, ["fazendo"], cor="contexto")
    s.box(900, 680, 220, 110, ["concluido"], cor="gerado")
    s.box(560, 850, 220, 100, ["bloqueado", "mem_bloqueado_por"], cor="executado", size=16)
    s.box(900, 850, 220, 100, ["cancelado"], cor="neutro")
    s.diamond(420, 735, 200, 140, ["mem_escopo:", "mudanca?"], cor="julgado", size=15)
    s.arrow([(280, 735), (318, 735)])
    s.arrow([(520, 735), (556, 735)], label="não", lpos=(538, 722), lsize=13)
    s.arrow([(780, 735), (896, 735)])
    s.arrow([(640, 790), (640, 846)])
    s.arrow([(700, 846), (700, 794)])
    s.arrow([(780, 760), (896, 880)])
    s.box(250, 850, 260, 100, ["mem_autorizacao", "→ link para a Decisao"], cor="julgado", size=16)
    s.arrow([(420, 805), (420, 846)], label="sim", lpos=(445, 832), lsize=13)
    s.arrow([(510, 870), (556, 760)], color=COR["julgado"][0])
    s.lines(1180, 700, ["Atividade de mudança em fazendo", "ou concluido sem o link para", "uma Decisao existente é erro",
                        "de lint — e o Stop não encerra", "o turno com erro de lint."], size=16, fill=COR["julgado"][0])
    return s


def main():
    if not shutil.which("rsvg-convert"):
        sys.exit("erro: rsvg-convert não encontrado (apt install librsvg2-bin)")
    SAIDA.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for nome, fn in [("01-o-problema", d1), ("02-arquitetura", d2), ("03-uma-sessao", d3),
                         ("04-captura-e-consolidacao", d4), ("05-ciclo-de-vida", d5)]:
            svg = Path(tmp) / f"{nome}.svg"
            svg.write_text(fn().svg(), encoding="utf-8")
            subprocess.run(["rsvg-convert", "-z", "1.5", str(svg), "-o", str(SAIDA / f"{nome}.png")], check=True)
            print(f"docs/img/{nome}.png")


if __name__ == "__main__":
    main()
