import os, io, base64, lzma
from flask import Flask, request, render_template, send_file, redirect, url_for, flash
from PIL import Image
import tempfile

app = Flask(__name__)
app.secret_key = 'themostpogkey'

MAX_PIXELS = 90000
HEADER_MAGIC = b'POG'  # The magic string to mark the start of a .pog file

# Temporary directory for storing files
temp_dir = tempfile.gettempdir()

def check_image_size(width, height):
    return width * height <= MAX_PIXELS

def resize_image(img, max_pixels):
    width, height = img.size
    total_pixels = width * height
    if total_pixels <= max_pixels:
        return img, False  # No resizing needed, image is already within limits
    
    scaling_factor = (max_pixels / total_pixels) ** 0.5
    new_width = int(width * scaling_factor)
    new_height = int(height * scaling_factor)
    resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    return resized_img, True

def get_pixel_hex(img, x, y):
    r, g, b, a = img.getpixel((x, y))
    return "{:02x}{:02x}{:02x}{:02x}".format(r, g, b, a)

def hex_to_rgba(hex_color):
    if len(hex_color) == 8:
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4, 6))
    else:
        raise ValueError("Hex string should be 8 characters long for RGBA.")

def get_4_bytes(byte_data, start_index):
    if start_index < 0 or start_index >= len(byte_data):
        raise ValueError("Start index is out of range")
    return byte_data[start_index:start_index + 4]

# Routes

@app.route('/')
def home():
    return render_template('home.html')

# Convert Image to .pog with compression choice
@app.route('/convert_to_pog')
def convert_to_pog_page():
    return render_template('convert_to_pog.html')

@app.route('/process_pog', methods=['POST'])
def process_pog():
    if 'image' not in request.files or request.files['image'].filename == '':
        return "No image uploaded"
    
    file = request.files['image']
    compression = request.form.get('compression')  # Get the compression type from form
    img = Image.open(file)
    img = img.convert('RGBA')

    # Resize if necessary
    img, resized = resize_image(img, MAX_PIXELS)

    if resized:
        flash("Image was too large and has been resized to fit within the limit.")

    width, height = img.size
    bwidth = width.to_bytes(length=4, byteorder='little')
    bheight = height.to_bytes(length=4, byteorder='little')

    pog_data = bwidth + bheight
    for iy in range(height):
        for ix in range(width):
            hex_value = get_pixel_hex(img, ix, iy)
            pog_data += bytes.fromhex(hex_value)

    # Add the header before saving the .pog file
    if compression == 'lzma':
        version = 1  # LZMA compressed version
        header = HEADER_MAGIC + bytes([version])
        pog_data = lzma.compress(pog_data)
    else:
        version = 0  # No compression
        header = HEADER_MAGIC + bytes([version])

    final_pog_data = header + pog_data

    # Save the .pog file to a temporary file
    temp_file_path = os.path.join(temp_dir, 'converted.pog')
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(final_pog_data)

    return redirect(url_for('download_pog'))

@app.route('/download_pog')
def download_pog():
    temp_file_path = os.path.join(temp_dir, 'converted.pog')

    if os.path.exists(temp_file_path):
        return render_template('download_pog.html', file_ready=True)
    else:
        return render_template('download_pog.html', file_ready=False)

@app.route('/download_file')
def download_file():
    temp_file_path = os.path.join(temp_dir, 'converted.pog')

    if os.path.exists(temp_file_path):
        return send_file(temp_file_path, as_attachment=True, download_name="converted.pog", mimetype='application/octet-stream')
    else:
        return "File not found", 404

# Route for converting .pog to image
@app.route('/convert_to_image')
def convert_to_image_page():
    return render_template('convert_to_image.html')

@app.route('/process_image', methods=['POST'])
def process_image():
    if 'pogfile' not in request.files or request.files['pogfile'].filename == '':
        return "No .pog file uploaded"
    
    file = request.files['pogfile']
    pog_data = file.read()

    # Check if the first 3 bytes are the magic header "POG"
    if pog_data[:3] != HEADER_MAGIC:
        return "Invalid .pog file format"

    # Check version (4th byte)
    ver = pog_data[3]
    pog_data = pog_data[4:]  # Skip the header and version byte

    if ver == 1:
        # Decompress if version is 1
        pog_data = lzma.decompress(pog_data)

    # Extract width and height from the first 8 bytes
    width = int.from_bytes(pog_data[0:4], byteorder='little')
    height = int.from_bytes(pog_data[4:8], byteorder='little')

    # Create a new image
    img = Image.new("RGBA", (width, height))
    index = 8  # Start after the width and height bytes

    for iy in range(height):
        for ix in range(width):
            hex_color = get_4_bytes(pog_data, index).hex().upper()
            img.putpixel((ix, iy), hex_to_rgba(hex_color))
            index += 4

    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, as_attachment=True, download_name="converted.png", mimetype='image/png')

# Route for viewing .pog as an image
@app.route('/view_pog')
def view_pog_page():
    return render_template('view_pog.html')

@app.route('/display_pog', methods=['POST'])
def display_pog():
    if 'pogfile' not in request.files or request.files['pogfile'].filename == '':
        return "No .pog file uploaded"
    
    file = request.files['pogfile']
    pog_data = file.read()

    # Check if the first 3 bytes are the magic header "POG"
    if pog_data[:3] != HEADER_MAGIC:
        return "Invalid .pog file format"

    # Check version (4th byte)
    ver = pog_data[3]
    pog_data = pog_data[4:]  # Skip the header and version byte

    if ver == 1:
        # Decompress if version is 1
        pog_data = lzma.decompress(pog_data)

    # Extract width and height from the next 8 bytes
    width = int.from_bytes(pog_data[0:4], byteorder='little')
    height = int.from_bytes(pog_data[4:8], byteorder='little')

    # Initialize a new RGBA image with the extracted width and height
    img = Image.new("RGBA", (width, height))

    # Pixel data starts after the width and height (byte 8 onwards)
    index = 8
    for iy in range(height):
        for ix in range(width):
            hex_color = get_4_bytes(pog_data, index).hex().upper()
            img.putpixel((ix, iy), hex_to_rgba(hex_color))
            index += 4

    # Convert the image to a byte stream to display as PNG
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    # Base64 encode the image for displaying in HTML
    img_base64 = base64.b64encode(img_io.getvalue()).decode('utf-8')

    return render_template('display_image.html', img_data=img_base64)

if __name__ == '__main__':
    app.run(debug=False)
