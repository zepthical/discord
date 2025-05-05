import discord
import requests
from base64 import b64decode
from base64 import b64encode
import os
import time  # To handle timestamps

DISCORD_BOT_TOKEN = "MTM2ODg0NDIyOTExMTE4OTU1NQ.GEVGqh.D1VLAPtC4oj-oPiqj5-sRwM9UOfnXYEmBvJIew"
GITHUB_TOKEN = "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"
REPO_OWNER = "zepthical"
REPO_NAME = "k"
FILE_PATH = "Keys.txt"
BRANCH = "main"

intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)

# Store the last request time for each user
user_cooldowns = {}

COOLDOWN_PERIOD = 86400  # 1 day in seconds (24 hours * 60 minutes * 60 seconds)

def get_keys_file():
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents/{FILE_PATH}?ref={BRANCH}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    res = requests.get(url, headers=headers)
    if res.status_code == 200:
        data = res.json()
        content = b64encode(res.content).decode("utf-8")
        return data["sha"], b64decode(data["content"]).decode("utf-8").splitlines()
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
        current_time = time.time()
        
        # Check if the user has a cooldown
        if message.author.id in user_cooldowns:
            last_request_time = user_cooldowns[message.author.id]
            time_elapsed = current_time - last_request_time
            
            # If less than the cooldown period has passed, deny the request
            if time_elapsed < COOLDOWN_PERIOD:
                remaining_time = COOLDOWN_PERIOD - time_elapsed
                await message.channel.send(f"❌ You must wait {int(remaining_time // 3600)} hours and {int((remaining_time % 3600) // 60)} minutes before requesting another key.")
                return
        
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
                
                # Update the cooldown for the user
                user_cooldowns[message.author.id] = current_time
            except discord.Forbidden:
                await message.channel.send("❌ I can't DM you. Please allow DMs.")
        else:
            await message.channel.send("❌ Failed to update the key file on GitHub.")

bot.run(DISCORD_BOT_TOKEN)

