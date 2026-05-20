# mypy violation fixture — reviewer calling health
# Expected: mypy error "has no attribute 'health'"
from uuid import uuid4

from praxis.kernel.runtime.proxies import ReviewerMemoryProxy

proxy = ReviewerMemoryProxy(memory=None, tenant_id="t", agent_name="a", spawn_id=uuid4())
proxy.health()  # violation
