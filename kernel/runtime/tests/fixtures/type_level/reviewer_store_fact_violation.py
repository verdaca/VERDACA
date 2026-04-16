# mypy violation fixture — reviewer calling store_fact
# Expected: mypy error "has no attribute 'store_fact'"
from uuid import uuid4

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy

proxy = ReviewerMemoryProxy(memory=None, tenant_id="t", agent_name="a", spawn_id=uuid4())
proxy.store_fact(tenant_id="t", agent_id="a", run_id="r", fact=None)  # violation
