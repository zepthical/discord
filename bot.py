import discord
import requests
import os
from base64 import b64decode, b64encode

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")  # Set as secret
GITHUB_TOKEN = os.getenv("TOKEN")            # Set as secret
REPO_OWNER = "zepthical"
REPO_NAME = "key"
FILE_PATH = "Keys.txt"
BRANCH = "main"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def get_keys_file():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        content = b64decode(data["content"]).decode("utf-8")
        return data["sha"], content.splitlines()
    else:
        print("❌ Failed to fetch keys:", res.status_code)
        return None, []

def update_keys_file(new_keys, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    new_content = "\n".join(new_keys)
    data = {
        "message": "Key used",
        "content": b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "branch": BRANCH,
        "sha": sha
    }
    res = requests.put(url, json=data, headers=headers)
    return res.status_code in [200, 201]

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if message.content.lower().startswith("!getkey"):
        sha, keys = get_keys_file()
        if not keys:
            await message.channel.send("❌ No keys found.")
            return

        key = keys[0]
        new_keys = keys[1:]

        if update_keys_file(new_keys, sha):
            try:
                await message.author.send(f"🔑 Your key: `{key}`")
                await message.channel.send("📬 Key sent via DM!")
            except discord.Forbidden:
                await message.channel.send("❌ I can't DM you. Please allow DMs.")
        else:
            await message.channel.send("❌ Failed to update keys on GitHub.")

bot.run(DISCORD_BOT_TOKEN)
