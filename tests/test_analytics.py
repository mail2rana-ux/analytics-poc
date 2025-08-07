import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..src.database.config import Base
from ..src.models.models import Organization, User, Badge, Course, Enrollment
from ..src.analytics.engine import AnalyticsEngine
from datetime import datetime, timedelta

# Test database
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    
    # Create test data
    org = Organization(name="Test Corp", description="Test Organization")
    session.add(org)
    
    badge1 = Badge(name="Python Test", description="Python Testing")
    badge2 = Badge(name="Data Test", description="Data Testing")
    session.add_all([badge1, badge2])
    
    course1 = Course(name="Python Course", description="Python Course")
    course2 = Course(name="Data Course", description="Data Course")
    session.add_all([course1, course2])
    
    user1 = User(name="Test User 1", email="user1@test.com", organization=org)
    user2 = User(name="Test User 2", email="user2@test.com", organization=org)
    session.add_all([user1, user2])
    
    # Create enrollments
    now = datetime.utcnow()
    enrollment1 = Enrollment(
        user=user1,
        badge=badge1,
        enrollment_date=now - timedelta(days=30),
        completion_date=now - timedelta(days=5)
    )
    enrollment2 = Enrollment(
        user=user1,
        badge=badge2,
        enrollment_date=now - timedelta(days=20)
    )
    enrollment3 = Enrollment(
        user=user2,
        badge=badge1,
        enrollment_date=now - timedelta(days=25),
        completion_date=now - timedelta(days=2)
    )
    session.add_all([enrollment1, enrollment2, enrollment3])
    
    session.commit()
    
    yield session
    
    Base.metadata.drop_all(bind=engine)

def test_badge_enrollments(db_session):
    analytics = AnalyticsEngine(db_session)
    result = analytics.get_badge_enrollments("Python Test")
    
    assert result["data"][0]["badge"] == "Python Test"
    assert result["data"][0]["total_enrollments"] == 2
    assert result["data"][0]["completed"] == 2
    assert "visualization" in result

def test_organization_trends(db_session):
    analytics = AnalyticsEngine(db_session)
    result = analytics.get_organization_trends("Test Corp")
    
    assert len(result["data"]) > 0
    assert result["data"][0]["organization"] == "Test Corp"
    assert "visualization" in result

def test_completion_metrics(db_session):
    analytics = AnalyticsEngine(db_session)
    result = analytics.get_completion_metrics()
    
    assert len(result["data"]) > 0
    assert result["data"][0]["organization"] == "Test Corp"
    assert "completion_rate" in result["data"][0]
    assert "visualization" in result

def test_learning_paths(db_session):
    analytics = AnalyticsEngine(db_session)
    result = analytics.get_learning_paths()
    
    assert len(result["data"]) > 0
    assert "visualization" in result
