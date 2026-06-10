from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship
from database import Base

DEFAULT_ROLES = [
    "frontend developer",
    "frontend engineer",
    "ui engineer",
    "ux engineer",
    "senior frontend",
    "react developer",
    "react engineer",
    "javascript developer",
    "javascript engineer",
    "next.js developer",
    "vue developer",
    "angular developer",
    "web developer",
    "ui developer",
]


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
    location = Column(String, default="")
    work_mode = Column(String, default="")    # remote | hybrid | on-site
    work_type = Column(String, default="")    # full-time | part-time | contract | internship
    experience = Column(String, default="")   # entry | mid | senior
    found_at = Column(DateTime, default=datetime.utcnow)
    emailed = Column(Boolean, default=False)
    company = relationship("Company", back_populates="jobs")


class Preferences(Base):
    __tablename__ = "preferences"

    id = Column(Integer, primary_key=True, default=1)
    roles = Column(JSON, default=lambda: list(DEFAULT_ROLES))
    locations = Column(JSON, default=list)    # empty = any location
    experience = Column(JSON, default=list)   # empty = any; values: entry | mid | senior
    work_type = Column(JSON, default=list)    # empty = any; values: full-time | part-time | contract | internship
    work_mode = Column(JSON, default=list)    # empty = any; values: remote | hybrid | on-site
    salary_min = Column(Integer, nullable=True)
    salary_max = Column(Integer, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow)
