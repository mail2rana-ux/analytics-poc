import uvicorn
from fastapi import FastAPI
from fastapi_mcp import FastApiMCP
import logging
from dotenv import load_dotenv

from src.deployment import app
from src.database.init_db import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def main():
    # Create FastApiMCP instance with operation IDs
    mcp = FastApiMCP(app, include_operations=[
        "get_badge_enrollments",
        "get_organization_trends",
        "get_completion_metrics",
        "get_learning_paths",
        "process_analytics_query"
    ])
    
    # Mount the MCP operations to the FastAPI app
    mcp.mount()
    
    # Initialize database
    try:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialization completed successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {str(e)}")
        raise
    
    # Run the FastAPI server with uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
