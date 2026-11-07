"""Instanzen: Beispiele, zufällige Live-Instanzen und Rasterinstanzen (dieselben wie in Stück 2 und 4)."""

import random
from dataclasses import dataclass

import arf_constants as C


@dataclass(frozen=True)
class Instance:
    sizes: tuple          # Paketgrößen, ganzzahlig und positiv
    cap: int              # Kapazität eines Containers

    def __post_init__(self):
        if self.cap <= 0:
            raise ValueError("Kapazität muss positiv sein")
        for s in self.sizes:
            if not isinstance(s, int) or s <= 0 or s > self.cap:
                raise ValueError(f"Paketgröße {s!r} ungültig (ganz, 1 bis {self.cap})")

    @property
    def n(self) -> int:
        return len(self.sizes)


def beispiel(index: int) -> Instance:
    sizes, cap = C.BEISPIELE[index]
    return Instance(tuple(sizes), cap)


def zufallsinstanz(lo: float, hi: float, n: int, seed: int, cap: int) -> Instance:
    """n Pakete, Größen ganzzahlig und gleichverteilt zwischen lo*cap und hi*cap (mindestens 1)."""
    rng = random.Random(seed)
    a, b = max(1, int(lo * cap)), int(hi * cap)
    return Instance(tuple(rng.randint(a, b) for _ in range(n)), cap)


def live_instanz(verteilung: int, n: int, seed: int) -> Instance:
    _, _, lo, hi = C.VERTEILUNGEN[verteilung]
    return zufallsinstanz(lo, hi, n, seed, C.CAP)


def quelle_instanz(quelle: int, verteilung: int, n: int, seed: int) -> Instance:
    """Instanz der App: Quelle 0 bis 4 = feste Beispiele (n, Verteilung und Seed ohne Wirkung), sonst eine Zufallsinstanz."""
    if quelle in C.BEISPIELE:
        return beispiel(quelle)
    return live_instanz(verteilung, n, seed)


def raster_seed(verteilung: int, n_index: int, j: int) -> int:
    """Fester Seed der j-ten Instanz einer Rasterzelle; derselbe wie in Stück 2 (schranken-beweis-demo) und Stück 4 (lp-schranke-demo): dieselben Instanzen."""
    return 1_000_000 * (verteilung + 1) + 1_000 * (n_index + 1) + j


def raster_instanz(verteilung: int, n_index: int, j: int) -> Instance:
    _, _, lo, hi = C.VERTEILUNGEN[verteilung]
    return zufallsinstanz(lo, hi, C.MESS_N[n_index], raster_seed(verteilung, n_index, j), C.MESS_CAP)
