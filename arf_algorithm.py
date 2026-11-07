"""Kern der Demo (numpy und scipy): das Arc-Flow-Modell für das eindimensionale Packen mit drei Stufen der Graphkompression, seine Lösung als LP und als ganzzahliges Programm, die Zerlegung des
Flusses in eine Packung und die Vergleichswerte FFD, L1, L2 und der LP von Stück 4.

Modell (Valério de Carvalho): Der Graph hat Knoten für Lasten 0 bis C. Ein Bogen (u, u + w) steht für ein Paket der Größe w, das bei der Last u in einen Container kommt; ein Container ist ein Weg
von 0 nach C (was bis C fehlt, ist Verlust). Ein Rückbogen von C nach 0 zählt die Container. Flusserhaltung in jedem Knoten; für jede Größe w mindestens so viele Bögen dieser Größe, wie es Pakete
dieser Größe gibt; gesucht ist der kleinste Fluss z. Als LP (reelle Flüsse) ist das die Schranke von Gilmore und Gomory für das Schneideproblem (Muster dürfen beliebig viele Exemplare einer Größe
enthalten, auch mehr, als es gibt); als ganzzahliges Programm ist es das exakte Optimum (überzählige Bögen lassen sich streichen).

Stufen der Kompression: 0 voll (alle Lasten 0 bis C als Knoten, jeder Bogen von jedem Knoten, Verlustbögen von u nach u + 1); 1 normal (Knoten nur an Lasten, die als Summe von Paketen vorkommen, jede
Größe höchstens so oft, wie es sie gibt; Verlustbögen von jedem Knoten nach C); 2 geordnet (wie 1, aber ein Bogen der Größe w beginnt nur an Knoten, die Summen von Paketen mit Größe mindestens w
sind: jedes Muster hat einen Weg mit absteigenden Größen, die übrigen Wege sind überflüssig)."""

import math

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp
from scipy.sparse import coo_matrix

RUND_TOL = 1e-6           # Toleranz beim Aufrunden eines LP-Wertes (Rundungsfehler des Lösers)
STUFEN = (0, 1, 2)


# --- Vergleichswerte: FFD, L1, L2, Optimum per Teilmengen-DP, LP von Stück 4 -------------------------------------------------------------------


def pruefe_pakete(sizes, cap: int):
    if cap <= 0:
        raise ValueError("Kapazität muss positiv sein")
    if any((not isinstance(s, int)) or s <= 0 or s > cap for s in sizes):
        raise ValueError("Paketgröße muss ganz sein und zwischen 1 und der Kapazität liegen")


def ffd(sizes, cap: int) -> list[list[int]]:
    """First Fit Decreasing: größte zuerst (Gleichstand: kleinere Nummer zuerst), jedes Paket in den ersten Container mit genug Platz. Container sind Listen von Paketnummern."""
    pruefe_pakete(sizes, cap)
    bins: list[list[int]] = []
    loads: list[int] = []
    for i in sorted(range(len(sizes)), key=lambda i: (-sizes[i], i)):
        s = sizes[i]
        for b, load in enumerate(loads):
            if load + s <= cap:
                bins[b].append(i)
                loads[b] += s
                break
        else:
            bins.append([i])
            loads.append(s)
    return bins


def container_pruefen(sizes, bins, cap: int) -> bool:
    """Unabhängiger Zulässigkeitsprüfer: jedes Paket genau einmal, keine Überfüllung, keine leeren Container."""
    gesehen = sorted(i for b in bins for i in b)
    return gesehen == list(range(len(sizes))) and all(b and sum(sizes[i] for i in b) <= cap for b in bins)


