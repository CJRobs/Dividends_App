# Dividend Portfolio Dashboard - Migration Plan
## From Streamlit to Next.js + FastAPI + Tailwind + shadcn/ui

---

## Overview

This document outlines the complete migration from the current Streamlit application to a modern tech stack:
- **Frontend**: Next.js 14 (React + TypeScript) + Tailwind CSS + shadcn/ui
- **Backend**: FastAPI (Python)
- **Visualization**: Recharts / Tremor
- **State Management**: Zustand
- **Data Fetching**: TanStack Query

---

## Project Structure (Target)

```
dividends/
├── backend/                    # FastAPI Backend
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI app entry
│   │   ├── config.py          # Configuration (migrated)
│   │   ├── models/            # Pydantic models
│   │   │   ├── __init__.py
│   │   │   ├── portfolio.py
│   │   │   └── dividend.py
│   │   ├── api/               # API routes
│   │   │   ├── __init__.py
│   │   │   ├── overview.py
│   │   │   ├── monthly.py
│   │   │   ├── stocks.py
│   │   │   ├── screener.py
│   │   │   ├── forecast.py
│   │   │   └── reports.py
│   │   ├── services/          # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── data_processor.py
│   │   │   ├── dividend_calculator.py
│   │   │   └── forecast_service.py
│   │   └── utils/             # Utilities (migrated)
│   │       ├── __init__.py
│   │       ├── chart_data.py
│   │       └── helpers.py
│   ├── requirements.txt
│   └── .env
│
├── frontend/                   # Next.js Frontend
│   ├── src/
│   │   ├── app/               # Next.js App Router
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   ├── overview/
│   │   │   ├── monthly/
│   │   │   ├── stocks/
│   │   │   ├── screener/
│   │   │   ├── forecast/
│   │   │   └── reports/
│   │   ├── components/        # React components
│   │   │   ├── ui/           # shadcn/ui components
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx
│   │   │   │   ├── Header.tsx
│   │   │   │   └── Layout.tsx
│   │   │   ├── charts/
│   │   │   │   ├── LineChart.tsx
│   │   │   │   ├── BarChart.tsx
│   │   │   │   └── PieChart.tsx
│   │   │   └── features/     # Feature-specific components
│   │   │       ├── overview/
│   │   │       ├── monthly/
│   │   │       ├── stocks/
│   │   │       ├── screener/
│   │   │       ├── forecast/
│   │   │       └── reports/
│   │   ├── lib/              # Utilities
│   │   │   ├── api.ts        # API client
│   │   │   ├── utils.ts      # Helper functions
│   │   │   └── constants.ts
│   │   ├── hooks/            # Custom React hooks
│   │   │   ├── usePortfolio.ts
│   │   │   └── useDividends.ts
│   │   ├── store/            # Zustand stores
│   │   │   └── portfolioStore.ts
│   │   └── types/            # TypeScript types
│   │       └── index.ts
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── next.config.js
│   └── .env.local
│
├── data/                      # Shared data files
│   └── dividends.csv
│
└── MIGRATION_PLAN.md          # This file
```

---

## Phase 1: Backend Setup (FastAPI)

### Step 1.1: Create Backend Directory Structure
- [ ] Create `backend/` directory
- [ ] Create `backend/app/` directory
- [ ] Create subdirectories: `models/`, `api/`, `services/`, `utils/`
- [ ] Create `__init__.py` files in each directory

### Step 1.2: Setup Backend Dependencies
- [ ] Create `backend/requirements.txt` with:
  ```
  fastapi>=0.104.0
  uvicorn[standard]>=0.24.0
  pandas>=2.0.0
  numpy>=1.24.0
  plotly>=5.15.0
  python-dotenv>=1.0.0
  pydantic>=2.5.0
  pydantic-settings>=2.1.0
  requests>=2.31.0
  reportlab>=4.0.0
  python-multipart>=0.0.6
  fastapi-cors>=0.0.6
  ```
- [ ] Create virtual environment: `python -m venv backend/venv`
- [ ] Install dependencies: `pip install -r backend/requirements.txt`

### Step 1.3: Migrate Configuration
- [ ] Copy `config.py` to `backend/app/config.py`
- [ ] Update to use Pydantic Settings
- [ ] Create `backend/.env` with environment variables
- [ ] Add CORS origins for frontend

