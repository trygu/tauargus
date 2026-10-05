"""Tau-Argus: Statistical Disclosure Control with open-source solvers (HiGHS).

High-level API:
    from tauargus import Engine
    eng = Engine()
    ...

The native engine (C++ core + HiGHS-backed solvers) is exposed through the
compiled extension ``tauargus._tauargus``.
"""

from ._tauargus import TauArgus, HiTaSCtrl, RounderCtrl  # noqa: F401

__version__ = "0.1.0"
__all__ = ["TauArgus", "HiTaSCtrl", "RounderCtrl", "Engine", "__version__"]


def __getattr__(name):
    # Lazy so `import tauargus` works even before engine.py is imported.
    if name == "Engine":
        from .engine import Engine

        return Engine
    raise AttributeError(name)
