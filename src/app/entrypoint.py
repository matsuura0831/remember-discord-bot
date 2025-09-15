import json
import os
import logging
import requests

import boto3
from discord_interactions import verify_key, InteractionType, InteractionResponseType

import commands

DISCORD_PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")
LAMBDA_FOLLOWUP_FUNCTION = os.environ.get("LAMBDA_FOLLOWUP_FUNCTION")

logger = logging.getLogger()

def make_response(code, body):
    return {
        "statusCode": code,
        "headers": { "Content-Type": "application/json" },
        "body": json.dumps(body),
    }

def verify_request(event):
    headers = event.get("headers", {})
    signature = headers.get("x-signature-ed25519")
    timestamp = headers.get("x-signature-timestamp")

    raw_body = event.get("body") or "{}"

    if signature is None or timestamp is None:
        return False
    return verify_key(raw_body.encode(), signature, timestamp, DISCORD_PUBLIC_KEY)

def lambda_handler(event, context):
    logger.info(event)
    logger.info(context)

    if not verify_request(event):
        logger.info("invalid request signature")
        return make_response(401, "invalid request signature")

    try:
        body = json.loads(event.get("body", "{}"))
        interaction_type = body.get("type")

        if interaction_type in [InteractionType.APPLICATION_COMMAND, InteractionType.MESSAGE_COMPONENT]:
            data = body.get("data")
            cmd = data.get("name")
            
            if "options" in data:
                # サブコマンドの場合はアンダーバーで連結したものを対象にする
                sub = data.get("options")[0]

                if "name" in sub:
                    sub_cmd = sub.get("name")

                    cmd = f"{cmd}_{sub_cmd}"
                    data = sub

            if commands.is_short(cmd):
                # コマンドを実行できるなら実行する
                msg = commands.call_short(cmd, body, data)
                res = {
                    "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
                    "data": {
                        "content": msg
                    }
                }
            elif commands.is_long(cmd):
                # 返事に時間がかかる場合は別途lambdaを起動して実行する
                id = body.get("id")
                interaction_token = body.get("token")

                url = f"https://discord.com/api/v10/interactions/{id}/{interaction_token}/callback"
                requests.post(
                    url,
                    json = { "type": InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE },
                )

                client = boto3.client("lambda")
                client.invoke(
                    FunctionName = LAMBDA_FOLLOWUP_FUNCTION,
                    InvocationType = "Event",
                    Payload = json.dumps(body)
                )
                res = {}
            else:
                raise ValueError(f"Illegal command: {cmd}.")
        else:
            res = { "type": InteractionResponseType.PONG }

        return make_response(200, res)
    except Exception as e:
        logger.error(e)
        return make_response(400, "invalid request type.")
