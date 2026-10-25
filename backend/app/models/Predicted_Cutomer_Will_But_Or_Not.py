from sqlalchemy import Column, Integer, Float
from app.core.database import Base



class Predicte_Customer_Will_Buy_Or_Not(Base):
    __tablename__ = "Predicte_Customer_Will_Buy_Or_Not"

    id = Column(Integer, primary_key=True)
    previous_purchases = Column(Integer)
    previous_visits = Column(Integer)
    avg_time = Column(Float)
    avg_pages = Column(Integer)
      
    purchased_next_visit = Column(Integer, nullable=True)

    prediction = Column(Integer, nullable=True)
    probability = Column(Float, nullable=True)