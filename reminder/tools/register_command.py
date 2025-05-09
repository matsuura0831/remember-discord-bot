import json
import os
import requests

from dotenv import load_dotenv
load_dotenv(".env")

DISCORD_APPLICATION_ID = os.getenv("APPLICATION_ID")
DISCORD_TOKEN = os.getenv("TOKEN")

print(DISCORD_APPLICATION_ID)
print(DISCORD_TOKEN)

def main():
    res = requests.post(
        url = f"https://discord.com/api/v10/applications/{DISCORD_APPLICATION_ID}/commands",
        headers = {
            "Authorization": f"Bot {DISCORD_TOKEN}",
            "Content-Type": "application/json",
        },
        data = json.dumps(
            {
                "name": "hello",
                "description": "hello world",
            }
        )
    )
    print(res.status_code)
    print(res.text)

if __name__ == "__main__":
    main()