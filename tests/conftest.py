"""Gemeinsame Fixtures: die Mini-Instanz, an der jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from arf_scenario import Instance  # noqa: E402


@pytest.fixture
def mini():
    """Das kleine Beispiel: vier Pakete der Größe 4 und eines der Größe 3, Kapazität 10. Von Hand gerechnet (Details in tests/test_algorithm.py): Graphen mit 11, 6 und 6 Knoten und 25, 11 und
    10 Bögen; Arc-Flow-LP 2,25 (LP von Stück 4: 2,5), Optimum 3, FFD 3, L1 2, L2 2: erst der aufgerundete LP-Wert beweist das Optimum."""
    return Instance((4, 4, 4, 4, 3), 10)
