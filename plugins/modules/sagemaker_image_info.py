#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

DOCUMENTATION = r"""
---
module: sagemaker_image_info
short_description: Gather information about SageMaker Images
version_added: "1.1.0"
author:
    - Jan Likar (@JanLikar)
description:
    - This module retrieves details for a single SageMaker Image or lists SageMaker Images with optional filters.
options:
    image_name:
        description:
            - The name of the SageMaker Image to retrieve.
            - If not provided, the module will list images, optionally filtered by the other options.
            - Mutually exclusive with all other options.
        type: str
    name_contains:
        description:
            - A string in the image name.
            - This filter returns only images whose name contains the specified string.
        type: str
    creation_time_after:
        description:
            - Only include images created after the specified time, in ISO 8601 format.
        type: str
    creation_time_before:
        description:
            - Only include images created before the specified time, in ISO 8601 format.
        type: str
    last_modified_time_after:
        description:
            - Only include images last modified after the specified time, in ISO 8601 format.
        type: str
    last_modified_time_before:
        description:
            - Only include images last modified before the specified time, in ISO 8601 format.
        type: str
    sort_by:
        description:
            - The field to sort results by.
        type: str
        choices: ['CREATION_TIME', 'LAST_MODIFIED_TIME', 'IMAGE_NAME']
    sort_order:
        description:
            - The sort order for results.
        type: str
        choices: ['ASCENDING', 'DESCENDING']
extends_documentation_fragment:
    - amazon.ai.common.modules
    - amazon.ai.region.modules
    - amazon.ai.boto3
"""


EXAMPLES = r"""
- name: Get info about a specific SageMaker Image
  amazon.ai.sagemaker_image_info:
    image_name: "my-image"

- name: List all SageMaker Images
  amazon.ai.sagemaker_image_info:

- name: List SageMaker Images filtered by name
  amazon.ai.sagemaker_image_info:
    name_contains: "my-project"
    sort_by: "CREATION_TIME"
    sort_order: "DESCENDING"
"""


RETURN = r"""
images:
    description: A list of dictionaries containing detailed configuration of SageMaker Images.
    type: list
    elements: dict
    returned: always
    contains:
        image_arn:
            description: The Amazon Resource Name (ARN) of the image.
            type: str
            sample: "arn:aws:sagemaker:us-east-1:123456789012:image/my-image"
        image_name:
            description: The name of the image.
            type: str
            sample: "my-image"
        image_status:
            description: The status of the image.
            type: str
            sample: "CREATED"
        creation_time:
            description: The date and time the image was created.
            type: str
            sample: "2025-10-01T15:36:41.199376+00:00"
        last_modified_time:
            description: The date and time the image was last modified.
            type: str
            sample: "2025-10-01T15:36:42.201271+00:00"
        description:
            description: The description of the image.
            type: str
            sample: "My image description"
        display_name:
            description: The display name of the image.
            type: str
            sample: "My Image"
        failure_reason:
            description: The failure reason, if the image is in a failed state.
            type: str
            sample: ""
"""


try:
    import botocore
except ImportError:
    pass  # Handled by AnsibleAWSModule

from typing import Any
from typing import Dict
from typing import List

from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import describe_image
from ansible_collections.amazon.ai.plugins.module_utils.sagemaker import list_images

from ansible.module_utils.common.dict_transformations import camel_dict_to_snake_dict

from ansible_collections.amazon.aws.plugins.module_utils.exceptions import AnsibleAWSError
from ansible_collections.amazon.aws.plugins.module_utils.modules import AnsibleAWSModule
from ansible_collections.amazon.aws.plugins.module_utils.retries import AWSRetry
from ansible_collections.amazon.aws.plugins.module_utils.transformation import scrub_none_parameters


def find_images(client, module: AnsibleAWSModule) -> List[Dict[str, Any]]:
    image_name = module.params.get("image_name")

    if image_name:
        image = describe_image(client, image_name)
        if image is None:
            module.fail_json(msg=f"SageMaker Image '{image_name}' does not exist.")
        return [image]

    params: Dict[str, Any] = scrub_none_parameters(
        {
            "NameContains": module.params.get("name_contains"),
            "CreationTimeAfter": module.params.get("creation_time_after"),
            "CreationTimeBefore": module.params.get("creation_time_before"),
            "LastModifiedTimeAfter": module.params.get("last_modified_time_after"),
            "LastModifiedTimeBefore": module.params.get("last_modified_time_before"),
            "SortBy": module.params.get("sort_by"),
            "SortOrder": module.params.get("sort_order"),
        }
    )
    return list_images(client, **params)


def main():
    argument_spec = {
        "image_name": {"type": "str"},
        "name_contains": {"type": "str"},
        "creation_time_after": {"type": "str"},
        "creation_time_before": {"type": "str"},
        "last_modified_time_after": {"type": "str"},
        "last_modified_time_before": {"type": "str"},
        "sort_by": {"type": "str", "choices": ["CREATION_TIME", "LAST_MODIFIED_TIME", "IMAGE_NAME"]},
        "sort_order": {"type": "str", "choices": ["ASCENDING", "DESCENDING"]},
    }

    module = AnsibleAWSModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        mutually_exclusive=[
            ("image_name", "name_contains"),
            ("image_name", "creation_time_after"),
            ("image_name", "creation_time_before"),
            ("image_name", "last_modified_time_after"),
            ("image_name", "last_modified_time_before"),
            ("image_name", "sort_by"),
            ("image_name", "sort_order"),
        ],
    )

    try:
        client = module.client("sagemaker", retry_decorator=AWSRetry.jittered_backoff())
    except (botocore.exceptions.ClientError, botocore.exceptions.BotoCoreError) as e:
        module.fail_json_aws(e, msg="Failed to connect to AWS.")

    images: List[Dict[str, Any]] = []

    try:
        images = find_images(client, module)
    except AnsibleAWSError as e:
        module.fail_json_aws_error(e)

    # `describe_image` also returns `RoleArn`, which `list_images` does not. Drop it so that
    # `images` is uniformly shaped regardless of which code path produced it.
    result: List[Dict[str, Any]] = [
        camel_dict_to_snake_dict({k: v for k, v in image.items() if k != "RoleArn"}) for image in images
    ]

    module.exit_json(images=result)


if __name__ == "__main__":
    main()
