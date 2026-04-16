"""ShellCostAdapter contract tests — test-strategy §4.2.

SHELL-T-ADAPT-CONTRACT-01: ULID-format request_id
SHELL-T-ADAPT-CONTRACT-02: MAC request_id stashed in tags
SHELL-T-ADAPT-CONTRACT-03: LLMResponse has NO usd_cost field
SHELL-T-ADAPT-CONTRACT-04: Only integer token counts forwarded
SHELL-T-ADAPT-CONTRACT-07: CostRecord has correct session_id + workflow_id
"""

from __future__ import annotations

import re

import pytest

from api.adapters.cost_adapter import (
    CostRecord,
    PiMonoLLMRequest,
    PiMonoLLMResponse,
    ShellCostAdapter,
    ULID_REGEX,
)
from tests.conftest import FakeCostTracker


ULID_PATTERN = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")


@pytest.fixture
def cost_adapter(fake_cost_tracker: FakeCostTracker) -> ShellCostAdapter:
    return ShellCostAdapter(tracker=fake_cost_tracker)


class TestShellCostAdapterContract:
    """C-2 / C-3 adapter contract verification."""

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_01_ulid_format(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """SHELL-T-ADAPT-CONTRACT-01: request_id is ULID format."""
        await cost_adapter.track_mac_call(
            mac_request_id="mac:cycle_1:propose:3",
            provider="anthropic",
            model_id="claude-sonnet-4-6",
            session_id="01HXYZ_SESSION",
            workflow_id="01HXYZ_WORKFLOW",
            input_tokens=1000,
            output_tokens=500,
        )

        assert len(fake_cost_tracker.events) == 1
        request, _ = fake_cost_tracker.events[0]
        assert ULID_PATTERN.match(request.request_id), (
            f"request_id {request.request_id!r} does not match ULID format"
        )

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_02_mac_id_in_tags(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """SHELL-T-ADAPT-CONTRACT-02: MAC request_id stashed in tags."""
        mac_id = "mac:cycle_1:propose:3"
        await cost_adapter.track_mac_call(
            mac_request_id=mac_id,
            provider="anthropic",
            model_id="claude-sonnet-4-6",
            session_id="01HXYZ_SESSION",
            workflow_id="01HXYZ_WORKFLOW",
            input_tokens=1000,
            output_tokens=500,
        )

        request, _ = fake_cost_tracker.events[0]
        assert request.tags["mac_request_id"] == mac_id

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_03_no_usd_cost(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """SHELL-T-ADAPT-CONTRACT-03: LLMResponse has NO usd_cost field."""
        await cost_adapter.track_mac_call(
            mac_request_id="mac:cycle_1:propose:1",
            provider="anthropic",
            model_id="claude-sonnet-4-6",
            session_id="01HXYZ_SESSION",
            workflow_id="01HXYZ_WORKFLOW",
            input_tokens=1000,
            output_tokens=500,
        )

        _, response = fake_cost_tracker.events[0]
        assert not hasattr(response, "usd_cost"), (
            "PiMonoLLMResponse must NOT have a usd_cost field (C-3 contract)"
        )

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_04_integer_tokens_only(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """SHELL-T-ADAPT-CONTRACT-04: Only integer token counts forwarded."""
        await cost_adapter.track_mac_call(
            mac_request_id="mac:cycle_2:review:1",
            provider="anthropic",
            model_id="claude-opus-4-6",
            session_id="01HXYZ_SESSION",
            workflow_id="01HXYZ_WORKFLOW",
            input_tokens=2000,
            output_tokens=800,
            cache_read_tokens=500,
            cache_write_tokens=100,
        )

        _, response = fake_cost_tracker.events[0]
        assert isinstance(response.input_tokens, int)
        assert isinstance(response.output_tokens, int)
        assert isinstance(response.cache_read_tokens, int)
        assert isinstance(response.cache_write_tokens, int)
        assert response.input_tokens == 2000
        assert response.output_tokens == 800
        assert response.cache_read_tokens == 500
        assert response.cache_write_tokens == 100

    @pytest.mark.shell_adapt
    @pytest.mark.critical
    async def test_adapt_contract_07_session_and_workflow_id(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """SHELL-T-ADAPT-CONTRACT-07: CostRecord has correct session_id + workflow_id."""
        session_id = "01HXYZ_SESSION_ABC"
        workflow_id = "01HXYZ_WORKFLOW_DEF"
        await cost_adapter.track_mac_call(
            mac_request_id="mac:cycle_1:propose:1",
            provider="anthropic",
            model_id="claude-sonnet-4-6",
            session_id=session_id,
            workflow_id=workflow_id,
            input_tokens=100,
            output_tokens=50,
        )

        request, _ = fake_cost_tracker.events[0]
        assert request.session_id == session_id
        assert request.workflow_id == workflow_id

    @pytest.mark.shell_adapt
    async def test_unique_ulid_per_call(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """Each track_mac_call mints a unique ULID."""
        for i in range(3):
            await cost_adapter.track_mac_call(
                mac_request_id=f"mac:cycle_1:propose:{i}",
                provider="anthropic",
                model_id="claude-sonnet-4-6",
                session_id="sess",
                workflow_id="wf",
                input_tokens=100,
                output_tokens=50,
            )

        ulids = [req.request_id for req, _ in fake_cost_tracker.events]
        assert len(set(ulids)) == 3, "Each call must produce a unique ULID"

    @pytest.mark.shell_adapt
    async def test_request_response_id_match(
        self, cost_adapter: ShellCostAdapter, fake_cost_tracker: FakeCostTracker
    ):
        """Request and response share the same ULID."""
        await cost_adapter.track_mac_call(
            mac_request_id="mac:cycle_1:propose:1",
            provider="anthropic",
            model_id="claude-sonnet-4-6",
            session_id="sess",
            workflow_id="wf",
            input_tokens=100,
            output_tokens=50,
        )

        request, response = fake_cost_tracker.events[0]
        assert request.request_id == response.request_id


class TestPiMonoLLMResponseShape:
    """Verify the PiMonoLLMResponse dataclass has no usd_cost field."""

    @pytest.mark.shell_adapt
    @pytest.mark.static
    def test_response_fields_exclude_usd_cost(self):
        """C-3 structural: PiMonoLLMResponse must not define usd_cost."""
        fields = {f.name for f in PiMonoLLMResponse.__dataclass_fields__.values()}
        assert "usd_cost" not in fields, (
            "PiMonoLLMResponse must NOT define usd_cost (C-3 contract)"
        )
