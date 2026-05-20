"""Adversarial corpus tests — Caveman S3/S4 validators.

Murat §9: 60+ hand-curated cases targeting semantic drift (CM5 RPN-9 BLOCK).
These tests verify the validators CATCH the attack patterns — not that Haiku
never produces them. The validators are the last line of defense.
"""
from __future__ import annotations

from typing import NamedTuple

import pytest

from praxis.kernel.compression.caveman.validate import validate_semantic, validate_structural


class Case(NamedTuple):
    name: str
    original: str
    compressed: str
    expected_errors: list[str]   # must contain at least these kinds
    unexpected_errors: list[str] = []  # must NOT contain these


# ---------------------------------------------------------------------------
# S3 — Polarity flip adversarial cases (the CM5 RPN-9 BLOCK)
# ---------------------------------------------------------------------------

POLARITY_FLIP_CASES: list[Case] = [
    Case(
        name="safe_to_unsafe",
        original="The authentication mechanism is safe and trusted.",
        compressed="The authentication mechanism is unsafe and untrusted.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="enable_to_disable",
        original="Enable the logging module and allow verbose output.",
        compressed="Disable the logging module and deny verbose output.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="valid_to_invalid",
        original="All configurations are valid and supported.",
        compressed="All configurations are invalid and unsupported.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="include_to_exclude",
        original="Include all required dependencies and accept the license.",
        compressed="Exclude all required dependencies and reject the license.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="correct_to_incorrect",
        original="The expected behavior is correct and the result is expected.",
        compressed="The expected behavior is incorrect and the result is unexpected.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="public_to_private",
        original="The public API allows all trusted requests.",
        compressed="The private API allows all untrusted requests.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="possible_to_impossible",
        original="It is possible to approve this configuration.",
        compressed="It is impossible to approve this configuration.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="require_to_optional",
        original="Authentication is required for all endpoints.",
        compressed="Authentication is optional for all endpoints.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="approve_to_reject",
        original="The committee will approve the proposed changes.",
        compressed="The committee will reject the proposed changes.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="allow_to_deny",
        original="The firewall rule will allow incoming connections from trusted sources.",
        compressed="The firewall rule will deny incoming connections from untrusted sources.",
        expected_errors=["polarity_flip"],
    ),
    # These should NOT trigger polarity flip (legitimate compression)
    Case(
        name="no_flip_both_safe",
        original="The system is safe and secure.",
        compressed="System is safe, secure.",
        expected_errors=[],
        unexpected_errors=["polarity_flip"],
    ),
    Case(
        name="no_flip_neutral",
        original="The user requested data processing.",
        compressed="User requested processing.",
        expected_errors=[],
        unexpected_errors=["polarity_flip"],
    ),
]

# ---------------------------------------------------------------------------
# S4 — Imperative inversion adversarial cases (FMEA V.3)
# ---------------------------------------------------------------------------

IMPERATIVE_INVERSION_CASES: list[Case] = [
    Case(
        name="do_to_dont",
        original="Do use the new API. Run the migration script. Include all tests.",
        compressed="Don't use the old API. Skip the migration. Omit the tests.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="use_to_avoid",
        original="Use the recommended configuration. Enable caching. Apply all patches.",
        compressed="Avoid the configuration. Disable caching. Omit all patches.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="include_to_exclude_imperative",
        original="Include all dependencies. Add the new module. Enable the feature.",
        compressed="Exclude all dependencies. Remove the module. Disable the feature.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="add_to_remove",
        original="Add the user to the group. Set the permission. Enable the role.",
        compressed="Remove the user from the group. Disable the permission. Skip the role.",
        expected_errors=["imperative_drift"],
    ),
    # Legitimate terse compression (should NOT trigger)
    Case(
        name="no_imperative_drift_terse",
        original="Use the API. Call the function. Set the flag.",
        compressed="Use API. Call function. Set flag.",
        expected_errors=[],
        unexpected_errors=["imperative_drift"],
    ),
]

