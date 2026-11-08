"""Packen: Arc-Flow, der Graph statt der Muster - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 5 der Reihe „Packen: Reihenfolge und Platzierungsregel“ (gelb). Das Arc-Flow-Modell packt nicht Muster, sondern einen Fluss in einem Graphen über die Lasten 0 bis C. Drei Stufen der Kompression
machen den Graphen klein; das ganzzahlige Programm liefert das Optimum, mit dem FFD und die Schranken aus Stück 2 und 4 verglichen werden. Das Messraster (vorberechnet in arf_precomputed.json)
zeigt an je 100 Instanzen, wie viel die Kompression spart und wie oft das Optimum bestimmbar ist.

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import arf_algorithm as A
import arf_constants as C
from arf_evaluation import (
    Settings,
    analyse,
    verdict_aktuell,
    verdict_entscheidung,
    verdict_groesse,
    verdict_kompression,
    verdict_lp,
    verdict_lp_raster,
    zeile,
)
from arf_layout import dunkles_design, kopf_css
from arf_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from arf_visualization import build_container, build_graph, build_groessen, build_raster_ausgang, build_raster_groesse

st.set_page_config(page_title="Packen – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Der Arc-Flow wird gelöst …")
def _analysis(settings):
    return analyse(settings)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in arf_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🕸️ Arc-Flow: der Graph statt der Muster")
st.markdown(
    """
Stück 2 und 4 haben mit Schranken und dem LP gefragt, ob FFD optimal ist. Das **Arc-Flow-Modell** liefert das Optimum selbst: Statt Muster (Teilmengen von Paketen) aufzuzählen, packt es einen **Fluss in einem Graphen über die Lasten 0 bis C**. Ein Container ist ein Weg von 0 nach C, jedes Paket ein Bogen. Zwei Fragen: **Wie viel spart die Graphkompression**, und **wie oft ist das Optimum damit bestimmbar**, auch dort, wo Stück 4 das Optimum offen ließ? Die Spaltenerzeugung (Column Generation) löst dasselbe Muster-Modell ohne Graph; sie wird hier nicht erklärt.

