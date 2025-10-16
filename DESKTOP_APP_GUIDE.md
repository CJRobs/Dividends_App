# Desktop Application Guide

How to run your Dividend Portfolio Dashboard as a desktop application with a clickable icon.

---

## Option 1: Simple Launcher Scripts (Recommended - Easiest)

### Create Startup Scripts

I'll create scripts that start both backend and frontend automatically, then open your browser.

#### For macOS (Your System)

**1. Create the launcher script:**

Create a file called `start-dividend-app.command` in your dividends folder:

```bash
#!/bin/bash

# Navigate to the dividends directory
cd "$(dirname "$0")"

# Kill any existing processes on ports 8000 and 3000
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Start backend in background
echo "Starting backend..."
cd backend
source venv/bin/activate
uvicorn app.main:app --reload > ../backend.log 2>&1 &
BACKEND_PID=$!
cd ..

# Wait for backend to start
echo "Waiting for backend to start..."
sleep 5

# Start frontend in background
echo "Starting frontend..."
cd frontend
npm run dev > ../frontend.log 2>&1 &
FRONTEND_PID=$!
cd ..

# Wait for frontend to start
echo "Waiting for frontend to start..."
sleep 10

# Open browser
echo "Opening browser..."
open http://localhost:3000

echo ""
echo "✅ Dividend Dashboard is running!"
echo "📊 Dashboard: http://localhost:3000"
echo "🔧 API Docs: http://localhost:8000/docs"
echo ""
echo "Backend PID: $BACKEND_PID (logs: backend.log)"
echo "Frontend PID: $FRONTEND_PID (logs: frontend.log)"
echo ""
echo "To stop the application, close this window or press Ctrl+C"
echo ""

# Keep script running
wait
```

**2. Make it executable:**

```bash
chmod +x start-dividend-app.command
```

**3. Double-click to run!**

Just double-click `start-dividend-app.command` and it will:
- Start the backend
- Start the frontend
- Open your browser automatically

---

## Option 2: Create macOS Desktop Icon with Automator (Professional Look)

### Step 1: Create the Application

1. **Open Automator**
   - Press `Cmd + Space`, type "Automator", press Enter

2. **Create New Application**
   - File → New
   - Choose "Application" type

3. **Add Run Shell Script Action**
   - In the left sidebar, find "Run Shell Script"
   - Drag it to the right panel
   - Change "Pass input" to "as arguments"

4. **Paste this script:**

```bash
#!/bin/bash

# Set the path to your dividends directory
DIVIDENDS_DIR="$HOME/Finances/dividends"
cd "$DIVIDENDS_DIR"

# Kill any existing processes
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# Start backend
osascript -e 'tell application "Terminal"
    do script "cd '"$DIVIDENDS_DIR"'/backend && source venv/bin/activate && uvicorn app.main:app --reload"
end tell'

# Wait for backend
sleep 5

# Start frontend
osascript -e 'tell application "Terminal"
    do script "cd '"$DIVIDENDS_DIR"'/frontend && npm run dev"
end tell'

# Wait for frontend
sleep 10

# Open browser
open http://localhost:3000

# Show success notification
osascript -e 'display notification "Dashboard is running at http://localhost:3000" with title "Dividend Dashboard" sound name "Glass"'
```

5. **Save the Application**
   - File → Save
   - Name: "Dividend Dashboard"
   - Location: Desktop (or Applications)
   - Format: Application

6. **Add a Custom Icon (Optional but Recommended)**

   **Create an icon:**
   - Find a chart/finance icon online or create one
   - Right-click the icon file → Get Info
   - Click the small icon in top-left → Cmd+C to copy
   - Right-click your "Dividend Dashboard.app" → Get Info
   - Click the small icon in top-left → Cmd+V to paste

### Step 2: Use Your Desktop Icon

Now you have "Dividend Dashboard.app" on your desktop!

**To use:**
- Double-click the icon
- Two Terminal windows will open (backend & frontend)
- Your browser will open automatically to the dashboard
- ✅ Done!

**To stop:**
- Close both Terminal windows
- Or run: `lsof -ti:8000,3000 | xargs kill -9`

---

## Option 3: Electron Desktop App (Most Professional)

Convert your web app to a true desktop application with Electron.

### Quick Setup

**1. Install Electron in your project:**

```bash
cd /Users/cameronroberts/Finances/dividends
npm init -y
npm install electron electron-builder concurrently wait-on
```

