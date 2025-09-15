# remember-discord-bot

## discord setting

OAuth2 SCOPE

* bot
* applications.commands

BOT PERMISSIONS

* Send Messages
* Read Message History
* Add Reactions

## venv

```sh
python3 -m venv .env
source .env/bin/activate
```

## deploy

Add parameter overrides in src/samconfig.toml

```diff
[default.deploy.parameters]
capabilities = "CAPABILITY_IAM"
confirm_changeset = true
resolve_s3 = true
+ parameter_overrides = "DiscordPublicKey=<str> DiscordAppId=<str> DiscordToken=<str>"
```

Build & deploy

```sh
./bin/sam_deploy.sh --profile dev-sso --guided
or 
./bin/sam_deploy.sh --profile dev-sso
```

## command update

make .env at src/tools/

```
DISCORD_APPLICATION_ID=...
DISCORD_TOKEN=...
```

```sh
./bin/command_update.sh
```
