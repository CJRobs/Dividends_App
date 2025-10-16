# How to Run Your Dividend Dashboard

## 🚀 Quick Start (Easiest Way)

### Step 1: Start the Application

**Double-click this file:** `start-dividend-app.command`

That's it! The script will:
1. ✅ Start the backend server
2. ✅ Start the frontend server
3. ✅ Automatically open your browser to the dashboard

**Wait about 20 seconds** for everything to start, then your browser will open automatically!

### Step 2: Use Your Dashboard

Your browser will open to: `http://localhost:3000`

You'll see:
- 📊 Portfolio Overview page with all your dividend data
- 💰 Total dividends and YTD performance
- 📈 Top dividend-paying stocks
- 💵 Recent dividend payments

### Step 3: Stop the Application

**Option A:** Close the Terminal window that opened

**Option B:** Double-click `stop-dividend-app.command`

**Option C:** In the Terminal window, press `Ctrl+C`

---

## 📱 Creating a Desktop Icon (Recommended!)

### Make it Look Professional

**1. Open Finder**

**2. Navigate to:** `/Users/cameronroberts/Finances/dividends/`

**3. Find:** `start-dividend-app.command`

**4. Right-click → Make Alias**

**5. Drag the alias to your Desktop**

**6. Rename it to:** "Dividend Dashboard"

**7. Change the icon (optional):**
   - Download a finance/chart icon image
   - Right-click the icon file → Get Info → Click the icon at top-left → Cmd+C
   - Right-click your "Dividend Dashboard" alias → Get Info → Click the icon at top-left → Cmd+V

Now you have a **clickable desktop icon**! 🎉

---

## 🖥️ Alternative: Use Automator for a Real App Icon

For an even more professional look, create a macOS application:

### Step-by-Step

**1. Open Automator**
   - Spotlight (Cmd+Space) → type "Automator" → Enter

**2. Create New Application**
   - File → New
   - Select "Application"

**3. Add "Run Shell Script"**
   - Search for "Run Shell Script" in the left panel
   - Drag it to the right workflow area

**4. Paste This Script:**

```bash
#!/bin/bash

# Navigate to dividends directory
cd /Users/cameronroberts/Finances/dividends

# Run the startup script
./start-dividend-app.command

# Keep the app running
sleep 30
```

**5. Save the Application**
   - File → Save
   - Name: "Dividend Dashboard"
   - Location: Desktop (or Applications folder)
   - Format: Application

**6. Done!**

Now you have `Dividend Dashboard.app` on your desktop that looks and works like a regular Mac app!

---

## 🔧 Troubleshooting

### Problem: "Permission Denied"

**Solution:**
```bash
cd /Users/cameronroberts/Finances/dividends
chmod +x start-dividend-app.command
chmod +x stop-dividend-app.command
```

### Problem: "Port Already in Use"

**Solution:** Run the stop script first:
```bash
./stop-dividend-app.command
```

Then try starting again.

### Problem: Backend Won't Start

**Solution:** Check your virtual environment:
```bash
cd backend
source venv/bin/activate
python -c "import fastapi; print('FastAPI installed!')"
```

If it says "No module named fastapi":
```bash
pip install -r requirements.txt
```

### Problem: Frontend Won't Start

**Solution:** Reinstall dependencies:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
```

### Problem: Browser Doesn't Open Automatically

**Solution:** Manually open your browser and go to:
- Dashboard: `http://localhost:3000`
- API Docs: `http://localhost:8000/docs`

---

## 📊 What You'll See

### When You Start the App

The Terminal will show:
```
╔════════════════════════════════════════════════════════════╗
║      📊 Starting Dividend Portfolio Dashboard 📊          ║
╚════════════════════════════════════════════════════════════╝

🚀 Starting FastAPI backend...
   ✓ Backend started
⏳ Waiting for backend to initialize...
   ✓ Backend is healthy!

🎨 Starting Next.js frontend...
   ✓ Frontend started
⏳ Waiting for frontend to build and start...

🌐 Opening dashboard in your default browser...

╔════════════════════════════════════════════════════════════╗
║                    ✅ Dashboard Running!                   ║
╠════════════════════════════════════════════════════════════╣
║  📊 Dashboard:  http://localhost:3000                      ║
║  🔧 API Docs:   http://localhost:8000/docs                 ║
╚════════════════════════════════════════════════════════════╝
```

### In Your Browser

You'll see:
- **Header** - Navigation and currency selector
- **Sidebar** - 6 menu options (Overview, Monthly, Stocks, etc.)
- **Overview Page** - With 4 metric cards:
  - Total Dividends
  - YTD Dividends (with % change)
  - Unique Stocks
  - Average Dividend
- **Top Stocks** - Your best dividend payers
- **Recent Dividends** - Latest payments

---

## 🎯 Daily Usage

### Starting Your Day

1. **Double-click** the desktop icon
2. **Wait 20 seconds**
3. **Use your dashboard!**

### During the Day

- Dashboard stays open in your browser
- Make changes to data → will auto-update
- Switch between pages using the sidebar

### Ending Your Day

1. **Close the browser tab** (dashboard closes)
2. **Click the stop script** or close Terminal (servers stop)

---

## 🚀 Auto-Start on Login (Optional)

Want the dashboard to start automatically when you login?

### Method 1: Login Items

1. **System Preferences** → Users & Groups
2. Click your username
3. **Login Items** tab
4. Click **"+"** button
5. Select your `Dividend Dashboard.app`
6. ✅ Done! It will auto-start on login

### Method 2: Keep It Running Always

If you want it running 24/7:
1. Start the dashboard
2. Keep the Terminal window minimized
3. Don't close it!

The dashboard uses minimal resources when idle.

---

## 📂 File Structure

```
/Users/cameronroberts/Finances/dividends/
├── start-dividend-app.command    ← Double-click to START
├── stop-dividend-app.command     ← Double-click to STOP
├── backend/                      ← FastAPI server
├── frontend/                     ← Next.js web app
├── dividends/                    ← Your CSV data
├── backend.log                   ← Backend logs (auto-created)
└── frontend.log                  ← Frontend logs (auto-created)
```

---

## 💡 Tips

1. **Bookmark it!** Even easier than desktop icon:
   - Start the app
   - In browser: Cmd+D to bookmark `http://localhost:3000`
   - Drag bookmark to bookmarks bar

2. **Monitor health:**
   - Visit `http://localhost:8000/health` to check backend status

3. **View logs:**
   ```bash
   tail -f backend.log    # Watch backend logs
   tail -f frontend.log   # Watch frontend logs
   ```

4. **Update data:**
   - Add new CSV files to `dividends/` folder
   - Restart the app or visit `http://localhost:8000/api/reload-data`

---

## ✅ Summary

**To Run:**
1. Double-click `start-dividend-app.command`
2. Wait 20 seconds
3. Browser opens automatically → Use your dashboard!

**To Stop:**
1. Close Terminal window
   OR
2. Double-click `stop-dividend-app.command`

**That's it!** Super simple. 🎉

---

## 🆘 Need Help?

- Check logs: `backend.log` and `frontend.log`
- Health check: `http://localhost:8000/health`
- API docs: `http://localhost:8000/docs`
- See troubleshooting section above

---

**Enjoy your new professional dividend tracking dashboard!** 📊💰
