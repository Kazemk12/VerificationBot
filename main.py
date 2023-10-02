import requests
import discord
import asyncio
from discord.ext import commands, tasks


HYPIXEL = '0919a174-6fba-43ec-a815-8bbb8366cffc'
DISCORD = 'ODA3NDkxMDMzMDQyMjU1OTMz.G84qZg.wtxW7okpeyyXz2YGXyhe6XHYOes1lGSdlprtCE'


def findUUID(name):
    try:
        response = requests.get("https://playerdb.co/api/player/minecraft/" + name)
        response.raise_for_status()  # Raise an exception if the request fails
        data = response.json()

        if 'data' in data and 'player' in data['data']:
            return data['data']['player']['id']
        else:
            return None  # Player data not found in the response
    except Exception as e:
        print(f"Error fetching player data: {e}")
        return None  # Handle the error gracefully
    

# Check if the user's Discord username is linked to the Minecraft username
def isDiscordLinked(playerUUID, discord_username):
    header = {
        "key": HYPIXEL,
        "uuid": playerUUID
    }

    response = requests.get("https://api.hypixel.net/player", params=header)
    data = response.json()

    if 'player' in data and 'socialMedia' in data['player']:
        player = data['player']['socialMedia']['links']
        linked_discord_username = player.get('DISCORD', None)
        
        if linked_discord_username:
            if linked_discord_username.lower() == discord_username.lower():
                return True, "Discord usernames match."
            else:
                return False, "Discord usernames do not match."
        else:
            return False, "Discord username not found in social media links."
    else:
        return False, "Error: Player not found, Make sure your hypixel link is the same as you discord username."

TOKEN = DISCORD
GUILD_ID = 901063590428147732  # Replace with your server's ID
ROLE_ID = 1158432723669635082  # Replace with your role's ID
VERIFICATION_CHANNEL_ID = 1158449777034403920
USER_ID_TO_EXCLUDE = 683558944479903811

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')
    cleanup_messages.start()
    
@tasks.loop(seconds=5)
async def cleanup_messages():
    guild = client.get_guild(GUILD_ID)
    channel = guild.get_channel(VERIFICATION_CHANNEL_ID)

    if channel:
        async for message in channel.history(limit=None):
            # Check if the message author's ID is not the one to exclude
            if message.author.id != USER_ID_TO_EXCLUDE:
                await message.delete()
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!verify'):
        # Split the message content into arguments
        args = message.content.split()[1:]
        
        if len(args) != 1:
            await message.channel.send('Invalid usage. Please use the command as follows: `!verify <Minecraft_username>`')
            return

        minecraft_username = args[0].lower()
        playerUUID = findUUID(minecraft_username)
        
        # Refresh the guild's member cache by fetching members
        guild = client.get_guild(GUILD_ID)
        member_list = [member async for member in guild.fetch_members(limit=None)]

        result, message_text = isDiscordLinked(playerUUID, message.author.name.lower())
        response_message = await message.channel.send(message_text)

        if result:
            member = next((m for m in member_list if m.id == message.author.id), None)

            if member:
                # Add a role
                role = discord.utils.get(guild.roles, id=ROLE_ID)
                if role:
                    await member.add_roles(role)

                # Change nickname
                await member.edit(nick=minecraft_username)
            else:
                await message.channel.send("Could not find the member in the guild.")
        
        # Delete the command message and the bot's reply message after a delay
        await asyncio.sleep(0)  # Adjust the delay time as needed
        await message.delete()
        await response_message.delete()
client.run(TOKEN)
