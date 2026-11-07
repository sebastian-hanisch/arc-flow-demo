"""Randfälle: leere Eingabe, ein Paket, Paket gleich Kapazität, lauter gleiche Größen, Kapazität 1, Zeitlimit ohne Lösung, ungültige Eingaben, Grenzen der Regler."""

import pytest

import arf_algorithm as A
import arf_constants as C
import arf_evaluation as ev
from arf_scenario import Instance, live_instanz, quelle_instanz, raster_instanz, raster_seed


@pytest.mark.parametrize("stufe", (0, 1, 2))
def test_leere_eingabe_ergibt_null_container(stufe):
    r = A.loese([], 10, stufe, True)
    assert r["wert"] == 0.0 and r["status"] == "optimal" and A.packung_aus_fluss([], r["bogen"], r["fluss"], 10) == []
    assert A.ffd([], 10) == [] and A.l1([], 10) == 0 and A.l2([], 10) == 0 and A.optimum_dp([], 10) == 0 and A.lp_muster([], 10) == 0.0
    assert A.gruppen([]) == [] and A.groessen([], 10)[0] == (11, 10)


@pytest.mark.parametrize("stufe", (0, 1, 2))
def test_ein_paket_und_paket_gleich_kapazitaet(stufe):
    for sizes, cap in (([7], 10), ([10], 10), ([1], 1)):
        r = A.loese(sizes, cap, stufe, True)
        assert r["wert"] == 1.0 and A.packung_aus_fluss(sizes, r["bogen"], r["fluss"], cap) == [[0]]
        assert A.loese(sizes, cap, stufe, False)["wert"] == pytest.approx(1.0)


@pytest.mark.parametrize("stufe", (0, 1, 2))
def test_lauter_gleiche_groessen_und_kapazitaet_1(stufe):
    assert A.loese([5] * 9, 10, stufe, True)["wert"] == 5.0                              # zwei je Container, 9 Stück: fünf
    assert A.loese([5] * 9, 10, stufe, False)["wert"] == pytest.approx(4.5)
    assert A.loese([1] * 6, 1, stufe, True)["wert"] == 6.0
    assert A.loese([6, 6, 6], 10, stufe, True)["wert"] == 3.0
    assert A.groessen([5] * 9, 10) == {0: (11, 16), 1: (3, 4), 2: (3, 4)}                    # Stufe 0: 6 Bögen der Größe 5 und 10 Verluste; sonst Knoten 0, 5, 10 und je zwei Bögen der Größe 5 und Verlust


def test_ein_knoten_graph_bei_einem_paket_der_groesse_kapazitaet():
    kn, bg = A.graph([10], 10, 2)
    assert kn == [0, 10] and bg == [(0, 10, 10), (0, 10, 0)]


def test_zeitlimit_ohne_loesung_und_mit_loesung(monkeypatch):
    class Res:
        def __init__(self, status, x, fun):
            self.status, self.x, self.fun = status, x, fun

    import numpy as np
    s = [4, 4, 4, 4, 3]
    n_bogen = len(A.graph(s, 10, 2)[1])
    monkeypatch.setattr(A, "milp", lambda *a, **k: Res(1, None, None))
    r = A.loese(s, 10, 2, True, 0.001)
    assert r["status"] == "zeit" and r["wert"] is None and r["fluss"] is None
    x = np.zeros(n_bogen + 1)
    x[-1] = 3.0
    monkeypatch.setattr(A, "milp", lambda *a, **k: Res(1, x, 3.0))
    r = A.loese(s, 10, 2, True, 0.001)
    assert r["status"] == "zeit" and r["wert"] == 3.0 and len(r["fluss"]) == n_bogen
    monkeypatch.setattr(A, "milp", lambda *a, **k: Res(2, None, None))
    assert A.loese(s, 10, 2, True, 1.0)["status"] == "unzulaessig"


def test_analyse_bei_zeitlimit_zeigt_warnung_ohne_packung(monkeypatch):
    echte = A.loese

    def schnell(sizes, cap, stufe=2, ganzzahlig=True, zeit=60.0):
        r = echte(sizes, cap, stufe, False, zeit)
        return {**r, "wert": None, "status": "zeit", "fluss": None} if ganzzahlig else r

    monkeypatch.setattr(A, "loese", schnell)
    a = ev.analyse(ev.Settings())
    assert a.opt is None and a.beste is None and a.bins == () and a.status == "zeit"
    kind, text = ev.verdict_aktuell(a)
    assert kind == "warning" and "nach 20 Sekunden kein Optimum bewiesen" in text and "FFD braucht 3" in text


def test_ungueltige_instanzen_werden_abgelehnt():
    for sizes, cap in (((0,), 10), ((11,), 10), ((3.5,), 10), ((3,), 0)):
        with pytest.raises(ValueError):
            Instance(sizes, cap)


def test_analyse_an_den_grenzen_der_regler():
    for quelle in C.BEISPIEL_NAMEN:
        for stufe in (0, 1, 2):
            a = ev.analyse(ev.Settings(quelle, 2, C.N_MIN, C.SEED_MAX, stufe))
            assert a.opt is not None and a.opt >= a.l1 and (a.opt_dp is None or a.opt == a.opt_dp)
    for n in (C.N_MIN, C.N_MAX):
        for seed in (0, C.SEED_MAX):
            a = ev.analyse(ev.Settings(C.ZUFALL, 0, n, seed, 2))
            assert a.inst.n == n and a.opt is not None and A.container_pruefen(list(a.inst.sizes), [list(b) for b in a.bins], 100) and len(a.bins) == a.opt


def test_optimum_ist_in_jeder_stufe_gleich_und_gleich_dem_dp():
    for quelle in (0, 1, 2, 3, 4):
        ergebnis = {ev.analyse(ev.Settings(quelle, 0, 12, 7, st)).opt for st in (0, 1, 2)}
        assert len(ergebnis) == 1


def test_zufallsinstanzen_haben_die_verlangten_groessen():
    for v, (_n, _t, lo, hi) in enumerate(C.VERTEILUNGEN):
        inst = live_instanz(v, 15, 3)
        assert inst.n == 15 and inst.cap == C.CAP and all(max(1, int(lo * 100)) <= x <= int(hi * 100) for x in inst.sizes)
    assert quelle_instanz(0, 2, 15, 3).sizes == (4, 4, 4, 4, 3) and quelle_instanz(C.ZUFALL, 1, 9, 5) == live_instanz(1, 9, 5)


def test_rasterinstanzen_sind_die_von_stueck_2_und_4():
    assert raster_seed(0, 0, 0) == 1_001_000 and raster_seed(2, 2, 99) == 3_003_099
    inst = raster_instanz(0, 0, 0)
    assert inst.cap == 1000 and inst.n == 12 and all(100 <= x <= 500 for x in inst.sizes)
    assert len({raster_seed(v, ni, j) for v in range(3) for ni in range(3) for j in range(100)}) == 900
