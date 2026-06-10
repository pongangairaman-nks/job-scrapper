from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from database import Base


class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False)
    added_at = Column(DateTime, default=datetime.utcnow)
    jobs = relationship("Job", back_populates="company", cascade="all, delete-orphan")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String, nullable=False)
    url = Column(String, default="")
    source = Column(String, default="unknown")
    found_at = Column(DateTime, default=datetime.utcnow)
    emailed = Column(Boolean, default=False)
    company = relationship("Company", back_populates="jobs")
