from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from mcp_python import MCPAsyncServer
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
import os
from dotenv import load_dotenv
from typing import Dict, Any
import json
import re
import logging

from .database.config import get_db
from .database.init_db import init_db
from .models.models import Organization, User, Badge, Course, Enrollment
from .analytics.engine import AnalyticsEngine
from .config.settings import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get settings
settings = get_settings()
logger.info(f"Using database: {settings.DATABASE_URL}")

app = FastAPI()
mcp_server = MCPAsyncServer()

try:
    # Initialize the database with sample data
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialization completed successfully!")
except Exception as e:
    logger.error(f"Error initializing database: {str(e)}")
    raise

# Initialize LLM
llm = ChatOpenAI(
    temperature=0,
    model="gpt-4",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=ConversationBufferMemory(),
    verbose=True
)

@mcp_server.handle_message
async def handle_analytics_query(message: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Handle analytics queries using LLM and return structured responses with visualizations
    """
    query = message.get("query", "")
    if not query:
        return {"error": "No query provided"}
    
    try:
        analytics = AnalyticsEngine(db)
        
        # Get basic statistics for context
        stats = {
            "total_users": db.query(User).count(),
            "total_badges": db.query(Badge).count(),
            "total_enrollments": db.query(Enrollment).count(),
            "total_organizations": db.query(Organization).count()
        }
        
        # Pattern matching for specific analytics queries
        badge_pattern = r"(?i)(how many|enrollments?|users?).+(?:badge|course)\s+[\"']?([^\"']+)[\"']?"
        org_pattern = r"(?i)(how many|enrollments?|users?).+(?:organization|org)\s+[\"']?([^\"']+)[\"']?"
        trend_pattern = r"(?i)(trend|over time|historical)"
        completion_pattern = r"(?i)(completion|success).+(rate|percentage)"
        path_pattern = r"(?i)(learning path|badge combination|journey)"
        
        # Initialize response data
        analytics_data = {}
        visualization = None
        
        # Check for specific patterns and get corresponding analytics
        if re.search(badge_pattern, query):
            badge_name = re.search(badge_pattern, query).group(2)
            result = analytics.get_badge_enrollments(badge_name)
            analytics_data.update(result['data'])
            visualization = result['visualization']
        
        elif re.search(org_pattern, query):
            org_name = re.search(org_pattern, query).group(2)
            result = analytics.get_organization_trends(org_name)
            analytics_data.update(result['data'])
            visualization = result['visualization']
        
        elif re.search(trend_pattern, query):
            result = analytics.get_organization_trends()
            analytics_data.update(result['data'])
            visualization = result['visualization']
        
        elif re.search(completion_pattern, query):
            result = analytics.get_completion_metrics()
            analytics_data.update(result['data'])
            visualization = result['visualization']
        
        elif re.search(path_pattern, query):
            result = analytics.get_learning_paths()
            analytics_data.update(result['data'])
            visualization = result['visualization']
        
        # Enhance the query with context and analytics data
        enhanced_query = f"""
        Based on the following data:
        - Total Users: {stats['total_users']}
        - Total Badges: {stats['total_badges']}
        - Total Enrollments: {stats['total_enrollments']}
        - Total Organizations: {stats['total_organizations']}
        
        Analytics Data:
        {json.dumps(analytics_data, indent=2)}
        
        Please analyze this query: {query}
        """
        
        # Process through LLM
        response = conversation.predict(input=enhanced_query)
        
        # Structure the response with visualization if available
        result = {
            "response": response,
            "type": "analytics",
            "metadata": {
                "confidence": 0.9,
                "query_type": "analytics",
                "database_stats": stats,
                "analytics_data": analytics_data
            }
        }
        
        if visualization:
            result["visualization"] = visualization
        
        return result
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp_server.run()
