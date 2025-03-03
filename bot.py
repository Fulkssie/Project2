import os
import discord
from dotenv import load_dotenv
import requests
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL = int(os.getenv('DISCORD_CHANNEL')) 
AUTHTOKEN  = os.getenv('API_KEY')
EVENT = os.getenv('EVENT_ID')

client = discord.Client(intents=discord.Intents.default())

if not AUTHTOKEN:
    raise ValueError('API_KEY environment variable not set')
apiVersion = 'alpha'

eventId = EVENT
perPage = 50
url = "https://api.start.gg/gql/{apiVersion}".format(apiVersion=apiVersion)

headers = {
    "Authorization": f"Bearer {AUTHTOKEN}",
    "Content-Type": "application/json"
}

sprDict = {
  1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 4, 7: 5, 8: 5, 9: 6, 10: 6,
  11: 6, 12: 6, 13: 7, 14: 7, 15: 7, 16: 7, 17: 8, 18: 8, 19: 8,
  20: 8, 21: 8, 22: 8, 23: 8, 24: 8, 25: 9, 26: 9, 27: 9, 28: 9,
  29: 9, 30: 9, 31: 9, 32: 9, 33: 10, 34: 10, 35: 10, 36: 10, 37: 10,
  38: 10, 39: 10, 40: 10, 41: 10, 42: 10, 43: 10, 44: 10, 45: 10, 46: 10,
  47: 10, 48: 10, 49: 11, 50: 11, 51: 11, 52: 11, 53: 11, 54: 11, 55: 11,
  56: 11, 57: 11, 58: 11, 59: 11, 60: 11, 61: 11, 62: 11, 63: 11, 64: 11,
}

queryEvent = '''
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

variablesEvent = {"eventId": eventId}
response = requests.post(url, headers=headers, json={"query": queryEvent, "variables": variablesEvent})

phaseIds = []
if response.status_code == 200:
    eventData = response.json()
    if 'errors' in eventData:
        print('Error:')
        print(eventData['errors'])
    elif not eventData['data']['event']:
        print('Event not found')
    else:
        event = eventData['data']['event']
        phase = eventData['data']['event']['phases']
        phaseIds = [x['id'] for x in sorted(phase, key=lambda x: x['phaseOrder'])]
        initialPhase = min(phase, key=lambda x: x['phaseOrder'], default=None)
        initphaseId = initialPhase['id'] if initialPhase else None
else:
    print(f"Error {response.status_code}: {response.text}")

queryInitPhase = '''
query Phase($phaseId: ID!, $page: Int!, $perPage: Int!) {
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
  }
}
'''

variablesInitPhase = {"phaseId": initphaseId, "page": 1, "perPage": perPage}

queryPhases ='''
query Phase($phaseId: ID!, $page: Int!, $perPage: Int!) {
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
        completedAt
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

def fetchInitPhaseData():
    initPhaseData = requests.post(url, headers=headers, json={"query": queryInitPhase, "variables": variablesInitPhase})
    if initPhaseData.status_code == 200:
        initPhaseData = initPhaseData.json()
        if 'errors' in initPhaseData:
            print('Error:')
            print(initPhaseData['errors'])
            return None
        elif not initPhaseData['data']['phase']:
            print('Phase not found')
            return None
        return initPhaseData

def fetchData():
    allSets = []
    for phaseId in phaseIds:
        variablesPhases = {"phaseId": phaseId, "page": 1, "perPage": perPage}
        response = requests.post(url, headers=headers, json={"query": queryPhases, "variables": variablesPhases})
        if response.status_code == 200:
            phaseData = response.json()
            if 'errors' in phaseData:
                print('Error:')
                print(phaseData['errors'])
                return None
            elif not phaseData['data']['phase']:
                print('Phase not found')
                return None
            allSets.extend(phaseData['data']['phase']['sets']['nodes'])
        else:
            print(f"Error {response.status_code}: {response.text}")
    return {"sets": allSets} if allSets else None
            

def calcSPR(seedNum):
    if seedNum in sprDict:
        return sprDict[seedNum]
    else:
        return seedNum

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
    seedData = fetchInitPhaseData()
    data = fetchData()
    if not seedData:
        return None
    if not data:
        return None

    combinedData = {}
    if 'errors' in seedData or 'errors' in data:
        print('Error:')
        print(seedData['errors'])
        print(data['errors'])
        return None
    elif not seedData['data']['phase'] or not data:
        print('Phase not found')
        return None

    seedings = seedData['data']['phase']['seeds']['nodes']
    sets = data['sets']
    seedsDict = {seed['entrant']['id']: seed for seed in seedings}

    for set in sets:
        setId = set['id']
        roundNum = set['round']
        completedAt = set.get('completedAt', 0)

        combinedData[setId] = {
            'setId': setId,
            'round': roundNum,
            'completedAt': completedAt,
            'slots': [],
            'winner': None,
            'loser': None
        }

        setWinner = None
        setLoser = None
        for slot in set['slots']:
            entrant = slot.get('entrant')
            if not entrant:
                continue
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


    sorted_sets = sorted(combinedData.items(), key=lambda x: x[1].get('completedAt', 0)or 0, reverse=True)
    
    for setId, setInfo in sorted_sets:
        if setInfo['winner']:
            winnerSeed = setInfo['winner']['seedNum']
            for slot in setInfo['slots']:
                if slot['entrantId'] != setInfo['winner']['entrantId']:
                    loserSeed = slot['seedNum']
                    UF = calcUF(winnerSeed, loserSeed)
                    isWinners = isWinnersSide(setInfo['round'])
                    if winnerSeed > loserSeed:
                        message = (f"{isWinners}{setInfo['winner']['entrantName']} (Seed {winnerSeed}) {setInfo['winner']['stats']['score']['value']} - {setInfo['loser']['stats']['score']['value']} {setInfo['loser']['entrantName']} (Seed {loserSeed}). Upset Factor: {UF}")
                        return message, setInfo['setId']
    return None

sentUpsets = set()
async def monitorUpsets(channel):
    global sentUpsets
    while True:
        message = getUpsets()[0]
        setId = getUpsets()[1]
        if setId in sentUpsets:
            return
        else:
            sentUpsets.add(setId)
            await channel.send(message)
        await asyncio.sleep(10)


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break
    channel = client.get_channel(CHANNEL)
    
    if channel:
        client.loop.create_task(monitorUpsets(channel))

    print(
        f'{client.user} has connected to the following guild:\n'
        f'{guild.name}(id: {guild.id})'
    )
client.run(TOKEN)