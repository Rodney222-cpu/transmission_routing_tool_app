# Collaborator Setup Guide - Transmission Routing Tool

## Important: Repository Access Method

**You have been added as a COLLABORATOR** to the main repository, NOT through forking.

### Forking vs Collaborator Access:
- ❌ **Forking** creates a separate copy on your account (NOT what you should use)
- ✅ **Collaborator** gives you direct access to push/pull from the main repository

---

## Step-by-Step Setup for Collaborators

### Option 1: Fresh Start (RECOMMENDED if having sync issues)

If you're experiencing sync issues or are behind on updates, **start fresh**:

#### 1. Delete your local copy (if exists)
```bash
# Navigate to where your current project is
cd path/to/parent/folder

# Remove the old folder (Windows)
rmdir /s transmission_routing_tool

# OR on PowerShell
Remove-Item -Recurse -Force transmission_routing_tool
```

#### 2. Clone the repository fresh
```bash
# Clone the main repository directly (NOT a fork)
git clone https://github.com/Rodney222-cpu/transmission_routing_tool_app.git

# Navigate into the project
cd transmission_routing_tool_app
```

#### 3. Set up your Git identity
```bash
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

#### 4. Download GIS Data Files
**IMPORTANT:** The repository no longer includes large GIS data files. You need to download them separately:

```bash
# Run the data download scripts
python download_uganda_data.py
python download_dem_usgs.py
# Or any other download scripts provided
```

**Why?** GIS files (DEMs, shapefiles, GeoJSON) are too large for GitHub (>100MB each). They stay in your local `data/` folder but aren't tracked by Git.

#### 5. Set up the project
```bash
# Create virtual environment
python -m venv .venv

# Activate it (Windows)
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

### Option 2: Fix Existing Setup (If you want to keep current work)

If you have uncommitted work you want to keep:

#### 1. Save your current work
```bash
# Check what you have
git status

# Stash any uncommitted changes
git stash save "my current work"
```

#### 2. Remove fork remote (if you accidentally forked)
```bash
# Check your remotes
git remote -v

# If you see your own username in the URL, remove it
git remote remove origin

# Add the correct main repository
git remote add origin https://github.com/Rodney222-cpu/transmission_routing_tool_app.git
```

#### 3. Fetch and reset to latest
```bash
# Fetch all latest changes
git fetch origin

# Reset to match the main branch exactly
git reset --hard origin/main

# Apply your stashed work (if any)
git stash pop
```

---

## Daily Workflow - How to Pull Updates

### Before you start working each day:
```bash
# Make sure you're on main branch
git checkout main

# Pull latest changes
git pull origin main
```

### When you make changes:
```bash
# 1. Check what changed
git status

# 2. Add your changes
git add .

# 3. Commit with a message
git commit -m "Description of what you changed"

# 4. Push to main repository
git push origin main
```

---

## Common Issues & Solutions

### Issue: "Your branch is behind 'origin/main' by X commits"
**Solution:**
```bash
git pull origin main
```

### Issue: "Merge conflicts" when pulling
**Solution:**
```bash
# Option 1: Accept their changes (if you haven't made important local changes)
git reset --hard origin/main

# Option 2: Manually resolve conflicts
git pull origin main
# Edit the conflicting files, then:
git add .
git commit -m "Resolved merge conflicts"
```

### Issue: "Permission denied" when pushing
**Solution:** Make sure you're using the main repository URL, not a fork:
```bash
git remote -v
# Should show: Rodney222-cpu/transmission_routing_tool_app.git
# NOT your-username/transmission_routing_tool_app.git
```

### Issue: Large file errors when pushing
**Solution:** The `.gitignore` is now set up to exclude large GIS files. If you still get errors:
```bash
# Check what large files you're trying to push
git lfs ls-files

# Remove them from tracking
git rm --cached data/*.tif data/*.shp data/*.geojson
git commit -m "Remove large files from tracking"
git push
```

### Issue: GIS data not loading in the app
**Solution:** Download the required data files:
```bash
# Check what's in your data folder
dir data

# If folders are empty, run download scripts
python download_uganda_data.py
```

---

## Important Notes

### ✅ DO:
- Pull changes before starting work each day
- Commit frequently with clear messages
- Keep GIS data files in `data/` folder (they're ignored by Git)
- Use `git status` often to check your state

### ❌ DON'T:
- Don't try to commit large GIS files (.tif, .shp, .geojson)
- Don't use a forked version if you're a collaborator
- Don't ignore merge conflicts - resolve them immediately
- Don't work for days without pulling - sync daily

---

## Quick Reference Commands

```bash
# Check current status
git status

# See recent commits
git log --oneline -10

# Check remote repository URL
git remote -v

# Pull latest changes
git pull origin main

# Push your changes
git push origin main

# Download GIS data (first time only)
python download_uganda_data.py
```

---

## Need Help?

If you're still having issues:
1. Run `git status` and share the output
2. Run `git remote -v` and share the output
3. Describe what error you're seeing

The repository owner can help troubleshoot!

---

## Summary

**For new collaborators:**
1. Delete old folders
2. Clone fresh from main repository
3. Download GIS data separately
4. Pull before working each day
5. Push your changes when done

**Remember:** GIS data files stay local, code goes to GitHub! 🚀
