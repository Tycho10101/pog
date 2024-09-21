import os, sys
from PIL import Image
import lzma

print("Choose a Type")
print("0 - No compression")
print("1 - lzma compression")
ver = input(">")
if ver.isnumeric():
    ver = int(ver)
    if ver > 1 or ver < 0:
        print("Invalid option")
        quit()
else:
    print("Not a number")
    quit()

def get_pixel_hex(x, y):
    r, g, b, a = img.getpixel((x, y))
    hex_value = "{:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)
    
    return hex_value

for infile in sys.argv[1:]:
    f, e = os.path.splitext(infile)
    outfile = f + ".png"
    if infile != outfile:
        try:
            with Image.open(infile) as im:
                im.save(outfile)
        except OSError:
            print("cannot convert", infile)
print("converted to png")
img = Image.open(outfile)
img = img.convert('RGBA')

width, height = img.size

header = b'POG' + bytes([ver])
bwidth = width.to_bytes(length=4, byteorder=sys.byteorder)
bheight = height.to_bytes(length=4, byteorder=sys.byteorder)

pog = bwidth + bheight
print("pog-fing")
iy = 0
while iy < height:
    ix = 0
    while ix < width:
        hex = get_pixel_hex(ix, iy)
        pog = pog + bytes.fromhex(hex)
        ix += 1
    iy += 1
  
print("done")

if ver == 0:
    with open(f + ".pog", "wb") as pogfile:
        pogfile.write(header + pog)
if ver == 1:
    with open(f + ".pog", "wb") as pogfile:
        pogfile.write(header + lzma.compress(pog))
