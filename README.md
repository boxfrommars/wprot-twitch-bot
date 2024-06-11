## Title Bot

Twitch Bot that allows users to purchase a title with channel points. When the user sends their first message in chat after a long time, the bot announces the user using the title.

### Installation

```sh
git clone ...
cd wprotbot
pip install -r requirements.txt
cp ./.env.example ./.env
```

Set enviroment variables:
* `ACCESS_TOKEN` *(required)* You can get access token using `oauth.htm` file: open the file and click the `Get token` link. Accept the permissions, and after the redirect to localhost copy `access_token` from the url
* `CHANNEL` *(required)* Bot must be a moderator on this channel
* `REWARD_ID` *(required)* The ID of the reward that the user must purchase to get a title
* `DB_NAME` *(optional, default `wprotbot.db`)* If the file doesn't exist, it will be created during the first run
* `TITLE_COOLDOWN_SEC` *(optional, default 6 hours)* If the user hasn't written in the chat for a long time, then announce them after their message
* `TITLE_LIFETIME_SEC` *(optional, default 2 weeks)* A title is purchased for this period
* `GREETING_TEMPLATE` *(optional, default `{title} @{username} has joined the chat!`)* Announcement template

Run bot:
```sh
python main.py
```

### Usage

Purchase custom reward with `REWARD_ID` to get a title

Available commands:
* `!tit` or `!tit info` Get your title info
* `!tit delete` Delete your title
* `!tit info @wprotvbanke` *(moderators only)* Get information about the title of a given user
* `!tit delete @wprotvbanke` *(moderators only)* Delete this user's title
