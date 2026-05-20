# mypy violation fixture — reviewer calling retrieve_similar_tasks
# Expected: mypy error "has no attribute 'retrieve_similar_tasks'"
from uuid import uuid4

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy

proxy = ReviewerMemoryProxy(memory=None, tenant_id="t", agent_name="a", spawn_id=uuid4())
proxy.retrieve_similar_tasks(tenant_id="t", signature=None)  # violation
