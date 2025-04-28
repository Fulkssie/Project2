import requests
import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
CHANNEL_ID = os.getenv("DISCORD_CHANNEL")
URL = os.getenv("URL")

# Initialize the bot with command prefix
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='/', intents=intents)

# Slash command to get set by Id
@bot.tree.command(name="set", description="Get a set by Id")
async def upset(interaction: discord.Interaction, id: int):
    response = requests.get(f"{URL}/sets/{id}")
    if response.status_code != 200:
        await interaction.response.send_message("Set not found.")
        return

    data = response.json()  # Correctly call json() here
    message = (
        f"**{data['Tournament']}**:\n"
        f"{data['Winner']} (Seed: {data['WinnerSeed']}) "
        f"{data['WinnerScore']} - {data['LoserScore']} "
        f"{data['Loser']} (Seed: {data['LoserSeed']})\n"
        f"Upset Factor: {data['UpsetFactor']}"
    )
    await interaction.response.send_message(message)

@bot.tree.command(name="sets-winner", description="Get all sets by winner")
async def sets_winner(interaction: discord.Interaction, winner: str):
    response = requests.get(f"{URL}/sets/winner/{winner}")
    if response.status_code != 200:
        await interaction.response.send_message("Sets not found.")
        return
    
    data = response.json()
    if not data:
        await interaction.response.send_message(f"No sets found for **{winner}**.")
        return
    
    lines = []
    for set in data:
        lines.append(
            f"**{set['Tournament']}**:\n"
            f"{set['Winner']} (Seed: {set['WinnerSeed']}) "
            f"{set['WinnerScore']} - {set['LoserScore']} "
            f"{set['Loser']} (Seed: {set['LoserSeed']})\n"
            f"Upset Factor: {set['UpsetFactor']}"
        )
    message = "\n".join(lines)
    await interaction.response.send_message(message)

@bot.tree.command(name="sets-loser", description="Get all sets by loser")
async def sets_loser(interaction: discord.Interaction, loser: str):
    response = requests.get(f"{URL}/sets/loser/{loser}")
    if response.status_code != 200:
        await interaction.response.send_message("Sets not found.")
        return
    
    data = response.json()
    if not data:
        await interaction.response.send_message(f"No sets found for **{loser}**.")
        return
    
    lines = []
    for set in data:
        lines.append(
            f"**{set['Tournament']}**:\n"
            f"{set['Winner']} (Seed: {set['WinnerSeed']}) "
            f"{set['WinnerScore']} - {set['LoserScore']} "
            f"{set['Loser']} (Seed: {set['LoserSeed']})\n"
            f"Upset Factor: {set['UpsetFactor']}"
        )
    message = "\n".join(lines)
    await interaction.response.send_message(message)

@bot.tree.command(name="sets-tournament", description="Get all sets from a tournament")
async def sets_tournament(interaction: discord.Interaction, tournament:str):
    response = requests.get(f"{URL}/sets/tournament/{tournament}")
    if response.status_code != 200:
        await interaction.response.send_message("Sets not found")
        return
    
    data = response.json()
    if not data:
        await interaction.response.send_message(f"No sets found for {tournament}.")
        return
    
    lines = []
    for set in data:
        lines.append(
            f"**{set['Tournament']}**:\n"
            f"{set['Winner']} (Seed: {set['WinnerSeed']}) "
            f"{set['WinnerScore']} - {set['LoserScore']} "
            f"{set['Loser']} (Seed: {set['LoserSeed']})\n"
            f"Upset Factor: {set['UpsetFactor']}"
        )
    message = "\n".join(lines)
    await interaction.response.send_message(message)

@bot.tree.command(name="add-set", description="Add a set to the database")
async def add_set(interaction: discord.Interaction,
    id: int,
    winner: str,
    loser: str,
    winner_seed: int,
    loser_seed: int,
    tournament: str,
    winner_score: int,
    loser_score: int
):  
    payload = {
        "Id": id,
        "Winner": winner,
        "Loser": loser,
        "WinnerSeed": winner_seed,
        "LoserSeed": loser_seed,
        "Tournament": tournament,
        "WinnerScore": winner_score,
        "LoserScore": loser_score
    }

    response = requests.post(f"{URL}/sets/", json=payload)
    if response.status_code == 200:
        await interaction.response.send_message("Set Added")
    else:
        await interaction.response.send_message("Error Adding Set")

@bot.tree.command(name="delete-set", description="Delete a set from the database")
async def delete_set(interaction: discord.Interaction, id: int):
    response = requests.delete(f"{URL}/sets/{id}")
    if response.status_code == 200:
        await interaction.response.send_message("Set Deleted")
    else:
        await interaction.response.send_message("Error Deleting Set")

@bot.tree.command(name="update-set", description="Update a set in the database")
async def update_set(interaction: discord.Interaction,
    id: int,
    winner: str,
    loser: str,
    winner_seed: int,
    loser_seed: int,
    tournament: str,
    winner_score: int,
    loser_score: int
):
    payload = {
        "Id": id,
        "Winner": winner,
        "Loser": loser,
        "WinnerSeed": winner_seed,
        "LoserSeed": loser_seed,
        "Tournament": tournament,
        "WinnerScore": winner_score,
        "LoserScore": loser_score
    }
    response = requests.put(f"{URL}/sets/{id}", json=payload)
    if response.status_code == 200:
        await interaction.response.send_message("Set Updated")
    else:
        await interaction.response.send_message("Error Updating Set")

# Sync the slash commands with Discord
@bot.event
async def on_ready():
    # Make sure to sync commands with Discord when the bot starts
    await bot.tree.sync()
    print(f'{bot.user} has connected to Discord!')

# Run the bot
bot.run(TOKEN)