#!/bin/bash

# Dividend Portfolio Dashboard Stopper
# Double-click this file to stop the application

echo "🛑 Stopping Dividend Portfolio Dashboard..."
echo ""

# Kill processes on ports 8000 and 3000
echo "Killing backend processes (port 8000)..."
lsof -ti:8000 | xargs kill -9 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Backend stopped"
else
    echo "   ℹ️  No backend running"
fi

echo "Killing frontend processes (port 3000)..."
lsof -ti:3000 | xargs kill -9 2>/dev/null
if [ $? -eq 0 ]; then
    echo "   ✓ Frontend stopped"
else
    echo "   ℹ️  No frontend running"
fi

echo ""
echo "✅ Dividend Dashboard stopped successfully!"
echo ""
echo "Press any key to close this window..."
read -n 1
