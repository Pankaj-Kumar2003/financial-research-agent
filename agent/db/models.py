from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class ResearchBrief(Base):
    __tablename__ = "research_briefs"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), index=True, nullable=False)
    company_name = Column(String(100), nullable=True)
    summary = Column(Text, nullable=True)
    full_report = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sources = relationship("Source", back_populates="brief", cascade="all, delete-orphan")

class Source(Base):
    __tablename__ = "sources"
    
    id = Column(Integer, primary_key=True, index=True)
    brief_id = Column(Integer, ForeignKey("research_briefs.id"), nullable=False)
    source_type = Column(String(50), nullable=False)  # SEC, News, YahooFinance
    title = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    content_snippet = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    brief = relationship("ResearchBrief", back_populates="sources")

class Query(Base):
    __tablename__ = "queries"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), index=True, nullable=False)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), index=True, nullable=False)
    total_latency_seconds = Column(Float, nullable=False)
    llm_latency_seconds = Column(Float, default=0.0)
    tool_latency_seconds = Column(Float, default=0.0)
    total_tokens = Column(Integer, default=0)
    estimated_cost_usd = Column(Float, default=0.0)
    error_count = Column(Integer, default=0)
    source_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