# ---------------------------------------------------------------------------
# S1 — Negation drift adversarial cases
# ---------------------------------------------------------------------------

NEGATION_DRIFT_CASES: list[Case] = [
    Case(
        name="strip_not",
        original="Do not disable the safety checks. Never remove the validation.",
        compressed="Disable the safety checks. Remove the validation.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="strip_never",
        original="Never expose the private key. Do not log passwords.",
        compressed="Expose the private key. Log passwords.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="strip_without",
        original="Do not proceed without authentication. Never skip the review.",
        compressed="Proceed without authentication. Skip the review.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="add_spurious_negations",
        original="Enable the feature and allow the connection.",
        compressed="Do not enable the feature. Never allow the connection. Cannot proceed.",
        expected_errors=["negation_drift"],
    ),
    # Legitimate (should NOT trigger)
    Case(
        name="no_negation_drift_preserved",
        original="Do not disable this. Never remove that.",
        compressed="Don't disable this. Never remove that.",
        expected_errors=[],
        unexpected_errors=["negation_drift"],
    ),
]

# ---------------------------------------------------------------------------
# S2 — Number loss adversarial cases
# ---------------------------------------------------------------------------

NUMBER_LOSS_CASES: list[Case] = [
    Case(
        name="drop_all_numbers",
        original="The limit is 100, the timeout is 30s, and the retry count is 3.",
        compressed="The limit, timeout, and retry count are configured.",
        expected_errors=["number_loss"],
    ),
    Case(
        name="change_critical_version",
        original="Requires Python 3.12 and pydantic 2.6.",
        compressed="Requires Python and pydantic.",
        expected_errors=["number_loss"],
    ),
    Case(
        name="drop_cost_figure",
        original="The total cost is $4.25 per 1000 tokens.",
        compressed="The total cost is configured per tokens.",
        expected_errors=["number_loss"],
    ),
    # Legitimate
    Case(
        name="no_number_loss_all_present",
        original="The limit is 100 tokens.",
        compressed="Limit: 100 tokens.",
        expected_errors=[],
        unexpected_errors=["number_loss"],
    ),
]

# ---------------------------------------------------------------------------
# S1 structural — code block corruption
# ---------------------------------------------------------------------------

CODE_BLOCK_CASES: list[Case] = [
    Case(
        name="modified_code_block",
        original="Example:\n```python\nprint('hello')\n```\nDone.",
        compressed="Example:\n```python\nprint('MODIFIED')\n```\nDone.",
        expected_errors=["code_block_corruption"],
    ),
    Case(
        name="removed_code_block",
        original="Example:\n```bash\necho hello\n```\nDone.",
        compressed="Example was shown. Done.",
        expected_errors=["code_block_corruption"],
    ),
    Case(
        name="preserved_code_block",
        original="Use:\n```bash\necho hello\n```",
        compressed="Run:\n```bash\necho hello\n```",
        expected_errors=[],
        unexpected_errors=["code_block_corruption"],
    ),
]

# ---------------------------------------------------------------------------
# S3 — Additional polarity flip cases
# ---------------------------------------------------------------------------

POLARITY_FLIP_CASES_2: list[Case] = [
    Case(
        name="secure_to_insecure",
        original="The connection is secure and the certificate is valid.",
        compressed="The connection is insecure and the certificate is invalid.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="trusted_to_untrusted",
        original="Only trusted administrators can access this resource.",
        compressed="Only untrusted users can access this resource.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="success_to_failure",
        original="The operation was successful and the result is correct.",
        compressed="The operation was unsuccessful and the result is incorrect.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="authorized_to_unauthorized",
        original="This endpoint is authorized for all verified users.",
        compressed="This endpoint is unauthorized for all unverified users.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="encrypt_to_decrypt_context",
        original="The data is encrypted and protected at rest.",
        compressed="The data is unencrypted and unprotected at rest.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="no_flip_paraphrase",
        original="The system is reliable and well-tested.",
        compressed="System is reliable, well-tested.",
        expected_errors=[],
        unexpected_errors=["polarity_flip"],
    ),
]

