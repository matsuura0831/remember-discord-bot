import json
import os
import requests

from dotenv import load_dotenv
load_dotenv(".env")

DISCORD_APPLICATION_ID = os.getenv("APPLICATION_ID")
DISCORD_TOKEN = os.getenv("TOKEN")

def main():
    commands = [{
        "name": "dice",
        "description": "1から指定された数値までの間でダイスを振ります",
        "options": [
            {
                "name": "max",
                "description": "ダイスの上限値",
                "type": 4, # INTEGER
                "required": True,
                "min_value": 1,
                "max_value": 1000,
            }, {
                "name": "num",
                "description": "ダイスの数",
                "type": 4, # INTEGER
                "min_value": 1,
                "max_value": 1000,
            }
        ]
    }, {
        "name": "remind",
        "description": "リマインダーを指定時刻に送ります",
        "options": [
            {
                "name": "description",
                "description": "リマインダ内容",
                "type": 3, # STRING
                "required": True,
            }, {
                "name": "channel",
                "description": "投稿先のチャンネルID。指定されなかった場合は登録元チャンネルIDを利用します",
                "type": 3, # STRING
            }, {
                "name": "title",
                "description": "リマインダタイトル",
                "type": 3, # STRING
            }, {
                "name": "emoji",
                "description": "リアクション文字列。複数を指定する場合はカンマ区切りで入力してください",
                "type": 3, # STRING
            }, {
                "name": "at",
                "description": "リマインダを1回限り投稿する場合に指定。Format: (<yyyy-mm-dd>T<hh:mm:ss>)。atかcronのどちらかは入力が必須です",
                "type": 3, # STRING
            }, {
                "name": "cron",
                "description": "リマインダを定期投稿する場合に指定。Format: (<minutes> <hours> <day> <month> <week> <year>)。atかcronのどちらかは入力が必須です",
                "type": 3, # STRING
            }, {
                "name": "timezone",
                "description": "リマインダのタイムゾーンを指定。指定されなかった場合は Asia/Tokyo を利用します",
                "type": 3, # STRING
            }
        ]
    }]

    for cmd in commands:
        res = requests.post(
            url = f"https://discord.com/api/v10/applications/{DISCORD_APPLICATION_ID}/commands",
            headers = {
                "Authorization": f"Bot {DISCORD_TOKEN}",
            },
            json = cmd
        )
        print(cmd["name"], res.status_code)
        print(res.text)

if __name__ == "__main__":
    main()