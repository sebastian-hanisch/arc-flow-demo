"""Orakel-Tests (DEMO-PLAYBOOK §12): jede Kernroutine gegen einen anderen Rechenweg, feste Seeds, zusammen unter 30 Sekunden.

  LP der Stufe voll        gegen  den LP über alle Muster mit beliebig vielen Exemplaren (Aufzählung aller Vielfachen, eigener `linprog`-Aufruf), samt Dualzertifikat (jedes Muster höchstens 1).
  Optimum (ganzzahlig)     gegen  die Teilmengen-DP (unabhängig vom Graphen), in jeder Stufe.
  Knoten der Stufe 1       gegen  alle Teilmengensummen über die einzelnen Pakete (Aufzählung aller Teilmengen).
  Vollständigkeit          jede zulässige Teilmenge von Paketen hat in der Stufe geordnet einen Weg mit absteigenden Größen (Weg-Suche, unabhängig vom Löser).
  Packung aus dem Fluss    zulässig (unabhängiger Prüfer) und so groß wie das Optimum.
  Eigenschaften:  LP voll <= LP normal <= LP geordnet <= LP von Stück 4 <= Optimum <= FFD; L1, L2 <= aufgerundeter LP-Wert-Optimum; Skalieren ändert das Optimum nicht; die Zahl der Bögen der Stufe voll folgt der Formel.
"""

import itertools
import random

import numpy as np
import pytest
from scipy.optimize import linprog

import arf_algorithm as A


def instanzen(anzahl, n_lo, n_hi, cap_lo=8, cap_hi=30, seed0=0):
    for seed in range(seed0, seed0 + anzahl):
        rng = random.Random(seed)
        cap = rng.randint(cap_lo, cap_hi)
        n = rng.randint(n_lo, n_hi)
        yield cap, [rng.randint(1, cap) for _ in range(n)]


