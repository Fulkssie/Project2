from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Upset(Base):
    __tablename__ = "Upsets"

    Id = Column(Integer, primary_key=True, autoincrement=True)
    Winner = Column(String, nullable=False)
    Loser = Column(String, nullable=False)
    WinnerSeed = Column(Integer, nullable=False)
    LoserSeed = Column(Integer, nullable=False)
    UpsetFactor = Column(Integer, nullable=False)
    Tournament = Column(String, nullable=False)
    WinnerScore = Column(Integer, nullable=False)
    LoserScore = Column(Integer, nullable=False)