Weiter unten: der Abschnitt **🔬 Experimente**, **🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So funktioniert der Arc-Flow", expanded=True):
    st.markdown(
        """
1. **Graph:** Die Knoten sind Lasten. Ein Bogen von u nach u + w heißt: Ein Paket der Größe w kommt bei der Last u in den Container. Ein grauer Verlustbogen füllt den Rest bis zur Kapazität C auf.
2. **Fluss:** Ein Rückbogen von C nach 0 zählt die Container. Im Graphen fließt so viel, dass jede Größe mindestens so oft vorkommt, wie es Pakete dieser Größe gibt. Der kleinste Fluss ist die Zahl der Container; als LP (Brüche erlaubt) ist er eine Schranke, als ganzes Programm das Optimum.
3. **Kompression:** *Voll* hat alle Lasten 0 bis C und jeden Bogen an jedem Knoten. *Normal* behält nur die Lasten, die Summen von Paketen sind. *Geordnet* lässt einen Bogen der Größe w nur an Lasten beginnen, die aus Paketen mindestens dieser Größe bestehen (jedes Muster hat einen Weg mit absteigenden Größen).
4. **Packung:** Der ganzzahlige Fluss wird in Wege zerlegt; jeder Weg ist ein Container, jeder Bogen nimmt ein Paket seiner Größe.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    quelle = st.selectbox("Instanz", list(C.BEISPIEL_NAMEN), format_func=C.BEISPIEL_NAMEN.get, key="quelle_select",
                          help="Fünf feste Beispiele (Kapazität 10 und 100) und eine Zufallsinstanz.")
    verteilung = st.selectbox("Verteilung der Größen (nur Zufallsinstanz)", list(range(len(C.VERTEILUNGEN))), format_func=lambda i: C.VERTEILUNGEN[i][1], key="verteilung_select",
                              help="Gilt nur für die Zufallsinstanz.")
    n = st.number_input("Zahl der Pakete (nur Zufallsinstanz)", *bounds("n_input"), key="n_input", step=1, help="Gilt nur für die Zufallsinstanz.")
    seed = st.number_input("Startzahl der Zufallsinstanz", *bounds("seed_input"), key="seed_input", step=1, help="Wirkt nur bei der Zufallsinstanz.")
    st.button("🎲 Neue Zufallsinstanz würfeln", width="stretch", on_click=randomize_seed)
    st.markdown("**Graph**")
    stufe = st.selectbox("Stufe der Kompression", list(C.STUFEN), format_func=C.STUFEN.get, key="stufe_select",
                         help="Welcher Graph gezeichnet und mit dem ganzzahligen Programm gelöst wird. Das Optimum ist in jeder Stufe dasselbe.")

sync_query_params({"quelle_select": int(quelle), "verteilung_select": int(verteilung), "n_input": int(n), "seed_input": int(seed), "stufe_select": int(stufe)})

settings = Settings(int(quelle), int(verteilung), int(n), int(seed), int(stufe))
a = _analysis(settings)

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2).
if a.opt is not None:
    m1.metric("Optimum (Arc-Flow)", a.opt, delta=a.opt - a.ffd, delta_color="inverse", help="Delta: Optimum minus FFD.")
else:
    m1.metric("Optimum (Arc-Flow)", "offen", delta="Zeitlimit erreicht", delta_color="off")
m2.metric("FFD", a.ffd, delta="Vergleich", delta_color="off")
m3.metric("L1 / L2", f"{a.l1} / {a.l2}", delta="Schranken aus Stück 2", delta_color="off")
m4.metric("Aufgerundeter LP-Wert", A.lp_aufgerundet(a.lp[2]), delta=f"LP {a.lp[2]:.2f} (geordnet)", delta_color="off")
st.caption(f"{a.inst.n} Pakete, Kapazität {a.inst.cap}, Summe der Größen {sum(a.inst.sizes)}, {len(A.gruppen(list(a.inst.sizes)))} verschiedene Größen. Gelöst im Graphen der Stufe {C.STUFEN_KURZ[a.stufe]}.")
kind, text = verdict_aktuell(a)
getattr(st, kind)(text)

st.markdown("### Der Graph und der Fluss")
farben = {w: C.GROESSEN_FARBEN[k % len(C.GROESSEN_FARBEN)] for k, (w, _b) in enumerate(A.gruppen(list(a.inst.sizes)))}
st.plotly_chart(build_graph(a.knoten, a.bogen, a.fluss, a.inst.cap, farben), width="stretch", key="graph_chart")
nur_fluss = len(a.bogen) > C.ZEICHEN_MAX
st.caption(f"Knoten sind Lasten, Bögen über der Achse sind Pakete (Farbe = Größe), graue Bögen darunter Verlust. Dick: Bögen mit Fluss, also die Container der Lösung. "
           + (f"Der Graph hat {len(a.bogen)} Bögen: Es werden nur die Bögen mit Fluss gezeichnet." if nur_fluss else "Blass: Bögen ohne Fluss."))

st.markdown("### Die Packung aus dem Fluss")
if a.bins:
    st.plotly_chart(build_container(list(a.inst.sizes), [list(b) for b in a.bins], a.inst.cap), width="stretch", key="main_chart")
    st.caption("Jeder Weg des Flusses ist ein Container, jeder Bogen ein Paket seiner Größe. Die Zerlegung ist nicht eindeutig; die Zahl der Container ist es.")
else:
    st.info("Das ganzzahlige Programm hat im Zeitlimit keine Packung gefunden.")

st.markdown("## ❓ Kernfrage: Wie viel spart die Kompression?")
st.plotly_chart(build_groessen(a.groessen), width="stretch", key="groessen_chart")
kind, text = verdict_kompression(a)
getattr(st, kind)(text)

st.markdown("### Verändert die Kompression den LP-Wert?")
tab = ["| Modell | LP-Wert | aufgerundet |", "|---|---|---|"]
for st_i in A.STUFEN:
    tab.append(f"| Arc-Flow, Stufe {C.STUFEN_KURZ[st_i]} | {a.lp[st_i]:.4f} | {A.lp_aufgerundet(a.lp[st_i])} |")
if a.lp_item is not None:
    tab.append(f"| LP von Stück 4 (Muster = Teilmengen) | {a.lp_item:.4f} | {A.lp_aufgerundet(a.lp_item)} |")
    tab.append(f"| Optimum (Teilmengen-DP, unabhängiger Weg) | {a.opt_dp} | {a.opt_dp} |")
st.markdown("\n".join(tab))
kind, text = verdict_lp(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experimente: Gilt das für viele Instanzen?")
st.caption(
    f"Gemessen an je {C.INSTANZEN} festen Instanzen pro Zelle, Kapazität {C.MESS_CAP}, ganzzahlige Größen; dieselben Instanzen wie in Stück 2 und 4. "
    "Die Zahlen sind vorberechnet (`generate_precomputed.py`)."
)
e1, e2 = st.columns(2)
vert = e1.selectbox("Verteilung der Größen", list(range(len(C.VERTEILUNGEN))), index=0, format_func=lambda i: C.VERTEILUNGEN[i][1], key="exp_verteilung")
ni = e2.selectbox("Zahl der Pakete n", list(range(len(C.MESS_N))), index=1, format_func=lambda i: str(C.MESS_N[i]), key="exp_n")
zeilen = [zeile(int(vert), k) for k in range(len(C.MESS_N))]
z = zeilen[int(ni)]

st.markdown("### Experiment 1: Wie klein wird der Graph?")
st.plotly_chart(build_raster_groesse(zeilen), width="stretch", key="exp_chart_1")
tab1 = ["| Pakete | Knoten voll / normal / geordnet | Bögen voll / normal / geordnet | Bögen geordnet am vollen |", "|---|---|---|---|"]
for zz in zeilen:
    tab1.append(f"| {zz['n']} | {zz['knoten'][0]:.0f} / {zz['knoten'][1]:.0f} / {zz['knoten'][2]:.0f} | {zz['bogen'][0]:.0f} / {zz['bogen'][1]:.0f} / {zz['bogen'][2]:.0f} | {zz['bogen_anteil']:.0f} % |")
st.markdown("\n".join(tab1))
st.caption("Mittlere Knoten und Bögen je Instanz einer Zelle. Die Ordnung der Größen verkleinert die Bögen der Stufe normal noch einmal (die Knoten bleiben gleich).")
kind, text = verdict_groesse(z)
getattr(st, kind)(text)

st.markdown("### Experiment 2: Wie oft ist das Optimum bestimmbar?")
st.plotly_chart(build_raster_ausgang(zeilen), width="stretch", key="exp_chart_2")
kind, text = verdict_entscheidung(z)
getattr(st, kind)(text)

st.markdown("### Experiment 3: Trifft der aufgerundete LP-Wert das Optimum?")
kind, text = verdict_lp_raster(z)
getattr(st, kind)(text)
tab3 = ["| Pakete | LP geordnet = Optimum | LP normal = Optimum | LP Stück 4 = Optimum | LP größer durch die Ordnung |", "|---|---|---|---|---|"]
for zz in zeilen:
    k = zz["lp"]
    tab3.append(f"| {zz['n']} | {k['rund_s2_opt']} von {zz['entschieden']} | {k['rund_s1_opt']} | {k['rund_item_opt']} | {k['s1_kleiner_s2']} |")
st.markdown("\n".join(tab3))
st.caption("Zahl der entschiedenen Instanzen, in denen der aufgerundete LP-Wert genau das Optimum ist. Die letzte Spalte zählt die Instanzen, in denen der LP-Wert der Stufe geordnet größer ist als der der Stufe normal. Die Stufe voll ist im Raster nicht gerechnet: Ihr LP hat bei Kapazität 1000 und 30 Paketen rund 20 000 bis 23 000 Bögen.")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist |
|---|---|
| **Kleine Paketzahlen, große Kapazität** | Die Kompression wirkt, solange die Lasten als Summen von Paketen dünn liegen. Bei vielen verschiedenen Größen füllen die Summen einen wachsenden Teil der Lasten (63 % bei 30 mittleren Paketen), und die Stufe normal spart weniger (Experiment 1). |
| **Das Optimum steht im Zeitlimit** | Das ganzzahlige Programm hat 60 Sekunden je Instanz; was darüber liegt, ist „nicht entschieden“. Die Zahl hängt von der Rechenzeit ab. |
| **Die Messung gilt für diese Instanzen** | Drei Verteilungen, Paketzahlen 12 bis 30, Kapazität 1000. Andere Verteilungen oder viel größere Instanzen können anders ausfallen. |
| **Nur FFD zum Vergleich** | Bessere Heuristiken können öfter optimal sein; die Demo misst sie nicht. |
| **Die Spaltenerzeugung ist nicht Gegenstand** | Das Muster-Modell mit Preisproblem löst dasselbe Problem ohne Graph; dort ist es erklärt: [Exakte Suche](https://sebastianhanisch.net/konzepte-exakte-suche.html). |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** *Gegeben:* Paketgrößen $w_1 > \dots > w_m$ mit Anzahlen $b_1, \dots, b_m$ und eine Kapazität $C$. *Gesucht:* die kleinste Zahl von Containern, in die alle Pakete passen.

| Symbol | Bedeutung |
|---|---|
| $m$ | Zahl der verschiedenen Größen |
| $w_i$, $b_i$ | Größe und Anzahl der Pakete der Größe $i$ |
| $C$ | Kapazität eines Containers |
| $V$ | Knoten des Graphen: Lasten |
| $A$ | Bögen $(u, v, w)$ mit $v = u + w$; $w = 0$ steht für Verlust |
| $x_a$ | Fluss auf Bogen $a$ |
| $z$ | Fluss auf dem Rückbogen $(C, 0)$: Zahl der Container |

**Modell.** $\min z$ unter $\sum_{a \in \delta^-(v)} x_a - \sum_{a \in \delta^+(v)} x_a = 0$ für jeden Knoten $v \notin \{0, C\}$, Abfluss aus $0$ gleich $z$ und Zufluss in $C$ gleich $z$, sowie $\sum_{a:\, w(a) = w_i} x_a \ge b_i$ für jede Größe $i$. Sind die $x_a$ ganz, ist $z$ das Optimum (überzählige Bögen lassen sich streichen); sind sie reell, ist $z$ der LP-Wert.

**Flusszerlegung.** Ein ganzzahliger Fluss ohne Kreise zerfällt in $z$ Wege von $0$ nach $C$; jeder Weg hat höchstens die Summe $C$ seiner Bogengrößen, ist also ein zulässiger Container.

**Stufen.** *Voll:* $V = \{0, \dots, C\}$, Bögen $(u, u + w_i, w_i)$ für alle $u \le C - w_i$ und Verlustbögen $(u, u + 1, 0)$. *Normal:* $V$ ist die Menge der Summen von Paketen (je Größe höchstens $b_i$ Stück) bis $C$ und der Endknoten $C$; Verlustbögen $(u, C, 0)$. *Geordnet:* Bögen der Größe $w_i$ beginnen nur an Summen von Paketen mit Größe mindestens $w_i$. Jedes Muster hat einen Weg mit absteigenden Größen, die Kompression ändert das ganzzahlige Optimum nicht.

**LP-Werte.** Weil in einer kleineren Stufe jeder Weg auch in der größeren existiert, gilt $\mathrm{LP}_{\text{voll}} \le \mathrm{LP}_{\text{normal}} \le \mathrm{LP}_{\text{geordnet}}$. Der volle Graph erlaubt Muster mit beliebig vielen Exemplaren einer Größe (Schneideproblem); der LP von Stück 4 erlaubt je Größe höchstens $b_i$ Exemplare und ist mindestens $\mathrm{LP}_{\text{geordnet}}$. Alle sind untere Schranken des Optimums.

**Schranken aus Stück 2.** $L_1 = \lceil \sum_i b_i w_i / C \rceil$; $L_2$ nach Martello und Toth.

**Literatur** (nur Name und Gegenstand, Originale nicht gelesen). Valério de Carvalho beschreibt den Arc-Flow für das Packen und Schneiden; Brandão und Pedroso beschreiben die Graphkompression und ihren Löser VPSolver. Die Demo übernimmt daraus keine Zahl und keine Gütegarantie.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
