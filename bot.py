import os
import discord
from dotenv import load_dotenv
import requests
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
authToken = os.getenv('API_KEY')

client = discord.Client(intents=discord.Intents.default())

if not authToken:
    raise ValueError('API_KEY environment variable not set')
apiVersion = 'alpha'

phaseId = 1899514
perPage = 70
url = "https://api.start.gg/gql/{apiVersion}".format(apiVersion=apiVersion)

headers = {
    "Authorization": f"Bearer {authToken}",
    "Content-Type": "application/json"
}

sprDict = {
  1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 5, 8: 5, 9: 6, 10: 6,
  11: 6, 12: 6, 13: 7, 14: 7, 15: 7, 16: 7, 17: 8, 18: 8, 19: 8,
  20: 8, 21: 8, 22: 8, 23: 8, 24: 8, 25: 9, 26: 9, 27: 9, 28: 9,
  29: 9, 30: 9, 31: 9, 32: 9
}

query ='''
query PhaseSeeds($phaseId: ID!, $page: Int!, $perPage: Int!) {
  phase(id: $phaseId) {
    id
    seeds(query: {page: $page, perPage: $perPage}) {
      pageInfo {
        total
        totalPages
      }
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
    sets(page: $page, perPage: $perPage, sortType: STANDARD) {
      pageInfo {
        total
      }
      nodes {
        id
        round
        slots {
          id
          entrant {
            id
            name
          }
          standing {
            placement
            stats {
              score {
                label
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

variables = {
  "phaseId": phaseId,
  "page": 1,
  "perPage": perPage
}

response = requests.post(url, headers=headers, json={"query": query, "variables": variables})

if response.status_code == 200:
  resData = response.json()
else:
  print(f"Error {response.status_code}: {response.text}")

def calcSPR(seedNum):
    if seedNum in sprDict:
        return sprDict[seedNum]
    else:
        return seedNum

if 'errors' in resData:
    print('Error:')
    print(resData['errors'])
elif not resData['data']['phase']:
    print('Phase not found')
else:
    seedings = resData['data']['phase']['seeds']['nodes']
    sets = resData['data']['phase']['sets']['nodes']
    
    seedsDict = {seed['entrant']['id']: seed for seed in seedings}

    combinedData = {}
    for set in sets:
        setId = set['id']
        roundNum = set['round']
        combinedData[setId] = {
            'setId': setId,
            'round': roundNum,
            'slots': [],
            'winner': None,
            'loser': None
        }
        setWinner = None
        setLoser = None
        for slot in set['slots']:
            entrant = slot['entrant']
            if entrant:
                entrantId = entrant['id']
                seedInfo = seedsDict.get(entrantId, {})
                slotData = {
                    'entrantId': entrantId,
                    'entrantName': entrant['name'],
                    'seedNum': seedInfo.get('seedNum', 'N/A'),
                    'gamerTag': seedInfo.get('entrant', {}).get('participants', [{}])[0].get('gamerTag', 'N/A'),
                    'placement': slot['standing']['placement'] if slot['standing'] else 'N/A',
                    'stats': slot['standing']['stats'] if slot['standing'] and slot['standing'].get('stats') else {}
                }
                combinedData[setId]['slots'].append(slotData)
                if slot['standing'] and slot['standing']['placement'] == 1:
                    setWinner = slotData
                elif slot['standing'] and slot['standing']['placement'] == 2:
                    setLoser = slotData
        combinedData[setId]['winner'] = setWinner
        combinedData[setId]['loser'] = setLoser

def isWinnersSide(roundNum):
    if roundNum > 0:
        return "\U0001F535 W: "
    else:
        return "\U0001F534 L: "
    
def calcUF(winnerSeed, loserSeed):
  winnerSpr = calcSPR(winnerSeed)
  loserSpr = calcSPR(loserSeed)

  UF = winnerSpr - loserSpr
  return(UF)

def getUpsets():
    for setId, setInfo in combinedData.items():
        if setInfo['winner']:
            winnerSeed = setInfo['winner']['seedNum']
            for slot in setInfo['slots']:
                if slot['entrantId'] != setInfo['winner']['entrantId']:
                    loserSeed = slot['seedNum']
                    UF = calcUF(winnerSeed, loserSeed)
                    isWinners = isWinnersSide(setInfo['round'])
                    if winnerSeed > loserSeed:
                        message = (f"{isWinners}{setInfo['winner']['entrantName']} (Seed {winnerSeed}) {setInfo['winner']['stats']['score']['value']} - {setInfo['loser']['stats']['score']['value']} {setInfo['loser']['entrantName']} (Seed {loserSeed}). Upset Facor: {UF}")
                        return message

lastUpset = None
async def monitorUpsets(channel):
    global lastUpset
    while True:
        message = getUpsets()
        if message and message != lastUpset:
            await channel.send(message)
            lastUpset = message
        await asyncio.sleep(10)

@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break
    channel = client.get_channel(1253590577598038029)
    
    if channel:
        client.loop.create_task(monitorUpsets(channel))

    print(
        f'{client.user} has connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )

client.run(TOKEN)