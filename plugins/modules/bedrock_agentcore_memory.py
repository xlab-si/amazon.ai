#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: bedrock_agentcore_memory
short_description: Manage Amazon Bedrock AgentCore memories
version_added: "2.0.0"
author:
    - Domen Dobnikar (@domendobnikar)
description:
    - Creates, updates, and deletes Amazon Bedrock AgentCore memories.
    - Manages the memory settings, its memory strategies, indexed keys, namespace keys, stream delivery and tags.
    - Memory strategies are declared as the complete desired set. Strategies are added, modified and deleted to
      match it.
requirements:
    - python >= 3.9
    - boto3 >= 1.39.7
    - botocore >= 1.39.7
options:
    state:
        description:
            - Whether the memory should exist or not.
        type: str
        default: "present"
        choices: ["present", "absent"]
    name:
        description:
            - The name of the memory.
            - Unique within the account and region, so it identifies the memory. A different name manages a different
              memory.
            - Must start with a letter and contain only letters, digits and underscores, up to 48 characters.
        type: str
        required: true
    description:
        description:
            - A description of the memory.
            - Updatable in place.
        type: str
    event_expiry_duration:
        description:
            - The number of days, between V(3) and V(365), after which memory events expire.
            - Required when the memory is created.
            - Updatable in place.
        type: int
    encryption_key_arn:
        description:
            - The ARN of the AWS KMS customer managed key that encrypts the memory.
            - Create-only. The module fails when it differs from the key of an existing memory.
        type: str
    memory_execution_role_arn:
        description:
            - The ARN of the IAM role the service assumes on behalf of the memory, for example to invoke models.
            - AWS requires it for strategies with an override configuration and for O(stream_delivery_resources).
            - Updatable in place.
        type: str
    memory_strategies:
        description:
            - The complete list of memory strategies of the memory.
            - "Each element sets exactly one of O(memory_strategies[].semantic_memory_strategy),
              O(memory_strategies[].summary_memory_strategy), O(memory_strategies[].user_preference_memory_strategy),
              O(memory_strategies[].episodic_memory_strategy) and O(memory_strategies[].custom_memory_strategy)."
            - Strategies are matched to existing ones by name. Listed strategies that do not exist are added, existing
              strategies that are not listed are deleted, and listed strategies that differ are modified.
            - Only the fields that are set are compared. An omitted field is left unchanged.
            - The type of a strategy cannot be changed. The module fails when an existing strategy name is declared
              under a different strategy key.
            - "When omitted, the strategies are left unchanged. Set to V([]) to delete every strategy."
            - AWS allows at most 6 strategies per memory.
        type: list
        elements: dict
        suboptions:
            semantic_memory_strategy:
                description:
                    - A built-in strategy that extracts facts and knowledge.
                type: dict
                suboptions:
                    name:
                        description:
                            - The name of the strategy.
                            - Identifies the strategy within the memory, so a declared strategy is matched to an
                              existing one by this name.
                            - Must start with a letter and contain only letters, digits and underscores, up to 48
                              characters.
                        type: str
                        required: true
                    description:
                        description:
                            - A description of the strategy.
                        type: str
                    namespace_templates:
                        description:
                            - "The namespace template under which memory records are stored, for example
                              V(/strategies/{memoryStrategyId}/actors/{actorId})."
                            - AWS accepts exactly one template.
                            - When omitted at creation, AWS assigns a default namespace.
                            - Requires botocore >= 1.42.70.
                        type: list
                        elements: str
                    memory_record_schema:
                        description:
                            - The schema of the metadata attached to memory records.
                            - Requires botocore >= 1.43.1.
                        type: dict
                        suboptions:
                            metadata_schema:
                                description:
                                    - The metadata fields of the memory records.
                                    - AWS accepts between 1 and 20 fields.
                                type: list
                                elements: dict
                                suboptions:
                                    key:
                                        description:
                                            - The name of the metadata field.
                                        type: str
                                        required: true
                                    type:
                                        description:
                                            - The type of the metadata value.
                                        type: str
                                        choices: ["STRING", "STRINGLIST", "NUMBER"]
                                    extraction_type:
                                        description:
                                            - How the metadata value is extracted.
                                            - Requires botocore >= 1.43.28.
                                        type: str
                                        choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                    extraction_config:
                                        description:
                                            - How a model extracts the metadata value.
                                            - Takes a C(llm_extraction_config) dictionary with C(definition),
                                              C(llm_extraction_instruction) and C(validation).
                                            - C(validation) takes one of C(string_validation), C(string_list_validation)
                                              or C(number_validation).
                                            - Keys are written in snake_case and passed to AWS without further
                                              validation.
                                        type: dict
                    record_expiry_specification:
                        description:
                            - When the memory records extracted by the strategy expire.
                            - Requires botocore >= 1.43.112.
                        type: dict
                        suboptions:
                            record_expiry_duration_days:
                                description:
                                    - The number of days, at least V(31), after which memory records expire.
                                type: int
                                required: true
            summary_memory_strategy:
                description:
                    - A built-in strategy that summarizes sessions.
                type: dict
                suboptions:
                    name:
                        description:
                            - The name of the strategy.
                            - Identifies the strategy within the memory, so a declared strategy is matched to an
                              existing one by this name.
                            - Must start with a letter and contain only letters, digits and underscores, up to 48
                              characters.
                        type: str
                        required: true
                    description:
                        description:
                            - A description of the strategy.
                        type: str
                    namespace_templates:
                        description:
                            - "The namespace template under which memory records are stored, for example
                              V(/strategies/{memoryStrategyId}/actors/{actorId})."
                            - AWS accepts exactly one template.
                            - When omitted at creation, AWS assigns a default namespace.
                            - Requires botocore >= 1.42.70.
                        type: list
                        elements: str
                    memory_record_schema:
                        description:
                            - The schema of the metadata attached to memory records.
                            - Requires botocore >= 1.43.1.
                        type: dict
                        suboptions:
                            metadata_schema:
                                description:
                                    - The metadata fields of the memory records.
                                    - AWS accepts between 1 and 20 fields.
                                type: list
                                elements: dict
                                suboptions:
                                    key:
                                        description:
                                            - The name of the metadata field.
                                        type: str
                                        required: true
                                    type:
                                        description:
                                            - The type of the metadata value.
                                        type: str
                                        choices: ["STRING", "STRINGLIST", "NUMBER"]
                                    extraction_type:
                                        description:
                                            - How the metadata value is extracted.
                                            - Requires botocore >= 1.43.28.
                                        type: str
                                        choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                    extraction_config:
                                        description:
                                            - How a model extracts the metadata value.
                                            - Takes a C(llm_extraction_config) dictionary with C(definition),
                                              C(llm_extraction_instruction) and C(validation).
                                            - C(validation) takes one of C(string_validation), C(string_list_validation)
                                              or C(number_validation).
                                            - Keys are written in snake_case and passed to AWS without further
                                              validation.
                                        type: dict
                    record_expiry_specification:
                        description:
                            - When the memory records extracted by the strategy expire.
                            - Requires botocore >= 1.43.112.
                        type: dict
                        suboptions:
                            record_expiry_duration_days:
                                description:
                                    - The number of days, at least V(31), after which memory records expire.
                                type: int
                                required: true
            user_preference_memory_strategy:
                description:
                    - A built-in strategy that extracts user preferences.
                type: dict
                suboptions:
                    name:
                        description:
                            - The name of the strategy.
                            - Identifies the strategy within the memory, so a declared strategy is matched to an
                              existing one by this name.
                            - Must start with a letter and contain only letters, digits and underscores, up to 48
                              characters.
                        type: str
                        required: true
                    description:
                        description:
                            - A description of the strategy.
                        type: str
                    namespace_templates:
                        description:
                            - "The namespace template under which memory records are stored, for example
                              V(/strategies/{memoryStrategyId}/actors/{actorId})."
                            - AWS accepts exactly one template.
                            - When omitted at creation, AWS assigns a default namespace.
                            - Requires botocore >= 1.42.70.
                        type: list
                        elements: str
                    memory_record_schema:
                        description:
                            - The schema of the metadata attached to memory records.
                            - Requires botocore >= 1.43.1.
                        type: dict
                        suboptions:
                            metadata_schema:
                                description:
                                    - The metadata fields of the memory records.
                                    - AWS accepts between 1 and 20 fields.
                                type: list
                                elements: dict
                                suboptions:
                                    key:
                                        description:
                                            - The name of the metadata field.
                                        type: str
                                        required: true
                                    type:
                                        description:
                                            - The type of the metadata value.
                                        type: str
                                        choices: ["STRING", "STRINGLIST", "NUMBER"]
                                    extraction_type:
                                        description:
                                            - How the metadata value is extracted.
                                            - Requires botocore >= 1.43.28.
                                        type: str
                                        choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                    extraction_config:
                                        description:
                                            - How a model extracts the metadata value.
                                            - Takes a C(llm_extraction_config) dictionary with C(definition),
                                              C(llm_extraction_instruction) and C(validation).
                                            - C(validation) takes one of C(string_validation), C(string_list_validation)
                                              or C(number_validation).
                                            - Keys are written in snake_case and passed to AWS without further
                                              validation.
                                        type: dict
                    record_expiry_specification:
                        description:
                            - When the memory records extracted by the strategy expire.
                            - Requires botocore >= 1.43.112.
                        type: dict
                        suboptions:
                            record_expiry_duration_days:
                                description:
                                    - The number of days, at least V(31), after which memory records expire.
                                type: int
                                required: true
            episodic_memory_strategy:
                description:
                    - A built-in strategy that extracts episodes and reflects on them.
                    - Requires botocore >= 1.42.1.
                type: dict
                suboptions:
                    name:
                        description:
                            - The name of the strategy.
                            - Identifies the strategy within the memory, so a declared strategy is matched to an
                              existing one by this name.
                            - Must start with a letter and contain only letters, digits and underscores, up to 48
                              characters.
                        type: str
                        required: true
                    description:
                        description:
                            - A description of the strategy.
                        type: str
                    namespace_templates:
                        description:
                            - "The namespace template under which memory records are stored, for example
                              V(/strategies/{memoryStrategyId}/actors/{actorId})."
                            - AWS accepts exactly one template.
                            - When omitted at creation, AWS assigns a default namespace.
                            - Requires botocore >= 1.42.70.
                        type: list
                        elements: str
                    memory_record_schema:
                        description:
                            - The schema of the metadata attached to memory records.
                            - Requires botocore >= 1.43.1.
                        type: dict
                        suboptions:
                            metadata_schema:
                                description:
                                    - The metadata fields of the memory records.
                                    - AWS accepts between 1 and 20 fields.
                                type: list
                                elements: dict
                                suboptions:
                                    key:
                                        description:
                                            - The name of the metadata field.
                                        type: str
                                        required: true
                                    type:
                                        description:
                                            - The type of the metadata value.
                                        type: str
                                        choices: ["STRING", "STRINGLIST", "NUMBER"]
                                    extraction_type:
                                        description:
                                            - How the metadata value is extracted.
                                            - Requires botocore >= 1.43.28.
                                        type: str
                                        choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                    extraction_config:
                                        description:
                                            - How a model extracts the metadata value.
                                            - Takes a C(llm_extraction_config) dictionary with C(definition),
                                              C(llm_extraction_instruction) and C(validation).
                                            - C(validation) takes one of C(string_validation), C(string_list_validation)
                                              or C(number_validation).
                                            - Keys are written in snake_case and passed to AWS without further
                                              validation.
                                        type: dict
                    record_expiry_specification:
                        description:
                            - When the memory records extracted by the strategy expire.
                            - Requires botocore >= 1.43.112.
                        type: dict
                        suboptions:
                            record_expiry_duration_days:
                                description:
                                    - The number of days, at least V(31), after which memory records expire.
                                type: int
                                required: true
                    reflection_configuration:
                        description:
                            - Where and how the strategy stores reflections.
                        type: dict
                        suboptions:
                            namespace_templates:
                                description:
                                    - "The namespace template under which memory records are stored, for example
                                      V(/strategies/{memoryStrategyId}/actors/{actorId})."
                                    - AWS accepts exactly one template.
                                    - When omitted at creation, AWS assigns a default namespace.
                                    - Requires botocore >= 1.42.70.
                                type: list
                                elements: str
                            memory_record_schema:
                                description:
                                    - The schema of the metadata attached to memory records.
                                    - Requires botocore >= 1.43.1.
                                type: dict
                                suboptions:
                                    metadata_schema:
                                        description:
                                            - The metadata fields of the memory records.
                                            - AWS accepts between 1 and 20 fields.
                                        type: list
                                        elements: dict
                                        suboptions:
                                            key:
                                                description:
                                                    - The name of the metadata field.
                                                type: str
                                                required: true
                                            type:
                                                description:
                                                    - The type of the metadata value.
                                                type: str
                                                choices: ["STRING", "STRINGLIST", "NUMBER"]
                                            extraction_type:
                                                description:
                                                    - How the metadata value is extracted.
                                                    - Requires botocore >= 1.43.28.
                                                type: str
                                                choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                            extraction_config:
                                                description:
                                                    - How a model extracts the metadata value.
                                                    - Takes a C(llm_extraction_config) dictionary with C(definition),
                                                      C(llm_extraction_instruction) and C(validation).
                                                    - C(validation) takes one of C(string_validation),
                                                      C(string_list_validation) or C(number_validation).
                                                    - Keys are written in snake_case and passed to AWS without further
                                                      validation.
                                                type: dict
            custom_memory_strategy:
                description:
                    - A strategy that overrides a built-in strategy or hands extraction to your own pipeline.
                type: dict
                suboptions:
                    name:
                        description:
                            - The name of the strategy.
                            - Identifies the strategy within the memory, so a declared strategy is matched to an
                              existing one by this name.
                            - Must start with a letter and contain only letters, digits and underscores, up to 48
                              characters.
                        type: str
                        required: true
                    description:
                        description:
                            - A description of the strategy.
                        type: str
                    namespace_templates:
                        description:
                            - "The namespace template under which memory records are stored, for example
                              V(/strategies/{memoryStrategyId}/actors/{actorId})."
                            - AWS accepts exactly one template.
                            - When omitted at creation, AWS assigns a default namespace.
                            - Requires botocore >= 1.42.70.
                        type: list
                        elements: str
                    memory_record_schema:
                        description:
                            - The schema of the metadata attached to memory records.
                            - Requires botocore >= 1.43.1.
                        type: dict
                        suboptions:
                            metadata_schema:
                                description:
                                    - The metadata fields of the memory records.
                                    - AWS accepts between 1 and 20 fields.
                                type: list
                                elements: dict
                                suboptions:
                                    key:
                                        description:
                                            - The name of the metadata field.
                                        type: str
                                        required: true
                                    type:
                                        description:
                                            - The type of the metadata value.
                                        type: str
                                        choices: ["STRING", "STRINGLIST", "NUMBER"]
                                    extraction_type:
                                        description:
                                            - How the metadata value is extracted.
                                            - Requires botocore >= 1.43.28.
                                        type: str
                                        choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                    extraction_config:
                                        description:
                                            - How a model extracts the metadata value.
                                            - Takes a C(llm_extraction_config) dictionary with C(definition),
                                              C(llm_extraction_instruction) and C(validation).
                                            - C(validation) takes one of C(string_validation), C(string_list_validation)
                                              or C(number_validation).
                                            - Keys are written in snake_case and passed to AWS without further
                                              validation.
                                        type: dict
                    record_expiry_specification:
                        description:
                            - When the memory records extracted by the strategy expire.
                            - Requires botocore >= 1.43.112.
                        type: dict
                        suboptions:
                            record_expiry_duration_days:
                                description:
                                    - The number of days, at least V(31), after which memory records expire.
                                type: int
                                required: true
                    configuration:
                        description:
                            - The configuration of the custom strategy.
                            - "Sets exactly one of
                              O(memory_strategies[].custom_memory_strategy.configuration.semantic_override),
                              O(memory_strategies[].custom_memory_strategy.configuration.summary_override),
                              O(memory_strategies[].custom_memory_strategy.configuration.user_preference_override),
                              O(memory_strategies[].custom_memory_strategy.configuration.episodic_override) and
                              O(memory_strategies[].custom_memory_strategy.configuration.self_managed_configuration)."
                        type: dict
                        suboptions:
                            semantic_override:
                                description:
                                    - Overrides the prompts and models of the semantic strategy.
                                type: dict
                                suboptions:
                                    extraction:
                                        description:
                                            - Overrides the extraction step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                                    consolidation:
                                        description:
                                            - Overrides the consolidation step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                            summary_override:
                                description:
                                    - Overrides the prompt and model of the summary strategy.
                                type: dict
                                suboptions:
                                    consolidation:
                                        description:
                                            - Overrides the consolidation step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                            user_preference_override:
                                description:
                                    - Overrides the prompts and models of the user preference strategy.
                                type: dict
                                suboptions:
                                    extraction:
                                        description:
                                            - Overrides the extraction step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                                    consolidation:
                                        description:
                                            - Overrides the consolidation step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                            episodic_override:
                                description:
                                    - Overrides the prompts and models of the episodic strategy.
                                    - Requires botocore >= 1.42.1.
                                type: dict
                                suboptions:
                                    extraction:
                                        description:
                                            - Overrides the extraction step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                                    consolidation:
                                        description:
                                            - Overrides the consolidation step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                                    reflection:
                                        description:
                                            - Overrides the reflection step.
                                        type: dict
                                        suboptions:
                                            append_to_prompt:
                                                description:
                                                    - Instructions appended to the built-in prompt of the step.
                                                type: str
                                                required: true
                                            model_id:
                                                description:
                                                    - The ID of the model that runs the step.
                                                type: str
                                                required: true
                                            namespace_templates:
                                                description:
                                                    - "The namespace template under which memory records are stored, for
                                                      example V(/strategies/{memoryStrategyId}/actors/{actorId})."
                                                    - AWS accepts exactly one template.
                                                    - When omitted at creation, AWS assigns a default namespace.
                                                    - Requires botocore >= 1.42.70.
                                                type: list
                                                elements: str
                                            memory_record_schema:
                                                description:
                                                    - The schema of the metadata attached to memory records.
                                                    - Requires botocore >= 1.43.1.
                                                type: dict
                                                suboptions:
                                                    metadata_schema:
                                                        description:
                                                            - The metadata fields of the memory records.
                                                            - AWS accepts between 1 and 20 fields.
                                                        type: list
                                                        elements: dict
                                                        suboptions:
                                                            key:
                                                                description:
                                                                    - The name of the metadata field.
                                                                type: str
                                                                required: true
                                                            type:
                                                                description:
                                                                    - The type of the metadata value.
                                                                type: str
                                                                choices: ["STRING", "STRINGLIST", "NUMBER"]
                                                            extraction_type:
                                                                description:
                                                                    - How the metadata value is extracted.
                                                                    - Requires botocore >= 1.43.28.
                                                                type: str
                                                                choices: ["LLM_INFERRED", "STRICTLY_CONSISTENT"]
                                                            extraction_config:
                                                                description:
                                                                    - How a model extracts the metadata value.
                                                                    - Takes a C(llm_extraction_config) dictionary with
                                                                      C(definition), C(llm_extraction_instruction) and
                                                                      C(validation).
                                                                    - C(validation) takes one of C(string_validation),
                                                                      C(string_list_validation) or C(number_validation).
                                                                    - Keys are written in snake_case and passed to AWS
                                                                      without further validation.
                                                                type: dict
                            self_managed_configuration:
                                description:
                                    - Hands memory record extraction to your own pipeline.
                                    - Requires botocore >= 1.40.50.
                                type: dict
                                suboptions:
                                    invocation_configuration:
                                        description:
                                            - Where the service delivers the session payloads for your pipeline.
                                        type: dict
                                        required: true
                                        suboptions:
                                            topic_arn:
                                                description:
                                                    - The ARN of the Amazon SNS topic notified when a payload is
                                                      delivered.
                                                type: str
                                                required: true
                                            payload_delivery_bucket_name:
                                                description:
                                                    - The name of the Amazon S3 bucket the payloads are written to.
                                                type: str
                                                required: true
                                    trigger_conditions:
                                        description:
                                            - The conditions that trigger your pipeline.
                                            - Each element sets exactly one of C(message_based_trigger),
                                              C(token_based_trigger) and C(time_based_trigger).
                                        type: list
                                        elements: dict
                                        suboptions:
                                            message_based_trigger:
                                                description:
                                                    - Triggers after a number of messages.
                                                type: dict
                                                suboptions:
                                                    message_count:
                                                        description:
                                                            - The number of messages, between V(1) and V(50).
                                                        type: int
                                            token_based_trigger:
                                                description:
                                                    - Triggers after a number of tokens.
                                                type: dict
                                                suboptions:
                                                    token_count:
                                                        description:
                                                            - The number of tokens, between V(100) and V(500000).
                                                        type: int
                                            time_based_trigger:
                                                description:
                                                    - Triggers after a session has been idle for some time.
                                                type: dict
                                                suboptions:
                                                    idle_session_timeout:
                                                        description:
                                                            - The idle time in seconds, between V(10) and V(3000).
                                                        type: int
                                    historical_context_window_size:
                                        description:
                                            - The number of previous messages, between V(0) and V(50), sent as context.
                                        type: int
    indexed_keys:
        description:
            - The metadata keys of memory records to index for filtering.
            - Keys can only be added. The module fails when a key of the memory is omitted or its type changed.
            - AWS accepts between 1 and 10 keys.
            - Requires botocore >= 1.43.1.
        type: list
        elements: dict
        suboptions:
            key:
                description:
                    - The name of the metadata key.
                type: str
                required: true
            type:
                description:
                    - The type of the metadata value.
                type: str
                required: true
                choices: ["STRING", "STRINGLIST", "NUMBER"]
    namespace_keys:
        description:
            - The variables that namespace templates can use, besides the built-in V(memoryStrategyId), V(actorId) and
              V(sessionId).
            - Replaces the existing set when it differs.
            - AWS accepts at most 5 keys.
            - Requires botocore >= 1.43.75.
        type: list
        elements: dict
        suboptions:
            key:
                description:
                    - The name of the variable.
                    - Must start with a lowercase letter and contain only lowercase letters and digits, up to 32
                      characters.
                type: str
                required: true
            validation:
                description:
                    - Restricts the values the variable accepts.
                type: dict
                suboptions:
                    allowed_values:
                        description:
                            - The values the variable accepts, between 1 and 10.
                        type: list
                        elements: str
                    regex_pattern:
                        description:
                            - A regular expression the value must match.
                        type: str
    stream_delivery_resources:
        description:
            - Streams memory records to Amazon Kinesis Data Streams.
            - AWS requires O(memory_execution_role_arn) for streaming.
            - "Replaces the existing configuration when it differs. Set O(stream_delivery_resources.resources) to V([])
              to stop streaming."
            - Requires botocore >= 1.42.63.
        type: dict
        suboptions:
            resources:
                description:
                    - The delivery targets.
                    - AWS accepts at most one target.
                type: list
                elements: dict
                required: true
                suboptions:
                    kinesis:
                        description:
                            - An Amazon Kinesis data stream target.
                        type: dict
                        required: true
                        suboptions:
                            data_stream_arn:
                                description:
                                    - The ARN of the Kinesis data stream.
                                type: str
                                required: true
                            content_configurations:
                                description:
                                    - What is streamed.
                                    - AWS accepts exactly one entry.
                                type: list
                                elements: dict
                                required: true
                                suboptions:
                                    type:
                                        description:
                                            - The type of content streamed.
                                        type: str
                                        required: true
                                        choices: ["MEMORY_RECORDS"]
                                    level:
                                        description:
                                            - How much of each memory record is streamed.
                                        type: str
                                        choices: ["METADATA_ONLY", "FULL_CONTENT"]
    tags:
        description:
            - A dictionary of tags to apply to the memory.
            - When omitted, the tags of the memory are left unchanged.
            - "To remove all tags set O(tags={}) and O(purge_tags=true)."
            - Requires botocore >= 1.40.46.
        type: dict
        aliases: ["resource_tags"]
    purge_tags:
        description:
            - Whether to remove tags of the memory that are not listed in O(tags).
            - Has no effect when O(tags) is omitted.
        type: bool
        default: true
    wait:
        description:
            - Whether to wait for the memory and its strategies to finish creating, updating or deleting.
        type: bool
        default: true
    wait_timeout:
        description:
            - How long, in seconds, to wait when O(wait=true).
        type: int
        default: 600