def lp_unbeschraenkt(sizes, cap):
    """LP über alle Muster mit beliebig vielen Exemplaren je Größe (Schneideproblem), durch Aufzählung aller Vielfachen; gibt (Wert, Dualpreise je Größe, Muster) zurück."""
    gr = A.gruppen(sizes)
    muster = [k for k in itertools.product(*[range(cap // w + 1) for w, _ in gr]) if any(k) and sum(ki * w for ki, (w, _) in zip(k, gr)) <= cap]
    a = np.array(muster, dtype=float).T
    res = linprog(np.ones(len(muster)), A_ub=-a, b_ub=-np.array([b for _, b in gr], dtype=float), bounds=(0, None), method="highs")
    return float(res.fun), [float(-m) for m in res.ineqlin.marginals], muster


def test_lp_der_stufe_voll_gegen_den_lp_ueber_alle_muster_und_dualzertifikat():
    geprueft = 0
    for cap, sizes in instanzen(40, 1, 9, cap_lo=6, cap_hi=18, seed0=10):
        if len(set(sizes)) > 4:
            continue
        wert, y, muster = lp_unbeschraenkt(sizes, cap)
        gr = A.gruppen(sizes)
        assert A.loese(sizes, cap, 0, False)["wert"] == pytest.approx(wert, abs=1e-7), (cap, sizes)
        assert all(sum(k * yi for k, yi in zip(m, y)) <= 1 + 1e-7 for m in muster)          # jedes Muster höchstens Wert 1
        assert sum(b * yi for (_, b), yi in zip(gr, y)) == pytest.approx(wert, abs=1e-7)      # die Dualsumme ist der LP-Wert: untere Schranke bewiesen
        geprueft += 1
    assert geprueft >= 15


def test_optimum_in_jeder_stufe_gegen_die_teilmengen_dp():
    for cap, sizes in instanzen(50, 1, 10, cap_lo=8, cap_hi=40, seed0=100):
        opt = A.optimum_dp(sizes, cap)
        for stufe in (0, 1, 2):
            r = A.loese(sizes, cap, stufe, True)
            assert r["status"] == "optimal" and r["wert"] == opt, (cap, sizes, stufe)
            bins = A.packung_aus_fluss(sizes, r["bogen"], r["fluss"], cap)
            assert A.container_pruefen(sizes, bins, cap) and len(bins) == opt and A.loesung_pruefen(sizes, cap, r["bogen"], r["fluss"])


def test_knoten_der_stufe_1_gegen_alle_teilmengensummen():
    for cap, sizes in instanzen(40, 1, 12, cap_lo=10, cap_hi=60, seed0=300):
        summen = {0}
        for k in range(1, len(sizes) + 1):
            for teil in itertools.combinations(sizes, k):
                if sum(teil) <= cap:
                    summen.add(sum(teil))
        knoten, _ = A.graph(sizes, cap, 1)
        assert knoten == sorted(summen | {cap}), (cap, sizes)
        assert A.graph(sizes, cap, 2)[0] == knoten


def weg_mit_absteigenden_groessen(bogen, cap, teil):
    """Gibt es in der Bogenmenge einen Weg von 0 nach cap, der die Größen der Teilmenge `teil` absteigend nimmt und dann den Rest als Verlust auffüllt?"""
    lasten = [0]
    for w in sorted(teil, reverse=True):
        lasten.append(lasten[-1] + w)
    bogen = set(bogen)
    schritte_ok = all((u, v, w) in bogen for (u, v), w in zip(zip(lasten, lasten[1:]), sorted(teil, reverse=True)))
    return schritte_ok and (lasten[-1] == cap or (lasten[-1], cap, 0) in bogen)


def test_jede_zulaessige_teilmenge_hat_in_der_stufe_geordnet_einen_weg():
    for cap, sizes in instanzen(25, 1, 9, cap_lo=10, cap_hi=40, seed0=500):
        _, bogen = A.graph(sizes, cap, 2)
        for k in range(1, len(sizes) + 1):
            for teil in itertools.combinations(sizes, k):
                if sum(teil) <= cap:
                    assert weg_mit_absteigenden_groessen(bogen, cap, teil), (cap, sizes, teil)


def test_lp_kette_der_stufen_gegen_den_lp_von_stueck_4_das_optimum_und_ffd():
    strikt = 0
    for cap, sizes in instanzen(40, 2, 10, cap_lo=10, cap_hi=40, seed0=700):
        lps = [A.loese(sizes, cap, st, False)["wert"] for st in (0, 1, 2)]
        item = A.lp_muster(sizes, cap)
        opt = A.optimum_dp(sizes, cap)
        assert lps[0] <= lps[1] + 1e-7 and lps[1] <= lps[2] + 1e-7 and lps[2] <= item + 1e-7 and item <= opt + 1e-7 and opt <= len(A.ffd(sizes, cap)), (cap, sizes, lps, item, opt)
        assert A.lp_aufgerundet(lps[2]) <= opt and A.l1(sizes, cap) <= opt and A.l2(sizes, cap) <= opt and A.l1(sizes, cap) <= A.l2(sizes, cap)
        strikt += lps[0] < lps[2] - 1e-7 or lps[2] < item - 1e-7
    assert strikt >= 5                                                                       # der Test prüft wirklich etwas: die Werte unterscheiden sich in einigen Instanzen


def test_gemeinsames_skalieren_aendert_optimum_und_lp_nicht():
    for cap, sizes in instanzen(20, 1, 9, cap_lo=8, cap_hi=20, seed0=900):
        gross = [3 * s for s in sizes]
        assert A.loese(gross, 3 * cap, 2, True)["wert"] == A.loese(sizes, cap, 2, True)["wert"]
        assert A.loese(gross, 3 * cap, 2, False)["wert"] == pytest.approx(A.loese(sizes, cap, 2, False)["wert"], abs=1e-7)


def test_die_reihenfolge_der_pakete_aendert_weder_graph_noch_wert():
    for cap, sizes in instanzen(20, 2, 10, cap_lo=8, cap_hi=30, seed0=1100):
        gemischt = list(sizes)
        random.Random(cap).shuffle(gemischt)
        for st in (0, 1, 2):
            assert A.graph(gemischt, cap, st) == A.graph(sizes, cap, st)
        assert A.loese(gemischt, cap, 2, True)["wert"] == A.loese(sizes, cap, 2, True)["wert"]


def test_formel_der_boegen_der_stufe_voll_und_die_stufen_werden_kleiner():
    for cap, sizes in instanzen(40, 1, 12, cap_lo=10, cap_hi=100, seed0=1300):
        g = A.groessen(sizes, cap)
        kn0, bg0 = A.graph(sizes, cap, 0)
        assert g[0] == (len(kn0), len(bg0)) == A.groesse_voll(sizes, cap)
        assert g[2][1] <= g[1][1] <= g[0][1] + cap and g[2][0] == g[1][0] <= g[0][0]


def test_flussprobe_ohne_loesung_wird_abgelehnt_und_ueberzaehlige_boegen_fallen_weg():
    s = [3, 3]
    kn, bg = A.graph(s, 10, 2)
    fluss = [0.0] * len(bg)
    j = bg.index((0, 3, 3))
    k = bg.index((3, 6, 3)) if (3, 6, 3) in bg else None
    assert k is not None
    fluss[j] = 2.0                                          # zwei Bögen der Größe 3 von 0 aus, aber kein Anschluss: Erhaltung verletzt
    assert not A.loesung_pruefen(s, 10, bg, fluss)
