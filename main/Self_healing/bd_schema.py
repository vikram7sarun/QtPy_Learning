from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class Selector(Base):
    __tablename__ = 'selectors'

    id = Column(Integer, primary_key=True)
    page_name = Column(String)
    element_name = Column(String)
    original_selector = Column(String)
    current_selector = Column(String)
    healing_enabled = Column(Boolean, default=True)
    last_updated = Column(DateTime, default=datetime.utcnow)
    selector_type = Column(String)  # CSS, XPath, etc.
    confidence_score = Column(Float)


class HealingReport(Base):
    __tablename__ = 'healing_reports'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    page_name = Column(String)
    element_name = Column(String)
    failed_selector = Column(String)
    healed_selector = Column(String)
    healing_score = Column(Float)
    screenshot_path = Column(String)
    status = Column(String)
    execution_time = Column(Float)