notes:
    - The IAM actions are bedrock-agentcore:CreateMemory, bedrock-agentcore:GetMemory, bedrock-agentcore:ListMemories,
      bedrock-agentcore:UpdateMemory, bedrock-agentcore:DeleteMemory, bedrock-agentcore:ListTagsForResource,
      bedrock-agentcore:TagResource and bedrock-agentcore:UntagResource.
    - iam:PassRole on the role may also be needed when O(memory_execution_role_arn) is set.
    - When O(encryption_key_arn) is set, the caller needs kms:CreateGrant, kms:Decrypt, kms:DescribeKey,
      kms:GenerateDataKey, kms:GenerateDataKeyWithoutPlaintext and kms:ReEncrypt* on the key, through the
      bedrock-agentcore service.
    - Some options need a later botocore release than the one in the requirements, as noted on each option. The module
      fails with the required version when such an option is set with O(state=present).
    - An omitted option leaves the matching setting of an existing memory unchanged, so a setting cannot be removed by
      omitting it.
    - A memory managed by another resource, reported in RV(memory.managed_by_resource_arn), can only have its strategies
      changed or be deleted through that resource. The module fails instead.
attributes:
    check_mode:
        description: Can run in check mode and report what would change without changing the target.
        support: full
seealso:
    - module: amazon.ai.bedrock_agentcore_memory_info
      description: Use the info module to retrieve one or all AgentCore memories.
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
"""

EXAMPLES = r"""
- name: Create a minimal memory
  amazon.ai.bedrock_agentcore_memory:
    name: "my_memory"
    event_expiry_duration: 30

