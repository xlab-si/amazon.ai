# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

import time
from enum import Enum
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from ansible_collections.amazon.ai.plugins.module_utils.utils import is_subset

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict
from ansible.module_utils.common.dict_transformations import snake_dict_to_camel_dict

from ansible_collections.amazon.aws.plugins.module_utils.botocore import is_boto3_error_code
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.tagging import compare_aws_tags
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


AGENTCORE_MINIMUM_BOTOCORE_VERSION = "1.39.7"


class AgentRuntimeStatus(str, Enum):
    DELETING = "DELETING"
    DELETED = "DELETED"
    CREATING = "CREATING"
    CREATE_FAILED = "CREATE_FAILED"
    UPDATING = "UPDATING"
    UPDATE_FAILED = "UPDATE_FAILED"
    READY = "READY"


class AgentRuntimeEndpointStatus(str, Enum):
    CREATING = "CREATING"
    CREATE_FAILED = "CREATE_FAILED"
    UPDATING = "UPDATING"
    UPDATE_FAILED = "UPDATE_FAILED"
    READY = "READY"
    DELETING = "DELETING"
    DELETED = "DELETED"


class MemoryStatus(str, Enum):
    CREATING = "CREATING"
    ACTIVE = "ACTIVE"
    FAILED = "FAILED"
    DELETING = "DELETING"
    UPDATING = "UPDATING"
    DELETED = "DELETED"


# Declared memory strategy key -> the `type` AWS reports for it on read.
MEMORY_STRATEGY_TYPES = {
    "semantic_memory_strategy": "SEMANTIC",
    "summary_memory_strategy": "SUMMARIZATION",
    "user_preference_memory_strategy": "USER_PREFERENCE",
    "episodic_memory_strategy": "EPISODIC",
    "custom_memory_strategy": "CUSTOM",
}

# Custom strategy override (create shape) -> {block: leaf key under the modify/read `custom_*_configuration`}.
_OVERRIDE_BLOCKS = {
    "semantic_override": {
        "extraction": "semantic_extraction_override",
        "consolidation": "semantic_consolidation_override",
    },
    "summary_override": {
        "consolidation": "summary_consolidation_override",
    },
    "user_preference_override": {
        "extraction": "user_preference_extraction_override",
        "consolidation": "user_preference_consolidation_override",
    },
    "episodic_override": {
        "extraction": "episodic_extraction_override",
        "consolidation": "episodic_consolidation_override",
        "reflection": "episodic_reflection_override",
    },
}

_CUSTOM_BLOCK_WRAPPERS = {
    "extraction": "custom_extraction_configuration",
    "consolidation": "custom_consolidation_configuration",
    "reflection": "custom_reflection_configuration",
}

_COMPARED_STRATEGY_FIELDS = ("description", "namespace_templates", "memory_record_schema")


@AWSRetry.jittered_backoff(retries=10)
def list_agent_runtimes(client) -> List[Dict[str, Any]]:
    """
    Retrieve all AgentCore runtime quick summaries using the AWS paginator.

    Args:
        client: The boto3 Bedrock Agent client.

    Returns:
        A list of agent runtimes quick (not detailed) summary dictionaries.
    """
    paginator = client.get_paginator("list_agent_runtimes")
    response = paginator.paginate().build_full_result()
    ignore_list = ("tags", "environmentVariables", "environment_variables")
    return [camel_dict_to_snake_dict(runtime, ignore_list=ignore_list) for runtime in response.get("agentRuntimes", [])]


def get_agent_runtime_quick_summary_by_name(client, agent_runtime_name: str) -> Optional[Dict[str, Any]]:
    """
    Get an AgentCore runtime's quick summary by its name.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_name: The name of the AgentCore runtime.

    Returns:
        The quick summary dictionary of the AgentCore runtime if found, else None.
    """
    for runtime in list_agent_runtimes(client):
        if runtime.get("agent_runtime_name") == agent_runtime_name:
            return runtime
    return None


