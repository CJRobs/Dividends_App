# Dividend Portfolio Dashboard

A modern, full-stack web application for tracking, analyzing, and forecasting dividend income built with **Next.js**, **FastAPI**, **Tailwind CSS**, and **shadcn/ui**.

![Tech Stack](https://img.shields.io/badge/Next.js-15-black)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Python](https://img.shields.io/badge/Python-3.13-blue)

## Features

- 📊 **Portfolio Overview** - Real-time dashboard with key metrics
- 📅 **Monthly Analysis** - Detailed month-by-month breakdown
- 🏢 **Stock Analysis** - Individual stock performance tracking
- 🔍 **Dividend Screener** - Filter and search dividend stocks
- 🔮 **Forecast** - Predict future dividend income
- 📄 **PDF Reports** - Generate comprehensive reports

## Tech Stack

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first CSS framework
- **shadcn/ui** - Beautiful, accessible component library
- **TanStack Query** - Powerful data fetching and caching
- **Zustand** - Lightweight state management
- **Recharts** - Charting library for React
- **Lucide Icons** - Beautiful icon library

### Backend
- **FastAPI** - Modern Python web framework
- **Pydantic** - Data validation using Python type hints
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Plotly** - Interactive visualizations
- **Uvicorn** - ASGI server

## Project Structure

```
dividends/
├── backend/               # FastAPI Backend
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── models/       # Pydantic models
│   │   ├── services/     # Business logic
│   │   ├── utils/        # Helper functions
│   │   └── main.py       # FastAPI app entry
│   ├── requirements.txt
│   └── .env
│
├── frontend/             # Next.js Frontend
│   ├── src/
│   │   ├── app/         # Next.js pages
│   │   ├── components/  # React components
│   │   ├── hooks/       # Custom React hooks
│   │   ├── lib/         # Utilities and API client
│   │   ├── store/       # Zustand stores
│   │   └── types/       # TypeScript types
│   ├── package.json
│   └── .env.local
│
├── dividends/           # Data directory
│   └── *.csv           # Dividend CSV files
│
├── MIGRATION_PLAN.md   # Detailed migration plan
└── README.md           # This file
```

## Getting Started

### Prerequisites

- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend)
- **npm** or **yarn** (for frontend package management)

### Backend Setup

1. **Navigate to backend directory**
   ```bash
   cd backend
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   - Copy `.env.example` to `.env`
   - Update the values as needed:
   ```bash
   cp .env.example .env
   ```

   Required variables:
   ```
   ALPHA_VANTAGE_API_KEY=your_api_key_here
   DEFAULT_CURRENCY=GBP
   DATA_PATH=../dividends
   CORS_ORIGINS=http://localhost:3000
   ```

5. **Run the backend**
   ```bash
   uvicorn app.main:app --reload
   ```

   The API will be available at: `http://localhost:8000`

   API Documentation: `http://localhost:8000/docs`

### Frontend Setup

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Configure environment variables**
   - The `.env.local` file should already exist with:
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

4. **Run the development server**
   ```bash
   npm run dev
   ```

   The app will be available at: `http://localhost:3000`

### Running Both Services

**Option 1: Two Terminals**

Terminal 1 (Backend):
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Terminal 2 (Frontend):
```bash
cd frontend
npm run dev
```

**Option 2: Using a process manager like `concurrently`** (future enhancement)

## Development

### Adding New Features

1. **Backend**: Add endpoints in `backend/app/api/`
2. **Frontend**: Add pages in `frontend/src/app/`
3. **Types**: Update TypeScript types in `frontend/src/types/`
4. **API Client**: Add API functions in `frontend/src/lib/api.ts`

### Code Quality

**Backend:**
```bash
# Format code
black app/

# Lint code
ruff check app/

# Type checking
mypy app/
```

**Frontend:**
```bash
# Lint
npm run lint

# Type check
npm run build

# Format (if configured)
npm run format
```

## API Endpoints

### Overview
- `GET /api/overview/` - Complete overview data
- `GET /api/overview/summary` - Portfolio summary
- `GET /api/overview/ytd-chart` - YTD chart data
- `GET /api/overview/monthly-chart` - Monthly chart
- `GET /api/overview/top-stocks` - Top dividend stocks
- `GET /api/overview/recent-dividends` - Recent payments

### Monthly Analysis
- `GET /api/monthly/summary` - Monthly summary
- `GET /api/monthly/comparison` - Year comparison