- name: Create a memory with a semantic strategy and a custom override strategy
  amazon.ai.bedrock_agentcore_memory:
    name: "my_memory"
    description: "Memory for my agent"
    event_expiry_duration: 90
    memory_execution_role_arn: "arn:aws:iam::123456789012:role/my-memory-role"
    memory_strategies:
      - semantic_memory_strategy:
          name: "facts"
          description: "Extracts facts from conversations"
          namespace_templates:
            - "/strategies/{memoryStrategyId}/actors/{actorId}"
      - custom_memory_strategy:
          name: "product_facts"
          configuration:
            semantic_override:
              extraction:
                append_to_prompt: "Focus on facts about products the user owns."
                model_id: "anthropic.claude-3-haiku-20240307-v1:0"
              consolidation:
                append_to_prompt: "Merge facts about the same product."
                model_id: "anthropic.claude-3-haiku-20240307-v1:0"
    tags:
      environment: "dev"

- name: Stream memory records of an existing memory to a Kinesis data stream
  amazon.ai.bedrock_agentcore_memory:
    name: "my_memory"
    memory_execution_role_arn: "arn:aws:iam::123456789012:role/my-memory-role"
    stream_delivery_resources:
      resources:
        - kinesis:
            data_stream_arn: "arn:aws:kinesis:us-east-1:123456789012:stream/my-stream"
            content_configurations:
              - type: "MEMORY_RECORDS"
                level: "FULL_CONTENT"

