# Aurora EDC AI Assistant

An AI-powered economic development assistant for Aurora Economic Development Council. This tool helps prospective businesses, site selectors, and EDC staff with site selection, permit navigation, incentive information, and workforce data—available 24/7.

## Features

### Public-Facing Business Navigator Chatbot
- Answer questions about Aurora (demographics, incentives, infrastructure, quality of life, major employers)
- Guide users through permit and licensing requirements
- Provide information on available commercial/industrial properties
- Explain tax incentives, enterprise zones, and economic development programs
- Capture lead information from serious inquiries
- Route qualified leads to appropriate EDC staff

### Knowledge Base & RAG System
- Document chunking with metadata (source, date, category)
- Semantic search with ChromaDB vector store
- Citation of sources in responses
- Aurora-specific knowledge about incentives, permits, properties, and workforce

### Staff Portal
- Lead management dashboard with scoring
- Analytics on chat usage and common questions
- Knowledge base management
- Conversation review interface

## Tech Stack

- **Backend**: Python (FastAPI)
- **Frontend**: React with TypeScript
- **AI/LLM**: Anthropic Claude API (claude-sonnet-4-20250514)
- **Vector Database**: ChromaDB
- **Database**: PostgreSQL
- **Styling**: Tailwind CSS

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker and Docker Compose
- Anthropic API key

### Quick Start with Docker

1. Clone the repository:
```bash
git clone <repo-url>
cd aurora-edc-ai
```

2. Copy environment file and add your API key:
```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

3. Start all services:
```bash
docker-compose up -d
```

4. Initialize the database and seed data:
```bash
# Run migrations
docker-compose exec backend alembic upgrade head

# Seed knowledge base
docker-compose exec backend python scripts/seed_knowledge_base.py

# Seed sample properties
docker-compose exec backend python scripts/seed_properties.py
```

5. Access the application:
- **Chat Interface**: http://localhost:5173
- **Staff Portal**: http://localhost:5173/staff
- **API Documentation**: http://localhost:8000/docs

### Local Development (without Docker)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
cp ../.env.example .env
# Edit .env with your configuration

# Start PostgreSQL (use Docker or local installation)
docker run -d --name aurora-db -p 5432:5432 \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=aurora_edc \
  postgres:15-alpine

# Run migrations
alembic upgrade head

# Seed data
python scripts/seed_knowledge_base.py
python scripts/seed_properties.py

# Start server
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## Project Structure

```
aurora-edc-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                 # FastAPI application
│   │   ├── config.py               # Environment configuration
│   │   ├── models/                 # Database models & schemas
│   │   ├── routers/                # API endpoints
│   │   ├── services/               # Business logic (LLM, RAG, leads)
│   │   └── knowledge/              # Document ingestion & chunking
│   ├── alembic/                    # Database migrations
│   ├── data/                       # Vector store data
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/             # React components
│   │   ├── pages/                  # Page components
│   │   ├── services/               # API client
│   │   └── hooks/                  # Custom React hooks
│   └── public/
├── scripts/                        # Utility scripts
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Chat
- `POST /chat/message` - Send a message and get AI response
- `POST /chat/message/stream` - Stream AI response (SSE)
- `GET /chat/conversation/{id}` - Get conversation history
- `POST /chat/feedback` - Submit feedback on a message

### Properties
- `GET /properties` - List properties with filters
- `POST /properties/search` - Natural language property search
- `GET /properties/{id}` - Get property details
- `GET /properties/stats/summary` - Property statistics

### Leads
- `GET /leads` - List leads with pagination
- `POST /leads` - Create a new lead
- `PATCH /leads/{id}` - Update lead status
- `GET /leads/{id}/conversation` - Get lead's chat history
- `GET /leads/stats/summary` - Lead statistics

### Analytics
- `GET /analytics/overview` - Dashboard metrics
- `GET /analytics/conversations/daily` - Daily conversation counts
- `GET /analytics/leads/funnel` - Lead conversion funnel
- `GET /analytics/questions/common` - Common question topics

### Knowledge Base
- `POST /knowledge/documents` - Add document
- `GET /knowledge/documents` - List documents
- `GET /knowledge/search` - Semantic search
- `GET /knowledge/stats` - Knowledge base statistics

## Configuration

Key environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `ANTHROPIC_API_KEY` | Claude API key | Required |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `CHROMA_PERSIST_DIR` | Vector store directory | `./data/chroma` |
| `CLAUDE_MODEL` | Claude model to use | `claude-sonnet-4-20250514` |
| `DEBUG` | Enable debug mode | `false` |

## Deployment

### Azure Deployment

The application is designed for Azure deployment:

1. **Azure App Service**: Backend API
2. **Azure Static Web Apps**: Frontend
3. **Azure Database for PostgreSQL**: Database
4. **Azure AI Search**: Production vector store (optional)

See `infrastructure/azure/` for Bicep templates.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

## License

Proprietary - Aurora Economic Development Council
