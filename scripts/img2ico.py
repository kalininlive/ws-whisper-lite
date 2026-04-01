import os
from PIL import Image
import sys

def convert_to_ico(png_path, ico_path):
    print(f"[*] Converting {png_path} to {ico_path}...")
    if not os.path.exists(png_path):
        print(f"[!] Error: {png_path} not found.")
        return
    try:
        img = Image.open(png_path)
        # Standard Windows icon sizes
        icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
        img.save(ico_path, sizes=icon_sizes)
        print(f"[+] Success: {ico_path} created successfully.")
    except Exception as e:
        print(f"[!] Error during conversion: {e}")

if __name__ == "__main__":
    # Ensure we are in the project root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(base_dir)
    
    png = os.path.join("assets", "icon.png")
    ico = os.path.join("assets", "icon.ico")
    convert_to_ico(png, ico)