- name: Stop streaming memory records
  amazon.ai.bedrock_agentcore_memory:
    name: "my_memory"
    stream_delivery_resources:
      resources: []

- name: Delete a memory
  amazon.ai.bedrock_agentcore_memory:
    name: "my_memory"
    state: absent
"""

RETURN = r"""
msg:
    description: A message describing the outcome.
    returned: always
    type: str
    sample: "Created memory my_memory."
memory:
    description:
        - The memory, as returned by AWS.
        - Empty when O(state=absent), and in check mode when the memory would be created.
    type: dict
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
                          RV(memory.strategies[].namespace_templates)."
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
                                                          of RV(memory.strategies[].namespace_templates)."
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
                                                  RV(memory.strategies[].namespace_templates)."
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
        tags:
            description:
                - The tags of the memory.
            type: dict
            returned: when O(tags) is set
            sample: {"environment": "dev"}
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import Optional

from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import AGENTCORE_MINIMUM_BOTOCORE_VERSION
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import MemoryStatus
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import create_memory
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import delete_memory
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import find_memory_by_name
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import get_memory
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import list_tags
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import update_memory
from ansible_collections.amazon.ai.plugins.module_utils.bedrock_agentcore import wait_for_memory_status
from ansible_collections.amazon.ai.plugins.module_utils.botocore import validate_botocore_option
from ansible_collections.amazon.ai.plugins.module_utils.botocore import validate_botocore_version

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry

