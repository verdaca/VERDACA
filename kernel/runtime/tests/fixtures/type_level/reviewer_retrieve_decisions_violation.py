# mypy violation fixture — reviewer calling retrieve_decisions
# Expected: mypy error "has no attribute 'retrieve_decisions'"
from uuid import uuid4

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy

proxy = ReviewerMemoryProxy(memory=None, tenant_id="t", agent_name="a", spawn_id=uuid4())
proxy.retrieve_decisions(tenant_id="t", query="q")  # violation