# ---------------------------------------------------------------------------
# S4 — Additional imperative inversion cases
# ---------------------------------------------------------------------------

IMPERATIVE_INVERSION_CASES_2: list[Case] = [
    Case(
        name="install_to_uninstall",
        original="Install the security patch. Run the update script. Restart the service.",
        compressed="Uninstall the security patch. Skip the update. Stop the service.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="enable_to_disable_imperative",
        original="Enable MFA for all accounts. Require strong passwords. Lock accounts after 3 attempts.",
        compressed="Disable MFA. Allow weak passwords. Never lock accounts.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="grant_to_revoke",
        original="Grant read access to the audit team. Allow API key generation.",
        compressed="Revoke read access. Deny API key generation.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="no_drift_imperative_preserved",
        original="Enable the feature. Deploy the service. Monitor the logs.",
        compressed="Enable feature. Deploy service. Monitor logs.",
        expected_errors=[],
        unexpected_errors=["imperative_drift"],
    ),
]

# ---------------------------------------------------------------------------
# S1 — Additional negation drift cases
# ---------------------------------------------------------------------------

NEGATION_DRIFT_CASES_2: list[Case] = [
    Case(
        name="strip_do_not_delete",
        original="Do not delete the production database. Never drop tables in staging.",
        compressed="Delete the production database. Drop tables in staging.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="strip_cannot_must_not",
        original="You must not bypass the authentication layer. Cannot grant root access.",
        compressed="Bypass the authentication layer. Grant root access.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="add_negations_spurious_2",
        original="Proceed with deployment. Accept the change request.",
        compressed="Do not proceed with deployment. Reject the change request. Never accept.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="no_negation_terse_preserved",
        original="Never skip validation. Do not expose keys.",
        compressed="Never skip validation. Don't expose keys.",
        expected_errors=[],
        unexpected_errors=["negation_drift"],
    ),
]

# ---------------------------------------------------------------------------
# S2 — Additional number loss cases
# ---------------------------------------------------------------------------

NUMBER_LOSS_CASES_2: list[Case] = [
    Case(
        name="drop_port_number",
        original="Connect to the server on port 8443 with a 60s timeout.",
        compressed="Connect to the server with a timeout.",
        expected_errors=["number_loss"],
    ),
    Case(
        name="change_memory_limit",
        original="Set the memory limit to 4096 MB and CPU to 2 cores.",
        compressed="Set the memory limit and CPU allocation.",
        expected_errors=["number_loss"],
    ),
    Case(
        name="drop_percentage",
        original="The success rate is 99.9% over 30 days.",
        compressed="The success rate over the evaluation period is high.",
        expected_errors=["number_loss"],
    ),
    Case(
        name="no_number_loss_decimal",
        original="The rate is 3.14 requests per second.",
        compressed="Rate: 3.14 req/s.",
        expected_errors=[],
        unexpected_errors=["number_loss"],
    ),
]

# ---------------------------------------------------------------------------
# S1 structural — additional code block cases
# ---------------------------------------------------------------------------

CODE_BLOCK_CASES_2: list[Case] = [
    Case(
        name="modified_python_block",
        original="Run:\n```python\nos.remove('/tmp/safe')\n```",
        compressed="Run:\n```python\nos.remove('/etc/passwd')\n```",
        expected_errors=["code_block_corruption"],
    ),
    Case(
        name="removed_json_block",
        original="Config:\n```json\n{\"key\": \"value\"}\n```\nApply it.",
        compressed="Apply the config.",
        expected_errors=["code_block_corruption"],
    ),
    Case(
        name="preserved_yaml_block",
        original="Use:\n```yaml\nkey: value\n```",
        compressed="Apply:\n```yaml\nkey: value\n```",
        expected_errors=[],
        unexpected_errors=["code_block_corruption"],
    ),
    Case(
        name="modified_sql_block",
        original="Query:\n```sql\nSELECT id FROM users WHERE active=1;\n```",
        compressed="Query:\n```sql\nDELETE FROM users;\n```",
        expected_errors=["code_block_corruption"],
    ),
]

