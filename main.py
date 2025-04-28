from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dbModels import Base, Upset
from apiModels import SetModel

# Initialize app
app = FastAPI()

# Set up database session
SQLALCHEMY_DATABASE_URL = "sqlite:///./upsets.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(engine)
session = sessionmaker(autocommit=False, autoflush= False, bind=engine)

def getDB():
    db = session()
    try:
        yield db
    finally:
        db.close()

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

def calc_spr(seed_num):
    """Calculate Seed Placement Rank (SPR)."""
    return SPR_DICT[seed_num]

def calc_upset_factor(winner_spr, loser_spr):
    """Calculate upset factor based on seed difference."""
    return winner_spr - loser_spr

@app.get("/sets/{Id}")
async def getsetsAsync(Id: int, db: Session = Depends(getDB)):
    result = db.query(Upset).filter(Upset.Id == Id).first()
    if not result:
        raise HTTPException(status_code=404, detail="Upset not found")
    return result

@app.get("/sets/winner/{Winner}")
async def getsetsbywinnerAsync(Winner: str, db: Session = Depends(getDB)):
    result = db.query(Upset).filter(Upset.Winner == Winner).all()
    if not result:
        raise HTTPException(status_code=404, detail="Upset not found")
    return result

@app.get("/sets/loser/{Loser}")
async def getsetsbyloserAsync(Loser: str, db: Session = Depends(getDB)):
    result = db.query(Upset).filter(Upset.Loser == Loser).all()
    if not result:
        raise HTTPException(status_code=404, detail="Upset not found")
    return result

@app.get("/sets/tournament/{Tournament}")
async def getsetsbywinnerAsync(Tournament: str, db: Session = Depends(getDB)):
    result = db.query(Upset).filter(Upset.Tournament == Tournament).all()
    if not result:
        raise HTTPException(status_code=404, detail="Upset not found")
    return result

@app.post("/sets/")
async def createSetAsync(upset: SetModel, db: Session = Depends(getDB)):
    newUpset = Upset(Id=upset.Id, 
                     Winner=upset.Winner, 
                     Loser=upset.Loser, 
                     WinnerSeed=upset.WinnerSeed, 
                     LoserSeed=upset.LoserSeed, 
                     Tournament=upset.Tournament, 
                     WinnerScore=upset.WinnerScore, 
                     LoserScore=upset.LoserScore)
    
    spr_winner = calc_spr(upset.WinnerSeed)
    spr_loser = calc_spr(upset.LoserSeed)
    newUpset.UpsetFactor = calc_upset_factor(spr_winner, spr_loser)
    db.add(newUpset)
    db.commit()
    db.refresh(newUpset)
    return newUpset

@app.delete("/sets/{Id}")
async def deletePostAsync(Id: int, db: Session = Depends(getDB)):
    upset = db.query(Upset).filter(Upset.Id == Id).first()
    if not upset:
        raise HTTPException(status_code=404, detail="Upset not found")
    db.delete(upset)
    db.commit()
    return {"message": "Upset deleted successfully!"}

@app.put("/sets/{Id}")
async def updatePostAsync(Id: int, upset: SetModel, db: Session = Depends(getDB)):
    set_to_update = db.query(Upset).filter(Upset.Id == Id).first()
    if not set_to_update:
        raise HTTPException(status_code=404, detail="Upset not found")
    
    set_to_update.Id = upset.Id
    set_to_update.Winner = upset.Winner
    set_to_update.Loser = upset.Loser
    set_to_update.WinnerSeed = upset.WinnerSeed
    set_to_update.LoserSeed = upset.LoserSeed
    set_to_update.Tournament = upset.Tournament
    set_to_update.WinnerScore = upset.WinnerScore
    set_to_update.LoserScore = upset.LoserScore

    spr_winner = calc_spr(upset.WinnerSeed)
    spr_loser = calc_spr(upset.LoserSeed)
    set_to_update.UpsetFactor = calc_upset_factor(spr_winner, spr_loser)

    db.commit()
    db.refresh(set_to_update)
    return set_to_update