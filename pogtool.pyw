import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import os
import platform
import subprocess
import lzma

class POGConverterApp:
    def __init__(self, root):
        self.root = root
        self.root.title(".pog Tool")

        # Set window size and minimum size
        self.root.geometry("800x600")
        self.root.minsize(800, 600)

        # Detect system dark mode
        self.dark_mode = tk.BooleanVar(value=self.detect_dark_mode())

        # Configure the UI with system-detected dark mode
        self.configure_ui()

        # Create a frame for the options on the right
        self.options_frame = tk.Frame(self.root, bg=self.bg_color)
        self.options_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Create a canvas for the image on the left
        self.canvas = tk.Canvas(self.root, bg=self.canvas_bg_color)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add a separator (line) between options and image
        self.separator = ttk.Separator(self.root, orient="vertical")
        self.separator.pack(side=tk.RIGHT, fill=tk.Y, padx=5)

        # Zoom-related variables
        self.zoom_level = 1.0
        self.original_image = None
        self.image_on_canvas = None

        # Create buttons and checkboxes in the options frame
        self.create_options()

        # Bind mouse wheel scroll for zooming
        self.canvas.bind("<MouseWheel>", self.zoom_image)

    def configure_ui(self):
        # Define colors based on dark mode setting
        if self.dark_mode.get():
            self.bg_color = "#2e2e2e"
            self.fg_color = "#ffffff"
            self.button_bg_color = "#444444"
            self.canvas_bg_color = "#1e1e1e"
            self.checkbox_bg_color = "#2e2e2e"
            self.checkbox_fg_color = "#ffffff"
        else:
            self.bg_color = "#f0f0f0"
            self.fg_color = "#000000"
            self.button_bg_color = "#e0e0e0"
            self.canvas_bg_color = "#ffffff"
            self.checkbox_bg_color = "#f0f0f0"
            self.checkbox_fg_color = "#000000"

        # Apply colors to the main window
        self.root.configure(bg=self.bg_color)

    def create_options(self):
        # LZMA Compression Checkbox
        self.compression_var = tk.BooleanVar(value=True)
        self.compression_checkbox = tk.Checkbutton(
            self.options_frame, text="Use LZMA Compression", variable=self.compression_var,
            bg=self.checkbox_bg_color, fg=self.checkbox_fg_color,
            activebackground=self.checkbox_bg_color, activeforeground=self.checkbox_fg_color,
            selectcolor=self.button_bg_color
        )
        self.compression_checkbox.pack(pady=5)

        # Open file button
        self.open_button = tk.Button(
            self.options_frame, text="Open File", command=self.open_file,
            bg=self.button_bg_color, fg=self.fg_color
        )
        self.open_button.pack(pady=5)

        # Export buttons
        self.export_pog_button = tk.Button(
            self.options_frame, text="Export as POG", command=lambda: self.export_file("pog"),
            bg=self.button_bg_color, fg=self.fg_color
        )
        self.export_pog_button.pack(pady=5)

        # Export as PNG button
        self.export_png_button = tk.Button(
            self.options_frame, text="Export as PNG", command=lambda: self.export_file("png"),
            bg=self.button_bg_color, fg=self.fg_color
        )
        self.export_png_button.pack(pady=5)

        # Export to... dropdown menu
        self.export_menu_label = tk.Label(self.options_frame, text="Export to...", bg=self.bg_color, fg=self.fg_color)
        self.export_menu_label.pack(pady=5)
        
        self.export_menu = ttk.Combobox(self.options_frame, values=["ICO", "JPEG", "BMP", "ICNS", "WEBP"])
        self.export_menu.pack(pady=5)
        self.export_menu.bind("<<ComboboxSelected>>", self.export_other)

    def open_file(self):
        # Allow the user to select an image file to open
        filetypes = [("All supported image files", "*.png *.jpg *.jpeg *.bmp *.ico *.icns *.webp *.pog")]
        file_path = filedialog.askopenfilename(filetypes=filetypes)

        if file_path:
            if file_path.endswith(".pog"):
                self.load_pog(file_path)
            else:
                self.load_image(file_path)

    def load_image(self, file_path):
        # Load the image and display it on the canvas
        try:
            self.original_image = Image.open(file_path)
            self.display_image(self.original_image)
        except Exception as e:
            messagebox.showerror("Error", f"Error loading image: {e}")

    def load_pog(self, file_path):
        try:
            with open(file_path, "rb") as f:
                header = f.read(3)  # Read the 3-byte header
                if header != b'POG':
                    raise ValueError("Invalid POG file header")

                version = f.read(1)  # Read the version byte
                compressed = version[0] == 1  # Check if the file is compressed

                # Read the pixel data
                pog_data = f.read()  # Read the rest as pixel data

                if compressed:
                    pog_data = lzma.decompress(pog_data)  # Decompress if necessary

                if len(pog_data) < 8:
                    raise ValueError("Insufficient data for width and height")

                width = int.from_bytes(pog_data[0:4], byteorder='little')
                height = int.from_bytes(pog_data[4:8], byteorder='little')
                pixel_data = pog_data[8:]  # Get the remaining data as pixel data

                # Check if pixel data length matches expected size
                expected_pixel_data_length = width * height * 4  # RGBA
                if len(pixel_data) != expected_pixel_data_length:
                    raise ValueError("Pixel data length does not match expected size")

                # Create a new RGBA image
                img = Image.new("RGBA", (width, height))

                # Set the pixel data in the image
                pixels = img.load()
                for y in range(height):
                    for x in range(width):
                        i = (y * width + x) * 4
                        r = pixel_data[i]
                        g = pixel_data[i + 1]
                        b = pixel_data[i + 2]
                        a = pixel_data[i + 3]
                        pixels[x, y] = (r, g, b, a)
    
                # Display the image
                self.original_image = img
                self.display_image(self.original_image)
        except Exception as e:
            print(f"Error loading POG file: {e}")

    def display_image(self, img):
        # Resize the image based on zoom level and display it on the canvas
        width, height = img.size
        zoomed_image = img.resize((int(width * self.zoom_level), int(height * self.zoom_level)), Image.NEAREST)
        self.tk_image = ImageTk.PhotoImage(zoomed_image)

        # Clear the canvas before displaying a new image
        self.canvas.delete("all")

        # Calculate the position to center the image
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        x = (canvas_width - zoomed_image.width) // 2
        y = (canvas_height - zoomed_image.height) // 2

        self.image_on_canvas = self.canvas.create_image(x, y, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def zoom_image(self, event):
        # Zoom in or out based on the scroll direction
        if event.delta > 0:
            self.zoom_level *= 1.1  # Zoom in
        else:
            self.zoom_level /= 1.1  # Zoom out

        if self.original_image:
            self.display_image(self.original_image)

    def export_file(self, file_type):
        # Define file extensions based on export type
        if file_type == "pog":
            ext = ".pog"
            filetypes = [("POG files", "*.pog")]  # Only POG files
        elif file_type == "png":
            ext = ".png"  # Default to PNG for images
            filetypes = [("PNG files", "*.png")]

        save_path = filedialog.asksaveasfilename(defaultextension=ext,
                                               filetypes=filetypes)
        if save_path:
            if file_type == "pog":
                self.save_as_pog(save_path)
            elif file_type == "png":
                self.save_as_image(save_path, "png")

    def export_other(self, event):
        # Export the image in the selected format from the dropdown
        selected_format = self.export_menu.get().lower()
        if selected_format:
            save_path = filedialog.asksaveasfilename(defaultextension=f".{selected_format}",
                                                       filetypes=[(f"{selected_format.upper()} files", f"*.{selected_format}")])
            if save_path:
                self.save_as_image(save_path, selected_format)

    def save_as_image(self, save_path, file_format):
        if self.original_image:
            try:
                self.original_image.save(save_path, file_format.upper())
                messagebox.showinfo("Success", f"File saved as {file_format.upper()}!")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving image: {e}")

    def save_as_pog(self, save_path):
        # Save the current image as a .pog file (custom format)
        try:
            # Get the width and height of the original image
            self.original_image = self.original_image.convert('RGBA')
            width, height = self.original_image.size
            if self.compression_var.get():
                header = b'POG' + bytes([1])  
            else:
                header = b'POG' + bytes([0]) 

            # Create pixel data
            pixel_data = b''.join(
                bytes(self.original_image.getpixel((x, y))) for y in range(height) for x in range(width)
            )

            # Prepare the POG data
            pog_data = width.to_bytes(4, byteorder='little') + height.to_bytes(4, byteorder='little') + pixel_data

            # Optionally apply LZMA compression based on the checkbox
            if self.compression_var.get():
                pog_data = lzma.compress(pog_data)

            # Write to file
            with open(save_path, "wb") as f:
                f.write(header + pog_data)
            print(f"Saved as POG to {save_path}")
        except Exception as e:
            print(f"Error saving POG file: {e}")

    def detect_dark_mode(self):
        if platform.system() == "Windows":
            try:
                import winreg
                registry = winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER)
                reg_key = winreg.OpenKey(registry, r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
                value, _ = winreg.QueryValueEx(reg_key, "AppsUseLightTheme")
                return value == 0
            except Exception as e:
                print(f"Error detecting dark mode: {e}")
        elif platform.system() == "Darwin":
            try:
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True, text=True
                )
                return "Dark" in result.stdout
            except Exception as e:
                print(f"Error detecting dark mode: {e}")

        return False

if __name__ == "__main__":
    root = tk.Tk()
    app = POGConverterApp(root)
    root.mainloop()
