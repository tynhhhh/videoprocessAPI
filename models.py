from database import Base
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

class OrginalVideos(Base):
    __tablename__ = "OriginalVideos"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

class SubVideos(Base):
    __tablename__ = "SubVideos"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String)
    date = Column(DateTime, default=datetime.utcnow)