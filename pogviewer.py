import os, sys
from PIL import Image

def hex_to_rgba(hex_color):
    if len(hex_color) == 8:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
    else:
        raise ValueError("Hex string should be 8 characters long for RGBA.")
    
def set_pixel_color(x, y, hex_color):
    rgba_color = hex_to_rgba(hex_color)
    img.putpixel((x, y), rgba_color)

def get_4_bytes(byte_data, start_index):
    if start_index < 0 or start_index >= len(byte_data):
        raise ValueError("Start index is out of range")
    return byte_data[start_index:start_index + 4]

pogfile = open(sys.argv[1], "rb")
size = pogfile.read(8)
pog = pogfile.read()
pogfile.close()

width = size[0:4]
height = size[4:8]
width = int.from_bytes(width, byteorder=sys.byteorder)
height = int.from_bytes(height, byteorder=sys.byteorder)
size = (width, height)

img = Image.new("RGBA", size)

print("depog-fing")
iy = 0
while iy < height:
    ix = 0
    while ix < width:
        hex = (iy * width) + ix
        hex = get_4_bytes(pog, hex * 4).hex().upper()
        set_pixel_color(ix, iy, hex)
        ix += 1
    iy += 1

print("now showing")
img.show()
