"""
Create very simple placeholder images without PIL
Uses basic HTML/SVG approach
"""
import os

# Create static/images directory
os.makedirs('static/images', exist_ok=True)

# Create a simple SVG logo
svg_logo = '''<svg width="300" height="100" xmlns="http://www.w3.org/2000/svg">
  <rect width="300" height="100" fill="#003366"/>
  <text x="150" y="40" font-family="Arial" font-size="28" fill="#FFD700" text-anchor="middle" font-weight="bold">UETCL</text>
  <text x="150" y="65" font-family="Arial" font-size="11" fill="white" text-anchor="middle">Uganda Electricity Transmission</text>
  <text x="150" y="80" font-family="Arial" font-size="11" fill="white" text-anchor="middle">Company Limited</text>
  <polygon points="20,30 30,50 25,50 35,70 25,55 30,55" fill="#FFD700"/>
</svg>'''

with open('static/images/uetcl_logo.svg', 'w') as f:
    f.write(svg_logo)

print("✅ Created: static/images/uetcl_logo.svg")
print("\nNOTE: The app expects PNG format. Please:")
print("1. Visit the UETCL website: https://www.uetcl.go.ug/")
print("2. Download their official logo")
print("3. Save it as: static/images/uetcl_logo.png")
print("\nFor background image:")
print("1. Search Google Images for 'Uganda transmission tower'")
print("2. Download a nice image")
print("3. Save it as: static/images/uetcl_background.jpg")

