from fastapi import FastAPI, Depends, Request, Body
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from langchain_community.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import json
import re
import logging

from src.database.config import get_db
from src.database.init_db import init_db
from src.models.models import Organization, User, Badge, Course, Enrollment
from src.analytics.engine import AnalyticsEngine
from src.config.settings import get_settings

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

# Define request model
class AnalyticsQuery(BaseModel):
    query: str = "How many people are enrolled in Python Basics badge?"
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "How many people are enrolled in Python Basics badge?"
            }
        }

app = FastAPI(
    title="Analytics LLM Server",
    description="A server that processes natural language queries about badge and course enrollment data",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return HTMLResponse("""
    <html>
        <head>
            <title>Analytics Query Interface</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 1000px; margin: 0 auto; }
                .form-group { margin-bottom: 20px; }
                textarea { width: 100%; height: 100px; margin-bottom: 10px; }
                button { padding: 10px 20px; background-color: #007bff; color: white; border: none; cursor: pointer; }
                #result { margin-top: 20px; }
                #visualization { width: 100%; height: 500px; margin-top: 20px; }
                .response-text { white-space: pre-wrap; margin-bottom: 20px; }
                .metadata { font-size: 0.9em; color: #666; margin-top: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Analytics Query Interface</h1>
                <div class="form-group">
                    <h3>Example queries:</h3>
                    <ul>
                        <li>"How many people are enrolled in Python Basics badge?"</li>
                        <li>"What's the enrollment trend for Microsoft over the last 6 months?"</li>
                        <li>"Show me the top 5 badges by enrollment"</li>
                        <li>"What's the completion rate for Python Basics?"</li>
                    </ul>
                </div>
                <div class="form-group">
                    <textarea id="query" placeholder="Enter your query here..."></textarea>
                    <button onclick="sendQuery()">Submit Query</button>
                </div>
                <div id="result">
                    <div id="response-text" class="response-text"></div>
                    <div id="visualization"></div>
                    <div id="metadata" class="metadata"></div>
                </div>
            </div>
            <script>
                async function sendQuery() {
                    const query = document.getElementById('query').value;
                    const responseText = document.getElementById('response-text');
                    const visualization = document.getElementById('visualization');
                    const metadata = document.getElementById('metadata');
                    
                    try {
                        const response = await fetch('/analytics', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({ query: query })
                        });
                        
                        const data = await response.json();
                        
                        // Display the response text
                        responseText.textContent = data.response;
                        
                        // Display the visualization if available
                        if (data.visualization) {
                            const figure = JSON.parse(data.visualization);
                            Plotly.newPlot('visualization', figure.data, figure.layout);
                        } else {
                            visualization.innerHTML = '';
                        }
                        
                        // Display metadata in a more readable format
                        metadata.innerHTML = '<h3>Statistics:</h3>' +
                            `<p>Total Users: ${data.metadata.database_stats.total_users}</p>` +
                            `<p>Total Badges: ${data.metadata.database_stats.total_badges}</p>` +
                            `<p>Total Enrollments: ${data.metadata.database_stats.total_enrollments}</p>` +
                            `<p>Total Organizations: ${data.metadata.database_stats.total_organizations}</p>`;
                    } catch (error) {
                        responseText.innerHTML = 'Error: ' + error.message;
                        visualization.innerHTML = '';
                        metadata.innerHTML = '';
                    }
                }
            </script>
        </body>
    </html>
    """)

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
    model="gpt-3.5-turbo",
    openai_api_key=os.getenv("OPENAI_API_KEY")
)

# Initialize conversation chain
conversation = ConversationChain(
    llm=llm,
    memory=ConversationBufferMemory(),
    verbose=True
)

@app.post("/analytics")
async def handle_analytics_query(
    query_data: AnalyticsQuery = Body(
        ...,
        examples=[{
            "query": "How many people are enrolled in Python Basics badge?"
        }, {
            "query": "What's the enrollment trend for Microsoft over the last 6 months?"
        }, {
            "query": "Show me the top 5 badges by enrollment"
        }]
    ),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Process natural language queries about badge and course enrollment data.
    """
    query = query_data.query
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
            if isinstance(result['data'], list):
                analytics_data['items'] = result['data']
            else:
                analytics_data.update(result['data'])
            visualization = result.get('visualizations', {}).get('bar')
        
        elif re.search(org_pattern, query):
            org_name = re.search(org_pattern, query).group(2)
            result = analytics.get_organization_trends(org_name)
            if isinstance(result['data'], list):
                analytics_data['items'] = result['data']
            else:
                analytics_data.update(result['data'])
            visualization = result.get('visualizations', {}).get('line')
        
        elif re.search(trend_pattern, query):
            result = analytics.get_organization_trends()
            if isinstance(result['data'], list):
                analytics_data['items'] = result['data']
            else:
                analytics_data.update(result['data'])
            visualization = result.get('visualizations', {}).get('line')
        
        elif re.search(completion_pattern, query):
            result = analytics.get_completion_metrics()
            if isinstance(result['data'], dict):
                analytics_data.update(result['data'])
            else:
                analytics_data['items'] = result['data']
            visualization = result.get('visualizations', {}).get('heatmap')
        
        elif re.search(path_pattern, query):
            result = analytics.get_learning_paths()
            if isinstance(result['data'], dict):
                analytics_data.update(result['data'])
            else:
                analytics_data['items'] = result['data']
            visualization = result.get('visualizations', {}).get('sankey')
        
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
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)