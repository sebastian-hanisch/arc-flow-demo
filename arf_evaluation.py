"""Kennzahlen, Verdikt-Logik und das Messraster (vorberechnet in arf_precomputed.json, erzeugt von generate_precomputed.py)."""

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import arf_algorithm as A
import arf_constants as C
from arf_scenario import Instance, quelle_instanz, raster_instanz

PRECOMPUTED = Path(__file__).resolve().parent / "arf_precomputed.json"
STUFEN = A.STUFEN


@dataclass(frozen=True)
class Settings:
    quelle: int = 0
    verteilung: int = 0
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    stufe: int = 2


@dataclass(frozen=True)
class Analysis:
    inst: Instance
    stufe: int            # die Stufe der Kompression, in der gelöst und gezeichnet wird
    groessen: dict        # {Stufe: (Knoten, Bögen)}
    knoten: tuple         # Knoten des gewählten Graphen
    bogen: tuple          # Bögen (von, nach, Größe; Größe 0 = Verlust) des gewählten Graphen
    fluss: object         # ganzzahliger Fluss je Bogen (Tupel) oder None
    status: str           # 'optimal', 'zeit' oder 'unzulaessig' beim ganzzahligen Programm
    opt: object           # Optimum (int), wenn bewiesen, sonst None
    beste: object         # beste gefundene Containerzahl (int) oder None
    bins: tuple           # Packung aus dem Fluss (Container als Tupel von Paketnummern)
    lp: dict              # {Stufe: LP-Wert} des Arc-Flow-Modells in allen drei Stufen
    lp_item: object       # LP von Stück 4 (Spalten: Teilmengen der Pakete), nur bis DP_LIMIT Pakete, sonst None
    opt_dp: object        # Optimum per Teilmengen-DP (unabhängiger Weg), nur bis DP_LIMIT Pakete, sonst None
    ffd: int
    l1: int
    l2: int
    settings: Settings


def analyse(s: Settings) -> Analysis:
    inst = quelle_instanz(s.quelle, s.verteilung, s.n, s.seed)
    sizes, cap = list(inst.sizes), inst.cap
    groessen = A.groessen(sizes, cap)
    lp = {st: A.loese(sizes, cap, st, False, C.ILP_ZEIT_LIVE)["wert"] for st in A.STUFEN}
    r = A.loese(sizes, cap, s.stufe, True, C.ILP_ZEIT_LIVE)
    fluss = tuple(r["fluss"]) if r["fluss"] is not None else None
    bins = tuple(tuple(b) for b in A.packung_aus_fluss(sizes, r["bogen"], fluss, cap)) if fluss is not None else ()
    if bins:
        assert A.container_pruefen(sizes, [list(b) for b in bins], cap)
        assert A.loesung_pruefen(sizes, cap, r["bogen"], fluss)
    opt = int(round(r["wert"])) if r["status"] == "optimal" else None
    beste = int(round(r["wert"])) if r["wert"] is not None else None
    klein = inst.n <= C.DP_LIMIT
    return Analysis(inst, s.stufe, groessen, tuple(r["knoten"]), tuple(r["bogen"]), fluss, r["status"], opt, beste, bins, lp, A.lp_muster(sizes, cap) if klein else None,
                    A.optimum_dp(sizes, cap, C.DP_LIMIT) if klein else None, len(A.ffd(sizes, cap)), A.l1(sizes, cap), A.l2(sizes, cap), s)


# ------------------------------------------------------------------------------------------------------------------------------------------
# Verdikte (reine Funktionen: (Art, Text))


def beweis_durch(opt: int, l1: int, l2: int, lp_zahl: int) -> str:
    """Welche Schranke das Optimum schon beweist: 'l1', 'l2', 'lp' oder 'ilp' (keine Schranke, nur das ganzzahlige Programm); Reihenfolge von der einfachsten zur stärksten."""
    if opt == l1:
        return "l1"
    if opt == l2:
        return "l2"
    if opt == lp_zahl:
        return "lp"
    return "ilp"


