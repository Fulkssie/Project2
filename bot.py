import os
import discord
import requests
import asyncio
import aiohttp
# import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")
CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL"))
AUTHTOKEN = os.getenv("API_KEY")
SLUG = os.getenv("EVENT_SLUG")

# Validate API key
if not AUTHTOKEN:
    raise ValueError("API_KEY environment variable not set")

# API Configuration
API_VERSION = "alpha"
URL = f"https://api.start.gg/gql/{API_VERSION}"
HEADERS = {
    "Authorization": f"Bearer {AUTHTOKEN}",
    "Content-Type": "application/json",
}
PER_PAGE = 50

# Seed Placement Rank (SPR) Mapping
SPR_DICT = {
    **{i: i - 1 for i in range(1, 5)},
    **{i: 4 for i in range(5, 7)},
    **{i: 5 for i in range(7, 9)},
    **{i: 6 for i in range(9, 13)},
    **{i: 7 for i in range(13, 17)},
    **{i: 8 for i in range(17, 25)},
    **{i: 9 for i in range(25, 33)},
    **{i: 10 for i in range(33, 49)},
    **{i: 11 for i in range(49, 65)},
    **{i: 12 for i in range(65, 97)},
    **{i: 13 for i in range(97, 129)},
    **{i: 14 for i in range(129, 193)},
    **{i: 15 for i in range(193, 257)},
    **{i: 16 for i in range(257, 385)}
}

# GraphQL Queries
QUERY_EVENT_ID = '''
query getEventId($slug: String) {
  event(slug: $slug) {
    id
    name
  }
}
'''

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
        lPlacement
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

def fetch_event_id():
    """Fetch the event ID from Start.gg API."""
    response = requests.post(URL, headers=HEADERS, json={"query": QUERY_EVENT_ID, "variables": {"slug": SLUG}})
    data = response.json()
    return data.get("data", {}).get("event", {}).get("id")


def fetch_event_data(event_id):
    """Fetch event details including phase IDs."""
    response = requests.post(URL, headers=HEADERS, json={"query": QUERY_EVENT, "variables": {"eventId": event_id}})

    if response.status_code != 200:
        print(f"Error {response.status_code}: {response.text}")
        return []

    data = response.json()
    if "errors" in data:
        print("Error:", data["errors"])
        return []

    phases = data.get("data", {}).get("event", {}).get("phases", [])
    return [phase["id"] for phase in sorted(phases, key=lambda x: x["phaseOrder"])]

# Cache for storing fetched seeds
SEED_CACHE = {}