**2. Create `electron-main.js`:**

```javascript
const { app, BrowserWindow } = require('electron');
const { spawn } = require('child_process');
const path = require('path');

let backendProcess;
let frontendProcess;
let mainWindow;

function startBackend() {
  backendProcess = spawn('uvicorn', ['app.main:app', '--reload'], {
    cwd: path.join(__dirname, 'backend'),
    shell: true,
    env: { ...process.env, VIRTUAL_ENV: path.join(__dirname, 'backend/venv') }
  });

  backendProcess.stdout.on('data', (data) => {
    console.log(`Backend: ${data}`);
  });
}

function startFrontend() {
  frontendProcess = spawn('npm', ['run', 'dev'], {
    cwd: path.join(__dirname, 'frontend'),
    shell: true
  });

  frontendProcess.stdout.on('data', (data) => {
    console.log(`Frontend: ${data}`);
  });
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    icon: path.join(__dirname, 'icon.png'), // Add your icon
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true
    }
  });

  // Wait for services to start, then load
  setTimeout(() => {
    mainWindow.loadURL('http://localhost:3000');
  }, 15000); // 15 seconds for everything to start

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

app.on('ready', () => {
  startBackend();
  startFrontend();
  createWindow();
});

app.on('window-all-closed', () => {
  if (backendProcess) backendProcess.kill();
  if (frontendProcess) frontendProcess.kill();
  app.quit();
});

app.on('activate', () => {
  if (mainWindow === null) {
    createWindow();
  }
});
```

**3. Update `package.json`:**

```json
{
  "name": "dividend-dashboard",
  "version": "1.0.0",
  "main": "electron-main.js",
  "scripts": {
    "electron": "electron .",
    "dist": "electron-builder"
  },
  "build": {
    "appId": "com.dividend.dashboard",
    "mac": {
      "category": "public.app-category.finance",
      "icon": "icon.png"
    }
  }
}
```

**4. Run Electron App:**

```bash
npm run electron
```

**5. Build Desktop App:**

```bash
npm run dist
```

This creates a standalone `.app` file in the `dist/` folder!

---

## Option 4: Simple Browser Bookmark (Quickest)

If the backend and frontend are running, just:

1. **Start services** (use the script from Option 1)
2. **Open** `http://localhost:3000`
3. **Bookmark it** (Cmd+D)
4. **Add to Desktop:**
   - Drag bookmark to desktop
   - Or use "Add to Dock" in Chrome/Safari

---

## Recommended Approach for You

I recommend **Option 1 + Option 2 combined**:

1. I'll create the startup script for you
2. Then wrap it in an Automator app
3. You get a desktop icon that starts everything automatically

Let me create these files for you now!

---

## Automatic Startup (Optional)

### Make it start when you login:

**macOS:**

1. System Preferences → Users & Groups
2. Click your username
3. Login Items tab
4. Click "+" and add "Dividend Dashboard.app"
5. ✅ It will auto-start when you login!

**Or use LaunchAgent** (more reliable):

Create `~/Library/LaunchAgents/com.dividend.dashboard.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.dividend.dashboard</string>
    <key>ProgramArguments</key>
    <array>
        <string>/Users/cameronroberts/Finances/dividends/start-dividend-app.command</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.dividend.dashboard.plist
```

---

## Troubleshooting

### "Permission Denied" on .command file

```bash
chmod +x start-dividend-app.command
```

### Ports already in use

```bash
# Kill existing processes
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Backend not activating venv

Make sure the path in the script matches your actual location:
```bash
cd /Users/cameronroberts/Finances/dividends/backend
source venv/bin/activate
```

---

## Summary of Options

| Option | Ease | Professional | Startup Time |
|--------|------|--------------|--------------|
| **1. Shell Script** | ⭐⭐⭐⭐⭐ Easiest | ⭐⭐⭐ Good | ~15s |
| **2. Automator App** | ⭐⭐⭐⭐ Easy | ⭐⭐⭐⭐ Great | ~15s |
| **3. Electron** | ⭐⭐ Complex | ⭐⭐⭐⭐⭐ Best | ~5s |
| **4. Bookmark** | ⭐⭐⭐⭐⭐ Easiest | ⭐ Basic | Instant |

**My Recommendation:** Start with Option 2 (Automator App) - it's easy and gives you a nice desktop icon!

---

Let me know which option you'd like and I'll create the exact files you need!
