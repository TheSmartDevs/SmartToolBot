#Copyright @ISmartDevs
#Channel t.me/TheSmartDev
#This Script Just For BG Removed Image Enhancement See rembg.py For Detailed Info Method By @abirxdhackz And @ISmartDevs
from PIL import Image

def enhance_resolution(input_path: str, output_path: str):
    """
    IMAGE INHANCE LIKE REMINI
    """
    with Image.open(input_path) as img:
        #HIGH QUALITY PROCESSING AND BG REMOVER
        high_res_img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        high_res_img.save(output_path, "PNG", quality=95)