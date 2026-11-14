"""Pool-engine BRLIA.

O hot path (admit -> ring -> pool_id, close + netting) vive no nucleo
compilado brlia_pool_core (Rust com binding PyO3). Este pacote expoe apenas o
control plane e as fachadas de integracao. Redis e PostgreSQL sao proibidos no
trajeto de admissao.
"""

__version__ = "2.1.0"
