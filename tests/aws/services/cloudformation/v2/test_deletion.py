import os

import pytest

from localstack.testing.pytest import markers
from localstack.utils.strings import short_uid


@markers.aws.validated
@markers.snapshot.skip_snapshot_verify(paths=["$..message"])
@pytest.mark.skip(
    reason="Invalid state found, trying to resolve the condition of the output from this stack on deletion"
)
def test_single_resource(deploy_cfn_template, aws_client, snapshot):
    value = short_uid()
    snapshot.add_transformer(snapshot.transform.regex(value, "<value>"))
    stack = deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../../templates/ssm_parameter_defaultname.yaml"
        ),
        parameters={"Input": value},
    )

    parameter_name = stack.outputs["CustomParameterOutput"]
    snapshot.add_transformer(snapshot.transform.regex(parameter_name, "<parameter-name>"))
    value = aws_client.ssm.get_parameter(Name=parameter_name)["Parameter"]
    snapshot.match("get-value", value)

    stack.destroy()

    with pytest.raises(aws_client.ssm.exceptions.ParameterNotFound) as exc_info:
        aws_client.ssm.get_parameter(Name=parameter_name)

    snapshot.match("exc-value", exc_info.value.response)
