import json
import os
import logging
import requests

import boto3
from discord_interactions import verify_key, InteractionType, InteractionResponseType

DISCORD_APP_ID = os.environ.get("DISCORD_APP_ID")
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")

logger = logging.getLogger()

def make_response(code, body):
    return {
        "statusCode": code,
        "headers": { "Content-Type": "application/json" },
        "body": json.dumps(body),
    }

def lambda_handler(event, context):
    logger.info(event)
    logger.info(context)
    
    import time
    time.sleep(10)

    data = event.get("data", {})
    interaction_token = event.get("token", "")
    url = f"https://discord.com/api/v10/webhooks/{DISCORD_APP_ID}/{interaction_token}"

    res = requests.post(
        url,
        data = json.dumps({"content": "Hello"}),
        headers = { "Content-Type": "application/json" },
    )

    return make_response(res.status_code, res.text)