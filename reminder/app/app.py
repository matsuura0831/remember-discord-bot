import json

import os
import logging

from nacl.signing import VerifyKey
from nacl.exceptions import BadSignatureError

# import requests

LOG_LEVEL = os.environ.get("LOG_LEVEL")
PUBLIC_KEY = os.environ.get("DISCORD_PUBLIC_KEY")

logger = logging.getLogger()
level = logging.getLevelName(LOG_LEVEL)
logger.setLevel(level)

def verify_request(event):
    signature = event["headers"]["x-signature-ed25519"]
    timestamp = event["headers"]["x-signature-timestamp"]

    vk = VerifyKey(bytes.fromhex(PUBLIC_KEY))
    msg = timestamp + event["body"]

    try:
        vk.verify(msg.encode(), signature=bytes.fromhex(signature))
    except BadSignatureError:
        return False
    return True

def make_response(code, body):
    return {
        "statusCode": code,
        "headers": { "Content-Type": "application/json" },
        "body": body
    }

def discord_handler(body):
    command = body["data"]["name"]

    if command == "hello":
        pass
    else:
        ValueError("f{command} is not supported.")

def lambda_handler(event, context):
    if not verify_request(event):
        return make_response(401, "invalid request signature")

    try:
        body = json.loads(event["body"])
        t = body["type"]

        if t == 1:
            # handle ping
            return make_response(200, json.dumps({"type": 1}))
        elif t == 2:
            msg = discord_handler(body)

            if msg is not None:
                return make_response(200, json.dumps(msg))
            else:
                logger.error("failed to make response")
                return make_response(400, "invalid request type.")
    except Exception as e:
        logger.error(e)
        return make_response(400, "invalid request type.")
