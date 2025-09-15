import json
import os
import logging
import requests

import commands

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

    interaction_token = event.get("token", "")
    url = f"https://discord.com/api/v10/webhooks/{DISCORD_APP_ID}/{interaction_token}"

    try:
        data = event.get("data", {})
        cmd = data.get("name")

        if "options" in data:
            # サブコマンドの場合はアンダーバーで連結したものを対象にする
            sub = data.get("options")[0]

            if "name" in sub:
                sub_cmd = sub.get("name")

                cmd = f"{cmd}_{sub_cmd}"
                data = sub

        if commands.is_long(cmd):
            # コマンドを実行できるなら実行する
            msg = commands.call_long(cmd, event, data)
            payload = { "content": msg }
        else:
            raise ValueError(f"Illegal command: {cmd}.")
    except Exception as e:
        logger.error(e)
        payload = { "content": f"コマンド実行に失敗しました: {e}" }

    response = requests.post(
        url,
        json = payload,
    )

    return make_response(response.status_code, response.text)