import json

import os
import logging

from discord_interactions import verify_key, InteractionType, InteractionResponseType


# import requests

LOG_LEVEL = os.environ.get("LOG_LEVEL")
PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")

logger = logging.getLogger()
level = logging.getLevelName(LOG_LEVEL)
logger.setLevel(level)

def verify_request(event):
    headers = event.get("headers", {})
    signature = headers.get("x-signature-ed25519")
    timestamp = headers.get("x-signature-timestamp")

    raw_body = event.get("body") or "{}"

    if signature is None or timestamp is None:
        return False
    return verify_key(raw_body.encode(), signature, timestamp, PUBLIC_KEY)

def make_response(code, body):
    return {
        "statusCode": code,
        "headers": { "Content-Type": "application/json" },
        "body": body
    }

def discord_handler(name, data):
    if name == "hello":
        return "HELLO WORLD"
    else:
        ValueError("f{name} is not supported.")

def lambda_handler(event, context):
    logger.info("handler arguments")
    logger.info(event)
    logger.info(context)

    if not verify_request(event):
        logger.info("invalid request signature")
        return make_response(401, "invalid request signature")

    try:
        body = json.loads(event.get("body", "{}"))
        interaction_type = body.get("type")

        if interaction_type in [InteractionType.APPLICATION_COMMAND, InteractionType.MESSAGE_COMPONENT]:
            data = body.get("data", {})
            cname = data.get("name")

            res_text = discord_handler(cname, data)
            res = { "type": InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE, "data": { "content": res_text }}
        else:
            res = { "type": InteractionResponseType.PONG }

        return make_response(200, json.dumps(res))
    except Exception as e:
        logger.error(e)
        return make_response(400, "invalid request type.")