# ---------------------------------------------------------------------------
# Mixed / edge-case corpus (brings total to >= 60)
# ---------------------------------------------------------------------------

MIXED_EDGE_CASES: list[Case] = [
    # Polarity
    Case(
        name="protected_to_unprotected",
        original="All endpoints are protected and verified by the firewall.",
        compressed="All endpoints are unprotected and unverified by the firewall.",
        expected_errors=["polarity_flip"],
    ),
    Case(
        name="supported_to_unsupported",
        original="This configuration is supported in all production environments.",
        compressed="This configuration is unsupported in all production environments.",
        expected_errors=["polarity_flip"],
    ),
    # Imperative
    Case(
        name="create_to_drop",
        original="Create the schema. Deploy the migration. Start the service.",
        compressed="Drop the schema. Delete the migration. Stop the service.",
        expected_errors=["imperative_drift"],
    ),
    Case(
        name="allow_to_revoke",
        original="Allow external API access. Grant read permissions. Enable audit logging.",
        compressed="Deny external API access. Revoke read permissions. Disable audit logging.",
        expected_errors=["imperative_drift"],
    ),
    # Negation
    Case(
        name="strip_must_not",
        original="You must not store credentials in plaintext. Never log raw tokens.",
        compressed="Store credentials in plaintext. Log raw tokens.",
        expected_errors=["negation_drift"],
    ),
    Case(
        name="inject_negation_3",
        original="Start the migration. Apply the patch.",
        compressed="Never start the migration. Do not apply the patch. Cannot proceed without auth.",
        expected_errors=["negation_drift"],
    ),
    # Number loss
    Case(
        name="drop_token_count",
        original="The maximum context window is 200,000 tokens.",
        compressed="The maximum context window is large.",
        expected_errors=["number_loss"],
    ),
    Case(
        name="drop_sla_percentage",
        original="SLA guarantees 99.95% uptime over 365 days.",
        compressed="SLA guarantees uptime over the year.",
        expected_errors=["number_loss"],
    ),
    # Code block
    Case(
        name="removed_shell_block",
        original="Bootstrap:\n```sh\ncurl -sSL https://example.com/install.sh | sh\n```\nDone.",
        compressed="Bootstrap using the install script. Done.",
        expected_errors=["code_block_corruption"],
    ),
]

# Combine all adversarial cases
ALL_CASES: list[Case] = (
    POLARITY_FLIP_CASES
    + POLARITY_FLIP_CASES_2
    + IMPERATIVE_INVERSION_CASES
    + IMPERATIVE_INVERSION_CASES_2
    + NEGATION_DRIFT_CASES
    + NEGATION_DRIFT_CASES_2
    + NUMBER_LOSS_CASES
    + NUMBER_LOSS_CASES_2
    + CODE_BLOCK_CASES
    + CODE_BLOCK_CASES_2
    + MIXED_EDGE_CASES
)


# ---------------------------------------------------------------------------
# Parametrized test
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("case", ALL_CASES, ids=[c.name for c in ALL_CASES])
def test_adversarial_case(case: Case) -> None:
    """Each case must match expected error kinds exactly."""
    struct_errors = validate_structural(case.original, case.compressed)
    sem_errors = validate_semantic(case.original, case.compressed)
    all_kinds = {e.kind for e in struct_errors} | {e.kind for e in sem_errors}

    for expected in case.expected_errors:
        assert expected in all_kinds, (
            f"[{case.name}] Expected error {expected!r} but got: {all_kinds}"
        )

    for unexpected in case.unexpected_errors:
        assert unexpected not in all_kinds, (
            f"[{case.name}] Unexpected error {unexpected!r} in: {all_kinds}"
        )


def test_adversarial_total_count():
    """Verify we have at least 60 adversarial cases (Murat §9 requirement)."""
    assert len(ALL_CASES) >= 60, (
        f"Only {len(ALL_CASES)} adversarial cases — Murat requires >= 60"
    )
