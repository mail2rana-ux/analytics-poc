
# Analytics LLM Server

This is an LLM-powered analytics server that processes natural language queries about badge and course enrollment data. The server uses the Model Context Protocol (MCP) to provide structured analytics responses.

## Features

- Natural language processing of analytics questions
- LLM-powered data analysis and query interpretation
- Support for multi-dimensional queries (organization + badge combinations)
- Integration with PostgreSQL database for real-time data access
- Structured response formatting for business stakeholders

## Project Structure

```
analytics-poc/
├── .github/
│   └── copilot-instructions.md
├── .vscode/
│   └── mcp.json
├── src/
│   ├── main.py
│   ├── database/
│   ├── models/
│   └── analytics/
└── tests/
```

## Create git account

## Create OpenAI Account

Go to https://platform.openai.com/ and create an account there. This is needed for creating the APIKey. You can sign using gmail account

## Create OpenAI APIKey

Go to https://platform.openai.com/api-keys and create an api key. Save it in a safe place and use it in .env file.

## Setup

1. Create a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up environment variables:
   Create a `.env` file with:

```
OPENAI_API_KEY=your_api_key
DATABASE_URL=postgresql://user:password@localhost:5432/dbname
```

4. Run the server:

```bash
python src/main.py
```

## Usage

The server accepts natural language queries about badge and course enrollment data. Example queries:

- "How many people are enrolled in [badge]?"
- "What's the enrollment trend for [organization] over the last 6 months?"
- "Show me the top 5 badges by enrollment"

## Development

This project uses:

- FastAPI for the server implementation
- Model Context Protocol (MCP) for LLM integration
- SQLAlchemy for database interactions
- LangChain for LLM chain management
- Plotly for data visualization

## Testing

Run tests using:

```bash
pytest tests/
```

## Documentation

For more details about the implementation and available features, see:

- [Technical Documentation](docs/technical_documentation.md)
- [Query Examples](docs/query_examples.md)
- [API Reference](docs/api_reference.md)

Removed the entry of mcp-python from requirements.txt. It was like this "git+https://github.com/modelcontextprotocol/mcp-python.git#egg=mcp-python".

I replaced it with running this command in VSCode terminal: "pip install mcp-python"

# How to run the server

1. Create virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

2. Used python3 and ugraded pip:

```
pip install --upgrade pip
```

3. Install dependencies:

```
pip install mcp-python
pip install -r requirements.txt
```

4. Set up your .env file with your OpenAI API key and database URL

5. Start the server:

```
python3 src/main.py
```
=======
# analytics-poc
POC for Analytics
>>>>>>> 146bde5213956c3bbd9c2d25554031dfaccd8839
