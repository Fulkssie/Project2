from pydantic import BaseModel

class SetModel(BaseModel):
    Id: int
    Winner: str
    Loser: str
    WinnerSeed: int
    LoserSeed: int
    Tournament: str
    WinnerScore: int
    LoserScore: int

    class Config:
        from_attributes = True