# First botocore release whose bedrock-agentcore-control model accepts each top-level option.
_OPTION_BOTOCORE_VERSIONS = (
    ("tags", "1.40.46"),
    ("stream_delivery_resources", "1.42.63"),
    ("indexed_keys", "1.43.1"),
    ("namespace_keys", "1.43.75"),
)

# First botocore release that accepts each key, wherever it appears under memory_strategies.
_STRATEGY_KEY_BOTOCORE_VERSIONS = (
    ("self_managed_configuration", "1.40.50"),
    ("episodic_memory_strategy", "1.42.1"),
    ("episodic_override", "1.42.1"),
    ("namespace_templates", "1.42.70"),
    ("memory_record_schema", "1.43.1"),
    ("extraction_type", "1.43.28"),
    ("record_expiry_specification", "1.43.112"),
)

_STRATEGY_KEYS = [
    "semantic_memory_strategy",
    "summary_memory_strategy",
    "user_preference_memory_strategy",
    "episodic_memory_strategy",
    "custom_memory_strategy",
]

_CUSTOM_CONFIGURATION_KEYS = [
    "semantic_override",
    "summary_override",
    "user_preference_override",
    "episodic_override",
    "self_managed_configuration",
]

_TRIGGER_KEYS = ["message_based_trigger", "token_based_trigger", "time_based_trigger"]

