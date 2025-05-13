import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageOps, UnidentifiedImageError
from collections import OrderedDict # For aspect ratios
import os

# Constants for preview size
PREVIEW_MAX_WIDTH = 550
PREVIEW_MAX_HEIGHT = 450
MIN_RECT_SIZE = 20 # Minimum pixel size for width/height of crop rect

# Constants for resize handles
HANDLE_SIZE = 8 # Pixel size of the handle detection area (e.g., 8x8 box for corners)
RESIZE_HANDLES = {
    "tl": "top-left", "tm": "top-middle", "tr": "top-right",
    "ml": "middle-left", "mr": "middle-right",
    "bl": "bottom-left", "bm": "bottom-middle", "br": "bottom-right"
}
CURSOR_MAP = {
    "tl": "size_nw_se", "tr": "size_ne_sw",
    "bl": "size_ne_sw", "br": "size_nw_se",
    "tm": "size_ns", "bm": "size_ns",
    "ml": "size_we", "mr": "size_we",
    "move": "fleur" # For moving the whole rectangle
}

# For HEIC support, pillow-heif needs to be imported,
# though its usage is often transparent via Pillow's Image.open
try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    print("pillow-heif not installed. HEIC support may be limited.")

class ImageManipulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comprehensive Image Manipulator")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # --- Crop Section State Variables ---
        self.crop_image_path = None
        self.original_crop_image_pil = None  
        self.display_crop_image_pil = None   
        self.display_crop_image_tk = None    
        self.crop_canvas = None
        self.crop_canvas_image_id = None     
        self.crop_rect_id = None             
        self.crop_start_x, self.crop_start_y = 0, 0
        self.crop_current_rect_coords = None 
        self.crop_area_details_var = tk.StringVar(value="Crop Area (X,Y,W,H): N/A")
        self.selected_crop_file_var = tk.StringVar(value="No file selected.")
        self.final_cropped_pil_image = None # To store the result of the crop
        self.pre_operation_pil_image = None # For undo functionality (crop, rotate, flip)
        self.cropped_preview_photo_image = None # For displaying in the preview label
        self.crop_canvas_image_offset_x = 0 # Offset of displayed image on canvas
        self.crop_canvas_image_offset_y = 0 # Offset of displayed image on canvas
        self.crop_image_scale_factor = 1.0 # Scale factor for image on canvas
        
        # State for moving existing crop rectangle
        self.is_moving_crop_rect = False
        self.drag_start_mouse_x = 0
        self.drag_start_mouse_y = 0
        self.drag_start_rect_x1 = 0
        self.drag_start_rect_y1 = 0
        self.drag_rect_width = 0 # Store width/height of rect being dragged
        self.drag_rect_height = 0
        
        # State for resize handles
        self.is_resizing_crop_rect = False
        self.current_resize_handle = None
        self.resize_start_rect_coords = None # Stores (x1,y1,x2,y2) at resize start

        # Aspect Ratios for Cropping
        self.aspect_ratios = OrderedDict([
            ("Freeform", None),
            ("Original", "original"),
            ("1:1 (Square)", 1.0),
            ("4:3", 4/3),
            ("3:2", 3/2),
            ("16:9", 16/9)
        ])
        self.selected_aspect_ratio_var = tk.StringVar(value="Freeform")
        self.current_aspect_ratio_val = None
        self.fixed_aspect_active = False
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(expand=True, fill=tk.BOTH)

        # Feature Notebook (Tabs)
        self.feature_notebook = ttk.Notebook(main_frame)
        self.feature_notebook.pack(expand=True, fill=tk.BOTH, pady=10)

        # --- Create tabs for each feature ---
        self.tab_crop = self.create_feature_tab("Enhanced Cropper") 
        self.tab_heic_to_jpg = self.create_feature_tab("HEIC to JPG")
        self.tab_resize = self.create_feature_tab("Resize Image")
        self.tab_compress = self.create_feature_tab("Compress Image")
        self.tab_base64 = self.create_feature_tab("Image to Base64")
        self.tab_webp = self.create_feature_tab("WebP Conversion")
        self.tab_bg_removal = self.create_feature_tab("Background Removal")

        # Populate the "Enhanced Cropper" tab.
        self.setup_crop_tab()

        # Status bar
        self.status_bar_text = tk.StringVar()
        self.status_bar_text.set("Ready")
        status_bar = ttk.Label(main_frame, textvariable=self.status_bar_text, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_feature_tab(self, tab_name):
        """Creates a new tab in the notebook and returns it."""
        tab = ttk.Frame(self.feature_notebook, padding="10")
        self.feature_notebook.add(tab, text=tab_name)
        return tab

    def setup_crop_tab(self):
        """Sets up the UI for the Enhanced Image Cropper tab."""
        for widget in self.tab_crop.winfo_children(): 
            widget.destroy()

        # Main content frame for the cropper tab
        cropper_content_frame = ttk.Frame(self.tab_crop)
        cropper_content_frame.pack(expand=True, fill=tk.BOTH)

        # Top: File selection and info
        top_frame = ttk.Frame(cropper_content_frame)
        top_frame.pack(fill=tk.X, pady=(0, 5))

        load_button = ttk.Button(top_frame, text="Select Image...", command=self.load_image_for_cropping)
        load_button.pack(side=tk.LEFT, padx=(0, 10))

        selected_file_label = ttk.Label(top_frame, textvariable=self.selected_crop_file_var, anchor=tk.W)
        selected_file_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Middle: Canvas and Controls
        middle_frame = ttk.Frame(cropper_content_frame)
        middle_frame.pack(expand=True, fill=tk.BOTH, pady=5)

        # Canvas Frame (Left part of middle_frame)
        canvas_frame = ttk.Frame(middle_frame, relief=tk.SUNKEN, borderwidth=1)
        canvas_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0, 10))
        
        self.crop_canvas = tk.Canvas(canvas_frame, bg='gray75', highlightthickness=0)
        self.crop_canvas.pack(expand=True, fill=tk.BOTH)
        # Bind mouse events
        self.crop_canvas.bind("<ButtonPress-1>", self._on_crop_canvas_press)
        self.crop_canvas.bind("<B1-Motion>", self._on_crop_canvas_drag)
        self.crop_canvas.bind("<ButtonRelease-1>", self._on_crop_canvas_release)
        self.crop_canvas.bind("<Motion>", self._on_crop_canvas_motion) # For cursor changes

        # Controls Frame (Right part of middle_frame)
        controls_frame = ttk.Frame(middle_frame, width=220) 
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)
        controls_frame.pack_propagate(False) 

        # Cropper Controls Frame (Select, Aspect Ratio, Crop, Save, Undo)
        cropper_controls_frame = ttk.LabelFrame(controls_frame, text="Controls", padding=10)
        cropper_controls_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10, anchor='nw')

        # Select Image Button
        self.select_image_button_crop = ttk.Button(cropper_controls_frame, text="Select Image...", command=self.load_image_for_cropping)
        self.select_image_button_crop.pack(fill=tk.X, pady=5)
        ttk.Label(cropper_controls_frame, textvariable=self.selected_crop_file_var).pack(fill=tk.X, pady=2)

        # Aspect Ratio Dropdown
        ttk.Label(cropper_controls_frame, text="Aspect Ratio:").pack(fill=tk.X, pady=(10,0))
        self.aspect_ratio_dropdown_crop = ttk.Combobox(cropper_controls_frame, textvariable=self.selected_aspect_ratio_var, values=list(self.aspect_ratios.keys()), state="readonly")
        self.aspect_ratio_dropdown_crop.pack(fill=tk.X, pady=2)
        self.aspect_ratio_dropdown_crop.bind("<<ComboboxSelected>>", self._on_aspect_ratio_change_crop)

        # Crop and Save Buttons
        self.crop_button = ttk.Button(cropper_controls_frame, text="Crop Image", command=self._perform_crop, state=tk.DISABLED)
        self.crop_button.pack(fill=tk.X, pady=(20,5))
        self.save_cropped_button = ttk.Button(cropper_controls_frame, text="Save Cropped Image", command=self._save_cropped_image, state=tk.DISABLED)
        self.save_cropped_button.pack(fill=tk.X, pady=5)

        # Undo Crop Button
        self.undo_operation_button = ttk.Button(cropper_controls_frame, text="Undo Last Op", command=self._undo_last_operation, state=tk.DISABLED)
        self.undo_operation_button.pack(fill=tk.X, pady=5)

        # Transformation Buttons Frame
        transform_buttons_frame = ttk.LabelFrame(cropper_controls_frame, text="Transformations")
        transform_buttons_frame.pack(fill=tk.X, pady=(15,5))

        self.rotate_left_button = ttk.Button(transform_buttons_frame, text="Rotate 90° Left", command=self._rotate_image_left, state=tk.DISABLED)
        self.rotate_left_button.pack(fill=tk.X, pady=2)

        self.rotate_right_button = ttk.Button(transform_buttons_frame, text="Rotate 90° Right", command=self._rotate_image_right, state=tk.DISABLED)
        self.rotate_right_button.pack(fill=tk.X, pady=2)

        self.flip_horizontal_button = ttk.Button(transform_buttons_frame, text="Flip Horizontal", command=self._flip_image_horizontal, state=tk.DISABLED)
        self.flip_horizontal_button.pack(fill=tk.X, pady=2)

        self.flip_vertical_button = ttk.Button(transform_buttons_frame, text="Flip Vertical", command=self._flip_image_vertical, state=tk.DISABLED)
        self.flip_vertical_button.pack(fill=tk.X, pady=2)

        # Crop Area Details Label
        ttk.Label(cropper_controls_frame, textvariable=self.crop_area_details_var).pack(fill=tk.X, pady=(10,0))

    def load_image_for_cropping(self):
        """Loads an image from disk for cropping operations.

        Opens a file dialog for the user to select an image file. Supported formats
        include common types like JPG, PNG, BMP, GIF, TIFF, and HEIC/HEIF (if
        pillow-heif is installed).
        
        If an image is successfully loaded:
        1. Stores the file path and the Pillow Image object (`self.original_crop_image_pil`).
        2. Converts the image to 'RGB' or 'RGBA' if it's not already in one of those modes.
        3. Updates UI elements (selected file label, status bar).
        4. Calls `_display_image_on_crop_canvas()` to render the image.
        5. If a fixed aspect ratio is active, redraws the default selection rectangle.
           Otherwise, resets the cropper selection state.
        6. Clears any previous undo state (`self.pre_operation_pil_image`) and
           final cropped image (`self.final_cropped_pil_image`).
        7. Resets and enables/disables relevant UI buttons (Undo, Save, Crop, Transformations).
        
        Handles potential errors during file loading and displays an error message.
        If loading is cancelled or fails, the cropper state is appropriately updated or reset.
        """
        self.update_status("Loading image for cropping...")
        file_path = filedialog.askopenfilename(
            title="Select Image for Cropping",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.heic *.heif"), ("All Files", "*.*")])

        if not file_path:
            self.update_status("Image loading cancelled.")
            return

        try:
            self.crop_image_path = file_path
            self.original_crop_image_pil = Image.open(file_path)
            
            if self.original_crop_image_pil.mode not in ('RGB', 'RGBA'):
                 self.original_crop_image_pil = self.original_crop_image_pil.convert('RGBA' if 'A' in self.original_crop_image_pil.mode else 'RGB')

            self.selected_crop_file_var.set(os.path.basename(file_path))
            self.update_status(f"Loaded: {os.path.basename(file_path)}")
            
            self._display_image_on_crop_canvas() # This will clear old rect
            # If a fixed aspect ratio is active, draw the default rect for it
            if self.fixed_aspect_active and self.current_aspect_ratio_val:
                self._draw_default_fixed_aspect_rectangle()
            else:
                self._reset_cropper_selection_state() # Standard reset for freeform
            
            self.pre_operation_pil_image = None # Clear undo state for new image
            self.final_cropped_pil_image = None   # Clear any previous final crop
            self.undo_operation_button['state'] = tk.DISABLED
            self.save_cropped_button['state'] = tk.DISABLED
            self.crop_button['state'] = tk.NORMAL # Enable crop button

            self._enable_transform_buttons(True if self.original_crop_image_pil else False)

        except Exception as e:
            messagebox.showerror("Error Loading Image", f"Could not load image: {e}")
            self.update_status("Error loading image.")
            self._reset_cropper_state()

    def _display_image_on_crop_canvas(self, image_to_display=None):
        """Displays or refreshes an image on the main crop canvas.

        This method scales and centers the provided `image_to_display` (or
        `self.original_crop_image_pil` if None) onto `self.crop_canvas`.
        The image is resized to fit within the canvas dimensions (or fallback
        to `PREVIEW_MAX_WIDTH`/`HEIGHT` if canvas is not yet sized) while
        maintaining aspect ratio using `Image.Resampling.LANCZOS`.
        
        Key actions:
        - Stores the scaled Pillow image as `self.display_crop_image_pil`.
        - Stores the PhotoImage for Tkinter as `self.display_crop_image_tk`.
        - Calculates and stores `self.crop_image_scale_factor` (actual image to displayed image).
        - Calculates and stores `self.crop_canvas_image_offset_x` and `_y` (for centering).
        - Clears the canvas (`"all"`) and draws the new image.
        - Resets `self.crop_rect_id`, `self.crop_current_rect_coords`, and updates
          the crop area details display to "N/A".
        
        Args:
            image_to_display (PIL.Image.Image, optional): The Pillow image object
                to display. Defaults to `self.original_crop_image_pil`.
        """
        if image_to_display is None:
            image_to_display = self.original_crop_image_pil
        
        if not image_to_display or not self.crop_canvas:
            return

        canvas_width = self.crop_canvas.winfo_width()
        canvas_height = self.crop_canvas.winfo_height()

        if canvas_width <= 1 or canvas_height <= 1: 
            canvas_width = PREVIEW_MAX_WIDTH
            canvas_height = PREVIEW_MAX_HEIGHT

        img_w, img_h = image_to_display.size
        
        scale_w = canvas_width / img_w
        scale_h = canvas_height / img_h
        scale_factor = min(scale_w, scale_h)
        
        self.crop_image_scale_factor = scale_factor # Store for coordinate conversion

        new_w = int(img_w * scale_factor)
        new_h = int(img_h * scale_factor)

        self.display_crop_image_pil = image_to_display.resize((new_w, new_h), Image.Resampling.LANCZOS)
        self.display_crop_image_tk = ImageTk.PhotoImage(self.display_crop_image_pil)

        self.crop_canvas.delete("all") 
        self.crop_canvas_image_offset_x = (canvas_width - new_w) / 2
        self.crop_canvas_image_offset_y = (canvas_height - new_h) / 2
        self.crop_canvas_image_id = self.crop_canvas.create_image(
            self.crop_canvas_image_offset_x + new_w // 2, self.crop_canvas_image_offset_y + new_h // 2, 
            anchor=tk.CENTER, 
            image=self.display_crop_image_tk
        )
        self.crop_rect_id = None 
        self.crop_current_rect_coords = None
        self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A")

    def _reset_cropper_state(self):
        """Resets the entire cropper tab to its initial state."""
        self.crop_image_path = None
        self.original_crop_image_pil = None
        self.display_crop_image_pil = None
        if self.crop_canvas_image_id:
            self.crop_canvas.delete(self.crop_canvas_image_id)
            self.crop_canvas_image_id = None
        if self.crop_rect_id:
            self.crop_canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None
        self.display_crop_image_tk = None 
        self.selected_crop_file_var.set("No file selected.")
        self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A")
        self.crop_button['state'] = tk.DISABLED
        self.save_cropped_button['state'] = tk.DISABLED
        self.undo_operation_button['state'] = tk.DISABLED
        self.selected_aspect_ratio_var.set("Freeform")
        self._on_aspect_ratio_change_crop() 
        self.update_status("Cropper reset.")

    def _reset_cropper_selection_state(self, clear_rect_only=False):
        """Resets only the crop selection rectangle and related info."""
        if self.crop_rect_id:
            self.crop_canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None
        self.crop_current_rect_coords = None
        self.is_moving_crop_rect = False
        # self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A") # Keep details if only clearing rect

        if not clear_rect_only:
            self.crop_start_x, self.crop_start_y = 0, 0
            self.crop_button['state'] = tk.DISABLED # Disable crop if selection cleared fully
            self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A")
        
        # If a fixed aspect is active, and an image is loaded, redraw default rect
        # This behavior might need adjustment based on clear_rect_only context.
        # For now, _perform_crop and _undo_crop use clear_rect_only=True to prevent default rect auto-draw.
        if not clear_rect_only and self.fixed_aspect_active and self.current_aspect_ratio_val and self.original_crop_image_pil:
             self._draw_default_fixed_aspect_rectangle()

    def _on_aspect_ratio_change_crop(self, event=None):
        """Handles changes to the selected aspect ratio for cropping.

        Triggered when the user selects a new value from the aspect ratio combobox.
        It updates `self.current_aspect_ratio_val` and `self.fixed_aspect_active`
        based on the selection. If "Original" is chosen, the aspect ratio is
        calculated from the loaded `self.original_crop_image_pil`.

        After updating the aspect ratio state:
        1. Resets the current crop selection via `_reset_cropper_selection_state()`.
        2. If an image is loaded and a fixed aspect ratio is now active (not "Freeform"),
           it calls `_draw_default_fixed_aspect_rectangle()` to draw a new selection
           matching the aspect ratio.
        3. Enables the crop button if an image is present.
        4. Updates the status bar message.

        Args:
            event (tk.Event, optional): The Tkinter event object. Defaults to None.
                                        Not directly used by the method's logic.
        """
        selected_ratio_str = self.selected_aspect_ratio_var.get()
        self.current_aspect_ratio_val = self.aspect_ratios.get(selected_ratio_str)
        
        if self.current_aspect_ratio_val == "original":
            if self.original_crop_image_pil:
                img_w, img_h = self.original_crop_image_pil.size
                self.current_aspect_ratio_val = img_w / img_h if img_h > 0 else None
            else:
                self.current_aspect_ratio_val = None

        self.fixed_aspect_active = self.current_aspect_ratio_val is not None
        self.update_status(f"Aspect ratio set to: {selected_ratio_str}")
        # Further logic to redraw selection rectangle if needed will be added here
        self._reset_cropper_selection_state() # For now, just clear selection on change
        
        if self.original_crop_image_pil and self.crop_canvas_image_id: # If image loaded and displayed
            if self.fixed_aspect_active and self.current_aspect_ratio_val:
                self._draw_default_fixed_aspect_rectangle()
            self.crop_button['state'] = tk.NORMAL

    def _get_canvas_image_bounds(self):
        """Returns the bounding box [x1, y1, x2, y2] of the image on the canvas."""
        if not self.crop_canvas_image_id or not self.display_crop_image_pil:
            return None
        
        canvas_width = self.crop_canvas.winfo_width()
        canvas_height = self.crop_canvas.winfo_height()
        img_disp_w, img_disp_h = self.display_crop_image_pil.size

        # Image is centered on canvas
        img_x1_on_canvas = (canvas_width - img_disp_w) / 2
        img_y1_on_canvas = (canvas_height - img_disp_h) / 2
        img_x2_on_canvas = img_x1_on_canvas + img_disp_w
        img_y2_on_canvas = img_y1_on_canvas + img_disp_h
        
        return img_x1_on_canvas, img_y1_on_canvas, img_x2_on_canvas, img_y2_on_canvas

    def _get_resize_handle_at_pos(self, x, y):
        """Determines if canvas coordinates (x, y) are over a resize handle.

        Checks if the given canvas coordinates (x, y) are positioned over one of
        the eight resize handles (corners or mid-points of edges) of an active
        fixed-aspect crop rectangle. Iterates through predefined handle positions,
        checks if the click is within HANDLE_SIZE of any handle.

        This check is only performed if a fixed aspect ratio is active and a
        crop rectangle (`self.crop_current_rect_coords`) exists.

        Args:
            x (int): The x-coordinate on the canvas.
            y (int): The y-coordinate on the canvas.

        Returns:
            str | None: A string identifier for the handle (e.g., "tl" for top-left,
                        "mr" for middle-right) if the coordinates are over a handle,
                        otherwise None.
        """
        if not self.crop_current_rect_coords or not self.fixed_aspect_active:
            return None

        r_x1, r_y1, r_x2, r_y2 = self.crop_current_rect_coords
        h_s = HANDLE_SIZE / 2 # half size for centered detection

        handles_pos = {
            "tl": (r_x1, r_y1),
            "tm": ((r_x1 + r_x2) / 2, r_y1),
            "tr": (r_x2, r_y1),
            "ml": (r_x1, (r_y1 + r_y2) / 2),
            "mr": (r_x2, (r_y1 + r_y2) / 2),
            "bl": (r_x1, r_y2),
            "bm": ((r_x1 + r_x2) / 2, r_y2),
            "br": (r_x2, r_y2)
        }

        for handle_name, (hx, hy) in handles_pos.items():
            if (hx - h_s <= x <= hx + h_s) and \
               (hy - h_s <= y <= hy + h_s):
                return handle_name
        return None

    def _on_crop_canvas_motion(self, event):
        if not self.display_crop_image_pil or not self.crop_canvas_image_id or self.is_moving_crop_rect or self.is_resizing_crop_rect:
            # Don't change cursor if already dragging/moving/resizing or no image
            # Or if drawing a new freeform rect (self.crop_rect_id exists but not fixed_aspect_active)
            if not self.fixed_aspect_active and self.crop_rect_id and not self.is_moving_crop_rect and not self.is_resizing_crop_rect:
                 self.crop_canvas.config(cursor="crosshair") # Default for drawing
            elif not self.is_moving_crop_rect and not self.is_resizing_crop_rect : # Not in any active drag operation
                 self.crop_canvas.config(cursor="") # Default arrow
            return

        active_handle = self._get_resize_handle_at_pos(event.x, event.y)

        if active_handle:
            self.crop_canvas.config(cursor=CURSOR_MAP.get(active_handle, ""))
        elif self.fixed_aspect_active and self.crop_current_rect_coords: # Check for move cursor
            r_x1, r_y1, r_x2, r_y2 = self.crop_current_rect_coords
            if r_x1 <= event.x <= r_x2 and r_y1 <= event.y <= r_y2:
                self.crop_canvas.config(cursor=CURSOR_MAP.get("move", "fleur"))
            else:
                self.crop_canvas.config(cursor="") # Default arrow outside
        elif not self.fixed_aspect_active : # Freeform mode, ready to draw
             self.crop_canvas.config(cursor="crosshair")
        else:
            self.crop_canvas.config(cursor="") # Default arrow

    def _on_crop_canvas_press(self, event):
        if not self.display_crop_image_pil or not self.crop_canvas_image_id:
            return # No image loaded/displayed

        img_bounds = self._get_canvas_image_bounds()
        if not img_bounds: return
        img_x1_cv, img_y1_cv, img_x2_cv, img_y2_cv = img_bounds
        
        self.is_moving_crop_rect = False # Reset at the start of any press
        self.is_resizing_crop_rect = False # Reset at the start of any press
        self.current_resize_handle = None

        if self.fixed_aspect_active: # Fixed Aspect Ratio Mode
            clicked_handle = self._get_resize_handle_at_pos(event.x, event.y)
            if clicked_handle and self.crop_current_rect_coords: # Clicked on a resize handle
                self.is_resizing_crop_rect = True
                self.current_resize_handle = clicked_handle
                self.drag_start_mouse_x = event.x
                self.drag_start_mouse_y = event.y
                self.resize_start_rect_coords = self.crop_current_rect_coords
                self.save_cropped_button['state'] = tk.DISABLED
                return # Ready for resize drag
            elif self.crop_rect_id and self.crop_current_rect_coords: # Check for move
                cr_x1, cr_y1, cr_x2, cr_y2 = self.crop_current_rect_coords
                if cr_x1 <= event.x <= cr_x2 and cr_y1 <= event.y <= cr_y2:
                    # Click is INSIDE the existing fixed rectangle (not on a handle), prepare to move
                    self.is_moving_crop_rect = True
                    self.drag_start_mouse_x = event.x
                    self.drag_start_mouse_y = event.y
                    self.drag_start_rect_x1 = cr_x1
                    self.drag_start_rect_y1 = cr_y1
                    self.drag_rect_width = cr_x2 - cr_x1
                    self.drag_rect_height = cr_y2 - cr_y1
                    self.save_cropped_button['state'] = tk.DISABLED
            # else: Click is OUTSIDE the existing fixed rectangle - do nothing, or no rect exists
            return # In fixed mode, either we resize, move, or do nothing on press

        # --- Freeform Mode Logic --- (only reached if not self.fixed_aspect_active)
        self.crop_start_x = max(img_x1_cv, min(event.x, img_x2_cv))
        self.crop_start_y = max(img_y1_cv, min(event.y, img_y2_cv))

        if self.crop_rect_id: # Delete any old rectangle (e.g. from previous freeform draw)
            self.crop_canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None 
            self.crop_current_rect_coords = None

        # Create a new rectangle for freeform drawing
        self.crop_rect_id = self.crop_canvas.create_rectangle(
            self.crop_start_x, self.crop_start_y, 
            self.crop_start_x, self.crop_start_y, 
            outline='red', width=2
        )
        self.save_cropped_button['state'] = tk.DISABLED

    def _on_crop_canvas_drag(self, event):
        if not self.display_crop_image_pil or not self.crop_canvas_image_id:
            return
        
        img_bounds = self._get_canvas_image_bounds()
        if not img_bounds: return
        img_x1_cv, img_y1_cv, img_x2_cv, img_y2_cv = img_bounds
        
        cur_x_event = event.x # Raw event x for delta calculations if moving
        cur_y_event = event.y # Raw event y for delta calculations if moving

        if self.is_moving_crop_rect and self.crop_rect_id: # This implies fixed_aspect_active was true
            delta_x = cur_x_event - self.drag_start_mouse_x
            delta_y = cur_y_event - self.drag_start_mouse_y

            new_rect_x1 = self.drag_start_rect_x1 + delta_x
            new_rect_y1 = self.drag_start_rect_y1 + delta_y
            new_rect_x2 = new_rect_x1 + self.drag_rect_width
            new_rect_y2 = new_rect_y1 + self.drag_rect_height

            # Clamp to image boundaries on canvas
            # Adjust x1,y1 if x2,y2 go out of bounds to maintain size
            if new_rect_x2 > img_x2_cv:
                new_rect_x1 -= (new_rect_x2 - img_x2_cv)
                new_rect_x2 = img_x2_cv
            if new_rect_y2 > img_y2_cv:
                new_rect_y1 -= (new_rect_y2 - img_y2_cv)
                new_rect_y2 = img_y2_cv
            if new_rect_x1 < img_x1_cv:
                new_rect_x2 += (img_x1_cv - new_rect_x1)
                new_rect_x1 = img_x1_cv
            if new_rect_y1 < img_y1_cv:
                new_rect_y2 += (img_y1_cv - new_rect_y1)
                new_rect_y1 = img_y1_cv
            
            # Final clamp to ensure width/height did not push it out again after adjustment
            final_x1 = max(img_x1_cv, new_rect_x1)
            final_y1 = max(img_y1_cv, new_rect_y1)
            final_x2 = min(img_x2_cv, final_x1 + self.drag_rect_width) # Ensure width is maintained
            final_y2 = min(img_y2_cv, final_y1 + self.drag_rect_height) # Ensure height is maintained
            # If width/height got reduced due to double clamping, adjust x1/y1 one last time
            final_x1 = final_x2 - self.drag_rect_width 
            final_y1 = final_y2 - self.drag_rect_height

            self.crop_canvas.coords(self.crop_rect_id, final_x1, final_y1, final_x2, final_y2)
            self.crop_current_rect_coords = (final_x1, final_y1, final_x2, final_y2)
            self._update_crop_area_details() # Update details while moving

        elif self.is_resizing_crop_rect and self.crop_rect_id and self.current_aspect_ratio_val: # Resizing fixed aspect rect
            handle = self.current_resize_handle
            aspect_ratio = self.current_aspect_ratio_val

            orig_x1, orig_y1, orig_x2, orig_y2 = self.resize_start_rect_coords
            
            new_x1, new_y1, new_x2, new_y2 = orig_x1, orig_y1, orig_x2, orig_y2

            # Determine the fixed point and the moving point based on the handle
            # For corners, one corner is fixed, the other moves with mouse, then adjust for aspect ratio.
            if handle == "tl":
                fixed_x, fixed_y = orig_x2, orig_y2
                new_x1 = max(img_x1_cv, min(cur_x_event, fixed_x - MIN_RECT_SIZE))
                new_y1 = max(img_y1_cv, min(cur_y_event, fixed_y - MIN_RECT_SIZE))
                # Adjust to maintain aspect ratio
                new_w = fixed_x - new_x1
                new_h = new_w / aspect_ratio
                new_y1 = fixed_y - new_h
                if new_y1 < img_y1_cv: # If y1 goes out of bounds, recalculate based on height
                    new_y1 = img_y1_cv
                    new_h = fixed_y - new_y1
                    new_w = new_h * aspect_ratio
                    new_x1 = fixed_x - new_w

            elif handle == "br":
                fixed_x, fixed_y = orig_x1, orig_y1
                new_x2 = min(img_x2_cv, max(cur_x_event, fixed_x + MIN_RECT_SIZE))
                new_y2 = min(img_y2_cv, max(cur_y_event, fixed_y + MIN_RECT_SIZE))
                # Adjust to maintain aspect ratio
                new_w = new_x2 - fixed_x
                new_h = new_w / aspect_ratio
                new_y2 = fixed_y + new_h
                if new_y2 > img_y2_cv: # If y2 goes out of bounds, recalculate based on height
                    new_y2 = img_y2_cv
                    new_h = new_y2 - fixed_y
                    new_w = new_h * aspect_ratio
                    new_x2 = fixed_x + new_w

            elif handle == "tr":
                fixed_x, fixed_y = orig_x1, orig_y2
                new_x2 = min(img_x2_cv, max(cur_x_event, fixed_x + MIN_RECT_SIZE))
                new_y1 = max(img_y1_cv, min(cur_y_event, fixed_y - MIN_RECT_SIZE))
                # Adjust to maintain aspect ratio
                new_w = new_x2 - fixed_x
                new_h = new_w / aspect_ratio
                new_y1 = fixed_y - new_h
                if new_y1 < img_y1_cv: # If y1 goes out of bounds, recalculate based on height
                    new_y1 = img_y1_cv
                    new_h = fixed_y - new_y1
                    new_w = new_h * aspect_ratio
                    new_x2 = fixed_x + new_w
            
            elif handle == "bl":
                fixed_x, fixed_y = orig_x2, orig_y1
                new_x1 = max(img_x1_cv, min(cur_x_event, fixed_x - MIN_RECT_SIZE))
                new_y2 = min(img_y2_cv, max(cur_y_event, fixed_y + MIN_RECT_SIZE))
                # Adjust to maintain aspect ratio
                new_w = fixed_x - new_x1
                new_h = new_w / aspect_ratio
                new_y2 = fixed_y + new_h
                if new_y2 > img_y2_cv: # If y2 goes out of bounds, recalculate based on height
                    new_y2 = img_y2_cv
                    new_h = new_y2 - fixed_y
                    new_w = new_h * aspect_ratio
                    new_x1 = fixed_x - new_w
            
            elif handle == "tm": # Top-middle
                fixed_y = orig_y2
                center_x = (orig_x1 + orig_x2) / 2
                new_y1 = max(img_y1_cv, min(cur_y_event, fixed_y - MIN_RECT_SIZE))
                
                new_h = fixed_y - new_y1
                if new_h < MIN_RECT_SIZE: 
                    new_h = MIN_RECT_SIZE
                    new_y1 = fixed_y - new_h
                
                new_w = new_h * aspect_ratio
                if new_w < MIN_RECT_SIZE: # Aspect ratio forces width to be too small
                    new_w = MIN_RECT_SIZE
                    new_h = new_w / aspect_ratio
                    new_y1 = fixed_y - new_h
                
                new_x1 = center_x - new_w / 2
                new_x2 = center_x + new_w / 2
                new_y2 = fixed_y

            elif handle == "bm": # Bottom-middle
                fixed_y = orig_y1
                center_x = (orig_x1 + orig_x2) / 2
                new_y2 = min(img_y2_cv, max(cur_y_event, fixed_y + MIN_RECT_SIZE))

                new_h = new_y2 - fixed_y
                if new_h < MIN_RECT_SIZE:
                    new_h = MIN_RECT_SIZE
                    new_y2 = fixed_y + new_h
                
                new_w = new_h * aspect_ratio
                if new_w < MIN_RECT_SIZE:
                    new_w = MIN_RECT_SIZE
                    new_h = new_w / aspect_ratio
                    new_y2 = fixed_y + new_h
                
                new_x1 = center_x - new_w / 2
                new_x2 = center_x + new_w / 2
                new_y1 = fixed_y

            elif handle == "ml": # Middle-left
                fixed_x = orig_x2
                center_y = (orig_y1 + orig_y2) / 2
                new_x1 = max(img_x1_cv, min(cur_x_event, fixed_x - MIN_RECT_SIZE))
                
                new_w = fixed_x - new_x1
                if new_w < MIN_RECT_SIZE:
                    new_w = MIN_RECT_SIZE
                    new_x1 = fixed_x - new_w
                
                new_h = new_w / aspect_ratio
                if new_h < MIN_RECT_SIZE:
                    new_h = MIN_RECT_SIZE
                    new_w = new_h * aspect_ratio
                    new_x1 = fixed_x - new_w

                new_y1 = center_y - new_h / 2
                new_y2 = center_y + new_h / 2
                new_x2 = fixed_x
            
            elif handle == "mr": # Middle-right
                fixed_x = orig_x1
                center_y = (orig_y1 + orig_y2) / 2
                new_x2 = min(img_x2_cv, max(cur_x_event, fixed_x + MIN_RECT_SIZE))
                
                new_w = new_x2 - fixed_x
                if new_w < MIN_RECT_SIZE:
                    new_w = MIN_RECT_SIZE
                    new_x2 = fixed_x + new_w
                
                new_h = new_w / aspect_ratio
                if new_h < MIN_RECT_SIZE:
                    new_h = MIN_RECT_SIZE
                    new_w = new_h * aspect_ratio
                    new_x2 = fixed_x + new_w
                    
                new_y1 = center_y - new_h / 2
                new_y2 = center_y + new_h / 2
                new_x1 = fixed_x

            # Final clamping and validation
            final_coords = self._validate_and_clamp_rect_coords(new_x1, new_y1, new_x2, new_y2, img_bounds)
            if final_coords:
                self.crop_canvas.coords(self.crop_rect_id, *final_coords)
                self.crop_current_rect_coords = final_coords
                self._update_crop_area_details()

        elif not self.fixed_aspect_active and self.crop_rect_id: # Drawing a new FREEFORM rectangle
            # Clamp current mouse position for new rectangle drawing
            clamped_cur_x = max(img_x1_cv, min(cur_x_event, img_x2_cv))
            clamped_cur_y = max(img_y1_cv, min(cur_y_event, img_y2_cv))

            x1, y1 = self.crop_start_x, self.crop_start_y
            x2, y2 = clamped_cur_x, clamped_cur_y

            # Ensure x1 < x2 and y1 < y2 for rectangle definition
            rect_x1 = min(x1, x2)
            rect_y1 = min(y1, y2)
            rect_x2 = max(x1, x2)
            rect_y2 = max(y1, y2)

            if self.fixed_aspect_active and self.current_aspect_ratio_val:
                # Adjust for fixed aspect ratio
                width = rect_x2 - rect_x1
                height = rect_y2 - rect_y1
                aspect = self.current_aspect_ratio_val

                if width / aspect > height: # Width is the dominant dimension
                    new_height = width / aspect
                    if y2 > y1: rect_y2 = rect_y1 + new_height
                    else: rect_y1 = rect_y2 - new_height # Dragging up
                else: # Height is the dominant dimension
                    new_width = height * aspect
                    if x2 > x1: rect_x2 = rect_x1 + new_width
                    else: rect_x1 = rect_x2 - new_width # Dragging left
            
                # Clamp to image boundaries again after aspect adjustment
                rect_x1 = max(img_x1_cv, rect_x1)
                rect_y1 = max(img_y1_cv, rect_y1)
                rect_x2 = min(img_x2_cv, rect_x2)
                rect_y2 = min(img_y2_cv, rect_y2)

                # One more pass to ensure aspect ratio after clamping, if clamping changed a dimension disproportionately
                # This can be complex; for now, prioritize clamping over perfect aspect ratio at extreme edges if they conflict.
                # A more robust solution involves scaling down the aspect-ratio-correct rect if it overflows.
                current_w = rect_x2 - rect_x1
                current_h = rect_y2 - rect_y1
                if abs(current_w / current_h - aspect) > 0.01: # If aspect ratio significantly off due to clamping
                    if current_w / aspect > current_h: # Width dominant after clamping
                         rect_y2 = rect_y1 + current_w / aspect
                    else: # Height dominant
                         rect_x2 = rect_x1 + current_h * aspect
                # Re-clamp after final adjustment
                rect_x1 = max(img_x1_cv, rect_x1)
                rect_y1 = max(img_y1_cv, rect_y1)
                rect_x2 = min(img_x2_cv, rect_x2)
                rect_y2 = min(img_y2_cv, rect_y2)

            self.crop_canvas.coords(self.crop_rect_id, rect_x1, rect_y1, rect_x2, rect_y2)
            self.crop_current_rect_coords = (rect_x1, rect_y1, rect_x2, rect_y2)
            self._update_crop_area_details()

    def _on_crop_canvas_release(self, event):
        if not self.display_crop_image_pil or not self.crop_canvas_image_id:
            self.is_moving_crop_rect = False
            self.is_resizing_crop_rect = False; self.current_resize_handle = None
            return
        
        original_cursor = "crosshair" if not self.fixed_aspect_active else ""

        # If not moving and not in freeform mode with an active rect_id, 
        # or simply no rect_id exists (e.g. click without drag in freeform on empty canvas)
        if not self.is_moving_crop_rect and not self.is_resizing_crop_rect and (self.fixed_aspect_active or not self.crop_rect_id):
            self.is_moving_crop_rect = False # Ensure flag is reset
            self.is_resizing_crop_rect = False; self.current_resize_handle = None
            # If it was a fixed aspect rect that was being moved, details already updated during drag
            # If it's freeform and no rect_id, or fixed aspect and not moving, nothing to finalize from drag
            # However, if a rect exists (it should for fixed mode), ensure its details are current
            if self.crop_rect_id and self.crop_current_rect_coords:
                 self._update_crop_area_details()
                 # Check if the existing rect is valid to enable crop button
                 rect_x1, rect_y1, rect_x2, rect_y2 = self.crop_current_rect_coords
                 if abs(rect_x2 - rect_x1) > 1 and abs(rect_y2 - rect_y1) > 1:
                     self.crop_button['state'] = tk.NORMAL
                 else:
                     self.crop_button['state'] = tk.DISABLED
            else:
                self.crop_button['state'] = tk.DISABLED # No valid rect
            self.crop_canvas.config(cursor=original_cursor) # Reset cursor
            return

        # This point is reached if: 
        # 1. We were moving a fixed rect (is_moving_crop_rect was true)
        # 2. We were drawing a new freeform rect (is_moving_crop_rect was false, not fixed_aspect_active, and crop_rect_id exists)
        # 3. We were resizing a fixed rect (is_resizing_crop_rect was true)
        self.is_moving_crop_rect = False # Reset move flag in all cases on release
        self.is_resizing_crop_rect = False; self.current_resize_handle = None

        self._update_crop_area_details()
        # Enable crop button if a valid rectangle is drawn/moved
        if self.crop_current_rect_coords:
            rect_x1, rect_y1, rect_x2, rect_y2 = self.crop_current_rect_coords
            if abs(rect_x2 - rect_x1) > 1 and abs(rect_y2 - rect_y1) > 1: # Min 1x1 pixel crop
                self.crop_button['state'] = tk.NORMAL
            else: # Rectangle too small or invalid
                self.crop_button['state'] = tk.DISABLED
                if self.crop_rect_id:
                    self.crop_canvas.delete(self.crop_rect_id)
                    self.crop_rect_id = None
                self.crop_current_rect_coords = None
                self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A")
        else:
            self.crop_button['state'] = tk.DISABLED

    def _update_crop_area_details(self):
        if not self.crop_current_rect_coords or not self.display_crop_image_pil:
            self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A")
            return

        img_bounds = self._get_canvas_image_bounds()
        if not img_bounds: return
        img_x1_cv, img_y1_cv, _, _ = img_bounds

        # Get rectangle coordinates relative to the canvas
        cv_x1, cv_y1, cv_x2, cv_y2 = self.crop_current_rect_coords

        # Convert canvas rectangle coordinates to coordinates on the *displayed* image
        # (subtracting the offset of the image on the canvas)
        disp_img_crop_x1 = cv_x1 - img_x1_cv
        disp_img_crop_y1 = cv_y1 - img_y1_cv
        disp_img_crop_x2 = cv_x2 - img_x1_cv
        disp_img_crop_y2 = cv_y2 - img_y1_cv

        w = disp_img_crop_x2 - disp_img_crop_x1
        h = disp_img_crop_y2 - disp_img_crop_y1

        self.crop_area_details_var.set(f"Crop Area (X,Y,W,H): {int(disp_img_crop_x1)}, {int(disp_img_crop_y1)}, {int(w)}, {int(h)}")

    def _perform_crop(self):
        if not self.original_crop_image_pil:
            messagebox.showwarning("Crop Error", "No image loaded to crop.")
            return
        if not self.crop_current_rect_coords:
            messagebox.showwarning("Crop Error", "No area selected to crop.")
            return

        # Store current state for undo
        if self.original_crop_image_pil:
            self.pre_operation_pil_image = self.original_crop_image_pil.copy()
        else: # Should not happen if button is enabled, but as a safeguard
            messagebox.showerror("Crop Error", "Cannot perform crop: Original image is missing.")
            return

        # 1. Get canvas selection coordinates
        rect_x1_cv, rect_y1_cv, rect_x2_cv, rect_y2_cv = self.crop_current_rect_coords

        # 2. Convert to coordinates relative to the displayed image on canvas
        # (these are the ones stored in self.crop_canvas_image_offset_x/y)
        rel_x1 = rect_x1_cv - self.crop_canvas_image_offset_x
        rel_y1 = rect_y1_cv - self.crop_canvas_image_offset_y
        rel_x2 = rect_x2_cv - self.crop_canvas_image_offset_x
        rel_y2 = rect_y2_cv - self.crop_canvas_image_offset_y

        # 3. Convert to coordinates on the original image
        # Ensure scale factor is not zero to avoid division by zero
        if self.crop_image_scale_factor == 0:
            messagebox.showerror("Crop Error", "Invalid image scale factor.")
            return

        orig_crop_x1 = int(rel_x1 / self.crop_image_scale_factor)
        orig_crop_y1 = int(rel_y1 / self.crop_image_scale_factor)
        orig_crop_x2 = int(rel_x2 / self.crop_image_scale_factor)
        orig_crop_y2 = int(rel_y2 / self.crop_image_scale_factor)

        # Ensure coordinates are within original image bounds and x1<x2, y1<y2
        w_orig, h_orig = self.original_crop_image_pil.size
        orig_crop_x1 = max(0, min(orig_crop_x1, w_orig))
        orig_crop_y1 = max(0, min(orig_crop_y1, h_orig))
        orig_crop_x2 = max(0, min(orig_crop_x2, w_orig))
        orig_crop_y2 = max(0, min(orig_crop_y2, h_orig))

        if orig_crop_x1 >= orig_crop_x2 or orig_crop_y1 >= orig_crop_y2:
            messagebox.showwarning("Crop Error", "Calculated crop area is invalid (e.g., zero width/height).")
            return

        # 4. Perform the crop using Pillow
        try:
            self.final_cropped_pil_image = self.original_crop_image_pil.crop(
                (orig_crop_x1, orig_crop_y1, orig_crop_x2, orig_crop_y2)
            )
        except Exception as e:
            messagebox.showerror("Crop Error", f"Failed to crop image: {e}")
            self.pre_operation_pil_image = None # Invalidate undo state on error
            return

        # 5. Display cropped image IN PLACE on the main canvas
        if self.final_cropped_pil_image:
            # The cropped image becomes the new original for further operations or saving
            self.original_crop_image_pil = self.final_cropped_pil_image.copy()
            
            # Update the canvas with the new (cropped) original_crop_image_pil
            # This will also recalculate scale factor and offsets for the new displayed image.
            self._display_image_on_crop_canvas() 
            # Selection rectangle should be cleared after crop is applied to main canvas
            self._reset_cropper_selection_state(clear_rect_only=True)

            self.save_cropped_button['state'] = tk.NORMAL
            self.undo_operation_button['state'] = tk.NORMAL
            self.update_status("Image cropped successfully. Canvas updated.")
        else:
            self.update_status("Cropping failed or produced no image.")
            self.save_cropped_button['state'] = tk.DISABLED
            self.undo_operation_button['state'] = tk.DISABLED
            self.pre_operation_pil_image = None # Invalidate undo state

    def _save_cropped_image(self):
        # Saves the self.final_cropped_pil_image (which is same as current original_crop_image_pil after a crop)
        if not self.original_crop_image_pil: # Check original_crop_image_pil as it's what's on canvas
            messagebox.showwarning("Save Error", "No image to save.")
            return
        # If self.final_cropped_pil_image is None but original is there, it means no crop was done since load/undo
        # For clarity, let's ensure we save what _perform_crop put into final_cropped_pil_image, OR
        # if no crop was done recently, the current original_crop_image_pil.
        # The current logic: self.original_crop_image_pil *is* the cropped image after _perform_crop.

        image_to_save = self.original_crop_image_pil

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG files", "*.png"),
                ("JPEG files", "*.jpg;*.jpeg"),
                ("WEBP files", "*.webp"),
                ("All files", "*.*")
            ],
            title="Save Cropped Image As"
        )
        if not file_path:
            return # User cancelled
        
        try:
            # Determine file format from extension
            fmt = os.path.splitext(file_path)[1][1:].upper()
            if fmt == 'JPG': fmt = 'JPEG' # Pillow uses JPEG
            if not fmt: fmt = 'PNG' # Default to PNG if no extension

            image_to_save.save(file_path, format=fmt)
            self.update_status(f"Cropped image saved to {file_path}")
            messagebox.showinfo("Save Successful", f"Cropped image saved to {os.path.basename(file_path)}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save cropped image: {e}")
            self.update_status("Failed to save cropped image.")

    def _undo_last_operation(self):
        if not self.pre_operation_pil_image:
            self.update_status("Nothing to undo.")
            return
        
        self.original_crop_image_pil = self.pre_operation_pil_image.copy()
        self.pre_operation_pil_image = None # Only one level of undo
        self.final_cropped_pil_image = None # Clear the last cropped result if undoing that

        self._display_image_on_crop_canvas()
        self._reset_cropper_selection_state(clear_rect_only=True) # Clear selection after undo
        
        self.update_status("Last operation undone.")
        self.undo_operation_button['state'] = tk.DISABLED
        self.save_cropped_button['state'] = tk.DISABLED # Cannot save a 'crop' that was undone or transform
        self.crop_button['state'] = tk.DISABLED # Require new selection after undo
        self._enable_transform_buttons(True)

    def _reset_cropper_ui_for_new_image(self):
        self.crop_canvas.delete("all") # Clear canvas drawings
        self.crop_canvas_image_id = None
        self.original_crop_image_pil = None
        self.display_crop_image_pil = None
        self.final_cropped_pil_image = None
        self.pre_operation_pil_image = None
        self.selected_crop_file_var.set("No file selected.")
        self.crop_area_details_var.set("Crop Area (X,Y,W,H): N/A")
        self._reset_cropper_selection_state()
        self.crop_button['state'] = tk.DISABLED
        self.save_cropped_button['state'] = tk.DISABLED
        self.undo_operation_button['state'] = tk.DISABLED
        self._enable_transform_buttons(False)

    def _enable_transform_buttons(self, enable=True):
        state = tk.NORMAL if enable else tk.DISABLED
        if hasattr(self, 'rotate_left_button'): self.rotate_left_button['state'] = state
        if hasattr(self, 'rotate_right_button'): self.rotate_right_button['state'] = state
        if hasattr(self, 'flip_horizontal_button'): self.flip_horizontal_button['state'] = state
        if hasattr(self, 'flip_vertical_button'): self.flip_vertical_button['state'] = state

    def _flip_image_horizontal(self):
        if not self.original_crop_image_pil: return
        self.update_status("Flipping image horizontally...")
        
        self.pre_operation_pil_image = self.original_crop_image_pil.copy()
        try:
            self.original_crop_image_pil = self.original_crop_image_pil.transpose(Image.FLIP_LEFT_RIGHT)
        except Exception as e:
            messagebox.showerror("Flip Error", f"Failed to flip image: {e}")
            self.pre_operation_pil_image = None # Invalidate undo
            self.update_status("Horizontal flip failed.")
            return

        self._display_image_on_crop_canvas()
        self._reset_cropper_selection_state(clear_rect_only=True)
        if self.fixed_aspect_active:
            self._draw_default_fixed_aspect_rectangle()
        self.undo_operation_button['state'] = tk.NORMAL
        self.crop_button['state'] = tk.DISABLED
        self.save_cropped_button['state'] = tk.DISABLED
        self.update_status("Image flipped horizontally. Redraw selection to crop.")

    def _flip_image_vertical(self):
        """Flips the current original image vertically.

        Performs an in-place vertical flip of `self.original_crop_image_pil`.
        The previous image state is saved to `self.pre_operation_pil_image`
        to enable undo functionality. Uses Pillow's `Image.FLIP_TOP_BOTTOM`.

        After flipping, the image display on the canvas is refreshed. Any
        existing crop selection is reset. If a fixed aspect ratio was active,
        the default selection rectangle for that ratio is redrawn.
        UI button states (Undo, Crop, Save) and the status bar are updated.
        """
        if not self.original_crop_image_pil: return
        self.update_status("Flipping image vertically...")
        
        self.pre_operation_pil_image = self.original_crop_image_pil.copy()
        try:
            self.original_crop_image_pil = self.original_crop_image_pil.transpose(Image.FLIP_TOP_BOTTOM)
        except Exception as e:
            messagebox.showerror("Flip Error", f"Failed to flip image: {e}")
            self.pre_operation_pil_image = None # Invalidate undo
            self.update_status("Vertical flip failed.")
            return

        self._display_image_on_crop_canvas()
        self._reset_cropper_selection_state(clear_rect_only=True)
        if self.fixed_aspect_active:
            self._draw_default_fixed_aspect_rectangle()
        self.undo_operation_button['state'] = tk.NORMAL
        self.crop_button['state'] = tk.DISABLED
        self.save_cropped_button['state'] = tk.DISABLED
        self.update_status("Image flipped vertically. Redraw selection to crop.")

    def _rotate_image_left(self):
        """Rotates the current original image 90 degrees counter-clockwise.

        Performs an in-place 90-degree counter-clockwise rotation of
        `self.original_crop_image_pil`. The previous image state is saved to
        `self.pre_operation_pil_image` for undo. Uses Pillow's
        `rotate(90, expand=True)` method; `expand=True` adjusts image
        dimensions to fit the rotated content.

        Post-rotation, the canvas display is refreshed, any crop selection
        is reset, and if a fixed aspect ratio was active, its default
        selection rectangle is redrawn. UI buttons and status bar are updated.
        """
        if not self.original_crop_image_pil: return
        self.update_status("Rotating image 90° left...")
        
        self.pre_operation_pil_image = self.original_crop_image_pil.copy()
        try:
            # Rotate 90 degrees counter-clockwise. PIL's rotate is counter-clockwise.
            self.original_crop_image_pil = self.original_crop_image_pil.rotate(90, expand=True)
        except Exception as e:
            messagebox.showerror("Rotation Error", f"Failed to rotate image: {e}")
            self.pre_operation_pil_image = None # Invalidate undo
            self.update_status("Rotation failed.")
            return

        self._display_image_on_crop_canvas()
        self._reset_cropper_selection_state(clear_rect_only=True) # Clear selection, new one needed
        if self.fixed_aspect_active:
            self._draw_default_fixed_aspect_rectangle()
        self.undo_operation_button['state'] = tk.NORMAL
        self.crop_button['state'] = tk.DISABLED # Require new selection
        self.save_cropped_button['state'] = tk.DISABLED # Image transformed, not cropped for saving
        self.update_status("Image rotated 90° left. Redraw selection to crop.")

    def _rotate_image_right(self):
        """Rotates the current original image 90 degrees clockwise.

        Performs an in-place 90-degree clockwise rotation of
        `self.original_crop_image_pil`. The previous image state is saved to
        `self.pre_operation_pil_image` for undo. Uses Pillow's
        `rotate(-90, expand=True)` method (a negative angle rotates clockwise);
        `expand=True` adjusts image dimensions.

        Post-rotation, the canvas display is refreshed, any crop selection
        is reset, and if a fixed aspect ratio was active, its default
        selection rectangle is redrawn. UI buttons and status bar are updated.
        """
        if not self.original_crop_image_pil: return
        self.update_status("Rotating image 90° right...")

        self.pre_operation_pil_image = self.original_crop_image_pil.copy()
        try:
            # Rotate 270 degrees counter-clockwise (which is 90 clockwise).
            self.original_crop_image_pil = self.original_crop_image_pil.rotate(-90, expand=True) # Or 270
        except Exception as e:
            messagebox.showerror("Rotation Error", f"Failed to rotate image: {e}")
            self.pre_operation_pil_image = None # Invalidate undo
            self.update_status("Rotation failed.")
            return
            
        self._display_image_on_crop_canvas()
        self._reset_cropper_selection_state(clear_rect_only=True)
        if self.fixed_aspect_active:
            self._draw_default_fixed_aspect_rectangle()
        self.undo_operation_button['state'] = tk.NORMAL
        self.crop_button['state'] = tk.DISABLED
        self.save_cropped_button['state'] = tk.DISABLED
        self.update_status("Image rotated 90° right. Redraw selection to crop.")

    def _draw_default_fixed_aspect_rectangle(self):
        """Draws a default crop selection rectangle for the current fixed aspect ratio.

        This is used when a fixed aspect ratio is first selected or after image
        transformations if a fixed aspect ratio was active. The rectangle is sized
        to fit the aspect ratio within the displayed image and centered.
        It clears any previous selection, updates coordinates, details, and button states.
        """
        if not self.display_crop_image_pil or not self.current_aspect_ratio_val or not self.crop_canvas_image_id:
            return

        # Clear existing rect before drawing new default one
        if self.crop_rect_id:
            self.crop_canvas.delete(self.crop_rect_id)
            self.crop_rect_id = None

        img_bounds = self._get_canvas_image_bounds()
        if not img_bounds: return
        img_x1_cv, img_y1_cv, img_x2_cv, img_y2_cv = img_bounds
        
        img_w_on_canvas = img_x2_cv - img_x1_cv
        img_h_on_canvas = img_y2_cv - img_y1_cv
        aspect = self.current_aspect_ratio_val

        rect_w = img_w_on_canvas
        rect_h = rect_w / aspect

        if rect_h > img_h_on_canvas:
            rect_h = img_h_on_canvas
            rect_w = rect_h * aspect
        
        # Center the rectangle on the displayed image
        offset_x = (img_w_on_canvas - rect_w) / 2
        offset_y = (img_h_on_canvas - rect_h) / 2

        rect_x1 = img_x1_cv + offset_x
        rect_y1 = img_y1_cv + offset_y
        rect_x2 = rect_x1 + rect_w
        rect_y2 = rect_y1 + rect_h

        self.crop_rect_id = self.crop_canvas.create_rectangle(
            rect_x1, rect_y1, rect_x2, rect_y2, outline='red', width=2
        )
        self.crop_current_rect_coords = (rect_x1, rect_y1, rect_x2, rect_y2)
        self._update_crop_area_details()
        self.crop_button['state'] = tk.NORMAL
        self.save_cropped_button['state'] = tk.DISABLED

    def _validate_and_clamp_rect_coords(self, x1, y1, x2, y2, img_bounds):
        """Validates and clamps rectangle coordinates against image bounds and minimum size.

        Ensures coordinates are ordered (x1 < x2, y1 < y2), clamps them within
        the provided 'img_bounds' (canvas coordinates of the displayed image),
        and checks against MIN_RECT_SIZE.

        Args:
            x1, y1, x2, y2: Proposed canvas coordinates for the rectangle.
            img_bounds: Tuple (img_x1_cv, img_y1_cv, img_x2_cv, img_y2_cv)
                        representing the image's bounding box on the canvas.

        Returns:
            Tuple (nx1, ny1, nx2, ny2) of validated coordinates, or None if invalid.
        """
        img_x1_cv, img_y1_cv, img_x2_cv, img_y2_cv = img_bounds

        # Ensure x1 < x2 and y1 < y2
        nx1, nx2 = min(x1, x2), max(x1, x2)
        ny1, ny2 = min(y1, y2), max(y1, y2)

        # Clamp to image boundaries
        nx1 = max(img_x1_cv, nx1)
        ny1 = max(img_y1_cv, ny1)
        nx2 = min(img_x2_cv, nx2)
        ny2 = min(img_y2_cv, ny2)

        # Check minimum size
        if (nx2 - nx1) < MIN_RECT_SIZE or (ny2 - ny1) < MIN_RECT_SIZE:
            # Attempt to preserve aspect ratio if possible, anchored at a primary point
            # This can get complex, for now, if too small, might revert or use last valid. 
            # Or, simply return None to indicate invalid resize here if strictness is desired.
            # For now, just ensure it's not inverted and clamped.
            # The resize logic should ideally prevent this before calling validate.
            if self.crop_current_rect_coords: # Fallback to last known good coords for now
                # This could be problematic if continuously dragged into invalid state.
                # A better approach might be to stop the rect from shrinking past MIN_RECT_SIZE in the drag logic itself.
                # The MIN_RECT_SIZE checks in handle logic are primary. This is a final safeguard.
                current_w = self.crop_current_rect_coords[2] - self.crop_current_rect_coords[0]
                current_h = self.crop_current_rect_coords[3] - self.crop_current_rect_coords[1]
                if current_w < MIN_RECT_SIZE or current_h < MIN_RECT_SIZE:
                    return None # previous was also invalid
                return self.crop_current_rect_coords
            return None 

        return nx1, ny1, nx2, ny2

    def update_status(self, message):
        """Updates the application's status bar with the given message.

        Args:
            message (str): The message to display in the status bar.
        """
        self.status_bar_text.set(message)
        self.root.update_idletasks() 

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageManipulatorApp(root)
    root.mainloop()