### Step 1.4: Create Pydantic Models
- [ ] Create `backend/app/models/portfolio.py` with:
  - `DividendRecord` model
  - `MonthlyData` model
  - `PortfolioSummary` model
- [ ] Create `backend/app/models/dividend.py` with:
  - `StockInfo` model
  - `DividendForecast` model
  - `ScreenerCriteria` model
  - `ScreenerResult` model

### Step 1.5: Migrate Utilities
- [ ] Copy and refactor `utils/utils.py` to `backend/app/services/data_processor.py`
- [ ] Remove Streamlit-specific code (st.cache, st.spinner, etc.)
- [ ] Update functions to return pure Python data structures
- [ ] Create helper functions for data validation

### Step 1.6: Create FastAPI Main Application
- [ ] Create `backend/app/main.py` with:
  - FastAPI app initialization
  - CORS middleware configuration
  - Router includes
  - Health check endpoint
  - Startup/shutdown events

### Step 1.7: Create API Endpoints - Overview
- [ ] Create `backend/app/api/overview.py`
- [ ] Migrate logic from `tabs/overview.py`
- [ ] Create endpoints:
  - `GET /api/overview/summary` - Portfolio summary stats
  - `GET /api/overview/ytd` - Year-to-date data
  - `GET /api/overview/charts` - Chart data (line, bar, pie)
  - `GET /api/overview/recent-dividends` - Recent dividend list

### Step 1.8: Create API Endpoints - Monthly Analysis
- [ ] Create `backend/app/api/monthly.py`
- [ ] Migrate logic from `tabs/monthly_analysis.py`
- [ ] Create endpoints:
  - `GET /api/monthly/summary` - Monthly summary by year
  - `GET /api/monthly/comparison` - Year-over-year comparison
  - `GET /api/monthly/charts` - Monthly charts data
  - `GET /api/monthly/{year}/{month}` - Specific month details

### Step 1.9: Create API Endpoints - Stock Analysis
- [ ] Create `backend/app/api/stocks.py`
- [ ] Migrate logic from `tabs/stock_analysis.py`
- [ ] Create endpoints:
  - `GET /api/stocks/list` - List all stocks
  - `GET /api/stocks/{symbol}` - Individual stock details
  - `GET /api/stocks/{symbol}/history` - Stock dividend history
  - `GET /api/stocks/{symbol}/chart` - Stock chart data

### Step 1.10: Create API Endpoints - Dividend Screener
- [ ] Create `backend/app/api/screener.py`
- [ ] Migrate logic from `tabs/dividend_screener.py`
- [ ] Create endpoints:
  - `POST /api/screener/search` - Search with criteria
  - `GET /api/screener/filters` - Get available filters
  - `GET /api/screener/top-performers` - Pre-filtered top performers

### Step 1.11: Create API Endpoints - Forecast
- [ ] Create `backend/app/api/forecast.py`
- [ ] Migrate logic from `tabs/forecast.py`
- [ ] Create endpoints:
  - `GET /api/forecast/predict` - Generate forecast
  - `GET /api/forecast/scenarios` - Scenario analysis
  - `POST /api/forecast/custom` - Custom forecast parameters

### Step 1.12: Create API Endpoints - PDF Reports
- [ ] Create `backend/app/api/reports.py`
- [ ] Migrate logic from `tabs/pdf_reports.py`
- [ ] Create endpoints:
  - `POST /api/reports/generate` - Generate PDF report
  - `GET /api/reports/{report_id}` - Download generated report
  - `GET /api/reports/templates` - Available report templates

### Step 1.13: Test Backend
- [ ] Run FastAPI server: `uvicorn app.main:app --reload`
- [ ] Test each endpoint using FastAPI docs at `http://localhost:8000/docs`
- [ ] Verify all data transformations work correctly
- [ ] Test error handling

---

## Phase 2: Frontend Setup (Next.js)

