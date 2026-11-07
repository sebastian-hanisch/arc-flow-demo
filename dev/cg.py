"""LP-Schranke (Gilmore und Gomory) per Spaltenerzeugung für viele Pakete: nur für Generator und Tests, nie für die App.

Muster sind Teilmengen der vorhandenen Pakete: ein Muster enthält von jeder Paketgröße höchstens so viele Exemplare, wie es von ihr gibt (Preisproblem: beschränkter Rucksack,
als 0/1-Rucksack über die einzelnen Pakete per DP gelöst). Das ist dieselbe Relaxation wie die mit allen Teilmengen in lpb_algorithm.lp_loesen (Gleichstände der Pakete lassen sich
vertauschen). Pakete gleicher Größe bilden eine Gruppe mit Nachfrage."""

import numpy as np
from scipy.optimize import linprog


def lp_wert_cg(items, cap: int, tol: float = 1e-9, max_iter: int = 3000) -> float:
    items = list(items)
    groessen = sorted(set(items))
    index = {g: k for k, g in enumerate(groessen)}
    nachfrage = np.array([items.count(g) for g in groessen], dtype=float)
    m = len(groessen)
    gruppe = [index[s] for s in items]                   # Gruppe jedes einzelnen Pakets
    spalten = []
    for k in range(m):                                    # Startspalten: ein Exemplar je Größe (Gewicht = Nachfrage deckt sie)
        spalte = [0] * m
        spalte[k] = 1
        spalten.append(spalte)
    for _ in range(max_iter):
        a = -np.array(spalten, dtype=float).T
        res = linprog(np.ones(len(spalten)), A_ub=a, b_ub=-nachfrage, bounds=(0, None), method="highs")
        y = -res.ineqlin.marginals
        # Preisproblem: 0/1-Rucksack über die einzelnen Pakete, Wert eines Pakets = Dualpreis seiner Gruppe
        dp = np.zeros(cap + 1)
        nimmt = []
        for s, g in zip(items, gruppe):
            neu = dp.copy()
            tritt = np.zeros(cap + 1, dtype=bool)
            if s <= cap:
                kand = dp[: cap + 1 - s] + y[g]
                besser = kand > dp[s:] + 1e-15
                neu[s:] = np.where(besser, kand, dp[s:])
                tritt[s:] = besser
            nimmt.append(tritt)
            dp = neu
        if dp[cap] <= 1 + tol:
            return float(res.fun)
        spalte = [0] * m
        c = cap
        for j in range(len(items) - 1, -1, -1):
            if nimmt[j][c]:
                spalte[gruppe[j]] += 1
                c -= items[j]
        spalten.append(spalte)
    raise RuntimeError("Spaltenerzeugung nicht konvergiert")