_METADATA_VALUE_TYPES = ["STRING", "STRINGLIST", "NUMBER"]


def _namespace_templates_spec() -> Dict[str, Any]:
    return dict(type="list", elements="str")


def _memory_record_schema_spec() -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            metadata_schema=dict(
                type="list",
                elements="dict",
                options=dict(
                    key=dict(type="str", required=True, no_log=False),
                    type=dict(type="str", choices=_METADATA_VALUE_TYPES),
                    extraction_type=dict(type="str", choices=["LLM_INFERRED", "STRICTLY_CONSISTENT"]),
                    extraction_config=dict(type="dict"),
                ),
            ),
        ),
    )


def _override_block_spec(**extra_options) -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            append_to_prompt=dict(type="str", required=True),
            model_id=dict(type="str", required=True),
            **extra_options,
        ),
    )


def _strategy_spec(**extra_options) -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            name=dict(type="str", required=True),
            description=dict(type="str"),
            namespace_templates=_namespace_templates_spec(),
            memory_record_schema=_memory_record_schema_spec(),
            record_expiry_specification=dict(
                type="dict",
                options=dict(record_expiry_duration_days=dict(type="int", required=True)),
            ),
            **extra_options,
        ),
    )


def _self_managed_configuration_spec() -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            invocation_configuration=dict(
                type="dict",
                required=True,
                options=dict(
                    topic_arn=dict(type="str", required=True),
                    payload_delivery_bucket_name=dict(type="str", required=True),
                ),
            ),
            trigger_conditions=dict(
                type="list",
                elements="dict",
                options=dict(
                    message_based_trigger=dict(type="dict", options=dict(message_count=dict(type="int"))),
                    token_based_trigger=dict(
                        type="dict", no_log=False, options=dict(token_count=dict(type="int", no_log=False))
                    ),
                    time_based_trigger=dict(type="dict", options=dict(idle_session_timeout=dict(type="int"))),
                ),
                mutually_exclusive=[_TRIGGER_KEYS],
                required_one_of=[_TRIGGER_KEYS],
            ),
            historical_context_window_size=dict(type="int"),
        ),
    )


