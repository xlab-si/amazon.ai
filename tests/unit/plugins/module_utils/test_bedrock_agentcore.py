#!/usr/bin/env python

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Unit tests for bedrock_agentcore module_utils and the runtime endpoint module."""

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import AgentRuntimeEndpointStatus
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import _create_agent_runtime_endpoint_api
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import create_agent_runtime_endpoint
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import diff_memory_strategies
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import strategy_configuration_to_modify_shape
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import wait_for_agent_runtime_endpoint_status
from ansible_collections.amazon.ai.plugins.modules.bedrock_agentcore_memory import _check_botocore_features
from ansible_collections.amazon.ai.plugins.modules.bedrock_agentcore_runtime_endpoint import (
    _runtime_endpoint_status_check,
)
from botocore.exceptions import ClientError


class FailJsonException(Exception):
    """Stand-in for AnsibleModule.fail_json, which terminates execution via sys.exit."""


class ExitJsonException(Exception):
    """Stand-in for AnsibleModule.exit_json, which terminates execution via sys.exit."""


def _make_module(check_mode=False, wait=True, wait_timeout=600):
    module = MagicMock()
    module.check_mode = check_mode
    module.params = {"wait": wait, "wait_timeout": wait_timeout}
    module.fail_json.side_effect = FailJsonException()
    module.exit_json.side_effect = ExitJsonException()
    return module


# ---------------------------------------------------------------------------
# wait_for_agent_runtime_endpoint_status
# ---------------------------------------------------------------------------


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_returns_cleanly_when_deleting_endpoint_disappears(mock_get):
    """A DELETED wait target is satisfied when the endpoint is gone (the DELETING regression)."""
    mock_get.return_value = None
    module = _make_module()

    wait_for_agent_runtime_endpoint_status(MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.DELETED)

    module.fail_json.assert_not_called()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_fails_when_endpoint_missing_but_target_is_ready(mock_get):
    """A missing endpoint while waiting for READY is a genuine error."""
    mock_get.return_value = None
    module = _make_module()

    with pytest.raises(FailJsonException):
        wait_for_agent_runtime_endpoint_status(
            MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.READY
        )

    module.fail_json.assert_called_once()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_returns_when_target_status_reached(mock_get):
    mock_get.return_value = {"name": "ep-name", "status": "READY"}
    module = _make_module()

    wait_for_agent_runtime_endpoint_status(MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.READY)

    module.fail_json.assert_not_called()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_fails_on_failed_status_by_default(mock_get):
    mock_get.return_value = {"name": "ep-name", "status": "CREATE_FAILED", "failure_reason": "boom"}
    module = _make_module()

    with pytest.raises(FailJsonException):
        wait_for_agent_runtime_endpoint_status(
            MagicMock(), module, "rt-id", "ep-name", AgentRuntimeEndpointStatus.READY
        )

    module.fail_json.assert_called_once()


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.get_agent_runtime_endpoint")
def test_wait_returns_on_failed_status_when_fail_disabled(mock_get):
    """With fail_on_failed_status=False a terminal *_FAILED state settles instead of failing."""
    mock_get.return_value = {"name": "ep-name", "status": "UPDATE_FAILED", "failure_reason": "boom"}
    module = _make_module()

    wait_for_agent_runtime_endpoint_status(
        MagicMock(),
        module,
        "rt-id",
        "ep-name",
        AgentRuntimeEndpointStatus.DELETED,
        fail_on_failed_status=False,
    )

    module.fail_json.assert_not_called()


# ---------------------------------------------------------------------------
# _runtime_endpoint_status_check (module level)
# ---------------------------------------------------------------------------

_MODULE = "ansible_collections.amazon.ai.plugins.modules.bedrock_agentcore_runtime_endpoint"


def test_status_check_returns_none_for_missing_endpoint():
    module = _make_module()
    assert _runtime_endpoint_status_check(MagicMock(), None, module, "rt-id", "present") is None


@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_passes_through_settled_endpoint(mock_wait):
    module = _make_module()
    endpoint = {"name": "ep-name", "status": "READY"}

    result = _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "present")

    assert result is endpoint
    mock_wait.assert_not_called()


@patch(f"{_MODULE}.get_agent_runtime_endpoint")
@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_deleting_waits_for_deleted_without_failing(mock_wait, mock_get):
    """DELETING + state=absent waits for DELETED and tolerates *_FAILED states."""
    mock_get.return_value = None
    module = _make_module()
    endpoint = {"name": "ep-name", "status": "DELETING"}

    result = _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "absent")

    assert result is None
    args = mock_wait.call_args.args
    kwargs = mock_wait.call_args.kwargs
    assert args[4] == AgentRuntimeEndpointStatus.DELETED
    assert kwargs["fail_on_failed_status"] is False


@patch(f"{_MODULE}.get_agent_runtime_endpoint")
@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_creating_waits_for_ready_and_fails_on_failure(mock_wait, mock_get):
    """CREATING + state=present waits for READY and surfaces *_FAILED states."""
    refreshed = {"name": "ep-name", "status": "READY"}
    mock_get.return_value = refreshed
    module = _make_module()
    endpoint = {"name": "ep-name", "status": "CREATING"}

    result = _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "present")

    assert result is refreshed
    args = mock_wait.call_args.args
    kwargs = mock_wait.call_args.kwargs
    assert args[4] == AgentRuntimeEndpointStatus.READY
    assert kwargs["fail_on_failed_status"] is True


@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_check_mode_short_circuits(mock_wait):
    module = _make_module(check_mode=True)
    endpoint = {"name": "ep-name", "status": "DELETING"}

    with pytest.raises(ExitJsonException):
        _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "absent")

    mock_wait.assert_not_called()
    module.exit_json.assert_called_once()


@patch(f"{_MODULE}.wait_for_agent_runtime_endpoint_status")
def test_status_check_no_wait_short_circuits(mock_wait):
    module = _make_module(wait=False)
    endpoint = {"name": "ep-name", "status": "CREATING"}

    with pytest.raises(ExitJsonException):
        _runtime_endpoint_status_check(MagicMock(), endpoint, module, "rt-id", "present")

    mock_wait.assert_not_called()
    module.exit_json.assert_called_once()


# ---------------------------------------------------------------------------
# create_agent_runtime_endpoint ConflictException retry
# ---------------------------------------------------------------------------


@patch("ansible_collections.amazon.aws.plugins.module_utils.cloud.time.sleep", return_value=None)
def test_create_endpoint_api_retries_on_conflict(_mock_sleep):
    """A ConflictException on an immediate re-create is retried until it succeeds."""
    client = MagicMock()
    conflict = ClientError(
        {"Error": {"Code": "ConflictException", "Message": "still deleting"}},
        "CreateAgentRuntimeEndpoint",
    )
    client.create_agent_runtime_endpoint.side_effect = [conflict, {"name": "ep-name"}]

    result = _create_agent_runtime_endpoint_api(client, agentRuntimeId="rt-id", name="ep-name")

    assert result == {"name": "ep-name"}
    assert client.create_agent_runtime_endpoint.call_count == 2


@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore._create_agent_runtime_endpoint_api")
@patch("ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore.wait_for_agent_runtime_endpoint_status")
def test_create_endpoint_uses_retrying_api(mock_wait, mock_api):
    mock_api.return_value = {"name": "ep-name"}
    module = _make_module()
    module.params.update({"endpoint_name": "ep-name", "agent_runtime_version": None, "description": None})
    client = MagicMock()

    changed, name, _msg = create_agent_runtime_endpoint(module, client, "rt-id")

    assert changed is True
    assert name == "ep-name"
    mock_api.assert_called_once()
    client.create_agent_runtime_endpoint.assert_not_called()
    mock_wait.assert_called_once()


def test_create_endpoint_check_mode_does_not_call_aws():
    module = _make_module(check_mode=True)
    module.params.update({"endpoint_name": "ep-name"})
    client = MagicMock()

    changed, name, _msg = create_agent_runtime_endpoint(module, client, "rt-id")

    assert changed is True
    assert name is None
    client.create_agent_runtime_endpoint.assert_not_called()


# ------------------------------------------------
# Tests for strategy_configuration_to_modify_shape
# ------------------------------------------------
BLOCK = {"append_to_prompt": "Focus on facts.", "model_id": "anthropic.claude-3-haiku-20240307-v1:0"}
SELF_MANAGED = {
    "invocation_configuration": {
        "topic_arn": "arn:aws:sns:us-east-1:123456789012:topic",
        "payload_delivery_bucket_name": "bucket",
    },
    "trigger_conditions": [{"message_based_trigger": {"message_count": 5}}],
    "historical_context_window_size": 4,
}
REFLECTION_CONFIGURATION = {"namespace_templates": ["/reflections/{actorId}"]}


def _custom(configuration):
    return {"name": "custom", "configuration": configuration}


@pytest.mark.parametrize(
    "strategy_key,strategy,expected",
    [
        (
            "custom_memory_strategy",
            _custom({"semantic_override": {"extraction": BLOCK}}),
            {"extraction": {"custom_extraction_configuration": {"semantic_extraction_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"semantic_override": {"consolidation": BLOCK}}),
            {"consolidation": {"custom_consolidation_configuration": {"semantic_consolidation_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"summary_override": {"consolidation": BLOCK}}),
            {"consolidation": {"custom_consolidation_configuration": {"summary_consolidation_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"user_preference_override": {"extraction": BLOCK}}),
            {"extraction": {"custom_extraction_configuration": {"user_preference_extraction_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"user_preference_override": {"consolidation": BLOCK}}),
            {
                "consolidation": {
                    "custom_consolidation_configuration": {"user_preference_consolidation_override": BLOCK}
                }
            },
        ),
        (
            "custom_memory_strategy",
            _custom({"episodic_override": {"extraction": BLOCK}}),
            {"extraction": {"custom_extraction_configuration": {"episodic_extraction_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"episodic_override": {"consolidation": BLOCK}}),
            {"consolidation": {"custom_consolidation_configuration": {"episodic_consolidation_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"episodic_override": {"reflection": BLOCK}}),
            {"reflection": {"custom_reflection_configuration": {"episodic_reflection_override": BLOCK}}},
        ),
        (
            "custom_memory_strategy",
            _custom({"self_managed_configuration": SELF_MANAGED}),
            {"self_managed_configuration": SELF_MANAGED},
        ),
        (
            "episodic_memory_strategy",
            {"name": "episodes", "reflection_configuration": REFLECTION_CONFIGURATION},
            {"reflection": {"episodic_reflection_configuration": REFLECTION_CONFIGURATION}},
        ),
        ("semantic_memory_strategy", {"name": "facts", "description": "Facts"}, {}),
        ("episodic_memory_strategy", {"name": "episodes", "reflection_configuration": None}, {}),
    ],
    ids=[
        "semantic-extraction",
        "semantic-consolidation",
        "summary-consolidation",
        "user-preference-extraction",
        "user-preference-consolidation",
        "episodic-extraction",
        "episodic-consolidation",
        "episodic-reflection",
        "self-managed",
        "episodic-reflection-configuration",
        "built-in-no-configuration",
        "episodic-without-reflection",
    ],
)
def test_strategy_configuration_to_modify_shape(strategy_key, strategy, expected):
    assert strategy_configuration_to_modify_shape(strategy_key, strategy) == expected


def test_strategy_configuration_to_modify_shape_combines_blocks_and_scrubs_none():
    strategy = _custom(
        {
            "semantic_override": {"extraction": BLOCK, "consolidation": dict(BLOCK, model_id="other")},
            "summary_override": None,
            "self_managed_configuration": None,
        }
    )
    assert strategy_configuration_to_modify_shape("custom_memory_strategy", strategy) == {
        "extraction": {"custom_extraction_configuration": {"semantic_extraction_override": BLOCK}},
        "consolidation": {
            "custom_consolidation_configuration": {"semantic_consolidation_override": dict(BLOCK, model_id="other")}
        },
    }


# --------------------------------
# Tests for diff_memory_strategies
# --------------------------------
def _declared(strategy_key, **strategy):
    """A memory_strategies element as AnsibleModule hands it over, unset keys included as None."""
    element = {
        key: None
        for key in (
            "semantic_memory_strategy",
            "summary_memory_strategy",
            "user_preference_memory_strategy",
            "episodic_memory_strategy",
            "custom_memory_strategy",
        )
    }
    element[strategy_key] = dict({"description": None, "namespace_templates": None}, **strategy)
    return element


SEMANTIC_CURRENT = {
    "strategy_id": "facts-abcdef1234",
    "name": "facts",
    "description": "Facts",
    "type": "SEMANTIC",
    "status": "ACTIVE",
    "namespaces": ["/strategy/{memoryStrategyId}/actors/{actorId}/"],
    "namespace_templates": ["/strategy/{memoryStrategyId}/actors/{actorId}/"],
}

CUSTOM_CURRENT = {
    "strategy_id": "custom-abcdef1234",
    "name": "custom",
    "type": "CUSTOM",
    "status": "ACTIVE",
    "namespace_templates": ["/custom/{actorId}"],
    "configuration": {
        "type": "SEMANTIC_OVERRIDE",
        "extraction": {"custom_extraction_configuration": {"semantic_extraction_override": BLOCK}},
    },
}


def test_diff_memory_strategies_no_change():
    desired = [
        _declared("semantic_memory_strategy", name="facts", description="Facts"),
        _declared("custom_memory_strategy", name="custom", configuration={"semantic_override": {"extraction": BLOCK}}),
    ]
    assert diff_memory_strategies([SEMANTIC_CURRENT, CUSTOM_CURRENT], desired) == ([], [], [])


def test_diff_memory_strategies_add_only():
    desired = [
        _declared("semantic_memory_strategy", name="facts", description="Facts"),
        _declared("summary_memory_strategy", name="summaries"),
    ]
    assert diff_memory_strategies([SEMANTIC_CURRENT], desired) == (
        [{"summary_memory_strategy": {"name": "summaries"}}],
        [],
        [],
    )


def test_diff_memory_strategies_delete_only():
    desired = [_declared("semantic_memory_strategy", name="facts")]
    assert diff_memory_strategies([SEMANTIC_CURRENT, CUSTOM_CURRENT], desired) == (
        [],
        [],
        [{"memory_strategy_id": "custom-abcdef1234"}],
    )


def test_diff_memory_strategies_empty_desired_deletes_all():
    assert diff_memory_strategies([SEMANTIC_CURRENT, CUSTOM_CURRENT], []) == (
        [],
        [],
        [{"memory_strategy_id": "facts-abcdef1234"}, {"memory_strategy_id": "custom-abcdef1234"}],
    )


def test_diff_memory_strategies_description_change():
    desired = [_declared("semantic_memory_strategy", name="facts", description="Durable facts")]
    assert diff_memory_strategies([SEMANTIC_CURRENT], desired) == (
        [],
        [{"memory_strategy_id": "facts-abcdef1234", "description": "Durable facts"}],
        [],
    )


def test_diff_memory_strategies_custom_override_change():
    changed_block = dict(BLOCK, append_to_prompt="Focus on preferences.")
    desired = [
        _declared(
            "custom_memory_strategy", name="custom", configuration={"semantic_override": {"extraction": changed_block}}
        )
    ]
    assert diff_memory_strategies([CUSTOM_CURRENT], desired) == (
        [],
        [
            {
                "memory_strategy_id": "custom-abcdef1234",
                "configuration": {
                    "extraction": {"custom_extraction_configuration": {"semantic_extraction_override": changed_block}}
                },
            }
        ],
        [],
    )


def test_diff_memory_strategies_record_expiry_change():
    current = dict(SEMANTIC_CURRENT, record_expiry_duration_days=60)
    unchanged = [
        _declared(
            "semantic_memory_strategy", name="facts", record_expiry_specification={"record_expiry_duration_days": 60}
        )
    ]
    changed = [
        _declared(
            "semantic_memory_strategy", name="facts", record_expiry_specification={"record_expiry_duration_days": 90}
        )
    ]
    assert diff_memory_strategies([current], unchanged) == ([], [], [])
    assert diff_memory_strategies([current], changed) == (
        [],
        [
            {
                "memory_strategy_id": "facts-abcdef1234",
                "record_expiry_specification": {"record_expiry_duration_days": 90},
            }
        ],
        [],
    )


def test_diff_memory_strategies_unsupplied_field_is_ignored():
    # AWS fills in a default namespace template the user never declared.
    desired = [_declared("semantic_memory_strategy", name="facts")]
    assert SEMANTIC_CURRENT["namespace_templates"]
    assert diff_memory_strategies([SEMANTIC_CURRENT], desired) == ([], [], [])


def test_diff_memory_strategies_type_change():
    desired = [_declared("summary_memory_strategy", name="facts")]
    with pytest.raises(ValueError, match=r"Memory strategy facts cannot change type from SEMANTIC to SUMMARIZATION"):
        diff_memory_strategies([SEMANTIC_CURRENT], desired)


def test_diff_memory_strategies_duplicate_desired_name():
    desired = [
        _declared("semantic_memory_strategy", name="facts"),
        _declared("summary_memory_strategy", name="facts"),
    ]
    with pytest.raises(ValueError, match=r"Memory strategy name facts is declared more than once"):
        diff_memory_strategies([], desired)


def test_diff_memory_strategies_duplicate_current_name():
    with pytest.raises(ValueError, match=r"Memory strategy name facts appears more than once"):
        diff_memory_strategies([SEMANTIC_CURRENT, dict(SEMANTIC_CURRENT, strategy_id="facts-zzzzzzzzzz")], [])


# --------------------------------
# bedrock_agentcore_memory botocore gates
# --------------------------------


def _make_versioned_module(installed, **params):
    module = _make_module()
    module.params.update(params)
    module.botocore_at_least.side_effect = lambda version: tuple(map(int, version.split("."))) <= installed
    return module


def test_memory_botocore_gate_fails_below_agentcore_floor():
    module = _make_versioned_module((1, 38, 0), state="absent")

    with pytest.raises(FailJsonException):
        _check_botocore_features(module)

    assert "requires botocore >= 1.39.7" in module.fail_json.call_args.kwargs["msg"]


def test_memory_botocore_gate_skips_options_when_absent():
    module = _make_versioned_module((1, 39, 7), state="absent", tags={"a": "b"}, namespace_keys=[{"key": "k"}])

    _check_botocore_features(module)

    module.fail_json.assert_not_called()


def test_memory_botocore_gate_fails_on_nested_strategy_key():
    strategies = [{"semantic_memory_strategy": {"name": "facts", "record_expiry_specification": {"x": 1}}}]
    module = _make_versioned_module((1, 43, 111), state="present", memory_strategies=strategies)

    with pytest.raises(FailJsonException):
        _check_botocore_features(module)

    assert module.fail_json.call_args.kwargs["msg"] == (
        "The record_expiry_specification option in memory_strategies requires botocore >= 1.43.112."
    )
