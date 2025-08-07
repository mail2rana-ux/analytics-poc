from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import inspect
from ..models.models import Organization, User, Badge, Course, Enrollment, Base
from ..database.config import engine, SessionLocal
import random
import logging

logger = logging.getLogger(__name__)

def init_db():
    """Initialize the database with tables and sample data."""
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    
    # Create all tables if they don't exist
    if not existing_tables:
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully!")
    else:
        logger.info("Database tables already exist.")
    
    db = SessionLocal()
    
    # Check if we already have data
    if db.query(Organization).first():
        logger.info("Sample data already exists in the database.")
        return
        
    logger.info("Initializing database with sample data...")
    
    # Sample Organizations
    organizations = [
        {"name": "Tech Corp", "description": "Technology Company"},
        {"name": "Education Plus", "description": "Educational Institution"},
        {"name": "Data Systems", "description": "Data Analytics Company"}
    ]
    
    org_objects = []
    for org in organizations:
        db_org = Organization(**org)
        db.add(db_org)
        org_objects.append(db_org)
    
    # Sample Badges
    badges = [
        {"name": "Python Master", "description": "Advanced Python Programming"},
        {"name": "Data Science Pro", "description": "Data Science and Analytics"},
        {"name": "Cloud Expert", "description": "Cloud Computing and Architecture"},
        {"name": "AI Developer", "description": "Artificial Intelligence Development"}
    ]
    
    badge_objects = []
    for badge in badges:
        db_badge = Badge(**badge)
        db.add(db_badge)
        badge_objects.append(db_badge)
    
    # Sample Courses
    courses = [
        {"name": "Python Programming", "description": "Learn Python basics to advanced"},
        {"name": "Data Analysis", "description": "Data analysis with Python"},
        {"name": "Cloud Computing", "description": "Introduction to cloud computing"},
        {"name": "Machine Learning", "description": "ML fundamentals"}
    ]
    
    course_objects = []
    for course in courses:
        db_course = Course(**course)
        db.add(db_course)
        course_objects.append(db_course)
    
    # Associate courses with badges
    course_objects[0].badges.append(badge_objects[0])  # Python course -> Python Master
    course_objects[1].badges.append(badge_objects[1])  # Data Analysis -> Data Science Pro
    course_objects[2].badges.append(badge_objects[2])  # Cloud Computing -> Cloud Expert
    course_objects[3].badges.append(badge_objects[3])  # ML -> AI Developer
    
    # Sample Users and Enrollments
    for org in org_objects:
        # Create 5 users per organization
        for i in range(5):
            user = User(
                email=f"user{i}@{org.name.lower().replace(' ', '')}.com",
                name=f"User {i} {org.name}",
                organization=org
            )
            db.add(user)
            
            # Enroll user in 1-3 random badges
            num_enrollments = random.randint(1, 3)
            selected_badges = random.sample(badge_objects, num_enrollments)
            
            for badge in selected_badges:
                enrollment_date = datetime.utcnow() - timedelta(days=random.randint(0, 180))
                completion_date = None
                if random.random() > 0.5:  # 50% chance of completion
                    completion_date = enrollment_date + timedelta(days=random.randint(30, 90))
                
                enrollment = Enrollment(
                    user=user,
                    badge=badge,
                    enrollment_date=enrollment_date,
                    completion_date=completion_date
                )
                db.add(enrollment)
    
    db.commit()
    db.close()

if __name__ == "__main__":
    init_db()
