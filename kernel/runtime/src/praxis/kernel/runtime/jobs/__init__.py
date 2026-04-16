"""Praxis Runtime — durable jobs infrastructure (F-3 absorption).

Architecture §4.2: jobs_queue + outbox_drain_retries tables + worker
lifecycle.  Satisfies NFR-C-A1 (7-day crypto-shred SLA) and NFR-Q6
(5-min crash RTO).
"""
