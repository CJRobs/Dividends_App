# Troubleshooting Guide

## Problem: Network Error in Browser

### What You're Seeing
```
Network Error: "Network Error"
src/lib/api.ts (42:15)
```

### Cause
The frontend (Next.js) can't connect to the backend (FastAPI) - backend isn't running.

### Solution 1: Wait Longer
The backend takes about 5-10 seconds to start. **Refresh your browser** after waiting.

### Solution 2: Check Backend is Running

**Open Terminal and run:**
```bash
curl http://localhost:8000/health
```

**Expected output:**
```json
{
  "status": "healthy",
  "data_loaded": true,
  "record_count": 433,
  ...
}
```

**If you get an error**, the backend isn't running. Start it manually:

```bash
cd /Users/cameronroberts/Finances/dividends/backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Solution 3: Check Backend Logs

```bash
cd /Users/cameronroberts/Finances/dividends
tail -50 backend.log
```

Look for errors in the log.

### Solution 4: Restart Everything

**Stop all processes:**
```bash
lsof -ti:8000,3000 | xargs kill -9
```

**Start again:**
```bash
./start-dividend-app.command
```

---

## Problem: Backend Won't Start

### Symptom
Backend.log shows errors or process dies immediately.

### Common Causes & Solutions

#### 1. Virtual Environment Not Activated

**Fix:**
```bash
cd backend
source venv/bin/activate
python -c "import fastapi; print('OK')"
```

If you get "No module named fastapi":
```bash
pip install -r requirements.txt
```

#### 2. Data Files Not Found

**Check:**
```bash
ls -la dividends/*.csv
```

**Fix:** Update `backend/.env`:
```
DATA_PATH=../dividends
```

#### 3. Port Already in Use

**Check:**
```bash
lsof -i:8000
```

**Fix:**
```bash
lsof -ti:8000 | xargs kill -9
```

---

## Problem: Frontend Won't Start

### Symptom
Frontend.log shows errors or npm fails.

### Solutions

#### 1. Node Modules Corrupted

```bash
cd frontend
rm -rf node_modules package-lock.json .next
npm install
```

#### 2. Port Already in Use

```bash
lsof -i:3000
lsof -ti:3000 | xargs kill -9
```

#### 3. Build Cache Issues

```bash
cd frontend
rm -rf .next
npm run dev
```

---

## Problem: Data Not Loading

### Symptom
Dashboard shows "No data" or empty.

### Check Backend Health

```bash
curl http://localhost:8000/health
```

Should show:
```json
{
  "status": "healthy",
  "data_loaded": true,
  "record_count": 433
}
```

If `data_loaded: false`, check:

1. **CSV files exist:**
   ```bash
   ls dividends/*.csv
   ```

2. **Backend .env is correct:**
   ```bash
   cat backend/.env | grep DATA_PATH
   ```
   Should show: `DATA_PATH=../dividends`

3. **Reload data:**
   ```bash
   curl -X POST http://localhost:8000/api/reload-data
   ```

---

## Problem: Startup Script Won't Run

### Symptom
Double-clicking `start-dividend-app.command` does nothing.

### Solution

**Make it executable:**
```bash
chmod +x /Users/cameronroberts/Finances/dividends/start-dividend-app.command
```

**Or run from Terminal:**
```bash
cd /Users/cameronroberts/Finances/dividends
./start-dividend-app.command
```

---

## Quick Health Checks

### Is Backend Running?
```bash
curl http://localhost:8000/health
```

### Is Frontend Running?
```bash
curl http://localhost:3000
```

### Check All Processes
```bash
lsof -i:8000,3000
```

### View Live Logs
```bash
# Backend
tail -f backend.log

# Frontend
tail -f frontend.log
```

---

## Complete Reset

If nothing works, do a complete reset:

### Step 1: Stop Everything
```bash
cd /Users/cameronroberts/Finances/dividends
lsof -ti:8000,3000 | xargs kill -9
```

### Step 2: Clean Backend
```bash
cd backend
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Clean Frontend
```bash
cd ../frontend
rm -rf node_modules package-lock.json .next
npm install
```

### Step 4: Test Backend Manually
```bash
cd ../backend
source venv/bin/activate
uvicorn app.main:app --reload
```

Leave this running, open new terminal:

### Step 5: Test Frontend Manually
```bash
cd frontend
npm run dev
```

### Step 6: Open Browser
```
http://localhost:3000
```

---

## Still Having Issues?

### Check These Common Problems

1. **Python Version**
   ```bash
   python3 --version  # Need 3.11+
   ```

2. **Node Version**
   ```bash
   node --version  # Need 18+
   ```

3. **Disk Space**
   ```bash
   df -h .
   ```

4. **Permissions**
   ```bash
   ls -la backend/.env
   ls -la dividends/*.csv
   ```

### Get Debug Info

Run this to collect debug info:
```bash
echo "=== System Info ==="
python3 --version
node --version
npm --version

echo -e "\n=== Backend Status ==="
curl -s http://localhost:8000/health || echo "Backend not running"

echo -e "\n=== Frontend Status ==="
curl -s http://localhost:3000 > /dev/null 2>&1 && echo "Frontend running" || echo "Frontend not running"

echo -e "\n=== Ports ==="
lsof -i:8000,3000

echo -e "\n=== Data Files ==="
ls -lh dividends/*.csv

echo -e "\n=== Backend Log (last 10 lines) ==="
tail -10 backend.log 2>/dev/null || echo "No backend.log"

echo -e "\n=== Frontend Log (last 10 lines) ==="
tail -10 frontend.log 2>/dev/null || echo "No frontend.log"
```

---

## Summary of Common Fixes

| Problem | Quick Fix |
|---------|-----------|
| Network Error | Wait 10s, refresh browser |
| Backend won't start | `cd backend && source venv/bin/activate && uvicorn app.main:app --reload` |
| Frontend won't start | `cd frontend && npm run dev` |
| Port in use | `lsof -ti:8000,3000 \| xargs kill -9` |
| No data | Check `backend/.env` DATA_PATH |
| Permission denied | `chmod +x start-dividend-app.command` |

---

## Contact for Help

If you've tried everything:

1. Check all logs: `backend.log` and `frontend.log`
2. Run health checks above
3. Verify data files exist
4. Try complete reset

Most issues are resolved by:
- Waiting for backend to fully start (10 seconds)
- Checking ports aren't already in use
- Verifying virtual environment is activated

---

**Remember:** The most common issue is **not waiting long enough** for the backend to start. Give it 10 seconds, then refresh your browser!