async def fetch_init_phase_data(session, phase_id):
    """Fetch initial phase data (seed information) with caching."""
    if phase_id in SEED_CACHE:
        return SEED_CACHE[phase_id]

    all_seeds = []
    page = 1
    retry_delay = 2

    while True:
        try:
            async with session.post(
                URL, headers=HEADERS, json={"query": QUERY_INIT_PHASE, "variables": {"phaseId": phase_id, "page": page, "perPage": PER_PAGE}}
            ) as response:
                if response.status == 429:
                    print(f"Rate limit hit. Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2
                    continue

                if response.status != 200:
                    print(f"Error fetching phase data (Phase {phase_id}, Page {page}): {response.status}")
                    print(await response.text())
                    break

                data = await response.json()
                seeds = data.get("data", {}).get("phase", {}).get("seeds", {}).get("nodes", [])

                if not seeds:
                    break

                all_seeds.extend(seeds)
                page += 1
                retry_delay = 2

        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    SEED_CACHE[phase_id] = {"data": {"phase": {"seeds": {"nodes": all_seeds}}}}
    print(f"Total seeds retrieved: {len(all_seeds)} (cached for future requests)")
    return SEED_CACHE[phase_id]

async def fetch_phase_data(session, phase_ids):
    """Fetch tournament sets data for all phases with rate limiting."""
    all_sets = []

    for phase_id in phase_ids:
        page = 1
        retry_delay = 2

        while True:
            try:
                async with session.post(
                    URL, headers=HEADERS, json={"query": QUERY_PHASES, "variables": {"phaseId": phase_id, "page": page, "perPage": PER_PAGE}}
                ) as response:
                    if response.status == 429:
                        print(f"Rate limit hit for sets. Retrying in {retry_delay} seconds...")
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue

                    if response.status != 200:
                        print(f"Error fetching sets data (Phase {phase_id}, Page {page}): {response.status}")
                        print(await response.text())
                        break

                    data = await response.json()
                    sets = data.get("data", {}).get("phase", {}).get("sets", {}).get("nodes", [])

                    if not sets:
                        break

                    all_sets.extend(sets)
                    page += 1
                    retry_delay = 2

            except Exception as e:
                print(f"Unexpected error: {e}")
                break

    print(f"Total sets retrieved: {len(all_sets)}")
    return all_sets

def calc_spr(seed_num):
    """Calculate Seed Placement Rank (SPR)."""
    return SPR_DICT.get(seed_num, seed_num)

def is_winners_side(round_num):
    """Determine if a match is from Winners or Losers bracket."""
    return "🔵 W: " if round_num > 0 else "🔴 L: "


def calc_upset_factor(winner_seed, loser_seed):
    """Calculate upset factor based on seed difference."""
    return calc_spr(winner_seed) - calc_spr(loser_seed)


def placement_suffix(placement):
    """Determine proper suffix for a placement (e.g., 1st, 2nd, 3rd)."""
    if 11 <= placement <= 13:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(placement % 10, "th")

async def get_upsets(session, init_phase_id, phase_ids):
    """Fetch and process upset data."""
    seed_data = await fetch_init_phase_data(session, init_phase_id)
    phase_data = await fetch_phase_data(session, phase_ids)

    if not seed_data or not phase_data:
        print("Error: Missing seed data or phase data.")
        return None

    seeds_dict = {seed["entrant"]["id"]: seed for seed in seed_data["data"]["phase"]["seeds"]["nodes"]}
    sorted_sets = sorted(phase_data, key=lambda x: x.get("completedAt", 0) or 0, reverse=True)
    dq_message = None

    for match in sorted_sets:
        if not match.get("slots"):
            continue

        if "preview" in str(match.get("id", "")): 
          continue

        loser_placement = match.get("lPlacement", "Unknown")
        winner, loser = None, None

        for slot in match["slots"]:
            if not slot or "entrant" not in slot or slot["entrant"] is None:
                continue

            entrant = slot["entrant"]
            entrant_id = entrant["id"]
            seed_info = seeds_dict.get(entrant_id, {})
            seed_num = seed_info.get("seedNum", "N/A")

            standing = slot.get("standing") or {}
            placement = standing.get("placement", None)
            stats = standing.get("stats") or {}
            score = (stats.get("score") or {}).get("value", "N/A")

            if score == -1:
                dq_message = f"🔴 DQ: {entrant['name']} (Seed {seed_num})"
                return dq_message, None, entrant_id

            if placement == 1:
                winner = (entrant["name"], seed_num, score)
            elif placement == 2:
                loser = (entrant["name"], seed_num, score)

        if winner and loser:
            winner_name, winner_seed, winner_score = winner
            loser_name, loser_seed, loser_score = loser
            upset_factor = calc_upset_factor(winner_seed, loser_seed)

            if upset_factor > 0:
                message = f"{is_winners_side(match['round'])}{winner_name} (Seed {winner_seed}) {winner_score} - {loser_score} {loser_name} (Seed {loser_seed}). Upset Factor: {upset_factor}."
                if message[2] == "L":
                    message += f" Out at {loser_placement}{placement_suffix(loser_placement)}"
                return message, match["id"], None

    return None

async def monitor_upsets(channel):
    """Continuously check for upsets and DQs, ensuring no duplicate messages are sent."""
    sent_upsets = set()
    sent_dqs = set()

    async with aiohttp.ClientSession() as session:
        while True:
            upset_message = await get_upsets(session, init_phase_id, phase_ids)

            if upset_message:
                message, set_id, player_id = upset_message
                
                if set_id is None and player_id not in sent_dqs:
                    sent_dqs.add(player_id)
                    await channel.send(message)
                elif set_id not in sent_upsets and set_id is not None:
                    sent_upsets.add(set_id)
                    print(sent_upsets)
                    await channel.send(message)

            await asyncio.sleep(3)
# Initialize Discord bot
intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    """Handle bot connection to Discord."""
    guild = discord.utils.get(client.guilds, name=GUILD)
    channel = client.get_channel(CHANNEL_ID)

    global event_id, phase_ids, init_phase_id
    event_id = fetch_event_id()
    phase_ids = fetch_event_data(event_id)
    init_phase_id = phase_ids[0] if phase_ids else None

    if channel:
        client.loop.create_task(monitor_upsets(channel))

    print(f'{client.user} has connected to: {guild.name} (id: {guild.id})')

@client.event
async def on_disconnect():
    print("Bot disconnected!")
    if hasattr(client, 'session') and not client.session.closed:
        await client.session.close()
        print("Session closed.")

'''
@client.event
async def on_message(message):
  emotes_dict = {}
  if message.author == client.user:
      return
  
  if "side bracket" in lower(message.content()):
      emotes = message.emojis

      for emote in emotes:
          key = 1
          emotes_dict[key] = emote.name
          key += 1

      rng = random.randint(1, len(emotes_dict))
      await message.add_reaction(emotes_dict[rng])
'''

# Run the bot
client.run(TOKEN)