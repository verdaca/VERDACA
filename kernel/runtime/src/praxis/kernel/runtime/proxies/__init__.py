"""Memory proxy types for the Praxis Runtime.

Public surface:
  AgentRole              — enum for proxy construction
  ProducerMemoryProxy    — full MemoryProtocol surface
  ReviewerMemoryProxy    — 2-method surface (store_decision, flag_and_quarantine)
  _construct_memory_proxy — single proxy creation point (Spawner uses this)
"""

from praxis.kernel.runtime.proxies._base import AgentRole
from praxis.kernel.runtime.proxies._construction import _construct_memory_proxy
from praxis.kernel.runtime.proxies.producer import ProducerMemoryProxy
from praxis.kernel.runtime.proxies.reviewer import ReviewerMemoryProxy

__all__ = [
    "AgentRole",
    "_construct_memory_proxy",
    "ProducerMemoryProxy",
    "ReviewerMemoryProxy",
]
