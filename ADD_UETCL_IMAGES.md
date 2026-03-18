# 🎨 How to Add UETCL Images

The application is already configured to use UETCL branding. You just need to add the image files.

## 📁 Required Images

Place these two images in the `static/images/` folder:

### 1. **UETCL Logo** (`uetcl_logo.png`)
- **Location:** `static/images/uetcl_logo.png`
- **Recommended size:** 200x200 pixels (or similar square/rectangular)
- **Format:** PNG (with transparent background preferred)
- **Used in:** Dashboard header and login page

### 2. **Login Background** (`uetcl_background.jpg`)
- **Location:** `static/images/uetcl_background.jpg`
- **Recommended size:** 1920x1080 pixels (Full HD)
- **Format:** JPG or PNG
- **Used in:** Login page background
- **Suggestion:** Use an image of transmission lines, substations, or Uganda landscape

---

## 🔍 Where to Get the Images

### Option 1: Official UETCL Website
1. Visit: **https://www.uetcl.go.ug/**
2. Right-click on the UETCL logo → "Save image as..."
3. Save as `uetcl_logo.png` in `static/images/`
4. For background: Look for transmission line photos on their website

### Option 2: Create Placeholder Images
If you can't access the official images, the app will work with fallback text "UETCL".

---

## ✅ Installation Steps

### Step 1: Create the images folder (if it doesn't exist)
```powershell
mkdir static\images
```

### Step 2: Add the logo
1. Download or copy `uetcl_logo.png`
2. Place it in: `static\images\uetcl_logo.png`

### Step 3: Add the background
1. Download or copy `uetcl_background.jpg`
2. Place it in: `static\images\uetcl_background.jpg`

### Step 4: Restart the server
```powershell
python run.py
```

---

## 🎨 What You'll See

### **With Images:**
- ✅ UETCL logo appears in dashboard header
- ✅ UETCL logo appears on login page
- ✅ Beautiful transmission line background on login page
- ✅ Professional UETCL branding throughout

### **Without Images:**
- ⚠️ Text fallback "UETCL" shows instead of logo
- ⚠️ Solid blue gradient background on login page
- ✅ All functionality still works perfectly!

---

## 🔧 Current Configuration

The application is already configured with:
- **Brand Color:** UETCL Dark Blue (#003366)
- **Company Name:** Uganda Electricity Transmission Company Limited (UETCL)
- **Logo Fallback:** Text "UETCL" displays if image not found
- **Background Fallback:** Blue gradient if background image not found

---

## 📝 Notes

- The app works perfectly without images (uses fallbacks)
- Images are optional but recommended for professional appearance
- You can update images anytime without code changes
- Just replace the files in `static/images/` and refresh browser

---

**The application is fully functional with or without images!** 🎉

