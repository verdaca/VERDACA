"""Praxis Runtime spawner package.

Public surface:
  budgets.py       — ResourceBudget, BudgetExceededError
  circular_guard.py — CircularSpawnGuard, MaxSpawnDepthExceededError, CircularSpawnError
  lifecycle.py     — SpawnedAgent
  spawner.py       — AgentSpawner, _construct_proxy_for_role, compute_child_allowlist
"""
