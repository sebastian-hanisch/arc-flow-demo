"""Erzeugt arf_precomputed.json: das Messraster (drei Verteilungen × Paketzahlen 12, 20, 30 × 100 feste Instanzen, dieselben wie in Stück 2 und 4, Kapazität 1000) mit dem Optimum aus dem Arc-Flow
(ganzzahliges Programm, geordnete Stufe, Zeitlimit je Instanz), den Größen des Graphen je Stufe, den LP-Vergleichen und der Stichprobe (die ersten Instanzen jeder Zelle einzeln, für die Tests).

    python generate_precomputed.py                         # rechnet alles neu (Optima mit dem Arc-Flow, mehrere Prozesse, einige Minuten)
    python generate_precomputed.py --keep-opt              # behält die in der Datei gespeicherten Optima und rechnet Raster und Stichprobe neu
    python generate_precomputed.py --nur-stichprobe        # ergänzt in der vorhandenen Datei nur die Stichprobe
    python generate_precomputed.py --check                 # rechnet das Raster (parallel) mit den gespeicherten Optima nach und vergleicht mit der Datei
    python generate_precomputed.py --check-opt             # rechnet die Optima neu und vergleicht die entschiedenen (hängt von der Rechenzeit ab: -1 = nicht entschieden)

Das Optimum je Instanz ist das ganzzahlige Arc-Flow-Programm der Stufe geordnet; -1 = nach dem Zeitlimit nicht bewiesen. Die Zahl der nicht entschiedenen Instanzen hängt von der Rechenzeit ab."""

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import arf_algorithm as A
import arf_constants as C
import arf_evaluation as ev
from arf_scenario import raster_instanz


def optimum_instanz(v: int, ni: int, j: int) -> int:
    """Optimum der Rasterinstanz (ganzzahliges Arc-Flow-Programm, Stufe geordnet); -1, wenn das Zeitlimit ohne Beweis erreicht wird."""
    inst = raster_instanz(v, ni, j)
    r = A.loese(list(inst.sizes), inst.cap, 2, True, C.ILP_ZEIT)
    return int(round(r["wert"])) if r["status"] == "optimal" else -1


def _optima(args):
    v, ni, j0, j1 = args
    return v, ni, j0, [optimum_instanz(v, ni, j) for j in range(j0, j1)]


def _zelle(args):
    v, ni, opt = args
    t = time.perf_counter()
    z = ev.messzelle(v, ni, opt)
    z["opt"] = opt
    return v, ni, z, time.perf_counter() - t


def _stichprobe_zelle(args):
    v, ni, opt = args
    return ev.zelle_schluessel(v, ni), {str(j): ev.messzelle(v, ni, opt, [j]) for j in C.STICHPROBE_J}


def _frisch(args):
    v, ni, opt = args
    z = ev.messzelle(v, ni, opt)
    z["opt"] = opt
    return ev.zelle_schluessel(v, ni), z


def _pool():
    return ProcessPoolExecutor(max(1, min(6, (os.cpu_count() or 2) // 2)))


def _zellen():
    return [(v, ni) for v in range(len(C.VERTEILUNGEN)) for ni in range(len(C.MESS_N))]


def optima_rechnen() -> dict:
    """Optimum je Instanz für alle Zellen; die 100 Instanzen jeder Zelle werden in Stücken zu 5 auf die Prozesse verteilt."""
    auftraege = [(v, ni, j0, j0 + 5) for v, ni in _zellen() for j0 in range(0, C.INSTANZEN, 5)]
    teile = {}
    with _pool() as pool:
        for v, ni, j0, werte in pool.map(_optima, auftraege):
            teile[(v, ni, j0)] = werte
            print(f"Optima {ev.zelle_schluessel(v, ni)} ab {j0}: {sum(1 for w in werte if w < 0)} offen", flush=True)
    return {ev.zelle_schluessel(v, ni): [w for j0 in range(0, C.INSTANZEN, 5) for w in teile[(v, ni, j0)]] for v, ni in _zellen()}


def stichprobe_ergaenzen(daten: dict) -> None:
    auftraege = [(v, ni, daten["zellen"][ev.zelle_schluessel(v, ni)]["opt"]) for v, ni in _zellen()]
    with _pool() as pool:
        daten["stichprobe"] = dict(pool.map(_stichprobe_zelle, auftraege))


def erzeugen(behalten: bool) -> dict:
    optima = {k: z["opt"] for k, z in ev.vorberechnet()["zellen"].items()} if behalten else optima_rechnen()
    daten = {"instanzen": C.INSTANZEN, "cap": C.MESS_CAP, "ilp_zeit": C.ILP_ZEIT, "zellen": {}}
    with _pool() as pool:
        for v, ni, z, sekunden in pool.map(_zelle, [(v, ni, optima[ev.zelle_schluessel(v, ni)]) for v, ni in _zellen()]):
            daten["zellen"][ev.zelle_schluessel(v, ni)] = z
            print(f"{ev.zelle_schluessel(v, ni)}: {sekunden:.0f} s", flush=True)
    daten["zellen"] = {ev.zelle_schluessel(v, ni): daten["zellen"][ev.zelle_schluessel(v, ni)] for v, ni in _zellen()}
    stichprobe_ergaenzen(daten)
    return daten


def schreiben(daten: dict) -> None:
    ev.PRECOMPUTED.write_text(json.dumps(daten, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print("geschrieben:", ev.PRECOMPUTED.name)


def pruefen() -> int:
    gespeichert = ev.vorberechnet()
    schlecht = 0
    with _pool() as pool:
        for schl, frisch in pool.map(_frisch, [(v, ni, gespeichert["zellen"][ev.zelle_schluessel(v, ni)]["opt"]) for v, ni in _zellen()]):
            if frisch != gespeichert["zellen"][schl]:
                schlecht += 1
                print("ABWEICHUNG", schl, flush=True)
    print("gleich" if not schlecht else f"{schlecht} Abweichungen")
    return 1 if schlecht else 0


def pruefen_optima() -> int:
    gespeichert = ev.vorberechnet()
    neu = optima_rechnen()
    schlecht = 0
    for k, liste in neu.items():
        alt = gespeichert["zellen"][k]["opt"]
        abw = [j for j, (a, b) in enumerate(zip(alt, liste)) if a >= 0 and b >= 0 and a != b]
        if abw:
            schlecht += len(abw)
            print("ABWEICHUNG Optimum", k, abw, flush=True)
    print("Optima gleich (soweit beide entschieden)" if not schlecht else f"{schlecht} Abweichungen")
    return 1 if schlecht else 0


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(pruefen())
    if "--check-opt" in sys.argv:
        sys.exit(pruefen_optima())
    if "--nur-stichprobe" in sys.argv:
        d = json.loads(ev.PRECOMPUTED.read_text(encoding="utf-8"))
        stichprobe_ergaenzen(d)
        schreiben(d)
        sys.exit(0)
    schreiben(erzeugen("--keep-opt" in sys.argv))
