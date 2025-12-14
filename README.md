# Dividend Portfolio Dashboard

A modern web application for tracking and analyzing dividend investments. Built with Next.js 15, FastAPI, and professional charting components.

## Features

- **Portfolio Overview**: Real-time summary of holdings, performance metrics, and recent dividends
- **Monthly Analysis**: Year-over-year comparisons, heatmaps, and expense coverage calculator
- **Stock Analysis**: Period breakdowns, concentration risk analysis, and individual company deep-dives
- **Dividend Screener**: Research new stocks with Alpha Vantage data (coming soon)
- **Forecast**: ML-powered dividend predictions with multiple models (coming soon)
- **PDF Reports**: Generate professional monthly, quarterly, and annual reports (coming soon)

## Tech Stack

**Frontend:**
- Next.js 15 with React 19
- TypeScript
- Tailwind CSS 4
- shadcn/ui components
- Recharts for data visualization
- TanStack React Query for data fetching

**Backend:**
- FastAPI with Python 3.11+
- Pydantic for data validation
- Pandas/NumPy for data processing

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.11+
- pip

### Quick Start

```bash
# Start the application
./start.sh
```

Or start each service manually:

```bash
# Terminal 1 - Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

The app will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Configuration

### Environment Variables

**Backend** (`backend/.env`):
```env
ALPHA_VANTAGE_API_KEY=your_api_key_here
DATA_PATH=../data/dividends.csv
```

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Data Format

Place your dividend data in `data/dividends.csv` with these columns:
- `Time`: Date of dividend payment (YYYY-MM-DD)
- `Name`: Company/stock name
- `Ticker`: Stock ticker symbol
- `Total`: Dividend amount
- `Account Type`: ISA or GIA

## Project Structure

```
dividends/
├── backend/                 # FastAPI backend
│   └── app/
│       ├── main.py         # Application entry
│       ├── config.py       # Configuration
│       ├── api/            # API endpoints
│       ├── models/         # Pydantic models
│       └── services/       # Business logic
│
├── frontend/               # Next.js frontend
│   └── src/
│       ├── app/           # Pages (App Router)
│       ├── components/    # React components
│       ├── hooks/         # Custom hooks
│       ├── lib/           # Utilities
│       └── types/         # TypeScript types
│
├── data/                   # Dividend CSV files
├── original/               # Archived Streamlit app
├── start.sh               # Quick start script
└── README.md
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/overview` | Portfolio summary and metrics |
| `GET /api/monthly/` | Monthly analysis data |
| `GET /api/monthly/heatmap` | Year x Month heatmap |
| `GET /api/monthly/coverage` | Expense coverage calculator |
| `GET /api/stocks/` | Stock analysis overview |
| `GET /api/stocks/{ticker}` | Individual stock details |
| `GET /api/stocks/concentration` | Portfolio concentration risk |

## Development

### Code Quality

- TypeScript strict mode enabled
- ESLint + Prettier for frontend
- Pydantic validation for backend
- Type hints throughout Python code

### Adding Features

1. Create backend endpoint in `backend/app/api/`
2. Add Pydantic models in `backend/app/models/`
3. Create frontend page in `frontend/src/app/`
4. Add React Query hook in `frontend/src/hooks/`

## Original Streamlit App

The original Streamlit implementation is preserved in the `original/` folder for reference. To run it:

```bash
cd original
pip install -r ../requirements.txt
streamlit run dividend_app.py
```

## License

MIT License - see LICENSE file for details.
