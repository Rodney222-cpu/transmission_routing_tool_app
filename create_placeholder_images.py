"""
Create placeholder images for UETCL branding
Run this script to generate logo and background images
"""
from PIL import Image, ImageDraw, ImageFont
import os

# Create static/images directory if it doesn't exist
os.makedirs('static/images', exist_ok=True)

# 1. Create UETCL Logo (300x100 px)
print("Creating UETCL logo...")
logo = Image.new('RGB', (300, 100), color='#003366')
draw = ImageDraw.Draw(logo)

# Draw a simple logo with text
try:
    # Try to use a nice font
    font_large = ImageFont.truetype("arial.ttf", 24)
    font_small = ImageFont.truetype("arial.ttf", 12)
except:
    # Fallback to default font
    font_large = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Draw UETCL text
draw.text((150, 30), "UETCL", fill='#FFD700', anchor="mm", font=font_large)
draw.text((150, 60), "Uganda Electricity Transmission", fill='white', anchor="mm", font=font_small)
draw.text((150, 75), "Company Limited", fill='white', anchor="mm", font=font_small)

# Add a simple graphic element (lightning bolt)
draw.polygon([(20, 30), (30, 50), (25, 50), (35, 70), (25, 55), (30, 55)], fill='#FFD700')

logo.save('static/images/uetcl_logo.png')
print("✅ Logo saved to: static/images/uetcl_logo.png")

# 2. Create Login Background (1920x1080 px)
print("\nCreating login background...")
background = Image.new('RGB', (1920, 1080), color='#003366')
draw = ImageDraw.Draw(background)

# Create a gradient effect
for y in range(1080):
    # Gradient from dark blue to lighter blue
    r = int(0 + (0 * y / 1080))
    g = int(51 + (51 * y / 1080))
    b = int(102 + (51 * y / 1080))
    draw.line([(0, y), (1920, y)], fill=(r, g, b))

# Add some decorative elements (transmission towers silhouette)
# Tower 1
tower_x = 300
draw.polygon([
    (tower_x, 800), (tower_x + 10, 600), (tower_x + 5, 600), 
    (tower_x + 5, 400), (tower_x - 5, 400), (tower_x - 5, 600),
    (tower_x - 10, 600)
], fill='#001a33', outline='#FFD700')

# Tower 2
tower_x = 1600
draw.polygon([
    (tower_x, 850), (tower_x + 10, 650), (tower_x + 5, 650), 
    (tower_x + 5, 450), (tower_x - 5, 450), (tower_x - 5, 650),
    (tower_x - 10, 650)
], fill='#001a33', outline='#FFD700')

# Add power lines
draw.line([(310, 420), (1595, 470)], fill='#FFD700', width=2)
draw.line([(310, 440), (1595, 490)], fill='#FFD700', width=2)

background.save('static/images/uetcl_background.jpg', quality=95)
print("✅ Background saved to: static/images/uetcl_background.jpg")

print("\n" + "="*60)
print("✅ PLACEHOLDER IMAGES CREATED SUCCESSFULLY!")
print("="*60)
print("\nYou can now:")
print("1. Run the Flask app and see the images")
print("2. Replace these with official UETCL images later")
print("\nTo replace with official images:")
print("- Download official UETCL logo and save as: static/images/uetcl_logo.png")
print("- Download official background and save as: static/images/uetcl_background.jpg")

