"""specsmith.esdb.bridge — thin re-export of chronomemory.EsdbBridge.

EsdbBridge lives in the chronomemory package; this module exposes it under
the specsmith.esdb.bridge namespace so that save/load commands can import it
without depending directly on chronomemory at the top of cli.py.
"""

from chronomemory import EsdbBridge

__all__ = ["EsdbBridge"]
