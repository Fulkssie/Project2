# Prettified by ChatGPT

import os
import discord
from dotenv import load_dotenv
import requests
import asyncio
import aiohttp

# Load environment variables
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = int(os.getenv('DISCORD_CHANNEL'))
AUTHTOKEN = os.getenv('API_KEY')
EVENT = os.getenv('EVENT_ID')

# Initialize Discord client
client = discord.Client(intents=discord.Intents.default())

# Validate API key
if not AUTHTOKEN:
    raise ValueError('API_KEY environment variable not set')

# API Configuration
API_VERSION = 'alpha'
URL = f"https://api.start.gg/gql/{API_VERSION}"
HEADERS = {
    "Authorization": f"Bearer {AUTHTOKEN}",
    "Content-Type": "application/json"
}
PER_PAGE = 50

# Seed Placement Rank (SPR) Mapping
SPR_DICT = {i: min(11, (i - 1) // 4) for i in range(1, 65)}

# GraphQL Queries
QUERY_EVENT = '''
query Event($eventId: ID!) {
  event(id: $eventId) {
    id
    name
    phases {
      id
      name
      phaseOrder
    }
  }
}
'''

QUERY_INIT_PHASE = '''
query Phase($phaseId: ID!, $page: Int!, $perPage: Int!) {
  phase(id: $phaseId) {
    id
    seeds(query: {page: $page, perPage: $perPage}) {
      nodes {
        id
        seedNum
        entrant {
          id
          participants {
            id
            gamerTag
          }
        }
      }
    }
  }
}
'''

QUERY_PHASES = '''
query Phase($phaseId: ID!, $page: Int!, $perPage: Int!) {
  phase(id: $phaseId) {
    id
    sets(page: $page, perPage: $perPage, sortType: STANDARD) {
      nodes {
        id
        round
        completedAt
        slots {
          entrant {
            id
            name
          }
          standing {
            placement
            stats {
              score {
                value
              }
            }
          }
        }
      }
    }
  }
}
'''

# Fetch event data
variables_event = {"eventId": EVENT}
response = requests.post(URL, headers=HEADERS, json={"query": QUERY_EVENT, "variables": variables_event})

phase_ids = []
if response.status_code == 200:
    event_data = response.json()
    if 'errors' in event_data:
        print("Error:", event_data['errors'])
    elif event_data['data']['event']:
        phases = event_data['data']['event']['phases']
        phase_ids = [phase['id'] for phase in sorted(phases, key=lambda x: x['phaseOrder'])]
        init_phase_id = phase_ids[0] if phase_ids else None
else:
    print(f"Error {response.status_code}: {response.text}")

# Async functions for fetching data
async def fetch_init_phase_data():
    """Fetch initial phase data (seed information)."""
    async with aiohttp.ClientSession() as session:
        async with session.post(URL, headers=HEADERS, json={"query": QUERY_INIT_PHASE, "variables": {"phaseId": init_phase_id, "page": 1, "perPage": PER_PAGE}}) as response:
            if response.status == 200:
                return await response.json()
            print(f"Error {response.status}: {await response.text()}")
            return None

async def fetch_phase_data():
    """Fetch tournament sets data for all phases."""
    all_sets = []
    async with aiohttp.ClientSession() as session:
        for phase_id in phase_ids:
            async with session.post(URL, headers=HEADERS, json={"query": QUERY_PHASES, "variables": {"phaseId": phase_id, "page": 1, "perPage": PER_PAGE}}) as response:
                if response.status == 200:
                    phase_data = await response.json()
                    if 'errors' not in phase_data and phase_data['data']['phase']:
                        all_sets.extend(phase_data['data']['phase']['sets']['nodes'])
                else:
                    print(f"Error {response.status}: {await response.text()}")
    return {"sets": all_sets} if all_sets else None

# Utility functions
def calc_spr(seed_num):
    """Calculate Seed Placement Rank (SPR)."""
    return SPR_DICT.get(seed_num, seed_num)

def is_winners_side(round_num):
    """Determine if a match is from Winners or Losers bracket."""
    return "🔵 W: " if round_num > 0 else "🔴 L: "

def calc_upset_factor(winner_seed, loser_seed):
    """Calculate upset factor based on seed difference."""
    return calc_spr(winner_seed) - calc_spr(loser_seed)

# Fetch and process upset data
async def get_upsets():
    seed_data = await fetch_init_phase_data()
    phase_data = await fetch_phase_data()

    if not seed_data or not phase_data:
        return None

    seeds_dict = {seed['entrant']['id']: seed for seed in seed_data['data']['phase']['seeds']['nodes']}
    sets = phase_data['sets']
    sorted_sets = sorted(sets, key=lambda x: x.get('completedAt', 0) or 0, reverse=True)

    for match in sorted_sets:
        if not match['slots']:
            continue

        winner, loser = None, None
        for slot in match['slots']:
            entrant = slot.get('entrant')
            if not entrant:
                continue
            entrant_id = entrant['id']
            seed_info = seeds_dict.get(entrant_id, {})
            seed_num = seed_info.get('seedNum', 'N/A')
            placement = slot.get('standing', {}).get('placement')
            stats = slot.get('standing', {}).get('stats', {})
            score = stats.get('score', {}).get('value', 'N/A')

            if placement == 1:
                winner = (entrant['name'], seed_num, score)
            elif placement == 2:
                loser = (entrant['name'], seed_num, score)

        if winner and loser:
            winner_name, winner_seed, winner_score = winner
            loser_name, loser_seed, loser_score = loser
            upset_factor = calc_upset_factor(winner_seed, loser_seed)

            if winner_seed > loser_seed:
                message = f"{is_winners_side(match['round'])}{winner_name} (Seed {winner_seed}) {winner_score} - {loser_score} {loser_name} (Seed {loser_seed}). Upset Factor: {upset_factor}"
                return message, match['id']

    return None

# Upset monitoring system
sent_upsets = set()

async def monitor_upsets(channel):
    """Continuously check for upsets and send messages to Discord."""
    global sent_upsets
    while True:
        upset_message = await get_upsets()
        if upset_message:
            message, set_id = upset_message
            if set_id not in sent_upsets:
                sent_upsets.add(set_id)
                await channel.send(message)
        await asyncio.sleep(10)

# Discord event handlers
@client.event
async def on_ready():
    """Handle bot connection to Discord."""
    client.session = aiohttp.ClientSession()
    guild = discord.utils.get(client.guilds, name=GUILD)
    channel = client.get_channel(CHANNEL)

    if channel:
        client.loop.create_task(monitor_upsets(channel))

    print(f'{client.user} has connected to: {guild.name} (id: {guild.id})')

@client.event
async def on_disconnect():
    """Ensure the session is closed when the bot disconnects."""
    if client.session:
        await client.session.close()

# Run the bot
client.run(TOKEN)