def verdict_aktuell(a: Analysis) -> tuple[str, str]:
    """Verdikt zur gewählten Instanz: Optimum des Arc-Flows gegen FFD und welche Schranke es beweist."""
    lp_zahl = A.lp_aufgerundet(a.lp[2])
    schranken = f"L1 {a.l1}, L2 {a.l2}, aufgerundeter LP-Wert {lp_zahl}"
    if a.opt is None:
        beste = "" if a.beste is None else f" Die beste gefundene Packung braucht {a.beste} Container."
        return "warning", f"Das ganzzahlige Programm hat nach {C.ILP_ZEIT_LIVE:.0f} Sekunden kein Optimum bewiesen.{beste} FFD braucht {a.ffd} ({schranken})."
    kopf = f"Der Arc-Flow findet **{a.opt}** Container und beweist, dass es nicht weniger geht."
    beweis = {"l1": "Schon L1 beweist das.", "l2": "Erst L2 beweist das.", "lp": "Erst der aufgerundete LP-Wert beweist das.",
              "ilp": "Keine Schranke beweist das: Nur das ganzzahlige Programm kennt das Optimum."}[beweis_durch(a.opt, a.l1, a.l2, lp_zahl)]
    if a.ffd > a.opt:
        return "success", kopf + f" FFD braucht {a.ffd}: **FFD verliert** um {a.ffd - a.opt}. {beweis} ({schranken}.)"
    return "info", kopf + f" FFD braucht ebenfalls {a.ffd}: FFD ist optimal. {beweis} ({schranken}.)"


def verdict_kompression(a: Analysis) -> tuple[str, str]:
    """Verdikt zur Größe des Graphen: gewählte Stufe gegen den vollen Graphen (Anteil der Bögen auf ganze Prozent gerundet)."""
    k0, b0 = a.groessen[0]
    k, b = a.groessen[a.stufe]
    if a.stufe == 0:
        return "info", f"Der volle Graph hat {k0} Knoten und {b0} Bögen (jede Last von 0 bis {a.inst.cap}, jede Größe an jedem Knoten); die Stufen normal und geordnet kommen mit {a.groessen[1][0]} und {a.groessen[2][0]} Knoten und {a.groessen[1][1]} und {a.groessen[2][1]} Bögen aus."
    anteil = round(100 * b / b0)
    return "success", (f"Der Graph der Stufe {C.STUFEN_KURZ[a.stufe]} hat {k} Knoten und {b} Bögen, der volle Graph {k0} Knoten und {b0} Bögen: Die Kompression behält **{anteil} %** der Bögen "
                       f"und {round(100 * k / k0)} % der Knoten.")


def verdict_lp(a: Analysis) -> tuple[str, str]:
    """Verdikt zu den LP-Werten: die drei Stufen des Arc-Flows und, bis 12 Pakete, der LP von Stück 4 (auf vier Stellen gerundet verglichen)."""
    w = [round(a.lp[st], 4) for st in A.STUFEN]
    teil = f"LP-Wert des Arc-Flows: voll {w[0]:.2f}, normal {w[1]:.2f}, geordnet {w[2]:.2f}"
    if a.lp_item is not None:
        teil += f"; LP von Stück 4 {round(a.lp_item, 4):.2f}"
    teil += "."
    if w[0] == w[1] == w[2] and (a.lp_item is None or round(a.lp_item, 4) == w[2]):
        return "info", teil + " Alle Werte sind gleich."
    if w[0] < w[2]:
        return "info", teil + " Die Kompression macht den LP-Wert hier **größer** (stärker): Im vollen Graphen darf ein Muster mehr Exemplare einer Größe enthalten, als es gibt."
    return "info", teil + " Die drei Stufen geben denselben Wert; der LP von Stück 4 ist größer, weil dort ein Muster höchstens so viele Exemplare einer Größe enthält, wie es gibt."


def instanz_code(ffd_zahl: int, schranke_l1: int, schranke_l2: int, lp_zahl: int, opt) -> str:
    """Ausgangscode einer Instanz (siehe C.AUSGANG_CODES): '1' FFD gleich L1, '2' FFD gleich L2, 'P' FFD gleich dem aufgerundeten LP, 'U' Optimum unbekannt, 'F' FFD optimal ohne Schranke, 'T' FFD verliert."""
    if ffd_zahl == schranke_l1:
        return "1"
    if ffd_zahl == schranke_l2:
        return "2"
    if ffd_zahl == lp_zahl:
        return "P"
    if opt is None or opt < 0:
        return "U"
    return "F" if opt == ffd_zahl else "T"


