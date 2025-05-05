import os
import discord
import requests
from base64 import b64decode
from base64 import b64encode

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_OWNER = "zepthical"
REPO_NAME = "k"
FILE_PATH = "Keys.txt"
BRANCH = "main"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

def get_keys_file():
    url = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        content = res.text  # Directly get the raw content as text
        return None, content.splitlines()  # Return lines as a list
    else:
        return None, []

def update_keys_file(new_keys, sha):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    new_content = "\n".join(new_keys)
    data = {
        "message": "Remove used key",
        "content": b64encode(new_content.encode("utf-8")).decode("utf-8"),
        "branch": BRANCH,
        "sha": sha
    }
    res = requests.put(url, json=data, headers=headers)
    return res.status_code == 200 or res.status_code == 201

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
            await message.channel.send("❌ Failed to update the key file on GitHub.")

bot.run(DISCORD_BOT_TOKEN)
