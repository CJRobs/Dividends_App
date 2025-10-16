#!/bin/bash

# Dividend Portfolio Dashboard Launcher
# Double-click this file to start the application

echo "╔════════════════════════════════════════════════════════════╗"
echo "║      📊 Starting Dividend Portfolio Dashboard 📊          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Navigate to the script's directory
cd "$(dirname "$0")"

# Kill any existing processes on ports 8000 and 3000
echo "🧹 Cleaning up any existing processes..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null
sleep 2

# Start backend in background
echo "🚀 Starting FastAPI backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..
echo "   ✓ Backend started (PID: $BACKEND_PID)"
echo "   📝 Backend logs: backend.log"

# Wait for backend to start
echo ""
echo "⏳ Waiting for backend to initialize..."
echo "   (This may take 5-10 seconds...)"

# Wait up to 30 seconds for backend to be healthy
COUNTER=0
until curl -s http://localhost:8000/health > /dev/null 2>&1; do
    sleep 1
    COUNTER=$((COUNTER+1))
    if [ $COUNTER -eq 30 ]; then
        echo "   ⚠️  Backend taking longer than expected. Check backend.log for errors."
        break
    fi
done

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✓ Backend is healthy and ready!"
else
    echo "   ⚠️  Backend might not be ready. Check backend.log"
fi

# Start frontend in background
echo ""
echo "🎨 Starting Next.js frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..
echo "   ✓ Frontend started (PID: $FRONTEND_PID)"
echo "   📝 Frontend logs: frontend.log"

# Wait for frontend to start
echo ""
echo "⏳ Waiting for frontend to build and start..."
sleep 12

# Open browser
echo ""
echo "🌐 Opening dashboard in your default browser..."
sleep 2
open http://localhost:3000

# Print success message
echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                    ✅ Dashboard Running!                   ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  📊 Dashboard:  http://localhost:3000                      ║"
echo "║  🔧 API Docs:   http://localhost:8000/docs                 ║"
echo "║  ❤️  Health:     http://localhost:8000/health              ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  Backend PID: $BACKEND_PID                                     ║"
echo "║  Frontend PID: $FRONTEND_PID                                    ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  📝 Logs:                                                  ║"
echo "║     Backend:  tail -f backend.log                          ║"
echo "║     Frontend: tail -f frontend.log                         ║"
echo "╠════════════════════════════════════════════════════════════╣"
echo "║  To STOP the application:                                  ║"
echo "║     1. Close this Terminal window, OR                      ║"
echo "║     2. Press Ctrl+C                                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Stopping Dividend Dashboard..."
    kill $BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    lsof -ti:8000 | xargs kill -9 2>/dev/null
    lsof -ti:3000 | xargs kill -9 2>/dev/null
    echo "✓ All processes stopped."
    echo "👋 Goodbye!"
    exit 0
}

# Trap exit signals
trap cleanup SIGINT SIGTERM EXIT

# Keep script running
echo "Press Ctrl+C to stop the dashboard..."
wait
