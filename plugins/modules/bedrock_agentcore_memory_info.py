#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agentcore_memory_info
short_description: Gather information about Amazon Bedrock AgentCore memories
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Gets the details of one Amazon Bedrock AgentCore memory, looked up by name or ID, or of every memory in the region.
    - A memory that does not exist is not an error; the result is an empty list.
requirements:
    - python >= 3.9
    - boto3 >= 1.39.7
    - botocore >= 1.39.7
options:
    name:
        description:
            - The exact name of the memory to retrieve.
            - When neither O(name) nor O(memory_id) is set, every memory in the region is returned.
        type: str
    memory_id:
        description:
            - The ID of the memory to retrieve.
        type: str
notes:
    - The IAM actions are bedrock-agentcore:GetMemory and bedrock-agentcore:ListMemories.
    - Tags are not returned. Use M(amazon.ai.bedrock_agentcore_memory) with O(amazon.ai.bedrock_agentcore_memory#module:tags)
      to read them.
attributes:
    check_mode:
        description: Can run in check mode and return the same information without changing the target.
        support: full
seealso:
    - module: amazon.ai.bedrock_agentcore_memory
      description: Use the resource module to create, update and delete AgentCore memories.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
"""

EXAMPLES = r"""
- name: Get a memory by name
  amazon.ai.bedrock_agentcore_memory_info:
    name: "my_memory"

- name: Get a memory by ID
  amazon.ai.bedrock_agentcore_memory_info:
    memory_id: "my_memory-a1b2c3d4e5"

- name: List every memory in the region
  amazon.ai.bedrock_agentcore_memory_info:
"""

RETURN = r"""
msg:
    description: A message describing the outcome.
    returned: always
    type: str
    sample: "Found 1 memory."
memories:
    description:
        - The memories, as returned by AWS.
        - Empty when no memory matches.
    type: list
    elements: dict
    returned: always
    contains:
        arn:
            description:
                - The ARN of the memory.
            type: str
            returned: always
            sample: "arn:aws:bedrock-agentcore:us-east-1:123456789012:memory/my_memory-a1b2c3d4e5"
        id:
            description:
                - The ID of the memory.
            type: str
            returned: always
            sample: "my_memory-a1b2c3d4e5"
        name:
            description:
                - The name of the memory.
            type: str
            returned: always
            sample: "my_memory"
        description:
            description:
                - The description of the memory.
            type: str
            returned: when set
            sample: "Memory for my agent"
        encryption_key_arn:
            description:
                - The ARN of the AWS KMS key that encrypts the memory.
            type: str
            returned: when set
            sample: "arn:aws:kms:us-east-1:123456789012:key/1234abcd-12ab-34cd-56ef-1234567890ab"
        memory_execution_role_arn:
            description:
                - The ARN of the IAM role the service assumes on behalf of the memory.
            type: str
            returned: when set
            sample: "arn:aws:iam::123456789012:role/my-memory-role"
        event_expiry_duration:
            description:
                - The number of days after which memory events expire.
            type: int
            returned: always
            sample: 30
        status:
            description:
                - The status of the memory, one of V(CREATING), V(ACTIVE), V(FAILED), V(DELETING) or V(UPDATING).
            type: str
            returned: always
            sample: "ACTIVE"
        failure_reason:
            description:
                - Why the memory failed.
            type: str
            returned: when set
            sample: "Access denied to the KMS key."
        created_at:
            description:
                - When the memory was created.
            type: str
            returned: always
            sample: "2026-11-02T10:42:45.123000+00:00"
        updated_at:
            description:
                - When the memory was last updated.
            type: str
            returned: always
            sample: "2026-11-02T10:42:45.123000+00:00"
        strategies:
            description:
                - The memory strategies of the memory.
            type: list
            elements: dict
            returned: when set
            contains:
                strategy_id:
                    description:
                        - The ID of the strategy.
                    type: str
                    returned: always
                    sample: "semantic_facts-a1b2c3d4e5"
                name:
                    description:
                        - The name of the strategy.
                    type: str
                    returned: always
                    sample: "semantic_facts"
                description:
                    description:
                        - The description of the strategy.
                    type: str
                    returned: when set
                    sample: "Extracts facts"
                type:
                    description:
                        - The type of the strategy, one of V(SEMANTIC), V(SUMMARIZATION), V(USER_PREFERENCE), V(CUSTOM)
                          or V(EPISODIC).
                    type: str
                    returned: always
                    sample: "SEMANTIC"
                status:
                    description:
                        - The status of the strategy, one of V(CREATING), V(ACTIVE), V(DELETING) or V(FAILED).
                    type: str
                    returned: when set
                    sample: "ACTIVE"
                namespaces:
                    description:
                        - "The namespaces of the strategy. Deprecated by AWS in favour of
                          RV(memories[].strategies[].namespace_templates)."
                    type: list
                    elements: str
                    returned: when set
                    sample: ["/strategies/{memoryStrategyId}/actors/{actorId}"]
                namespace_templates:
                    description:
                        - The namespace templates under which memory records are stored.
                    type: list
                    elements: str
                    returned: when set
                    sample: ["/strategies/{memoryStrategyId}/actors/{actorId}"]
                memory_record_schema:
                    description:
                        - The schema of the metadata attached to memory records.
                    type: dict
                    returned: when set
                    contains:
                        metadata_schema:
                            description:
                                - The metadata fields of the memory records.
                            type: list
                            elements: dict
                            returned: when set
                            contains:
                                key:
                                    description:
                                        - The name of the metadata field.
                                    type: str
                                    returned: always
                                    sample: "topic"
                                type:
                                    description:
                                        - The type of the metadata value.
                                    type: str
                                    returned: when set
                                    sample: "STRING"
                                extraction_type:
                                    description:
                                        - How the metadata value is extracted.
                                    type: str
                                    returned: when set
                                    sample: "LLM_INFERRED"
                                extraction_config:
                                    description:
                                        - How a model extracts the metadata value.
                                        - Holds C(llm_extraction_config) with C(definition),
                                          C(llm_extraction_instruction) and C(validation).
                                    type: dict
                                    returned: when set
                record_expiry_duration_days:
                    description:
                        - The number of days after which memory records extracted by the strategy expire.
                    type: int
                    returned: when set
                    sample: 90
                configuration:
                    description:
                        - The override or self-managed configuration of a custom or episodic strategy.
                    type: dict
                    returned: when set
                    contains:
                        type:
                            description:
                                - The type of override, one of V(SEMANTIC_OVERRIDE), V(SUMMARY_OVERRIDE),
                                  V(USER_PREFERENCE_OVERRIDE), V(SELF_MANAGED) or V(EPISODIC_OVERRIDE).
                            type: str
                            returned: when set
                            sample: "SEMANTIC_OVERRIDE"
                        extraction:
                            description:
                                - The extraction override.
                            type: dict
                            returned: when set
                            contains:
                                custom_extraction_configuration:
                                    description:
                                        - The custom extraction configuration, holding one override.
                                    type: dict
                                    returned: always
                                    contains:
                                        semantic_extraction_override:
                                            description:
                                                - The semantic extraction override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                                        user_preference_extraction_override:
                                            description:
                                                - The user preference extraction override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                                        episodic_extraction_override:
                                            description:
                                                - The episodic extraction override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                        consolidation:
                            description:
                                - The consolidation override.
                            type: dict
                            returned: when set
                            contains:
                                custom_consolidation_configuration:
                                    description:
                                        - The custom consolidation configuration, holding one override.
                                    type: dict
                                    returned: always
                                    contains:
                                        semantic_consolidation_override:
                                            description:
                                                - The semantic consolidation override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                                        summary_consolidation_override:
                                            description:
                                                - The summary consolidation override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                                        user_preference_consolidation_override:
                                            description:
                                                - The user preference consolidation override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                                        episodic_consolidation_override:
                                            description:
                                                - The episodic consolidation override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                        reflection:
                            description:
                                - The reflection configuration of an episodic strategy.
                            type: dict
                            returned: when set
                            contains:
                                custom_reflection_configuration:
                                    description:
                                        - The custom reflection configuration of an episodic override.
                                    type: dict
                                    returned: when set
                                    contains:
                                        episodic_reflection_override:
                                            description:
                                                - The episodic reflection override.
                                            type: dict
                                            returned: when set
                                            contains:
                                                append_to_prompt:
                                                    description:
                                                        - Instructions appended to the built-in prompt of the step.
                                                    type: str
                                                    returned: always
                                                    sample: "Focus on facts."
                                                model_id:
                                                    description:
                                                        - The ID of the model that runs the step.
                                                    type: str
                                                    returned: always
                                                    sample: "anthropic.claude-3-haiku-20240307-v1:0"
                                                namespaces:
                                                    description:
                                                        - "The namespaces of the strategy. Deprecated by AWS in favour
                                                          of RV(memories[].strategies[].namespace_templates)."
                                                    type: list
                                                    elements: str
                                                    returned: when set
                                                    sample: ["/strategies/{memoryStrategyId}/actors/{actorId}"]
                                                namespace_templates:
                                                    description:
                                                        - The namespace templates under which memory records are stored.
                                                    type: list
                                                    elements: str
                                                    returned: when set
                                                    sample: ["/strategies/{memoryStrategyId}/actors/{actorId}"]
                                                memory_record_schema:
                                                    description:
                                                        - The schema of the metadata attached to memory records.
                                                    type: dict
                                                    returned: when set
                                                    contains:
                                                        metadata_schema:
                                                            description:
                                                                - The metadata fields of the memory records.
                                                            type: list
                                                            elements: dict
                                                            returned: when set
                                                            contains:
                                                                key:
                                                                    description:
                                                                        - The name of the metadata field.
                                                                    type: str
                                                                    returned: always
                                                                    sample: "topic"
                                                                type:
                                                                    description:
                                                                        - The type of the metadata value.
                                                                    type: str
                                                                    returned: when set
                                                                    sample: "STRING"
                                                                extraction_type:
                                                                    description:
                                                                        - How the metadata value is extracted.
                                                                    type: str
                                                                    returned: when set
                                                                    sample: "LLM_INFERRED"
                                                                extraction_config:
                                                                    description:
                                                                        - How a model extracts the metadata value.
                                                                        - Holds C(llm_extraction_config) with
                                                                          C(definition), C(llm_extraction_instruction)
                                                                          and C(validation).
                                                                    type: dict
                                                                    returned: when set
                                episodic_reflection_configuration:
                                    description:
                                        - The reflection configuration of a built-in episodic strategy.
                                    type: dict
                                    returned: when set
                                    contains:
                                        namespaces:
                                            description:
                                                - "The namespaces of the strategy. Deprecated by AWS in favour of
                                                  RV(memories[].strategies[].namespace_templates)."
                                            type: list
                                            elements: str
                                            returned: when set
                                            sample: ["/strategies/{memoryStrategyId}/actors/{actorId}"]
                                        namespace_templates:
                                            description:
                                                - The namespace templates under which memory records are stored.
                                            type: list
                                            elements: str
                                            returned: when set
                                            sample: ["/strategies/{memoryStrategyId}/actors/{actorId}"]
                                        memory_record_schema:
                                            description:
                                                - The schema of the metadata attached to memory records.
                                            type: dict
                                            returned: when set
                                            contains:
                                                metadata_schema:
                                                    description:
                                                        - The metadata fields of the memory records.
                                                    type: list
                                                    elements: dict
                                                    returned: when set
                                                    contains:
                                                        key:
                                                            description:
                                                                - The name of the metadata field.
                                                            type: str
                                                            returned: always
                                                            sample: "topic"
                                                        type:
                                                            description:
                                                                - The type of the metadata value.
                                                            type: str
                                                            returned: when set
                                                            sample: "STRING"
                                                        extraction_type:
                                                            description:
                                                                - How the metadata value is extracted.
                                                            type: str
                                                            returned: when set
                                                            sample: "LLM_INFERRED"
                                                        extraction_config:
                                                            description:
                                                                - How a model extracts the metadata value.
                                                                - Holds C(llm_extraction_config) with C(definition),
                                                                  C(llm_extraction_instruction) and C(validation).
                                                            type: dict
                                                            returned: when set
                        self_managed_configuration:
                            description:
                                - The self-managed configuration.
                            type: dict
                            returned: when set
                            contains:
                                trigger_conditions:
                                    description:
                                        - The conditions that trigger the pipeline.
                                    type: list
                                    elements: dict
                                    returned: always
                                    contains:
                                        message_based_trigger:
                                            description:
                                                - Triggers after a number of messages.
                                            type: dict
                                            returned: when set
                                            contains:
                                                message_count:
                                                    description:
                                                        - The number of messages.
                                                    type: int
                                                    returned: when set
                                                    sample: 10
                                        token_based_trigger:
                                            description:
                                                - Triggers after a number of tokens.
                                            type: dict
                                            returned: when set
                                            contains:
                                                token_count:
                                                    description:
                                                        - The number of tokens.
                                                    type: int
                                                    returned: when set
                                                    sample: 1000
                                        time_based_trigger:
                                            description:
                                                - Triggers after a session has been idle for some time.
                                            type: dict
                                            returned: when set
                                            contains:
                                                idle_session_timeout:
                                                    description:
                                                        - The idle time in seconds.
                                                    type: int
                                                    returned: when set
                                                    sample: 60
                                invocation_configuration:
                                    description:
                                        - Where the service delivers the session payloads.
                                    type: dict
                                    returned: always
                                    contains:
                                        topic_arn:
                                            description:
                                                - The ARN of the Amazon SNS topic.
                                            type: str
                                            returned: always
                                            sample: "arn:aws:sns:us-east-1:123456789012:my-topic"
                                        payload_delivery_bucket_name:
                                            description:
                                                - The name of the Amazon S3 bucket.
                                            type: str
                                            returned: always
                                            sample: "my-payload-bucket"
                                historical_context_window_size:
                                    description:
                                        - The number of previous messages sent as context.
                                    type: int
                                    returned: always
                                    sample: 4
                created_at:
                    description:
                        - When the strategy was created.
                    type: str
                    returned: when set
                    sample: "2026-11-02T10:42:45.123000+00:00"
                updated_at:
                    description:
                        - When the strategy was last updated.
                    type: str
                    returned: when set
                    sample: "2026-11-02T10:42:45.123000+00:00"
        indexed_keys:
            description:
                - The indexed metadata keys of the memory records.
            type: list
            elements: dict
            returned: when set
            contains:
                key:
                    description:
                        - The name of the metadata key.
                    type: str
                    returned: always
                    sample: "topic"
                type:
                    description:
                        - The type of the metadata value.
                    type: str
                    returned: always
                    sample: "STRING"
        namespace_keys:
            description:
                - The variables namespace templates can use.
            type: list
            elements: dict
            returned: when set
            contains:
                key:
                    description:
                        - The name of the variable.
                    type: str
                    returned: always
                    sample: "tenant"
                validation:
                    description:
                        - Restricts the values the variable accepts.
                    type: dict
                    returned: when set
                    contains:
                        allowed_values:
                            description:
                                - The values the variable accepts.
                            type: list
                            elements: str
                            returned: when set
                            sample: ["acme"]
                        regex_pattern:
                            description:
                                - A regular expression the value must match.
                            type: str
                            returned: when set
                            sample: "^[a-z]+$"
        stream_delivery_resources:
            description:
                - Where memory records are streamed.
            type: dict
            returned: when set
            contains:
                resources:
                    description:
                        - The delivery targets.
                    type: list
                    elements: dict
                    returned: always
                    contains:
                        kinesis:
                            description:
                                - An Amazon Kinesis data stream target.
                            type: dict
                            returned: when set
                            contains:
                                data_stream_arn:
                                    description:
                                        - The ARN of the Kinesis data stream.
                                    type: str
                                    returned: always
                                    sample: "arn:aws:kinesis:us-east-1:123456789012:stream/my-stream"
                                content_configurations:
                                    description:
                                        - What is streamed.
                                    type: list
                                    elements: dict
                                    returned: always
                                    contains:
                                        type:
                                            description:
                                                - The type of content streamed.
                                            type: str
                                            returned: always
                                            sample: "MEMORY_RECORDS"
                                        level:
                                            description:
                                                - How much of each memory record is streamed.
                                            type: str
                                            returned: when set
                                            sample: "FULL_CONTENT"
        managed_by_resource_arn:
            description:
                - The ARN of the resource that manages the memory, when another resource manages it.
            type: str
            returned: when set
            sample: "arn:aws:bedrock-agentcore:us-east-1:123456789012:runtime/my_runtime-a1b2c3d4e5"
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import AGENTCORE_MINIMUM_BOTOCORE_VERSION
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import find_memory_by_name
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_memory
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import list_memories
from ansible_collections.amazon.ai.plugins.module_utils.botocore import validate_botocore_version

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry


def _find_memories(client, name: Optional[str], memory_id: Optional[str]) -> List[Dict[str, Any]]:
    """Return the raw memories matching the lookup, or every memory when neither name nor ID is given."""
    if memory_id:
        memory = get_memory(client, memory_id)
        return [memory] if memory else []
    if name:
        memory = find_memory_by_name(client, name)
        return [memory] if memory else []

    memories = list()
    for summary in list_memories(client):
        memory = get_memory(client, summary["id"])
        if memory:
            memories.append(memory)
    return memories


def main() -> None:
    argument_spec = dict(
        name=dict(type="str"),
        memory_id=dict(type="str"),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        mutually_exclusive=[["name", "memory_id"]],
        supports_check_mode=True,
    )
    validate_botocore_version(
        module,
        AGENTCORE_MINIMUM_BOTOCORE_VERSION,
        f"Bedrock AgentCore requires botocore >= {AGENTCORE_MINIMUM_BOTOCORE_VERSION} "
        "to support the service model features used by this module.",
    )

    memories: List[Dict[str, Any]] = list()

    try:
        try:
            client = module.client("bedrock-agentcore-control", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        memories = _find_memories(client, module.params.get("name"), module.params.get("memory_id"))
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    noun = "memory" if len(memories) == 1 else "memories"
    module.exit_json(
        changed=False,
        msg=f"Found {len(memories)} {noun}.",
        memories=[camel_dict_to_snake_dict(memory, ignore_list=["tags", "Tags"]) for memory in memories],
    )


if __name__ == "__main__":
    main()
