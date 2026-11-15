"""Conectores de leitura somente: erp, core-banking, tms, pix-api.

Nenhum conector escreve no sistema do host. Nenhum conector altera codigo,
configuracao ou estado do ERP, do core banking ou do TMS. A coleta e
somente leitura e alimenta eventos pseudonimizados.
"""

from __future__ import annotations

from connectors.erp import ErpConnector
from connectors.core_banking import CoreBankingConnector
from connectors.tms import TmsConnector
from connectors.pix_api import PixApiConnector

__all__ = ["ErpConnector", "CoreBankingConnector", "TmsConnector", "PixApiConnector"]
