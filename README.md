# Tournament Upset Tracker
This is a full-stack application for tracking competitive match upsets in tournaments using a FastAPI backend and a Discord bot frontend. The backend manages set data and calculates upset factors based on player seeds, while the bot allows users to interact with this data directly from Discord using slash commands.

📦 Features
🧠 FastAPI Backend
Store match data (winner, loser, scores, seeds, tournament).

Calculate and return Upset Factor based on a Seed Placement Rank (SPR) model.

RESTful API endpoints to:

Create, read, update, delete sets

Query sets by winner, loser, or tournament.

🤖 Discord Bot
Slash commands for:

Getting a set by ID

Listing sets by winner, loser, or tournament

Adding, deleting, and updating sets

Fetches data directly from the FastAPI backend.

🔧 Setup Instructions
1. Clone the Repository
bash
Copy
Edit
git clone https://github.com/yourusername/tournament-upset-tracker.git
cd tournament-upset-tracker
⚙️ Backend (FastAPI)
🔌 Requirements
bash
Copy
Edit
pip install fastapi uvicorn sqlalchemy pydantic
📂 File Structure
main.py: FastAPI app with endpoints

dbModels.py: SQLAlchemy models (must include Upset and Base)

apiModels.py: Pydantic schema (SetModel)

upsets.db: SQLite DB file (auto-created)

🚀 Run the Backend
bash
Copy
Edit
uvicorn main:app --reload
The API will be live at http://localhost:8000.

You can test endpoints via Swagger: http://localhost:8000/docs

🤖 Discord Bot
🔌 Requirements
bash
Copy
Edit
pip install discord.py python-dotenv requests
🔐 Environment Variables
Create a .env file in the root directory:

env
Copy
Edit
DISCORD_TOKEN=your_discord_bot_token_here
DISCORD_GUILD=your_guild_id_here
DISCORD_CHANNEL=your_channel_id_here
URL=http://localhost:8000
You can also use .env.example as a template.

▶️ Run the Bot
bash
Copy
Edit
python bot.py
🧮 Upset Factor Calculation
The Upset Factor is calculated by mapping each seed to a Seed Placement Rank (SPR). A larger difference between the SPR of the winner and the loser indicates a bigger upset.

Example logic:

Seed 1 → SPR 0

Seed 10 → SPR 6

Seed 50 → SPR 11
If seed 50 beats seed 10 → Upset Factor = 11 - 6 = 5

The mapping logic is defined in a Python dictionary in the FastAPI code.

🧪 Example Usage in Discord
bash
Copy
Edit
/set 1
→ Returns set with ID 1

bash
Copy
Edit
/sets-winner Mango
→ Returns all sets where Mango is the winner

bash
Copy
Edit
/add-set id=5 winner=Zain loser=Leffen winner_seed=5 loser_seed=2 tournament=Genesis10 winner_score=3 loser_score=1
→ Adds a new set to the database

📎 Notes
This is designed for offline/local use by default. To deploy publicly, make sure to:

Use a production database

Enable HTTPS

Secure the API with authentication

📜 License
MIT License

