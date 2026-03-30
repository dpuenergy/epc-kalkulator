"""
Generátory Word výstupů pro EP a EA.

Použití::
    from epc_engine.reports import generuj_ep, generuj_ea
"""
from .ep_generator import generuj_ep
from .ea_generator import generuj_ea
from .vr_generator import generuj_prilohu_vr
from .hpr_generator import generuj_hpr
from .ses_generator import generuj_ses_prilohy

__all__ = ["generuj_ep", "generuj_ea", "generuj_prilohu_vr", "generuj_hpr", "generuj_ses_prilohy"]