# ------------------------------------------------------------------------------------------------------------------------------------------
# Messraster


def instanz_werte(inst: Instance, opt: int, lp_item_fn=None) -> dict:
    """Alle Zahlen einer Rasterinstanz (ganze Zahlen und Zeichen, damit der Vergleich exakt ist). `opt` ist das Optimum (-1 = nicht entschieden), `lp_item_fn(sizes, cap)` der LP von Stück 4.
    Der LP der Stufe voll wird im Raster nicht gerechnet: Bei Kapazität 1000 hat er bis zu 20 000 Bögen und braucht Sekunden bis Minuten je Instanz."""
    if lp_item_fn is None:
        from dev.cg import lp_wert_cg as lp_item_fn
    sizes, cap = list(inst.sizes), inst.cap
    gr = A.groessen(sizes, cap)
    l1_, l2_ = (A.loese(sizes, cap, st, False, C.ILP_ZEIT)["wert"] for st in (1, 2))
    item = lp_item_fn(sizes, cap)
    e = 1e-6
    z1, z2, zi = A.lp_aufgerundet(l1_), A.lp_aufgerundet(l2_), A.lp_aufgerundet(item)
    f, a1, a2 = len(A.ffd(sizes, cap)), A.l1(sizes, cap), A.l2(sizes, cap)
    return {
        "knoten": [gr[st][0] for st in A.STUFEN], "bogen": [gr[st][1] for st in A.STUFEN], "dup": int(len(set(sizes)) < len(sizes)), "code": instanz_code(f, a1, a2, z2, opt),
        "s1_kleiner_s2": int(l1_ < l2_ - e), "s2_kleiner_item": int(l2_ < item - e), "s2_groesser_item": int(l2_ > item + e),
        "rund_s1_item": int(z1 == zi), "rund_s2_item": int(z2 == zi), "rund_s1_opt": int(opt >= 0 and z1 == opt), "rund_s2_opt": int(opt >= 0 and z2 == opt), "rund_item_opt": int(opt >= 0 and zi == opt),
        "lp_ueber_l2": int(z2 > a2), "lp_unter_l2": int(z2 < a2),
    }


LP_ZAEHLER = ("dup", "s1_kleiner_s2", "s2_kleiner_item", "s2_groesser_item", "rund_s1_item", "rund_s2_item", "rund_s1_opt", "rund_s2_opt", "rund_item_opt", "lp_ueber_l2", "lp_unter_l2")


def messzelle(verteilung: int, n_index: int, opt: list, instanzen=None, lp_item_fn=None) -> dict:
    """Rechnet eine Zelle des Messrasters frisch (mit den gespeicherten Optima `opt`, -1 = nicht entschieden): Summen über die INSTANZEN festen Instanzen (oder nur über die Nummern `instanzen`,
    so rechnen die Tests Stichproben nach). Gibt Summen der Knoten und Bögen je Stufe, die Ausgangscodes als Zeichenkette und die Zählungen der LP-Vergleiche zurück."""
    nummern = list(range(C.INSTANZEN)) if instanzen is None else list(instanzen)
    werte = [instanz_werte(raster_instanz(verteilung, n_index, j), opt[j], lp_item_fn) for j in nummern]
    out = {"knoten": [sum(w["knoten"][st] for w in werte) for st in A.STUFEN], "bogen": [sum(w["bogen"][st] for w in werte) for st in A.STUFEN], "codes": "".join(w["code"] for w in werte)}
    for k in LP_ZAEHLER:
        out[k] = sum(w[k] for w in werte)
    return out


@lru_cache(maxsize=1)
def vorberechnet() -> dict:
    return json.loads(PRECOMPUTED.read_text(encoding="utf-8"))


def zelle_schluessel(verteilung: int, n_index: int) -> str:
    return f"{C.VERTEILUNGEN[verteilung][0]}|{C.MESS_N[n_index]}"


