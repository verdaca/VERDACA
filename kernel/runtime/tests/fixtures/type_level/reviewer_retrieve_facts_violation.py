# mypy violation fixture — reviewer calling retrieve_facts
# Expected: mypy error "has no attribute 'retrieve_facts'"
from uuid import uuid4

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy

proxy = ReviewerMemoryProxy(memory=None, tenant_id="t", agent_name="a", spawn_id=uuid4())
proxy.retrieve_facts(tenant_id="t", agent_id="a", run_id="r", query="q")  # violation
