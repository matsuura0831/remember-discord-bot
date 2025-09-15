import json
import os, glob
import requests
import base64

from dotenv import load_dotenv
load_dotenv(".env")

DISCORD_APPLICATION_ID = os.getenv("APPLICATION_ID")
DISCORD_TOKEN = os.getenv("TOKEN")

def main():
    url = f"https://discord.com/api/v10/applications/{DISCORD_APPLICATION_ID}/emojis"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bot {DISCORD_TOKEN}"
    }

    for fpath in glob.glob("./emoji/*.png"):
        name = os.path.basename(fpath).split('.')[0]
        print(fpath, name)

        with open(fpath, "rb") as fp:
            data = base64.b64encode(fp.read()).decode("utf-8")

        payload = {
            "name": name,
            "image": f"data:image/png;base64,{data}"
        }

        res = requests.post(
            url,
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bot {DISCORD_TOKEN}"
            },
            json = {
                "name": name,
                "image": f"data:image/png;base64,{data}"
            }
        )
        print(res.status_code, res.text)
    
    res = requests.get(url, headers = headers)

    if res.status_code == 200:
        with open("./emoji/data.txt", "w") as fp:
            for item in res.json()["items"]:
                id = item["id"]
                name = item["name"]

                fp.write(f":{name}:{id}\n")


if __name__ == "__main__":
    main()