def zeile(verteilung: int, n_index: int, daten: dict | None = None) -> dict:
    """Mittelwerte, Zählungen und Anteile einer Zelle aus den vorberechneten Summen."""
    daten = daten or vorberechnet()
    z = daten["zellen"][zelle_schluessel(verteilung, n_index)]
    k = daten["instanzen"]
    codes = z["codes"]
    ausgang = {name: codes.count(c) for c, name in C.AUSGANG_CODES.items()}
    entschieden = k - ausgang["offen"]
    return {
        "verteilung": verteilung, "name": C.VERTEILUNG_LANG[verteilung], "n": C.MESS_N[n_index], "instanzen": k,
        "knoten": [x / k for x in z["knoten"]], "bogen": [x / k for x in z["bogen"]], "bogen_anteil": 100.0 * z["bogen"][2] / z["bogen"][0], "knoten_anteil": 100.0 * z["knoten"][2] / z["knoten"][0],
        "ausgang": ausgang, "entschieden": entschieden, "offen": ausgang["offen"], "lp": {x: z[x] for x in LP_ZAEHLER},
    }


def verdict_groesse(z: dict) -> tuple[str, str]:
    """Experiment 1: mittlere Knoten und Bögen je Stufe und der Anteil der Bögen der Stufe geordnet am vollen Graphen (auf ganze Prozent gerundet)."""
    kn, bg = z["knoten"], z["bogen"]
    anteil = round(z["bogen_anteil"])
    teil = (f"Für {z['name']} mit n = {z['n']} hat der Graph im Mittel {kn[0]:.0f} / {kn[1]:.0f} / {kn[2]:.0f} Knoten und {bg[0]:.0f} / {bg[1]:.0f} / {bg[2]:.0f} Bögen "
            f"(voll / normal / geordnet, {z['instanzen']} Instanzen): Die geordnete Stufe behält **{anteil} %** der Bögen und {round(z['knoten_anteil'])} % der Knoten.")
    return ("success" if anteil <= 50 else "info"), teil


def verdict_entscheidung(z: dict) -> tuple[str, str]:
    """Experiment 2: wie viele Instanzen das ganzzahlige Programm entscheidet und wie sie sich auf die Ausgänge verteilen."""
    a = z["ausgang"]
    teil = (f"Für {z['name']} mit n = {z['n']} entscheidet das ganzzahlige Programm **{z['entschieden']}** von {z['instanzen']} Instanzen: bewiesen durch L1 {a['l1']}, durch L2 {a['l2']}, durch den LP {a['lp']}; "
            f"FFD optimal, nur das Programm zeigt es, in {a['ffd_nur_ilp']}; FFD verliert in {a['ffd_verliert']}.")
    if z["offen"]:
        return "warning", teil + f" {z['offen']} Instanzen bleiben nach {C.ILP_ZEIT:.0f} Sekunden offen."
    return "success", teil + " Keine Instanz bleibt offen."


def verdict_lp_raster(z: dict) -> tuple[str, str]:
    """Experiment 3: wie oft der aufgerundete LP-Wert das Optimum trifft (Stufe geordnet, Stufe normal, LP von Stück 4) und in wie vielen Instanzen die Ordnung der Größen den LP-Wert vergrößert."""
    k = z["lp"]
    e = z["entschieden"]
    teil = (f"Für {z['name']} mit n = {z['n']} trifft der aufgerundete LP-Wert das Optimum in {k['rund_s2_opt']} von {e} entschiedenen Instanzen (Stufe geordnet), in {k['rund_s1_opt']} (Stufe normal) "
            f"und in {k['rund_item_opt']} (LP von Stück 4). Die Ordnung der Größen macht den LP-Wert in {k['s1_kleiner_s2']} von {z['instanzen']} Instanzen größer (normal zu geordnet); "
            f"der LP der Stufe geordnet ist in {k['s2_kleiner_item']} Instanzen kleiner als der von Stück 4.")
    if k["rund_s2_opt"] == e:
        return "success", teil + " Der aufgerundete LP-Wert verfehlt das Optimum nie."
    return "warning", teil + " Der aufgerundete LP-Wert verfehlt das Optimum in einigen Instanzen."
