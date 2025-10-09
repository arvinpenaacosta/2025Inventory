import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os

def convert_png_to_ico():
    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(
        title="Select PNG Image",
        filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
    )
    if not file_path:
        messagebox.showinfo("Info", "No file selected. Operation cancelled.")
        return
    try:
        if not file_path.lower().endswith('.png'):
            messagebox.showerror("Error", "Please select a PNG file.")
            return
        img = Image.open(file_path)
        output_path = os.path.join(os.path.dirname(file_path), "icon.ico")
        icon_sizes = [(16, 16), (32, 32), (64, 64), (128, 128), (256, 256)]
        img.save(output_path, format="ICO", sizes=icon_sizes)
        messagebox.showinfo("Success", f"Icon saved as {output_path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to convert image: {str(e)}")

if __name__ == "__main__":
    convert_png_to_ico()