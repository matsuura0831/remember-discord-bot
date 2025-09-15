import os
import re
import json
import random
import datetime

import logging

import boto3
from botocore.exceptions import ClientError

from utils import short_command, long_command, get_commands

# for use followup lambda
SCHEDULER_ROLE = os.environ.get("SCHEDULER_ROLE")
SCHEDULER_GROUP = os.environ.get("SCHEDULER_GROUP")
LAMBDA_MESSAGE = os.environ.get("LAMBDA_MESSAGE")

PREVIOUS_SCHEDULE_GROUP_PREFIX = "remind"
CURRENT_SCHEDULE_GROUP_PREFIX = "v2"

# Main funcitons ----------------------------------------

logger = logging.getLogger()

@long_command
def remind_migrate(interaction):
    channel = interaction.get("channel_id")

    client = boto3.client("scheduler")
    paginator = client.get_paginator("list_schedules")
    res_itr = paginator.paginate(
        GroupName = SCHEDULER_GROUP,
        MaxResults = 100,
        NamePrefix = PREVIOUS_SCHEDULE_GROUP_PREFIX,
    )

    renames = []
    for r in res_itr:
        for s in r["Schedules"]:
            name = s["Name"]

            ret = client.get_schedule(
                GroupName = SCHEDULER_GROUP,
                Name = name,
            )
            payload = json.loads(ret["Target"]["Input"])
            target_ch = payload["channel"]

            if channel == target_ch:
                logger.info(ret)
                expression = ret["ScheduleExpression"]
                timezone = ret["ScheduleExpressionTimezone"]

                t = ret["CreationDate"]
                t = t.astimezone(datetime.timezone(datetime.timedelta(hours=9))) # UTC to JST
                t = t.strftime("%Y%m%d%H%M%S")

                schedule_name = f"{CURRENT_SCHEDULE_GROUP_PREFIX}-{channel}-{t}"

                p = {
                    "Name": schedule_name,
                    "FlexibleTimeWindow": { "Mode": "OFF" },
                    "ScheduleExpression": expression,
                    "ScheduleExpressionTimezone": timezone,
                    "ActionAfterCompletion": "DELETE",
                    "GroupName": SCHEDULER_GROUP,
                    "State": "ENABLED",
                    "Target": {
                        "Arn": LAMBDA_MESSAGE,
                        "RoleArn": SCHEDULER_ROLE,
                        "Input": json.dumps(payload),
                    }
                }
                client.create_schedule(**p)

                p = {
                    "GroupName": SCHEDULER_GROUP,
                    "Name": name,
                }
                client.delete_schedule(**p)

                renames.append(f"* From: {name}, To: {schedule_name}")

    logger.info(renames)
    return f"以下の通り再構築を行いました\n{"\n".join(renames)}"
    
@long_command
def remind_del(interaction, name):
    channel = interaction.get("channel_id")
    schedule_name = f"{CURRENT_SCHEDULE_GROUP_PREFIX}-{channel}-{name}"

    p = {
        "GroupName": SCHEDULER_GROUP,
        "Name": schedule_name,
    }

    try:
        client = boto3.client("scheduler")
        client.delete_schedule(**p)

        msg = "指定された通知を削除しました"
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            msg = "指定された通知名は存在しませんでした"
        else:
            raise e
    return msg

@long_command
def remind_show(interaction, name):
    channel = interaction.get("channel_id")
    schedule_name = f"{CURRENT_SCHEDULE_GROUP_PREFIX}-{channel}-{name}"

    data = []
    try:
        client = boto3.client("scheduler")
        ret = client.get_schedule(
            GroupName = SCHEDULER_GROUP,
            Name = schedule_name,
        )

        expression = ret["ScheduleExpression"]
        match = re.search("(?P<type>cron|at?)\\((?P<value>.+?)\\)", expression)
        if match:
            data.append(f"* {match.group("type")} = {match.group("value")}")

        payload = json.loads(ret["Target"]["Input"])
        for k, v in payload.items():
            if k == "description":
                # 特殊文字を修正する
                for dst, src in [["\\n", "\n"], ["\\r", "\r"], ["\\t", "\t"]]:
                    v = v.replace(src, dst)

            data.append(f"* {k} = {v}")

        msg = f"詳細は以下の通りです\n{"\n".join(data)}"
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            msg = "指定された通知名は存在しませんでした"
        else:
            raise e
    return msg

