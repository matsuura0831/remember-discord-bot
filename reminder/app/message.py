import json
import os
import logging
import random
import requests
import urllib.parse

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

    channel_id = event.get("channel")
    title = event.get("title", "")
    description = event.get("description")
    emoji = event.get("emoji", [])
    rnd_emoji = event.get("rnd_emoji", None)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bot {DISCORD_TOKEN}",
    }
    payload = {
        "tts": False,
        "embeds": [{
            "title": title,
            "description": description,
        }]
    }

    url = f"https://discord.com/api/v10/channels/{channel_id}/messages"
    logger.info(f"post: {url}, payload: {json.dumps(payload)}")
    response = requests.post( url, headers = headers, json = payload)
    logger.info(f"code: {response.status_code}, text: {response.text}")

    if response.status_code == 200:
        data = json.loads(response.text)
        msg_id = data.get("id")

        if emoji:
            for e in emoji:
                emoji_id = urllib.parse.quote(e)
                url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}/reactions/{emoji_id}/@me"
                requests.put(url, headers = headers)

        if rnd_emoji is not None:
            e = rnd_emoji.split(",")
            payload["rnd_emoji"] = random.choice(e)

            emoji_id = urllib.parse.quote(rnd_emoji)
            url = f"https://discord.com/api/v10/channels/{channel_id}/messages/{msg_id}/reactions/{emoji_id}/@me"
            requests.put(url, headers = headers)


    return make_response(response.status_code, response.text)
