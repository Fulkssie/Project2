# Tournament Upset Tracker
This is a full-stack application for tracking competitive match upsets in tournaments using a FastAPI backend and a Discord bot frontend. The backend manages set data and calculates upset factors based on player seeds, while the bot allows users to interact with this data directly from Discord using slash commands.

## Features
### FastAPI Backend
- Store match data (winner, loser, scores, seeds, tournament).
- Calculate and return Upset Factor based on a Seed Placement Rank (SPR) model.
- Create, read, update, delete sets
- Query sets by winner, loser, or tournament.

### Discord Bot
- Slash commands for:
  - Getting a set by ID
  - Listing sets by winner, loser, or tournament
  - Adding, deleting, and updating sets
- Fetches data directly from the FastAPI backend.

## File Structure
- main.py: FastAPI app with endpoints
- dbModels.py: SQLAlchemy models (must include Upset and Base)
- apiModels.py: Pydantic schema (SetModel)
- upsets.db: SQLite DB file (auto-created)
- bot.py: Discord client that used the API to pull from the database

## Upset Factor Calculation
The Upset Factor is calculated by mapping each seed to a Seed Placement Rank (SPR). A larger difference between the SPR of the winner and the loser indicates a bigger upset.
SPR - the number of upsets a certain seed needs to win to get 1st place

### Example logic:

Seed 1 → SPR 0

Seed 10 → SPR 6

Seed 50 → SPR 11
If seed 50 beats seed 10 → Upset Factor = 11 - 6 = 5

The mapping logic is defined in a Python dictionary in the FastAPI code.

## Example Usage in Discord

/set 1
→ Returns set with ID 1

/sets-winner Mango
→ Returns all sets where Mango is the winner

/add-set id=5 winner=Zain loser=Leffen winner_seed=5 loser_seed=2 tournament=Genesis10 winner_score=3 loser_score=1
→ Adds a new set to the database

## Notes
This is designed for offline/local use by default. To deploy publicly, make sure to:

- Use a production database
- Enable HTTPS
- Secure the API with authentication
