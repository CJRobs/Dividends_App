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

**Backend Configuration:**

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```env
   ALPHA_VANTAGE_API_KEY=your_actual_api_key_here  # Get from https://www.alphavantage.co/support/#api-key
   DATA_PATH=../data/dividends.csv
   ENVIRONMENT=development  # or 'production'
   ```

3. **⚠️ Security:** Never commit `.env` files to git. The API key should remain private.

**Frontend** (`frontend/.env.local`):
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Getting an Alpha Vantage API Key

1. Visit [Alpha Vantage](https://www.alphavantage.co/support/#api-key)
2. Sign up for a free API key
3. Add it to your `.env` file
4. The screener feature requires this key for stock research

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

## Security

### Best Practices

- **Never commit API keys** - Use `.env` files (already in `.gitignore`)
- **Rotate keys regularly** - Change your Alpha Vantage API key periodically
- **Protect your data** - CSV files contain personal financial information
- **Use HTTPS in production** - Configure a reverse proxy with TLS

### Application Logs

**Development Mode:**
- Logs output to console only
- DEBUG level logging for detailed troubleshooting

**Production Mode:**
- Logs saved to `backend/logs/app.log`
- Automatic log rotation (10MB max size, 5 backups)
- INFO level logging for performance

To enable production logging:
```bash
export ENVIRONMENT=production
cd backend && uvicorn app.main:app
```

### Security Features

- ✅ Environment variable validation at startup
- ✅ API key format validation
- ✅ Data schema validation
- ✅ File permission checks
- ✅ Structured logging with audit trail
- ✅ Request/response logging
- ✅ Graceful error handling

For more details, see [SECURITY.md](SECURITY.md)

## License

MIT License - see LICENSE file for details.
