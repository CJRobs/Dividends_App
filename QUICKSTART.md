# Quick Start Guide

Get your Dividend Portfolio Dashboard up and running in minutes!

## Prerequisites Check

```bash
# Check Node.js version (need 18+)
node --version

# Check Python version (need 3.11+)
python3 --version

# Check npm
npm --version
```

## 🚀 Start Backend (Terminal 1)

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Backend will start at:** `http://localhost:8000`

**API Docs:** `http://localhost:8000/docs`

## 🎨 Start Frontend (Terminal 2)

```bash
cd frontend
npm install
npm run dev
```

**Frontend will start at:** `http://localhost:3000`

## ✅ Verify Everything Works

1. **Backend Health Check:**
   - Open: `http://localhost:8000/health`
   - Should see: `{"status": "healthy", "data_loaded": true, ...}`

2. **Frontend:**
   - Open: `http://localhost:3000`
   - You should see the Overview page with your dividend data!

## 🎯 What's Working

- ✅ Backend API with FastAPI
- ✅ Frontend with Next.js + Tailwind CSS + shadcn/ui
- ✅ Overview page showing:
  - Total dividends
  - YTD performance
  - Top dividend-paying stocks
  - Recent dividend payments
- ✅ Responsive sidebar navigation
- ✅ Modern, professional UI

## 🔍 Troubleshooting

### Backend Issues

**"Data not loaded"**
```bash
# Check your data path in backend/.env
DATA_PATH=../dividends

# Verify CSV files exist
ls ../dividends/*.csv
```

**"Module not found"**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Frontend Issues

**"Cannot connect to API"**
```bash
# Check backend is running
curl http://localhost:8000/health

# Verify API URL in frontend/.env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**Build errors**
```bash
# Clear cache and rebuild
rm -rf .next node_modules
npm install
npm run dev
```

## 📁 Project Structure

```
dividends/
├── backend/          # FastAPI Backend (Port 8000)
│   ├── app/
│   │   ├── api/      # ✅ Overview endpoint working
│   │   ├── models/   # ✅ Pydantic models
│   │   ├── services/ # ✅ Data processing
│   │   └── main.py   # ✅ FastAPI app
│   └── .env          # Configure here
│
├── frontend/         # Next.js Frontend (Port 3000)
│   ├── src/
│   │   ├── app/      # ✅ Overview page
│   │   ├── components/
│   │   │   ├── layout/ # ✅ Sidebar, Header
│   │   │   └── ui/     # ✅ shadcn components
│   │   ├── hooks/    # ✅ Data fetching hooks
│   │   └── store/    # ✅ State management
│   └── .env.local    # Configure here
│
└── dividends/        # ✅ CSV data files
```

## 🎨 Current Features

### Working Now ✅
- **Overview Page** - Complete with metrics and charts
- **Responsive Layout** - Works on mobile, tablet, desktop
- **Modern UI** - Tailwind CSS + shadcn/ui components
- **Type-Safe** - Full TypeScript + Pydantic
- **Fast API** - REST API with automatic docs

### Coming Soon 🚧
- Monthly Analysis page
- Stock Analysis page
- Dividend Screener
- Forecast functionality
- PDF Reports
- Interactive charts with Recharts
- Dark mode toggle

## 🎯 Next Steps

1. **Explore the Overview page** - See your dividend data visualized
2. **Check the API docs** - `http://localhost:8000/docs`
3. **Review the migration plan** - See `MIGRATION_PLAN.md` for remaining features
4. **Customize** - Modify colors, add features, etc.

## 💡 Tips

- **Hot Reload**: Both frontend and backend support hot reload - changes appear instantly
- **API First**: All data flows through the REST API - easy to test and debug
- **Component Library**: Use shadcn/ui components - `npx shadcn@latest add [component]`
- **State Management**: Zustand for global state, TanStack Query for server state

## 📚 Documentation

- **Full README**: See `README_NEW.md` for comprehensive docs
- **Migration Plan**: See `MIGRATION_PLAN.md` for detailed architecture
- **API Docs**: `http://localhost:8000/docs` (when backend running)

## 🆘 Still Having Issues?

1. Make sure both terminals are running (backend + frontend)
2. Check no other services are using ports 8000 or 3000
3. Verify your CSV data files are in the correct location
4. Review the troubleshooting section in README_NEW.md

---

**Ready to continue?** Check `MIGRATION_PLAN.md` to see what features to build next!

The foundation is solid - now you can build out the remaining pages following the same patterns. 🚀
