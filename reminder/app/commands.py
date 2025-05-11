import os
import json
import random
import logging

import boto3

from utils import short_command, long_command, get_commands

# for use followup lambda
SCHEDULER_ROLE = os.environ.get("SCHEDULER_ROLE")
SCHEDULER_GROUP = os.environ.get("SCHEDULER_GROUP")
LAMBDA_MESSAGE = os.environ.get("LAMBDA_MESSAGE")

# Main funcitons ----------------------------------------

logger = logging.getLogger()

@short_command
def dice(interaction, max, num=1):
    d = [str(random.randint(1, max)) for i in range(num)]
    d = ",".join(d)
    return f"{num}D{max} = {d}"

@long_command
def remind(interaction, description, channel=None, title="", emoji="", rnd_emoji="", at=None, cron=None, timezone="Asia/Tokyo"):
    schedule_prefix = "remind"
    client = boto3.client("scheduler")

    # 現時点のスケジュール数をカウントして登録名を決定する
    paginator = client.get_paginator("list_schedules")
    res_itr = paginator.paginate(
        GroupName = SCHEDULER_GROUP,
        MaxResults = 100,
        NamePrefix = schedule_prefix,
    )

    schedules = []
    for r in res_itr:
        for s in r["Schedules"]:
            schedules.append([s["Arn"], s["Name"]])
    n = len(schedules)
    schedule_name = f"{schedule_prefix}{n}"

    logger.info(interaction)
    logger.info(channel)
    if channel is None:
        # チャンネルIDが明に指定されていない場合は発言元のチャンネルにする
        channel = interaction.get("channel_id")
        logger.info(channel)

    # 特殊文字を修正する
    for src, dst in [["\\n", "\n"], ["\\r", "\r"], ["\\t", "\t"]]:
        description = description.replace(src, dst)

    payload = {
        "channel": channel,
        "title": title,
        "description": description,
        "emoji": emoji.split(","),
    }

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
    return f"以下の名前で登録しました: {schedule_name}"


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

def call_short(name, body):
    data = body.get("data", {})
    options = data.get("options", {})

    p = {o["name"]: o["value"] for o in options}
    p = {**p, "interaction": body }

    return SHORT_COMMANDS[name](**p)

def call_long(name, body):
    data = body.get("data", {})
    options = data.get("options", {})

    p = {o["name"]: o["value"] for o in options}
    p = {**p, "interaction": body }

    return LONG_COMMANDS[name](**p)