def _custom_configuration_spec() -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            semantic_override=dict(
                type="dict",
                options=dict(extraction=_override_block_spec(), consolidation=_override_block_spec()),
            ),
            summary_override=dict(type="dict", options=dict(consolidation=_override_block_spec())),
            user_preference_override=dict(
                type="dict",
                options=dict(extraction=_override_block_spec(), consolidation=_override_block_spec()),
            ),
            episodic_override=dict(
                type="dict",
                options=dict(
                    extraction=_override_block_spec(),
                    consolidation=_override_block_spec(),
                    reflection=_override_block_spec(
                        namespace_templates=_namespace_templates_spec(),
                        memory_record_schema=_memory_record_schema_spec(),
                    ),
                ),
            ),
            self_managed_configuration=_self_managed_configuration_spec(),
        ),
        mutually_exclusive=[_CUSTOM_CONFIGURATION_KEYS],
        required_one_of=[_CUSTOM_CONFIGURATION_KEYS],
    )


def _memory_strategies_spec() -> Dict[str, Any]:
    return dict(
        type="list",
        elements="dict",
        options=dict(
            semantic_memory_strategy=_strategy_spec(),
            summary_memory_strategy=_strategy_spec(),
            user_preference_memory_strategy=_strategy_spec(),
            episodic_memory_strategy=_strategy_spec(
                reflection_configuration=dict(
                    type="dict",
                    options=dict(
                        namespace_templates=_namespace_templates_spec(),
                        memory_record_schema=_memory_record_schema_spec(),
                    ),
                ),
            ),
            custom_memory_strategy=_strategy_spec(configuration=_custom_configuration_spec()),
        ),
        mutually_exclusive=[_STRATEGY_KEYS],
        required_one_of=[_STRATEGY_KEYS],
    )


def _stream_delivery_resources_spec() -> Dict[str, Any]:
    return dict(
        type="dict",
        options=dict(
            resources=dict(
                type="list",
                elements="dict",
                required=True,
                options=dict(
                    kinesis=dict(
                        type="dict",
                        required=True,
                        options=dict(
                            data_stream_arn=dict(type="str", required=True),
                            content_configurations=dict(
                                type="list",
                                elements="dict",
                                required=True,
                                options=dict(
                                    type=dict(type="str", required=True, choices=["MEMORY_RECORDS"]),
                                    level=dict(type="str", choices=["METADATA_ONLY", "FULL_CONTENT"]),
                                ),
                            ),
                        ),
                    ),
                ),
            ),
        ),
    )


def _uses_key(data: Any, key: str) -> bool:
    """Whether ``key`` is set to a non-None value anywhere in a nested dict/list structure."""
    if isinstance(data, dict):
        return any((k == key and v is not None) or _uses_key(v, key) for k, v in data.items())
    if isinstance(data, list):
        return any(_uses_key(item, key) for item in data)
    return False


