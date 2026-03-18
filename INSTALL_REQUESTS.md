# Installing the 'requests' Module

## ⚠️ Required for Real GIS Data Loading

The `requests` module is required to fetch real Uganda GIS data from OpenStreetMap.

---

## 🔧 Installation Steps

### Option 1: Using pip (Recommended)

Open your terminal in the project directory and run:

```powershell
python -m pip install requests
```

### Option 2: Using the virtual environment directly

```powershell
.venv\Scripts\python.exe -m pip install requests
```

### Option 3: Install all requirements

```powershell
python -m pip install -r requirements.txt
```

---

## ✅ Verify Installation

After installation, run:

```powershell
python -c "import requests; print('requests installed successfully!')"
```

You should see: `requests installed successfully!`

---

## 🚀 Then Start the Server

```powershell
python run.py
```

---

## 📝 What Happens Without 'requests'?

If `requests` is not installed:
- ✅ The application will still run
- ✅ All core features work (route optimization, etc.)
- ❌ Real-time GIS data loading from OSM will not work
- ⚠️ You'll see a warning message on startup

**To use real Uganda GIS data, you MUST install the `requests` module.**

---

## 🔍 Troubleshooting

### If installation fails:

1. **Check your internet connection**
2. **Try updating pip first:**
   ```powershell
   python -m pip install --upgrade pip
   ```
3. **Then install requests:**
   ```powershell
   python -m pip install requests
   ```

### If you see "Operation cancelled by user":
- Don't press Ctrl+C during installation
- Let the installation complete

### If you see "pip not found":
- Make sure you're in the virtual environment
- Activate it with: `.venv\Scripts\activate`
- Then try again

---

## 📦 Alternative: Download Local GIS Data

If you can't install `requests`, you can still use real GIS data by:

1. **Downloading GeoJSON files manually** (see QUICK_START_DOWNLOAD.md)
2. **Placing them in the data/ folders**
3. **The app will use local files instead of fetching from OSM**

---

**After installing `requests`, restart the server and the real GIS data loading will work!**