@long_command
def remind_ls(interaction):
    channel = interaction.get("channel_id")
    schedule_prefix = f"{CURRENT_SCHEDULE_GROUP_PREFIX}-{channel}-"

    client = boto3.client("scheduler")
    paginator = client.get_paginator("list_schedules")
    res_itr = paginator.paginate(
        GroupName = SCHEDULER_GROUP,
        MaxResults = 100,
        NamePrefix = schedule_prefix,
    )

    data = []
    for r in res_itr:
        for s in r["Schedules"]:
            name = s["Name"]
            show_name = name.split("-")[-1] # v2-<ch>-<date> の <date>のみを返す

            ret = client.get_schedule(
                GroupName = SCHEDULER_GROUP,
                Name = name,
            )
            expression = ret["ScheduleExpression"]
            data.append(f"* Name: {show_name}, Expression: {expression}")

    return f"登録されている通知は以下の通りです\n{"\n".join(data)}"

@short_command
def dice(interaction, max, num=1):
    d = [str(random.randint(1, max)) for i in range(num)]
    d = ",".join(d)
    return f"{num}D{max} = {d}"

@long_command
def remind_add(interaction, description, channel=None, title=None, emoji=None, rnd_emoji="", at=None, cron=None, timezone="Asia/Tokyo"):
    schedule_prefix = "remind"
    client = boto3.client("scheduler")

    # 現時点のスケジュール数をカウントして登録名を決定する
    paginator = client.get_paginator("list_schedules")
    res_itr = paginator.paginate(
        GroupName = SCHEDULER_GROUP,
        MaxResults = 100,
        NamePrefix = schedule_prefix,
    )

    logger.info(interaction)
    logger.info(channel)
    if channel is None:
        # チャンネルIDが明に指定されていない場合は発言元のチャンネルにする
        channel = interaction.get("channel_id")
        logger.info(channel)

    t = datetime.datetime.now()
    t = t.astimezone(datetime.timezone(datetime.timedelta(hours=9))) # UTC to JST
    t = t.strftime("%Y%m%d%H%M%S")
    schedule_name = f"{CURRENT_SCHEDULE_GROUP_PREFIX}-{channel}-{t}"

    # 特殊文字を修正する
    for src, dst in [["\\n", "\n"], ["\\r", "\r"], ["\\t", "\t"]]:
        description = description.replace(src, dst)

    payload = {
        "channel": channel,
        "description": description,
    }

    if title is not None:
        payload["title"] = title

    if emoji is not None:
        payload["emoji"] = emoji.split(",")

    if rnd_emoji != "":
        payload["rnd_emoji"] = rnd_emoji

    p = {
        "Name": schedule_name,
        "FlexibleTimeWindow": { "Mode": "OFF" },
        "ScheduleExpressionTimezone": timezone,
        "ActionAfterCompletion": "DELETE",
        "GroupName": SCHEDULER_GROUP,
        "State": "ENABLED",
        "Target": {
            "Arn": LAMBDA_MESSAGE,
            "RoleArn": SCHEDULER_ROLE,
            "Input": json.dumps(payload),
        }
    }
    
    if cron is not None:
        p["ScheduleExpression"] = f"cron({cron})"
    elif at is not None:
        p["ScheduleExpression"] = f"at({at})"
    else:
        raise ValueError("Option 'cron' or 'at' is required")

    res = client.create_schedule(**p)
    # return res["ScheduleArn"]
    return f"以下の名前で登録しました: {t}"


@long_command
def hello(interaction):
    import time
    time.sleep(5)

    return "HELLO"

# Util funcitons ----------------------------------------

SHORT_COMMANDS = get_commands(__name__, short_command)
LONG_COMMANDS = get_commands(__name__, long_command)

def is_short(name):
    return name in SHORT_COMMANDS

def is_long(name):
    return name in LONG_COMMANDS

def call_short(name, body, data):
    options = data.get("options", [])

    p = {o["name"]: o["value"] for o in options}
    p = {**p, "interaction": body }

    return SHORT_COMMANDS[name](**p)

def call_long(name, body, data):
    options = data.get("options", [])

    p = {o["name"]: o["value"] for o in options}
    p = {**p, "interaction": body }

    return LONG_COMMANDS[name](**p)