### Step 2.1: Initialize Next.js Project
- [ ] Run: `npx create-next-app@latest frontend --typescript --tailwind --app --src-dir`
- [ ] Configure during setup:
  - ✅ TypeScript: Yes
  - ✅ ESLint: Yes
  - ✅ Tailwind CSS: Yes
  - ✅ `src/` directory: Yes
  - ✅ App Router: Yes
  - ❌ Import alias: No (use default @/*)

### Step 2.2: Install Frontend Dependencies
- [ ] Navigate to `frontend/` directory
- [ ] Install core dependencies:
  ```bash
  npm install @tanstack/react-query zustand
  npm install recharts lucide-react
  npm install axios date-fns
  npm install clsx tailwind-merge
  npm install class-variance-authority
  ```
- [ ] Install dev dependencies:
  ```bash
  npm install -D @types/node
  ```

### Step 2.3: Setup shadcn/ui
- [ ] Initialize shadcn/ui: `npx shadcn-ui@latest init`
- [ ] Configure:
  - Style: Default
  - Base color: Slate
  - CSS variables: Yes
- [ ] Install needed components:
  ```bash
  npx shadcn-ui@latest add button
  npx shadcn-ui@latest add card
  npx shadcn-ui@latest add tabs
  npx shadcn-ui@latest add table
  npx shadcn-ui@latest add select
  npx shadcn-ui@latest add input
  npx shadcn-ui@latest add label
  npx shadcn-ui@latest add badge
  npx shadcn-ui@latest add separator
  npx shadcn-ui@latest add skeleton
  npx shadcn-ui@latest add dropdown-menu
  npx shadcn-ui@latest add dialog
  npx shadcn-ui@latest add toast
  ```

### Step 2.4: Configure Tailwind
- [ ] Update `tailwind.config.ts` with custom colors for financial data
- [ ] Add custom utilities for charts
- [ ] Configure dark mode support
- [ ] Add custom animations

### Step 2.5: Setup API Client
- [ ] Create `src/lib/api.ts` with Axios instance
- [ ] Configure base URL (environment variable)
- [ ] Add request/response interceptors
- [ ] Create type-safe API functions

### Step 2.6: Create TypeScript Types
- [ ] Create `src/types/index.ts` with interfaces matching backend Pydantic models:
  - `DividendRecord`
  - `MonthlyData`
  - `PortfolioSummary`
  - `StockInfo`
  - `DividendForecast`
  - `ScreenerCriteria`
  - `ScreenerResult`

### Step 2.7: Setup TanStack Query
- [ ] Create `src/app/providers.tsx` with QueryClientProvider
- [ ] Wrap app in providers in `src/app/layout.tsx`
- [ ] Configure query defaults (staleTime, cacheTime, etc.)

### Step 2.8: Create Zustand Store
- [ ] Create `src/store/portfolioStore.ts` with:
  - Selected date range
  - Currency preference
  - Filter settings
  - UI state (sidebar open/closed, etc.)

### Step 2.9: Setup Environment Variables
- [ ] Create `frontend/.env.local` with:
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```

---

## Phase 3: Build Core UI Components

### Step 3.1: Create Layout Components
- [ ] Create `src/components/layout/Layout.tsx` - Main layout wrapper
- [ ] Create `src/components/layout/Sidebar.tsx` - Navigation sidebar
- [ ] Create `src/components/layout/Header.tsx` - Top header with title
- [ ] Create `src/components/layout/MobileNav.tsx` - Mobile responsive nav

### Step 3.2: Create Chart Components
- [ ] Create `src/components/charts/LineChart.tsx` - Reusable line chart
- [ ] Create `src/components/charts/BarChart.tsx` - Reusable bar chart
- [ ] Create `src/components/charts/PieChart.tsx` - Reusable pie chart
- [ ] Create `src/components/charts/AreaChart.tsx` - Reusable area chart
- [ ] Add chart customization props (colors, tooltips, legends)

### Step 3.3: Create Shared Components
- [ ] Create `src/components/MetricCard.tsx` - Stat card component
- [ ] Create `src/components/DataTable.tsx` - Reusable data table
- [ ] Create `src/components/LoadingSpinner.tsx` - Loading states
- [ ] Create `src/components/ErrorMessage.tsx` - Error display
- [ ] Create `src/components/DateRangePicker.tsx` - Date range selector
- [ ] Create `src/components/CurrencySelector.tsx` - Currency dropdown

### Step 3.4: Create Custom Hooks
- [ ] Create `src/hooks/usePortfolio.ts` - Portfolio data fetching
- [ ] Create `src/hooks/useDividends.ts` - Dividend data fetching
- [ ] Create `src/hooks/useMonthly.ts` - Monthly analysis data
- [ ] Create `src/hooks/useStocks.ts` - Stock data fetching
- [ ] Create `src/hooks/useScreener.ts` - Screener functionality
- [ ] Create `src/hooks/useForecast.ts` - Forecast data

---

## Phase 4: Build Feature Pages

### Step 4.1: Overview Page
- [ ] Create `src/app/page.tsx` (default overview)
- [ ] Create `src/components/features/overview/SummaryStats.tsx`
- [ ] Create `src/components/features/overview/YTDChart.tsx`
- [ ] Create `src/components/features/overview/RecentDividends.tsx`
- [ ] Create `src/components/features/overview/TopStocks.tsx`
- [ ] Integrate with API endpoints
- [ ] Add loading states
- [ ] Add error handling

### Step 4.2: Monthly Analysis Page
- [ ] Create `src/app/monthly/page.tsx`
- [ ] Create `src/components/features/monthly/MonthlyTable.tsx`
- [ ] Create `src/components/features/monthly/YearComparison.tsx`
- [ ] Create `src/components/features/monthly/MonthlyChart.tsx`
- [ ] Create `src/components/features/monthly/MonthSelector.tsx`
- [ ] Integrate with API endpoints

### Step 4.3: Stock Analysis Page
- [ ] Create `src/app/stocks/page.tsx` - Stock list
- [ ] Create `src/app/stocks/[symbol]/page.tsx` - Individual stock
- [ ] Create `src/components/features/stocks/StockList.tsx`
- [ ] Create `src/components/features/stocks/StockDetail.tsx`
- [ ] Create `src/components/features/stocks/StockHistory.tsx`
- [ ] Create `src/components/features/stocks/StockChart.tsx`
- [ ] Integrate with API endpoints

### Step 4.4: Dividend Screener Page
- [ ] Create `src/app/screener/page.tsx`
- [ ] Create `src/components/features/screener/FilterPanel.tsx`
- [ ] Create `src/components/features/screener/ResultsTable.tsx`
- [ ] Create `src/components/features/screener/SavedFilters.tsx`
- [ ] Create `src/components/features/screener/ExportResults.tsx`
- [ ] Integrate with API endpoints
- [ ] Add filter persistence (localStorage)

### Step 4.5: Forecast Page
- [ ] Create `src/app/forecast/page.tsx`
- [ ] Create `src/components/features/forecast/ForecastChart.tsx`
- [ ] Create `src/components/features/forecast/ScenarioBuilder.tsx`
- [ ] Create `src/components/features/forecast/ForecastSettings.tsx`
- [ ] Create `src/components/features/forecast/ConfidenceInterval.tsx`
- [ ] Integrate with API endpoints

### Step 4.6: PDF Reports Page
- [ ] Create `src/app/reports/page.tsx`
- [ ] Create `src/components/features/reports/ReportBuilder.tsx`
- [ ] Create `src/components/features/reports/TemplateSelector.tsx`
- [ ] Create `src/components/features/reports/ReportHistory.tsx`
- [ ] Create `src/components/features/reports/DownloadButton.tsx`
- [ ] Integrate with API endpoints
- [ ] Handle PDF download

---

## Phase 5: Styling & Polish

### Step 5.1: Implement Dark Mode
- [ ] Configure dark mode in `tailwind.config.ts`
- [ ] Add theme toggle component
- [ ] Update all components with dark mode styles
- [ ] Persist theme preference (localStorage)

### Step 5.2: Responsive Design
- [ ] Test all pages on mobile (375px)
- [ ] Test on tablet (768px)
- [ ] Test on desktop (1920px)
- [ ] Adjust charts for mobile
- [ ] Adjust tables for mobile (horizontal scroll or cards)
- [ ] Test sidebar on mobile

### Step 5.3: Add Animations
- [ ] Page transitions
- [ ] Chart loading animations
- [ ] Hover effects on cards
- [ ] Skeleton loaders for data fetching
- [ ] Success/error toast animations

### Step 5.4: Accessibility
- [ ] Add ARIA labels
- [ ] Keyboard navigation
- [ ] Focus indicators
- [ ] Screen reader support
- [ ] Color contrast checks

### Step 5.5: Performance Optimization
- [ ] Implement React.memo where needed
- [ ] Optimize chart re-renders
- [ ] Add proper loading states
- [ ] Implement error boundaries
- [ ] Add service worker for caching (optional)

---

## Phase 6: Data Migration & Testing

### Step 6.1: Data Source Setup
- [ ] Update backend to read from `data/dividends.csv`
- [ ] Add data validation
- [ ] Create data backup
- [ ] Test with current data

### Step 6.2: Integration Testing
- [ ] Test all API endpoints with frontend
- [ ] Test error scenarios
- [ ] Test loading states
- [ ] Test empty states
- [ ] Cross-browser testing (Chrome, Firefox, Safari)

### Step 6.3: User Acceptance Testing
- [ ] Compare features with original Streamlit app
- [ ] Verify all calculations are correct
- [ ] Check all visualizations match
- [ ] Test all user workflows
- [ ] Document any differences

---

## Phase 7: Deployment

### Step 7.1: Backend Deployment
- [ ] Choose hosting (Railway, Render, DigitalOcean, AWS)
- [ ] Configure environment variables
- [ ] Setup database (if needed)
- [ ] Deploy backend
- [ ] Test deployed API endpoints
- [ ] Setup monitoring/logging

### Step 7.2: Frontend Deployment
- [ ] Choose hosting (Vercel, Netlify, Cloudflare Pages)
- [ ] Configure environment variables
- [ ] Update API_URL to production backend
- [ ] Deploy frontend
- [ ] Test production build
- [ ] Setup custom domain (optional)

### Step 7.3: Post-Deployment
- [ ] Monitor performance
- [ ] Check error logs
- [ ] Test all features in production
- [ ] Create backup strategy
- [ ] Document deployment process

---

## Phase 8: Documentation & Cleanup

### Step 8.1: Code Documentation
- [ ] Add JSDoc comments to key functions
- [ ] Document API endpoints (OpenAPI/Swagger)
- [ ] Create component documentation
- [ ] Add inline code comments where needed

### Step 8.2: User Documentation
- [ ] Create README.md with:
  - Project overview
  - Installation instructions
  - Development setup
  - Deployment guide
  - Environment variables
- [ ] Create CHANGELOG.md
- [ ] Add screenshots to README

### Step 8.3: Cleanup
- [ ] Remove old Streamlit files (or keep in `/legacy` folder)
- [ ] Clean up unused dependencies
- [ ] Remove console.logs and debug code
- [ ] Run linters (ESLint, Prettier, Black, Ruff)
- [ ] Final code review

---

## Timeline Estimate

- **Phase 1 (Backend)**: 2-3 days
- **Phase 2 (Frontend Setup)**: 1 day
- **Phase 3 (Core UI)**: 2-3 days
- **Phase 4 (Feature Pages)**: 5-7 days
- **Phase 5 (Polish)**: 2-3 days
- **Phase 6 (Testing)**: 2-3 days
- **Phase 7 (Deployment)**: 1 day
- **Phase 8 (Documentation)**: 1 day

**Total Estimated Time**: 16-24 days

---

## Success Criteria

- [ ] All features from Streamlit app are functional
- [ ] Performance is better than Streamlit version
- [ ] UI is modern and responsive
- [ ] No data calculation discrepancies
- [ ] Application is deployed and accessible
- [ ] Documentation is complete

---

## Rollback Plan

If migration encounters critical issues:
1. Keep original Streamlit app in `/legacy` folder
2. Keep original data processing logic intact
3. Can revert to Streamlit while debugging new version
4. Test new version alongside old version before full switch

---

## Notes

- Keep both versions running during migration for comparison
- Test calculations thoroughly - financial data must be accurate
- Consider adding features that were difficult in Streamlit:
  - Real-time updates
  - Better mobile experience
  - User authentication (future)
  - Multiple portfolios (future)
  - Export to Excel (future)

---

## Questions to Address During Migration

1. Should we add a database or keep CSV files?
2. Do we want user authentication for multiple users?
3. Should we add real-time stock price updates?
4. Do we want to add more advanced forecasting models?
5. Should we implement data caching strategies?

---

*Last Updated: 2025-10-16*
*Version: 1.0*