def _check_botocore_features(module: AnsibleAWSModule) -> None:
    """Fail early when botocore is below the AgentCore floor, or a supplied option needs a newer release."""
    validate_botocore_version(
        module,
        AGENTCORE_MINIMUM_BOTOCORE_VERSION,
        f"Bedrock AgentCore requires botocore >= {AGENTCORE_MINIMUM_BOTOCORE_VERSION} "
        "to support the service model features used by this module.",
    )
    # Options are only sent to AWS on state=present.
    if module.params["state"] != "present":
        return

    for option, version in _OPTION_BOTOCORE_VERSIONS:
        validate_botocore_option(module, option, version)

    memory_strategies = module.params.get("memory_strategies")
    for key, version in _STRATEGY_KEY_BOTOCORE_VERSIONS:
        if _uses_key(memory_strategies, key):
            validate_botocore_version(
                module, version, f"The {key} option in memory_strategies requires botocore >= {version}."
            )


def _memory_result(client, module: AnsibleAWSModule, memory: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Snake_case a raw memory for output, adding its tags only when the tags option was given."""
    if not memory:
        return dict()
    result = camel_dict_to_snake_dict(memory, ignore_list=["tags", "Tags"])
    if module.params.get("tags") is not None:
        result["tags"] = list_tags(client, memory["arn"])
    return result


def _memory_status_check(
    client, module: AnsibleAWSModule, existing: Optional[Dict[str, Any]], state: str
) -> Optional[Dict[str, Any]]:
    """
    Handle a memory that is mid-transition or failed before acting on it.

    Exits early for an in-flight memory that is not waited on, fails where the desired state cannot be
    reached, and otherwise returns the memory to act on, re-read after any wait.
    """
    if existing is None:
        return None

    name: str = existing["name"]
    status = existing.get("status")
    should_wait = module.params["wait"] and not module.check_mode

    if status == MemoryStatus.DELETING:
        if state == "present":
            module.fail_json(msg=f"Memory {name} is currently being deleted; re-run once deletion completes.")
        if should_wait:
            wait_for_memory_status(client, module, existing["id"], MemoryStatus.DELETED)
        module.exit_json(changed=False, msg=f"Memory {name} is currently being deleted.", memory=dict())

    if status in (MemoryStatus.CREATING, MemoryStatus.UPDATING):
        if not should_wait:
            suffix = " (check mode)" if module.check_mode else ""
            memory = _memory_result(client, module, existing) if state == "present" else dict()
            module.exit_json(changed=False, msg=f"Memory {name} is currently in {status} state{suffix}.", memory=memory)
        wait_for_memory_status(client, module, existing["id"], MemoryStatus.ACTIVE)
        return get_memory(client, existing["id"])

    if status == MemoryStatus.FAILED and state == "present":
        failure_reason = existing.get("failureReason", "Unknown failure reason")
        module.fail_json(
            msg=f"Memory {name} is in FAILED state: {failure_reason}. Delete it with state=absent and re-create it.",
            failure_reason=existing.get("failureReason"),
        )

    return existing


def main() -> None:
    argument_spec = dict(
        state=dict(type="str", default="present", choices=["present", "absent"]),
        name=dict(type="str", required=True),
        description=dict(type="str"),
        event_expiry_duration=dict(type="int"),
        encryption_key_arn=dict(type="str", no_log=False),
        memory_execution_role_arn=dict(type="str"),
        memory_strategies=_memory_strategies_spec(),
        indexed_keys=dict(
            type="list",
            elements="dict",
            no_log=False,
            options=dict(
                key=dict(type="str", required=True, no_log=False),
                type=dict(type="str", required=True, choices=_METADATA_VALUE_TYPES),
            ),
        ),
        namespace_keys=dict(
            type="list",
            elements="dict",
            no_log=False,
            options=dict(
                key=dict(type="str", required=True, no_log=False),
                validation=dict(
                    type="dict",
                    options=dict(
                        allowed_values=dict(type="list", elements="str"),
                        regex_pattern=dict(type="str"),
                    ),
                ),
            ),
        ),
        stream_delivery_resources=_stream_delivery_resources_spec(),
        tags=dict(type="dict", aliases=["resource_tags"]),
        purge_tags=dict(type="bool", default=True),
        wait=dict(type="bool", default=True),
        wait_timeout=dict(type="int", default=600),
    )

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
    )
    _check_botocore_features(module)

    state: str = module.params["state"]
    name: str = module.params["name"]
    changed: bool = False
    msg: str = ""
    memory: Dict[str, Any] = dict()

    try:
        try:
            client = module.client("bedrock-agentcore-control", retry_decorator=AWSRetry.jittered_backoff())
        except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
            module.fail_json_aws(e, msg="Failed to connect to AWS.")

        existing = find_memory_by_name(client, name)
        existing = _memory_status_check(client, module, existing, state)

        if state == "present":
            if existing is None:
                changed, memory_id, msg = create_memory(module, client)
            else:
                changed, msg = update_memory(module, client, existing)
                memory_id = existing["id"]
            if module.check_mode:
                memory = _memory_result(client, module, existing)
            elif memory_id:
                memory = _memory_result(client, module, get_memory(client, memory_id))
        elif existing is not None:
            changed, msg = delete_memory(module, client, existing)
        else:
            msg = f"Memory {name} does not exist."
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    module.exit_json(changed=changed, msg=msg, memory=memory)


if __name__ == "__main__":
    main()
