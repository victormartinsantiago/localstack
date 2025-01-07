import pytest

from localstack.testing.aws.util import in_default_partition
from localstack.testing.pytest import markers
from localstack.utils.common import short_uid


@pytest.mark.skipif(
    not in_default_partition(), reason="Test not applicable in non-default partitions"
)
@markers.aws.validated
def test_list_schedules(aws_client):
    # simple smoke test to assert that the provider is available, without creating any schedules
    result = aws_client.scheduler.list_schedules()
    assert isinstance(result.get("Schedules"), list)


@markers.aws.validated
def test_tag_resource(aws_client, events_scheduler_create_schedule_group, snapshot):
    name = short_uid()
    schedule_group_arn = events_scheduler_create_schedule_group(name)

    response = aws_client.scheduler.tag_resource(
        ResourceArn=schedule_group_arn,
        Tags=[
            {
                "Key": "TagKey",
                "Value": "TagValue",
            }
        ],
    )

    response = aws_client.scheduler.list_tags_for_resource(ResourceArn=schedule_group_arn)

    assert response["Tags"][0]["Key"] == "TagKey"
    assert response["Tags"][0]["Value"] == "TagValue"

    snapshot.match("list-tagged-schedule", response)


@markers.aws.validated
def test_untag_resource(aws_client, events_scheduler_create_schedule_group, snapshot):
    name = short_uid()
    tags = [
        {
            "Key": "TagKey",
            "Value": "TagValue",
        }
    ]
    schedule_group_arn = events_scheduler_create_schedule_group(name, Tags=tags)

    response = aws_client.scheduler.untag_resource(
        ResourceArn=schedule_group_arn, TagKeys=["TagKey"]
    )

    response = aws_client.scheduler.list_tags_for_resource(ResourceArn=schedule_group_arn)

    assert response["Tags"] == []

    snapshot.match("list-untagged-schedule", response)


class TestScheduleGroupe:
    @markers.aws.validated
    @pytest.mark.parametrize("with_tags", [True, False])
    @pytest.mark.parametrize("with_client_token", [True, False])
    def test_create_schedule_group(
        self, with_tags, with_client_token, events_scheduler_create_schedule_group, snapshot
    ):
        name = f"test-schedule-group-{short_uid()}"
        kwargs = {}
        if with_client_token:
            kwargs["ClientToken"] = f"test-client_token-{short_uid()}"
        if with_tags:
            kwargs["Tags"] = [
                {
                    "Key": "TagKey",
                    "Value": "TagValue",
                }
            ]
        response = events_scheduler_create_schedule_group(
            name,
            **kwargs,
        )

        snapshot.add_transformer(snapshot.transform.regex(name, "<name>"))
        snapshot.match("create-schedule-group", response)

    @markers.aws.validated
    @pytest.mark.parametrize("with_tags", [True, False])
    def test_get_schedule_group(
        self, with_tags, aws_client, events_scheduler_create_schedule_group, snapshot
    ):
        name = f"test-schedule-group-{short_uid()}"
        kwargs = {"Tags": [{"Key": "TagKey", "Value": "TagValue"}]} if with_tags else {}
        schedule_group_arn = events_scheduler_create_schedule_group(name, **kwargs)

        response = aws_client.scheduler.get_schedule_group(Name=name)

        assert response["Arn"] == schedule_group_arn
        assert response["Name"] == name

        snapshot.add_transformer(snapshot.transform.regex(name, "<name>"))
        snapshot.match("get-schedule-group", response)

    @markers.aws.validated
    def test_get_schedule_group_not_found(self, aws_client, snapshot):
        with pytest.raises(Exception) as exc:
            aws_client.scheduler.get_schedule_group(Name="not-existing-name")

        assert exc.typename == "ResourceNotFoundException"

        snapshot.match("get-schedule-group-not-found", exc.value.response)

    @markers.aws.validated
    @pytest.mark.parametrize("with_tags", [True, False])
    def test_list_schedule_groups(
        self, with_tags, aws_client, events_scheduler_create_schedule_group, snapshot
    ):
        kwargs = {"Tags": [{"Key": "TagKey", "Value": "TagValue"}]} if with_tags else {}
        name_one = f"test-schedule-groupe-one-{short_uid()}"
        events_scheduler_create_schedule_group(name_one, **kwargs)

        name_two = f"test-schedule-groupe-two-{short_uid()}"
        events_scheduler_create_schedule_group(name_two, **kwargs)

        response = aws_client.scheduler.list_schedule_groups()

        assert len(response["ScheduleGroups"]) == 3  # default schedule group + 2 created

        snapshot.add_transformers_list(
            [
                snapshot.transform.regex(name_one, "<name-groupe-one>"),
                snapshot.transform.regex(name_two, "<name-groupe-two>"),
            ]
        )
        snapshot.match("list-schedule-groups", response)

    @markers.aws.validated
    def test_list_schedule_groups_not_found(self, aws_client, snapshot):
        response = aws_client.scheduler.list_schedule_groups()

        assert len(response["ScheduleGroups"]) == 1  # default schedule group

        snapshot.match("list-schedule-groups-not-found", response)