def l1(sizes, cap: int) -> int:
    """Volumenschranke: Summe der Größen durch die Kapazität, aufgerundet."""
    return -(-sum(sizes) // cap) if sizes else 0


def _l2_alpha(sizes, cap: int, alpha: int) -> int:
    j1 = [s for s in sizes if s > cap - alpha]
    j2 = [s for s in sizes if cap - alpha >= s and 2 * s > cap]
    j3 = [s for s in sizes if 2 * s <= cap and s >= alpha]
    frei = len(j2) * cap - sum(j2)
    extra = max(0, -(-(sum(j3) - frei) // cap)) if j3 else 0
    return len(j1) + len(j2) + extra


def l2(sizes, cap: int) -> int:
    """Schranke L2 nach Martello und Toth: Maximum von L1 und L(alpha) über alpha = 0 und alle Paketgrößen bis zur halben Kapazität."""
    best = l1(sizes, cap)
    for alpha in {0} | {s for s in sizes if 2 * s <= cap}:
        best = max(best, _l2_alpha(sizes, cap, alpha))
    return best


def optimum_dp(sizes, cap: int, limit: int = 12):
    """Kleinste mögliche Containerzahl per Teilmengen-DP, oder None, wenn mehr als `limit` Pakete vorliegen (unabhängiger Weg zum Optimum, nicht der Arc-Flow)."""
    n = len(sizes)
    if n > limit:
        return None
    if n == 0:
        return 0
    full = (1 << n) - 1
    dp = [(n + 1, cap + 1)] * (full + 1)
    dp[0] = (1, 0)
    for mask in range(full + 1):
        b, last = dp[mask]
        if b > n:
            continue
        for i in range(n):
            if mask >> i & 1:
                continue
            s = sizes[i]
            nxt = (b, last + s) if last + s <= cap else (b + 1, s)
            m2 = mask | (1 << i)
            if nxt < dp[m2]:
                dp[m2] = nxt
    return dp[full][0]


def lp_muster(sizes, cap: int) -> float:
    """LP-Wert von Stück 4: jedes Paket einzeln mindestens einmal überdeckt, die Muster sind alle zulässigen Teilmengen der Pakete (höchstens 14 Pakete). Bei gleichen Größen ist er mindestens so
    groß wie der Arc-Flow-LP (der Muster mit beliebig vielen Exemplaren zulässt)."""
    n = len(sizes)
    if n > 14:
        raise ValueError("zu viele Pakete für die Aufzählung aller Muster")
    if n == 0:
        return 0.0
    masken = np.arange(1, 1 << n)
    bits = (masken[:, None] >> np.arange(n)) & 1
    p = bits[bits @ np.asarray(sizes, dtype=np.int64) <= cap].astype(float)
    res = linprog(np.ones(len(p)), A_ub=-p.T, b_ub=-np.ones(n), bounds=(0, None), method="highs")
    if res.status != 0:
        raise RuntimeError(f"LP nicht gelöst: {res.message}")
    return float(res.fun)


def lp_aufgerundet(wert: float) -> int:
    """Aufgerundeter LP-Wert mit Toleranz für Rundungsfehler des Lösers."""
    return math.ceil(wert - RUND_TOL)


# --- Arc-Flow-Graph ------------------------------------------------------------------------------------------------------------------------------


def gruppen(sizes) -> list[tuple[int, int]]:
    """Paketgrößen absteigend mit ihrer Anzahl: [(Größe, Anzahl)]."""
    z: dict[int, int] = {}
    for s in sizes:
        z[s] = z.get(s, 0) + 1
    return sorted(z.items(), key=lambda t: -t[0])


def last_stufen(gr, cap: int) -> list[set]:
    """Erreichbare Lasten nach den ersten i Größen (i = 0 bis m), jede Größe höchstens so oft, wie es sie gibt; Summen über cap werden verworfen."""
    reach = {0}
    stufen = [set(reach)]
    for w, b in gr:
        neu = set(reach)
        front = set(reach)
        for _ in range(b):
            front = {r + w for r in front if r + w <= cap}
            if not front:
                break
            neu |= front
        reach = neu
        stufen.append(set(reach))
    return stufen


def graph(sizes, cap: int, stufe: int):
    """(Knoten aufsteigend, Bögen) des Graphen der Stufe 0, 1 oder 2; ein Bogen ist (von, nach, Größe), Größe 0 bedeutet Verlust."""
    pruefe_pakete(sizes, cap)
    if stufe not in STUFEN:
        raise ValueError(f"Stufe {stufe!r} unbekannt")
    gr = gruppen(sizes)
    if stufe == 0:
        knoten = list(range(cap + 1))
        bogen = [(u, u + w, w) for w, _ in gr for u in range(cap - w + 1)] + [(u, u + 1, 0) for u in range(cap)]
        return knoten, bogen
    stufen = last_stufen(gr, cap)
    alle = stufen[-1] | {cap}
    knoten = sorted(alle)
    bogen = []
    for i, (w, _) in enumerate(gr):
        start = alle if stufe == 1 else stufen[i + 1]
        for u in sorted(start):
            if u + w <= cap and u + w in alle:
                bogen.append((u, u + w, w))
    bogen += [(u, cap, 0) for u in knoten if u != cap]
    return knoten, bogen


def groesse_voll(sizes, cap: int) -> tuple[int, int]:
    """(Knoten, Bögen) der Stufe 0 ohne den Graphen zu bauen: cap + 1 Knoten, je Größe cap - w + 1 Bögen und cap Verlustbögen."""
    return cap + 1, sum(cap - w + 1 for w, _ in gruppen(sizes)) + cap


def groessen(sizes, cap: int) -> dict:
    """{Stufe: (Knoten, Bögen)} für die drei Stufen."""
    r = {0: groesse_voll(sizes, cap)}
    for st in (1, 2):
        kn, bg = graph(sizes, cap, st)
        r[st] = (len(kn), len(bg))
    return r


# --- Lösen und Zerlegen --------------------------------------------------------------------------------------------------------------------------


def loese(sizes, cap: int, stufe: int = 2, ganzzahlig: bool = True, zeit: float = 60.0) -> dict:
    """Kleinster Fluss z des Arc-Flow-Modells (HiGHS über scipy.optimize.milp). Gibt zurück: `wert` (z; bei Zeitüberschreitung die beste gefundene ganze Zahl oder None), `status` ('optimal',
    'zeit' ohne Beweis, 'unzulaessig'), `knoten`, `bogen` (Bögen des Graphen) und `fluss` (Fluss je Bogen, ganzzahlig gerundet beim ganzzahligen Programm, sonst reell; None ohne Lösung)."""
    kn, bg = graph(sizes, cap, stufe)
    if not sizes:
        return {"wert": 0.0, "status": "optimal", "knoten": kn, "bogen": bg, "fluss": [0.0] * len(bg)}
    gr = gruppen(sizes)
    nk, nb = len(kn), len(bg)
    idx = {v: i for i, v in enumerate(kn)}
    zeilen, spalten, werte = [], [], []
    for j, (u, v, _w) in enumerate(bg):
        zeilen += [idx[v], idx[u]]
        spalten += [j, j]
        werte += [1.0, -1.0]
    zeilen += [idx[cap], idx[0]]
    spalten += [nb, nb]
    werte += [-1.0, 1.0]                                  # Rückbogen (C, 0): Zufluss bei 0, Abfluss bei C
    erh = coo_matrix((werte, (zeilen, spalten)), shape=(nk, nb + 1)).tocsr()
    zeile_von = {w: r for r, (w, _) in enumerate(gr)}
    z2 = [zeile_von[w] for (_u, _v, w) in bg if w]
    s2 = [j for j, (_u, _v, w) in enumerate(bg) if w]
    dem = coo_matrix(([1.0] * len(z2), (z2, s2)), shape=(len(gr), nb + 1)).tocsr()
    c = np.zeros(nb + 1)
    c[nb] = 1.0
    cons = [LinearConstraint(erh, 0, 0), LinearConstraint(dem, np.array([b for _, b in gr], dtype=float), np.inf)]
    integ = np.ones(nb + 1) if ganzzahlig else np.zeros(nb + 1)
    res = milp(c, constraints=cons, integrality=integ, bounds=Bounds(0, np.inf), options={"time_limit": float(zeit), "disp": False})
    if res.status == 0:
        x = res.x[:nb]
        return {"wert": float(res.x[nb]) if not ganzzahlig else float(round(res.x[nb])), "status": "optimal", "knoten": kn, "bogen": bg, "fluss": [float(round(v)) for v in x] if ganzzahlig else [float(v) for v in x]}
    if res.status == 1:
        return {"wert": float(round(res.x[nb])) if res.x is not None else None, "status": "zeit", "knoten": kn, "bogen": bg, "fluss": [float(round(v)) for v in res.x[:nb]] if res.x is not None else None}
    return {"wert": None, "status": "unzulaessig", "knoten": kn, "bogen": bg, "fluss": None}


def wege(bogen, fluss, cap: int) -> list[list[int]]:
    """Zerlegt einen ganzzahligen Fluss in Wege von 0 nach C: eine Liste von Bogennummern je Weg. Immer dem ersten Bogen mit Restfluss folgen (deterministisch)."""
    rest = [int(round(f)) for f in fluss]
    von: dict[int, list[int]] = {}
    for j, (u, _v, _w) in enumerate(bogen):
        von.setdefault(u, []).append(j)
    out = []
    while True:
        u, weg = 0, []
        while u != cap:
            j = next((j for j in von.get(u, []) if rest[j] > 0), None)
            if j is None:
                break
            weg.append(j)
            rest[j] -= 1
            u = bogen[j][1]
        if u != cap or not weg:
            break
        out.append(weg)
    return out


def packung_aus_fluss(sizes, bogen, fluss, cap: int) -> list[list[int]]:
    """Packung aus einem ganzzahligen Fluss: Jeder Weg ist ein Container; die Bögen einer Größe nehmen nacheinander die Pakete dieser Größe (kleinere Nummer zuerst), überzählige Bögen fallen weg,
    leere Container entfallen. Container sind Listen von Paketnummern."""
    vorrat: dict[int, list[int]] = {}
    for i in sorted(range(len(sizes)), reverse=True):
        vorrat.setdefault(sizes[i], []).append(i)
    bins = []
    for weg in wege(bogen, fluss, cap):
        inhalt = []
        for j in weg:
            w = bogen[j][2]
            if w and vorrat.get(w):
                inhalt.append(vorrat[w].pop())
        if inhalt:
            bins.append(inhalt)
    return bins


def loesung_pruefen(sizes, cap: int, bogen, fluss) -> bool:
    """Unabhängige Prüfung eines ganzzahligen Flusses: Flusserhaltung in jedem Knoten, jede Größe mindestens so oft wie vorhanden, Zufluss in C gleich Abfluss aus 0, kein negativer Fluss."""
    f = [int(round(x)) for x in fluss]
    if any(x < 0 for x in f):
        return False
    bilanz: dict[int, int] = {}
    for (u, v, _w), x in zip(bogen, f):
        bilanz[u] = bilanz.get(u, 0) - x
        bilanz[v] = bilanz.get(v, 0) + x
    if any(b != 0 for k, b in bilanz.items() if k not in (0, cap)):
        return False
    if bilanz.get(0, 0) != -bilanz.get(cap, 0) or bilanz.get(0, 0) > 0:
        return False
    return all(sum(x for (_u, _v, w2), x in zip(bogen, f) if w2 == w) >= b for w, b in gruppen(sizes))