def get_agent_runtime_by_name(client, agent_runtime_name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore runtime by its name.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_name: The name of the AgentCore runtime.

    Returns:
        The detailed dictionary of the AgentCore runtime if found, else None.
    """
    runtime_quick_summary: Optional[Dict[str, Any]] = get_agent_runtime_quick_summary_by_name(
        client, agent_runtime_name
    )
    existing_runtime: Optional[Dict[str, Any]] = None
    if runtime_quick_summary:
        existing_runtime = get_agent_runtime_by_id(client, runtime_quick_summary["agent_runtime_id"])
    return existing_runtime


def modify_runtime_response(response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Modify the response from Boto3's get_agent_runtime to exclude deprecated fields.
    If these fields are left in and sent back they may cause errors.

    Args:
        response: The original response dictionary from get_agent_runtime.

    Returns:
        The modified response dictionary with deprecated fields removed.
    """
    if "networkConfiguration" in response and "networkModeConfig" in response["networkConfiguration"]:
        response["networkConfiguration"]["networkModeConfig"].pop("requireServiceS3Endpoint", None)
    return response


@AWSRetry.jittered_backoff(retries=10)
def get_agent_runtime_by_id(client, agent_runtime_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore runtime by its ID.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_id: The ID of the AgentCore runtime.

    Returns:
        The detailed dictionary of the AgentCore runtime if found, else None.
    """
    try:
        response = client.get_agent_runtime(agentRuntimeId=agent_runtime_id)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    ignore_list = ("tags", "environmentVariables", "environment_variables")
    return camel_dict_to_snake_dict(modify_runtime_response(response), ignore_list=ignore_list)


@AWSRetry.jittered_backoff(retries=10)
def list_agent_runtime_endpoints(client, agent_runtime_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve all endpoints for an AgentCore runtime using the AWS paginator.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_id: The ID of the AgentCore runtime.

    Returns:
        A list of agent runtime endpoint dictionaries.
    """
    paginator = client.get_paginator("list_agent_runtime_endpoints")
    response = paginator.paginate(agentRuntimeId=agent_runtime_id).build_full_result()
    return [camel_dict_to_snake_dict(endpoint) for endpoint in response.get("runtimeEndpoints", [])]


@AWSRetry.jittered_backoff(retries=10)
def get_agent_runtime_endpoint(
    client,
    agent_runtime_id: str,
    endpoint_name: str,
) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore runtime endpoint.

    Args:
        client: The boto3 Bedrock Agent client.
        agent_runtime_id: The ID of the AgentCore runtime.
        endpoint_name: The name of the endpoint.

    Returns:
        The detailed dictionary of the AgentCore runtime endpoint if found, else None.
    """
    try:
        response = client.get_agent_runtime_endpoint(
            agentRuntimeId=agent_runtime_id,
            endpointName=endpoint_name,
        )
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    return camel_dict_to_snake_dict(response)


@AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=["ThrottledException"])
def list_memories(client) -> List[Dict[str, Any]]:
    """
    Retrieve all AgentCore memory summaries using the AWS paginator.

    Args:
        client: The boto3 Bedrock AgentCore control client.

    Returns:
        A list of raw (camelCase) memory summary dictionaries. Summaries carry no ``name``.
    """
    paginator = client.get_paginator("list_memories")
    response = paginator.paginate().build_full_result()
    return response.get("memories", [])


@AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=["ThrottledException"])
def get_memory(client, memory_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore memory by its ID.

    Args:
        client: The boto3 Bedrock AgentCore control client.
        memory_id: The ID of the memory.

    Returns:
        The raw (camelCase) memory dictionary if found, else None.
    """
    try:
        response = client.get_memory(memoryId=memory_id)
    except is_boto3_error_code("ResourceNotFoundException"):
        return None
    return response["memory"]


def find_memory_by_name(client, name: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information for an AgentCore memory by its name.

    ``list_memories`` does not return names, so only summaries whose ID follows the
    ``<name>-<10 characters>`` convention are fetched, and the name is confirmed on the full record.

    Args:
        client: The boto3 Bedrock AgentCore control client.
        name: The name of the memory.

    Returns:
        The raw (camelCase) memory dictionary if found, else None.
    """
    prefix = f"{name}-"
    for summary in list_memories(client):
        memory_id = summary.get("id", "")
        if not memory_id.startswith(prefix) or len(memory_id) != len(prefix) + 10:
            continue
        memory = get_memory(client, memory_id)
        if memory and memory.get("name") == name:
            return memory
    return None


@AWSRetry.jittered_backoff(retries=10, catch_extra_error_codes=["ThrottlingException"])
def list_tags(client, resource_arn: str) -> Dict[str, str]:
    """
    Retrieve the tags of an AgentCore resource.

    Args:
        client: The boto3 Bedrock AgentCore control client.
        resource_arn: The ARN of the AgentCore resource.

    Returns:
        The tags as a raw key/value map, without case conversion.
    """
    return client.list_tags_for_resource(resourceArn=resource_arn).get("tags", {})


def _update_tags(module: AnsibleAWSModule, client, resource_arn: str) -> bool:
    """
    Reconcile the tags of any taggable AgentCore resource in place, honouring ``purge_tags``.

    Reads the desired tags from the ``tags`` and ``purge_tags`` module options; does nothing when
    ``tags`` is not set, and makes no API writes in check mode.

    Args:
        module: The AnsibleAWSModule instance.
        client: The boto3 Bedrock AgentCore control client.
        resource_arn: The ARN of the AgentCore resource.

    Returns:
        True if tags were (or would be, in check mode) changed.
    """
    if module.params.get("tags") is None:
        return False
    current_tags = list_tags(client, resource_arn)
    tags_to_add, tags_to_remove = compare_aws_tags(
        current_tags,
        module.params["tags"],
        module.params.get("purge_tags", True),
    )
    if module.check_mode:
        return bool(tags_to_add or tags_to_remove)
    if tags_to_remove:
        client.untag_resource(resourceArn=resource_arn, tagKeys=tags_to_remove)
    if tags_to_add:
        client.tag_resource(resourceArn=resource_arn, tags=tags_to_add)
    return bool(tags_to_add or tags_to_remove)


def _runtime_artifact(module: AnsibleAWSModule, existing_runtime: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generates agent runtime artifact dictionary based on the module inputs and existing runtime.

    Args:
        module: The AnsibleAWSModule instance.
        existing_runtime: The existing runtime configuration, if any.

    Returns:
        The agent runtime artifact dictionary.
    """
    artifact = dict()
    if module.params.get("container_configuration") is not None:
        artifact["container_configuration"] = module.params["container_configuration"]
    elif module.params.get("code_configuration") is not None:
        artifact["code_configuration"] = module.params["code_configuration"]
    elif existing_runtime:
        artifact = existing_runtime.get("agent_runtime_artifact", dict())
    return artifact


def _runtime_storage(
    module: AnsibleAWSModule,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generates storage configuration for an AgentCore runtime based on the module inputs and existing runtime.

    Args:
        module: The AnsibleAWSModule instance.
        params: The parameters dictionary for the AgentCore runtime.

    Returns:
        An updated params dictionary with storage configuration for the AgentCore runtime.
    """
    if module.params.get("capacity_provider_arn"):
        params["capacity_provider_configuration"] = dict(capacity_provider_arn=module.params["capacity_provider_arn"])
    if module.params.get("session_storage"):
        params["filesystem_configurations"] = [dict(session_storage=module.params["session_storage"])]
    elif module.params.get("s3_files_access_point"):
        params["filesystem_configurations"] = [dict(s3_files_access_point=module.params["s3_files_access_point"])]
    elif module.params.get("efs_access_point"):
        params["filesystem_configurations"] = [dict(efs_access_point=module.params["efs_access_point"])]
    elif module.params.get("capacity_provider_volume"):
        params["filesystem_configurations"] = [dict(capacity_provider_volume=module.params["capacity_provider_volume"])]
    return params


def _runtime_case_sensitive_parameters(
    module: AnsibleAWSModule,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Adjusts parameters for an AgentCore runtime to account for case sensitivity content.

    Args:
        module: The AnsibleAWSModule instance.
        params: The parameters dictionary for the AgentCore runtime.
    Returns:
        An updated params dictionary with added case-sensitive parameters.
    """
    if module.params.get("tags"):
        params["tags"] = module.params.get("tags")
    if module.params.get("description") is not None:
        params["description"] = module.params["description"]
    if module.params.get("environment_variables"):
        params["environmentVariables"] = module.params["environment_variables"]

    if module.params.get("authorizer_discovery_url"):
        params["authorizerConfiguration"] = dict(
            customJWTAuthorizer=dict(
                discoveryUrl=module.params["authorizer_discovery_url"],
                allowedAudience=module.params.get("authorizer_allowed_audience"),
                allowedClients=module.params.get("authorizer_allowed_clients"),
                allowedScopes=module.params.get("authorizer_allowed_scopes"),
            )
        )
    return params


def _runtime_parameters(
    module: AnsibleAWSModule,
    existing_runtime: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Generates parameters for an AgentCore runtime based on the module inputs and existing runtime.

    Args:
        module: The AnsibleAWSModule instance.
        existing_runtime: The existing runtime configuration, if any.

    Returns:
        A dictionary of parameters for the AgentCore runtime.
    """
    params: Dict[str, Any] = dict(
        agent_runtime_artifact=_runtime_artifact(module, existing_runtime),
        role_arn=module.params.get("role_arn") or (existing_runtime or dict()).get("role_arn"),
    )
    network_mode = module.params.get("network_mode")
    if network_mode:
        params["network_configuration"] = dict(network_mode=network_mode)
        if network_mode == "VPC":
            params["network_configuration"]["network_mode_config"] = dict(
                security_groups=module.params.get("network_security_groups"),
                subnets=module.params.get("network_subnets"),
            )

    if module.params.get("protocol"):
        params["protocol_configuration"] = dict(server_protocol=module.params["protocol"])
    lifecycle_configuration = scrub_none_parameters(
        dict(
            idle_runtime_session_timeout=module.params.get("idle_runtime_session_timeout"),
            max_lifetime=module.params.get("max_lifetime"),
        )
    )
    if lifecycle_configuration:
        params["lifecycle_configuration"] = lifecycle_configuration

    params = _runtime_storage(module, params)
    params = snake_dict_to_camel_dict(scrub_none_parameters(params))
    params = _runtime_case_sensitive_parameters(module, params)
    return scrub_none_parameters(params)


def _runtime_update_needed(module: AnsibleAWSModule, existing_runtime: Dict[str, Any]) -> bool:
    """
    Determines if an update to the agent runtime is needed based on the desired and existing configurations.

    Args:
        module: The AnsibleAWSModule instance.
        existing_runtime: The existing runtime configuration.

    Returns:
        True if an update is needed, False otherwise.
    """
    desired: Dict[str, Any] = _runtime_parameters(module, existing_runtime)
    current = dict(
        agentRuntimeArtifact=existing_runtime.get("agent_runtime_artifact"),
        roleArn=existing_runtime.get("role_arn"),
        networkConfiguration=existing_runtime.get("network_configuration"),
        description=existing_runtime.get("description"),
        protocolConfiguration=existing_runtime.get("protocol_configuration"),
        lifecycleConfiguration=existing_runtime.get("lifecycle_configuration"),
        environmentVariables=existing_runtime.get("environment_variables"),
        authorizerConfiguration=existing_runtime.get("authorizer_configuration"),
        capacityProviderConfiguration=existing_runtime.get("capacity_provider_configuration"),
        filesystemConfigurations=existing_runtime.get("filesystem_configurations"),
    )
    desired_values: Dict[str, Any] = {
        key: value for key, value in desired.items() if key in current and value is not None
    }
    ignore_list = ("tags", "environmentVariables", "environment_variables")
    return any(
        camel_dict_to_snake_dict({key: value}, ignore_list=ignore_list)
        != camel_dict_to_snake_dict({key: current[key]}, ignore_list=ignore_list)
        for key, value in desired_values.items()
    )


def wait_for_agent_runtime_status(
    client,
    module: AnsibleAWSModule,
    agent_runtime_id: str,
    status: AgentRuntimeStatus,
    sleep_time: int = 5,
) -> None:
    """
    Wait for an Amazon Bedrock Agent Runtime to reach a specific status.

    This function polls the Bedrock Agent Runtime at fixed intervals until it either
    reaches the desired `status` or the configured timeout expires.

    Behavior:
        - Uses `client.get_agent_runtime()` to retrieve the agent runtime's current status.
        - Waits `sleep_time` seconds between each polling attempt.
        - Stops early if the agent runtime reaches the desired status or is deleted
          while waiting for the AgentRuntimeStatus.DELETING state.
        - Fails the Ansible module gracefully if the timeout expires.

    Args:
        client: A boto3 Bedrock Agent client instance.
        module: The current Ansible module object, used for error reporting
                and accessing parameters (specifically `wait_timeout`).
        agent_runtime_id (str): The unique identifier of the Bedrock Agent runtime to monitor.
        status (AgentRuntimeStatus): The target agent status to wait for
                      (e.g., AgentRuntimeStatus.READY, AgentRuntimeStatus.DELETING).
        sleep_time (int, optional): Number of seconds to sleep between polling
                                    attempts. Defaults to 5 seconds.

    Raises:
        ClientError: If AWS returns an unexpected error during polling.
        TimeoutError: If the agent runtime does not reach the target status before
                      the timeout expires.
    """
    wait_timeout = module.params.get("wait_timeout", 600)
    max_attempts = max(1, wait_timeout // sleep_time)
    current_status = None

    for attempt in range(max_attempts):
        runtime = get_agent_runtime_by_id(client, agent_runtime_id)
        if runtime is None:
            if status == AgentRuntimeStatus.DELETED:
                return
            module.fail_json(msg=f"Agent runtime {agent_runtime_id} was not found while waiting for status '{status}'.")

        current_status = runtime.get("status")
        if current_status == status:
            return
        if current_status in {AgentRuntimeStatus.CREATE_FAILED, AgentRuntimeStatus.UPDATE_FAILED}:
            module.fail_json(
                msg=f"Agent runtime {agent_runtime_id} failed with status '{current_status}': "
                f"{runtime.get('failure_reason', 'Unknown failure reason')}."
            )
        if attempt < max_attempts - 1:
            time.sleep(sleep_time)

    module.fail_json(
        msg=f"Timeout waiting for agent runtime {agent_runtime_id} to reach status '{status}'. "
        f"Last known status: '{current_status}'."
    )


def create_agent_runtime(module: AnsibleAWSModule, client) -> Tuple[bool, Optional[str], str]:
    """
    Creates a new agent runtime if not in check_mode, otherwise simulates creation.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.

    Returns:
        (changed, agent_runtime_id, message)
    """
    name: str = module.params["agent_runtime_name"]
    if module.check_mode:
        return True, None, f"Check mode: would have created agent runtime {name}."

    params: Dict[str, Any] = _runtime_parameters(module)
    params["agentRuntimeName"] = name
    response = client.create_agent_runtime(**params)
    agent_runtime_id = response.get("agentRuntimeId")
    # User has an option to wait for the runtime to be ready, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_status(client, module, agent_runtime_id, AgentRuntimeStatus.READY)
    return True, agent_runtime_id, f"Agent runtime {name} created successfully."


def update_agent_runtime(
    module: AnsibleAWSModule,
    client,
    existing_runtime: Dict[str, Any],
) -> Tuple[bool, Optional[str], str]:
    """
    Updates an existing agent runtime if not in check_mode, otherwise simulates the update.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        existing_runtime: The existing runtime configuration.

    Returns:
        (changed, agent_runtime_id, message)
    """
    agent_runtime_id = existing_runtime["agent_runtime_id"]
    if not _runtime_update_needed(module, existing_runtime):
        return False, agent_runtime_id, "No updates needed."
    if module.check_mode:
        return (
            True,
            agent_runtime_id,
            f"Check mode: would have updated agent runtime {existing_runtime['agent_runtime_name']}.",
        )

    params = _runtime_parameters(module, existing_runtime)
    params["agentRuntimeId"] = agent_runtime_id
    response = client.update_agent_runtime(**params)
    updated_id = response.get("agentRuntimeId", agent_runtime_id)
    # User has an option to wait for the runtime to be ready, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_status(client, module, updated_id, AgentRuntimeStatus.READY)
    return True, updated_id, f"Agent runtime {existing_runtime['agent_runtime_name']} updated successfully."


def delete_agent_runtime(module: AnsibleAWSModule, client, existing_runtime: Dict[str, Any]) -> Tuple[bool, str]:
    name = existing_runtime["agent_runtime_name"]
    if module.check_mode:
        return True, f"Check mode: would have deleted agent runtime '{name}'."

    params = {"agentRuntimeId": existing_runtime["agent_runtime_id"]}
    if module.params.get("agent_runtime_version") is not None:
        params["agentRuntimeVersion"] = module.params["agent_runtime_version"]
    client.delete_agent_runtime(**params)

    # User has an option to wait for the runtime to be deleted, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_status(client, module, existing_runtime["agent_runtime_id"], AgentRuntimeStatus.DELETED)
    return True, f"Agent runtime {name} deleted successfully."


def wait_for_agent_runtime_endpoint_status(
    client,
    module: AnsibleAWSModule,
    agent_runtime_id: str,
    endpoint_name: str,
    status: str,
    sleep_time: int = 5,
    fail_on_failed_status: bool = True,
) -> None:
    """
    Wait for an Amazon Bedrock Agent Runtime Endpoint to reach a specific status.

    This function polls the Bedrock Agent Runtime Endpoint at fixed intervals until it either
    reaches the desired `status` or the configured timeout expires.

    Behavior:
        - Uses `client.get_agent_runtime_endpoint()` to retrieve the agent runtime endpoint's current status.
        - Waits `sleep_time` seconds between each polling attempt.
        - Stops early if the agent runtime reaches the desired status or is deleted
          while waiting for the "DELETED" state.
        - Fails the Ansible module gracefully if the timeout expires.

    Args:
        client: A boto3 Bedrock Agent client instance.
        module: The current Ansible module object, used for error reporting
                and accessing parameters (specifically `wait_timeout`).
        agent_runtime_id (str): The unique identifier of the Bedrock Agent runtime that owns the endpoint to monitor.
        endpoint_name (str): The name of the agent runtime endpoint to monitor.
        status (str): The target agent status to wait for
                      (e.g., "PREPARED", "DELETED").
        sleep_time (int, optional): Number of seconds to sleep between polling
                                    attempts. Defaults to 5 seconds.
        fail_on_failed_status (bool, optional): When True (default), a CREATE_FAILED or
                                    UPDATE_FAILED status fails the module. When False, such
                                    a terminal failed status is treated as "settled" and the
                                    function returns so the caller can act on it (for example,
                                    delete a failed endpoint). Defaults to True.

    Raises:
        ClientError: If AWS returns an unexpected error during polling.
        TimeoutError: If the agent runtime endpoint does not reach the target status before
                      the timeout expires.
    """
    wait_timeout = module.params.get("wait_timeout", 600)
    max_attempts = max(1, wait_timeout // sleep_time)
    current_status = None

    for attempt in range(max_attempts):
        endpoint = get_agent_runtime_endpoint(client, agent_runtime_id, endpoint_name)
        if endpoint is None:
            if status == AgentRuntimeEndpointStatus.DELETED:
                return
            module.fail_json(
                msg=f"Agent runtime endpoint {endpoint_name} was not found while waiting for status '{status}'."
            )

        current_status = endpoint.get("status")
        if current_status == status:
            return
        if current_status in {AgentRuntimeEndpointStatus.CREATE_FAILED, AgentRuntimeEndpointStatus.UPDATE_FAILED}:
            if fail_on_failed_status:
                module.fail_json(
                    msg=f"Agent runtime endpoint {endpoint_name} failed with status '{current_status}': "
                    f"{endpoint.get('failure_reason', 'Unknown failure reason')}."
                )
            # Terminal failed state reached; let the caller decide what to do next
            # (e.g. delete a CREATE_FAILED/UPDATE_FAILED endpoint for state=absent).
            return
        if attempt < max_attempts - 1:
            time.sleep(sleep_time)

    module.fail_json(
        msg=f"Timeout waiting for agent runtime endpoint {endpoint_name} to reach status '{status}'. "
        f"Last known status: '{current_status}'."
    )


def _runtime_endpoint_case_sensitive_parameters(module: AnsibleAWSModule, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Adjusts parameters for an AgentCore runtime endpoint to account for case sensitivity content.

    Args:
        module: The AnsibleAWSModule instance.
        params: The parameters dictionary for the AgentCore runtime endpoint.
    Returns:
        An updated params dictionary with added case-sensitive parameters.
    """
    if module.params.get("tags"):
        params["tags"] = module.params.get("tags")
    return params


# A freshly deleted endpoint name may not be immediately reusable: AWS can still
# report the old resource until its deletion fully propagates, returning
# ConflictException on an immediate re-create (e.g. state=present against an endpoint
# that was mid-DELETING when the task started). Retry on ConflictException so the
# re-create succeeds once the name is released.
@AWSRetry.jittered_backoff(retries=5, delay=3, catch_extra_error_codes=["ConflictException"])
def _create_agent_runtime_endpoint_api(client, **params) -> Dict[str, Any]:
    return client.create_agent_runtime_endpoint(**params)


def create_agent_runtime_endpoint(
    module: AnsibleAWSModule,
    client,
    agent_runtime_id: str,
) -> Tuple[bool, Optional[str], str]:
    """
    Creates a new agent runtime endpoint if not in check_mode, otherwise simulates creation.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        agent_runtime_id: The ID of the agent runtime for which to create the endpoint.

    Returns:
        (changed, endpoint_name, message)
    """
    endpoint_name = module.params["endpoint_name"]
    if module.check_mode:
        return True, None, f"Check mode: would have created agent runtime endpoint {endpoint_name}."

    params: Dict[str, Any] = dict(
        agent_runtime_id=agent_runtime_id,
        name=endpoint_name,
        agent_runtime_version=module.params.get("agent_runtime_version"),
        description=module.params.get("description"),
    )
    params = snake_dict_to_camel_dict(scrub_none_parameters(params))
    params = _runtime_endpoint_case_sensitive_parameters(module, params)
    response = _create_agent_runtime_endpoint_api(client, **params)

    endpoint_name_resp: str = response.get("name", endpoint_name)
    # User has an option to wait for the endpoint to be ready, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_endpoint_status(
            client, module, agent_runtime_id, endpoint_name_resp, AgentRuntimeEndpointStatus.READY
        )
    return True, endpoint_name_resp, f"Agent runtime endpoint {endpoint_name} created successfully."


def update_agent_runtime_endpoint(
    module: AnsibleAWSModule,
    client,
    agent_runtime_id: str,
    existing_endpoint: Dict[str, Any],
) -> Tuple[bool, Optional[str], str]:
    """
    Updates an existing agent runtime endpoint if not in check_mode, otherwise simulates the update.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        agent_runtime_id: The ID of the agent runtime for which to update the endpoint.
        existing_endpoint: The current state of the agent runtime endpoint.

    Returns:
        (changed, endpoint_name, message)
    """
    endpoint_name: str = existing_endpoint["name"]
    if module.check_mode:
        return True, endpoint_name, f"Check mode: would have updated agent runtime endpoint {endpoint_name}."

    desired: Dict[str, Any] = dict(
        agent_runtime_version=module.params.get("agent_runtime_version"),
        description=module.params.get("description"),
    )
    current: Dict[str, Any] = dict(
        agent_runtime_version=existing_endpoint.get("target_version", existing_endpoint.get("live_version")),
        description=existing_endpoint.get("description"),
    )
    if not any(value is not None and value != current[key] for key, value in desired.items()):
        return False, endpoint_name, "No updates needed."

    params: Dict[str, Any] = dict(
        agent_runtime_id=agent_runtime_id,
        endpoint_name=endpoint_name,
        **desired,
    )
    response = client.update_agent_runtime_endpoint(**snake_dict_to_camel_dict(scrub_none_parameters(params)))
    updated_name: str = response.get("name", endpoint_name)
    # User has an option to wait for the endpoint to be ready, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_endpoint_status(
            client, module, agent_runtime_id, updated_name, AgentRuntimeEndpointStatus.READY
        )
    return True, updated_name, f"Agent runtime endpoint {endpoint_name} updated successfully."


def delete_agent_runtime_endpoint(
    module: AnsibleAWSModule,
    client,
    agent_runtime_id: str,
    existing_endpoint: Dict[str, Any],
) -> Tuple[bool, str]:
    """
    Deletes an existing agent runtime endpoint if not in check_mode, otherwise simulates the deletion.

    Args:
        module: The AnsibleAWSModule instance.
        client: boto3 bedrock-agent client.
        agent_runtime_id: The ID of the agent runtime for which to delete the endpoint.
        existing_endpoint: The current state of the agent runtime endpoint.

    Returns:
        (changed, message)
    """
    endpoint_name: str = existing_endpoint["name"]
    if module.check_mode:
        return True, f"Check mode: would have deleted agent runtime endpoint '{endpoint_name}'."

    client.delete_agent_runtime_endpoint(agentRuntimeId=agent_runtime_id, endpointName=endpoint_name)
    # User has an option to wait for the endpoint to be deleted, default is True
    if module.params.get("wait", True):
        wait_for_agent_runtime_endpoint_status(
            client,
            module,
            agent_runtime_id,
            endpoint_name,
            AgentRuntimeEndpointStatus.DELETED,
        )
    return True, f"Agent runtime endpoint {endpoint_name} deleted successfully."


def strategy_configuration_to_modify_shape(strategy_key: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
    """
    Translate a declared memory strategy's configuration from the create shape into the shape
    ``update_memory`` accepts in ``modifyMemoryStrategies[].configuration`` (and ``get_memory``
    reports in ``strategies[].configuration``), in snake_case.

    Args:
        strategy_key: The declared strategy key, e.g. ``custom_memory_strategy``.
        strategy: The strategy body declared under that key.

    Returns:
        The configuration in modify shape; ``{}`` when the strategy carries none.
    """
    strategy = scrub_none_parameters(strategy)

    if strategy_key == "episodic_memory_strategy":
        reflection_configuration = strategy.get("reflection_configuration")
        if not reflection_configuration:
            return {}
        return {"reflection": {"episodic_reflection_configuration": reflection_configuration}}

    if strategy_key != "custom_memory_strategy":
        return {}

    configuration = strategy.get("configuration") or {}
    modify_shape = {}
    for override_key, blocks in _OVERRIDE_BLOCKS.items():
        override = configuration.get(override_key) or {}
        for block, leaf in blocks.items():
            if override.get(block):
                modify_shape[block] = {_CUSTOM_BLOCK_WRAPPERS[block]: {leaf: override[block]}}
    if configuration.get("self_managed_configuration"):
        modify_shape["self_managed_configuration"] = configuration["self_managed_configuration"]
    return modify_shape


def _declared_strategy(element: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Return the single (strategy key, strategy body) pair a declared strategy element sets."""
    declared = [(key, value) for key, value in element.items() if key in MEMORY_STRATEGY_TYPES and value is not None]
    if len(declared) != 1:
        raise ValueError(f"Each memory strategy must set exactly one of: {', '.join(MEMORY_STRATEGY_TYPES)}.")
    return declared[0]


def _strategy_changes(strategy_key: str, strategy: Dict[str, Any], current: Dict[str, Any]) -> Dict[str, Any]:
    """Return the supplied strategy fields that differ from ``current``, in modify shape."""
    changes = {}
    for field in _COMPARED_STRATEGY_FIELDS:
        if field in strategy and not is_subset(strategy[field], current.get(field)):
            changes[field] = strategy[field]

    record_expiry = strategy.get("record_expiry_specification") or {}
    if "record_expiry_duration_days" in record_expiry:
        if record_expiry["record_expiry_duration_days"] != current.get("record_expiry_duration_days"):
            changes["record_expiry_specification"] = record_expiry

    configuration = strategy_configuration_to_modify_shape(strategy_key, strategy)
    if configuration:
        current_configuration = {k: v for k, v in (current.get("configuration") or {}).items() if k != "type"}
        if not is_subset(configuration, current_configuration):
            changes["configuration"] = configuration

    return changes


def diff_memory_strategies(
    current: List[Dict[str, Any]], desired: List[Dict[str, Any]]
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Diff a memory's existing strategies against the complete desired set, matching them by name.

    Only fields the user supplied are compared, so AWS-filled defaults never cause a diff.

    Args:
        current: The snake_cased ``strategies`` of a ``get_memory`` response.
        desired: The declared ``memory_strategies`` elements (create shape).

    Returns:
        ``(strategies_to_add, strategies_to_modify, strategies_to_delete)`` in snake_case: create-shape
        elements, modify-shape entries carrying ``memory_strategy_id``, and
        ``{"memory_strategy_id": ...}`` entries.

    Raises:
        ValueError: On a strategy changing type, or a strategy name appearing twice in either list.
    """
    desired_by_name = {}
    for element in desired:
        element = scrub_none_parameters(element)
        strategy_key, strategy = _declared_strategy(element)
        if strategy["name"] in desired_by_name:
            raise ValueError(f"Memory strategy name {strategy['name']} is declared more than once.")
        desired_by_name[strategy["name"]] = (strategy_key, strategy, element)

    current_by_name = {}
    for strategy in current:
        if strategy["name"] in current_by_name:
            raise ValueError(f"Memory strategy name {strategy['name']} appears more than once on the memory.")
        current_by_name[strategy["name"]] = strategy

    strategies_to_add = []
    strategies_to_modify = []
    for name, (strategy_key, strategy, element) in desired_by_name.items():
        existing = current_by_name.get(name)
        if existing is None:
            strategies_to_add.append(element)
            continue
        desired_type = MEMORY_STRATEGY_TYPES[strategy_key]
        if existing.get("type") != desired_type:
            raise ValueError(
                f"Memory strategy {name} cannot change type from {existing.get('type')} to {desired_type}; "
                "remove it and add it under a new name."
            )
        changes = _strategy_changes(strategy_key, strategy, existing)
        if changes:
            strategies_to_modify.append({"memory_strategy_id": existing["strategy_id"], **changes})

    strategies_to_delete = [
        {"memory_strategy_id": strategy["strategy_id"]}
        for name, strategy in current_by_name.items()
        if name not in desired_by_name
    ]

    return strategies_to_add, strategies_to_modify, strategies_to_delete


def wait_for_memory_status(
    client,
    module: AnsibleAWSModule,
    memory_id: str,
    status: MemoryStatus,
    sleep_time: int = 5,
) -> None:
    """
    Wait for an AgentCore memory to reach a specific status.

    Polls ``get_memory`` every ``sleep_time`` seconds, bounded by the ``wait_timeout`` option.

    Behavior:
        - ``MemoryStatus.ACTIVE``: succeeds once the memory and every one of its strategies are
          ``ACTIVE``; fails as soon as the memory or any strategy is ``FAILED``, or if the memory
          disappears.
        - ``MemoryStatus.DELETED``: succeeds once the memory is no longer found; fails if it turns
          ``FAILED``.
        - Any other target: succeeds once the memory reports that status.
        - Fails the module when the timeout expires.

    Args:
        client: The boto3 Bedrock AgentCore control client.
        module: The AnsibleAWSModule instance, used for error reporting and ``wait_timeout``.
        memory_id: The ID of the memory to monitor.
        status: The target status, e.g. ``MemoryStatus.ACTIVE`` or ``MemoryStatus.DELETED``.
        sleep_time: Seconds to sleep between polling attempts. Defaults to 5.
    """
    target = MemoryStatus(status).value
    wait_timeout = module.params.get("wait_timeout", 600)
    max_attempts = max(1, wait_timeout // sleep_time)
    name = memory_id

    for attempt in range(max_attempts):
        memory = get_memory(client, memory_id)
        if memory is None:
            if target == MemoryStatus.DELETED:
                return
            module.fail_json(msg=f"Memory {name} was not found while waiting for it to reach {target}.")

        name = memory.get("name", memory_id)
        current_status = memory.get("status")
        if current_status == MemoryStatus.FAILED:
            module.fail_json(
                msg=f"Memory {name} failed: {memory.get('failureReason', 'Unknown failure reason')}.",
                failure_reason=memory.get("failureReason"),
            )

        if target == MemoryStatus.ACTIVE:
            strategies = memory.get("strategies") or []
            failed_strategies = [s.get("name") for s in strategies if s.get("status") == MemoryStatus.FAILED]
            if failed_strategies:
                module.fail_json(msg=f"Memory {name} has failed strategies: {', '.join(failed_strategies)}.")
            if current_status == MemoryStatus.ACTIVE and all(
                s.get("status") == MemoryStatus.ACTIVE for s in strategies
            ):
                return
        elif current_status == target:
            return

        if attempt < max_attempts - 1:
            time.sleep(sleep_time)

    module.fail_json(msg=f"Timed out waiting for memory {name} to reach {target}.")


def create_memory(module: AnsibleAWSModule, client) -> Tuple[bool, Optional[str], str]:
    """
    Creates a new memory if not in check_mode, otherwise simulates creation.

    Args:
        module: The AnsibleAWSModule instance.
        client: The boto3 Bedrock AgentCore control client.

    Returns:
        (changed, memory_id, message)
    """
    name: str = module.params["name"]
    if module.params.get("event_expiry_duration") is None:
        module.fail_json(msg="event_expiry_duration is required to create a memory.")
    if module.check_mode:
        return True, None, f"Check mode: would have created memory {name}."

    params: Dict[str, Any] = dict(
        name=name,
        description=module.params.get("description"),
        event_expiry_duration=module.params["event_expiry_duration"],
        encryption_key_arn=module.params.get("encryption_key_arn"),
        memory_execution_role_arn=module.params.get("memory_execution_role_arn"),
        memory_strategies=module.params.get("memory_strategies"),
        indexed_keys=module.params.get("indexed_keys"),
        namespace_keys=module.params.get("namespace_keys"),
        stream_delivery_resources=module.params.get("stream_delivery_resources"),
    )
    params = snake_dict_to_camel_dict(scrub_none_parameters(params))
    if module.params.get("tags"):
        params["tags"] = module.params["tags"]

    response = client.create_memory(**params)
    memory_id: str = response["memory"]["id"]
    # User has an option to wait for the memory to be active, default is True
    if module.params.get("wait", True):
        wait_for_memory_status(client, module, memory_id, MemoryStatus.ACTIVE)
    return True, memory_id, f"Created memory {name}."


def _memory_update_params(module: AnsibleAWSModule, existing: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build the ``update_memory`` kwargs for every supplied option that differs from the memory.

    Fails the module on a change AWS cannot make in place (``encryption_key_arn``, removing or
    retyping an indexed key, a strategy changing type) and on a strategy change to a memory
    managed by another resource.

    Args:
        module: The AnsibleAWSModule instance.
        existing: The raw (camelCase) ``get_memory`` result.

    Returns:
        The snake_case kwargs to send, without ``memory_id``; an empty dict when nothing differs.
    """
    current = camel_dict_to_snake_dict(existing, ignore_list=["tags", "Tags"])
    name = current["name"]
    params: Dict[str, Any] = dict()

    encryption_key_arn = module.params.get("encryption_key_arn")
    if encryption_key_arn is not None and encryption_key_arn != current.get("encryption_key_arn"):
        module.fail_json(msg="encryption_key_arn cannot be changed on an existing memory; delete and recreate it.")

    for option in ("description", "event_expiry_duration", "memory_execution_role_arn"):
        value = module.params.get(option)
        if value is not None and value != current.get(option):
            params[option] = value

    indexed_keys = module.params.get("indexed_keys")
    if indexed_keys is not None:
        desired_types = {entry["key"]: entry["type"] for entry in indexed_keys}
        current_types = {entry["key"]: entry.get("type") for entry in current.get("indexed_keys") or []}
        keys_to_reject = sorted(key for key, key_type in current_types.items() if desired_types.get(key) != key_type)
        if keys_to_reject:
            module.fail_json(
                msg=f"Indexed keys cannot be removed or changed once declared: {', '.join(keys_to_reject)}."
            )
        keys_to_add = [scrub_none_parameters(entry) for entry in indexed_keys if entry["key"] not in current_types]
        if keys_to_add:
            params["add_indexed_keys"] = keys_to_add

    namespace_keys = module.params.get("namespace_keys")
    if namespace_keys is not None:
        desired_keys = {entry["key"]: scrub_none_parameters(entry) for entry in namespace_keys}
        current_keys = {entry["key"]: entry for entry in current.get("namespace_keys") or []}
        if desired_keys.keys() != current_keys.keys() or not all(
            is_subset(entry, current_keys[key]) for key, entry in desired_keys.items()
        ):
            params["namespace_keys"] = list(desired_keys.values())

    stream_delivery_resources = module.params.get("stream_delivery_resources")
    if stream_delivery_resources is not None:
        desired_delivery = scrub_none_parameters(stream_delivery_resources)
        current_delivery = current.get("stream_delivery_resources") or dict(resources=[])
        if not is_subset(desired_delivery, current_delivery):
            params["stream_delivery_resources"] = desired_delivery

    memory_strategies = module.params.get("memory_strategies")
    if memory_strategies is not None:
        try:
            strategies_to_add, strategies_to_modify, strategies_to_delete = diff_memory_strategies(
                current.get("strategies") or [], memory_strategies
            )
        except ValueError as e:
            module.fail_json(msg=str(e))
        strategy_changes = scrub_none_parameters(
            dict(
                add_memory_strategies=strategies_to_add or None,
                modify_memory_strategies=strategies_to_modify or None,
                delete_memory_strategies=strategies_to_delete or None,
            )
        )
        if strategy_changes:
            if current.get("managed_by_resource_arn"):
                module.fail_json(
                    msg=f"Memory {name} is managed by {current['managed_by_resource_arn']}; "
                    "change it through that resource."
                )
            params["memory_strategies"] = strategy_changes

    return params


def update_memory(module: AnsibleAWSModule, client, existing: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Updates an existing memory and its tags if not in check_mode, otherwise simulates the update.

    Args:
        module: The AnsibleAWSModule instance.
        client: The boto3 Bedrock AgentCore control client.
        existing: The raw (camelCase) ``get_memory`` result.

    Returns:
        (changed, message)
    """
    name: str = existing["name"]
    params = _memory_update_params(module, existing)

    if module.check_mode:
        if params or _update_tags(module, client, existing["arn"]):
            return True, f"Check mode: would have updated memory {name}."
        return False, f"Memory {name} is already in the desired state."

    if params:
        client.update_memory(memoryId=existing["id"], **snake_dict_to_camel_dict(params))
    tags_changed = _update_tags(module, client, existing["arn"])
    if not params and not tags_changed:
        return False, f"Memory {name} is already in the desired state."

    # User has an option to wait for the memory to be active, default is True
    if params and module.params.get("wait", True):
        wait_for_memory_status(client, module, existing["id"], MemoryStatus.ACTIVE)
    return True, f"Updated memory {name}."


def delete_memory(module: AnsibleAWSModule, client, existing: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Deletes an existing memory if not in check_mode, otherwise simulates the deletion.

    Args:
        module: The AnsibleAWSModule instance.
        client: The boto3 Bedrock AgentCore control client.
        existing: The raw (camelCase) ``get_memory`` result.

    Returns:
        (changed, message)
    """
    name: str = existing["name"]
    managed_by = existing.get("managedByResourceArn")
    if managed_by:
        module.fail_json(msg=f"Memory {name} is managed by {managed_by}; change it through that resource.")
    if module.check_mode:
        return True, f"Check mode: would have deleted memory {name}."

    client.delete_memory(memoryId=existing["id"])
    # User has an option to wait for the memory to be deleted, default is True
    if module.params.get("wait", True):
        wait_for_memory_status(client, module, existing["id"], MemoryStatus.DELETED)
    return True, f"Deleted memory {name}."