### Stock Analysis
- `GET /api/stocks/list` - All stocks
- `GET /api/stocks/{symbol}` - Stock details

### Dividend Screener
- `POST /api/screener/search` - Search with criteria

### Forecast
- `GET /api/forecast/predict` - Generate forecast

### Reports
- `POST /api/reports/generate` - Generate PDF

### Admin
- `GET /health` - Health check
- `POST /api/reload-data` - Reload data from source

## Data Format

The application expects CSV files in the `dividends/` directory with the following columns:

- `Action` - Type of action (e.g., "Dividend")
- `Time` - Payment date/time
- `ISIN` - International Securities ID
- `Ticker` - Stock ticker symbol
- `Name` - Company name
- `No. of shares` - Number of shares
- `Price / share` - Dividend per share
- `Currency (Price / share)` - Currency code
- `Exchange rate` - Exchange rate if applicable
- `Total` - Total dividend amount
- `Currency (Total)` - Currency of total
- `Withholding tax` - Tax withheld
- `Currency (Withholding tax)` - Tax currency

## Deployment

### Backend Deployment

Recommended platforms:
- **Railway** - Easy Python deployment
- **Render** - Free tier available
- **DigitalOcean App Platform** - Good for production
- **AWS EC2** - Full control

Example deployment (Railway):
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and init
railway login
railway init

# Deploy
railway up
```

### Frontend Deployment

Recommended platforms:
- **Vercel** - Optimal for Next.js (recommended)
- **Netlify** - Good alternative
- **Cloudflare Pages** - Fast global CDN

Example deployment (Vercel):
```bash
# Install Vercel CLI
npm install -g vercel

# Deploy
cd frontend
vercel

# Set environment variable
vercel env add NEXT_PUBLIC_API_URL
```

## Migration from Streamlit

This application is a modern rewrite of the original Streamlit-based dashboard. See [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for detailed migration steps.

### Key Improvements

1. **Better Performance** - Faster page loads and interactions
2. **Modern UI** - Clean, professional interface with Tailwind CSS
3. **Mobile Responsive** - Works great on all devices
4. **Type Safety** - Full TypeScript support
5. **API-First** - Decoupled frontend and backend
6. **Scalable** - Easy to add features and deploy

## Troubleshooting

### Backend Issues

**Problem**: `Data not loaded` error
- **Solution**: Check that CSV files exist in `dividends/` directory
- **Solution**: Verify `DATA_PATH` in `.env` points to correct location

**Problem**: CORS errors
- **Solution**: Ensure `CORS_ORIGINS` in backend `.env` includes frontend URL

**Problem**: Import errors
- **Solution**: Ensure virtual environment is activated
- **Solution**: Reinstall dependencies: `pip install -r requirements.txt`

### Frontend Issues

**Problem**: "Cannot connect to API"
- **Solution**: Ensure backend is running on `http://localhost:8000`
- **Solution**: Check `NEXT_PUBLIC_API_URL` in `.env.local`

**Problem**: Build errors
- **Solution**: Delete `.next/` and `node_modules/`, then reinstall
- **Solution**: Clear Next.js cache: `rm -rf .next`

**Problem**: Type errors
- **Solution**: Run `npm run build` to see all TypeScript errors
- **Solution**: Ensure types in `src/types/` match backend models

## Contributing

1. Follow the migration plan for adding new features
2. Maintain type safety (TypeScript + Pydantic)
3. Add tests for new functionality
4. Update documentation as needed
5. Follow existing code style

## License

This project is for personal use. Modify as needed for your portfolio tracking needs.

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review [MIGRATION_PLAN.md](MIGRATION_PLAN.md) for implementation details
3. Check API docs at `http://localhost:8000/docs`

## Roadmap

### Completed ✅
- [x] Backend API with FastAPI
- [x] Frontend with Next.js + Tailwind
- [x] Overview page with key metrics
- [x] Responsive layout with sidebar
- [x] API client and data fetching

### In Progress 🚧
- [ ] Monthly Analysis page
- [ ] Stock Analysis page
- [ ] Dividend Screener page
- [ ] Forecast page
- [ ] PDF Reports page
- [ ] Charts with Recharts

### Planned 📋
- [ ] Dark mode toggle
- [ ] User authentication
- [ ] Multiple portfolios
- [ ] Real-time stock prices
- [ ] Advanced forecasting models
- [ ] Export to Excel
- [ ] Email notifications
- [ ] Mobile app

---

**Version:** 1.0.0
**Last Updated:** October 16, 2025
