# mypy violation fixture — reviewer calling store_task_outcome
# Expected: mypy error "has no attribute 'store_task_outcome'"
from uuid import uuid4

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy

proxy = ReviewerMemoryProxy(memory=None, tenant_id="t", agent_name="a", spawn_id=uuid4())
proxy.store_task_outcome(tenant_id="t", task=None, outcome=None)  # violation
