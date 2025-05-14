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

class ToolTip:
    """Create a tooltip for a given widget."""
    def __init__(self, widget, text='widget info', delay=500):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.tooltip = None
        self.id = None
        self.x = self.y = 0
        self._schedule()

    def _schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        if self.tooltip or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox('insert')
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry(f"+{x}+{y}")
        
        label = ttk.Label(tw, text=self.text, justify='left',
                         background='#ffffe0', relief='solid', borderwidth=1,
                         font=('Segoe UI', 9))
        label.pack(ipadx=1)
        
        self.widget.bind('<Leave>', self.hide)

    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        self.unschedule()

    def update_text(self, text):
        self.text = text
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
            self.show()

class ImageManipulatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comprehensive Image Manipulator")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Style
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Custom styling
        self.style.configure('.', font=('Segoe UI', 10))
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0')
        self.style.configure('TButton', padding=6, relief='flat', background='#e1e1e1')
        self.style.map('TButton',
                     foreground=[('pressed', 'black'), ('active', 'black')],
                     background=[('pressed', '!disabled', '#d0d0d0'), ('active', '#e8e8e8')])
        
        # Style for active tab
        self.style.configure('TNotebook.Tab', padding=[12, 4], font=('Segoe UI', 10, 'bold'))
        self.style.map('TNotebook.Tab',
                     background=[('selected', '#f0f0f0'), ('!selected', '#d0d0d0')],
                     foreground=[('selected', '#2c3e50'), ('!selected', '#7f8c8d')],
                     padding=[('selected', [12, 4]), ('!selected', [12, 4])])
        
        # Style for entry fields
        self.style.configure('TEntry', padding=4)
        
        # Style for the status bar
        self.style.configure('Status.TLabel', background='#2c3e50', foreground='white', padding=8, font=('Segoe UI', 9))
        
        # Style for listbox
        self.style.configure('TListbox', background='white', fieldbackground='white', foreground='#2c3e50')
        
        # Style for the scale (quality slider)
        self.style.configure('Horizontal.TScale', background='#f0f0f0')

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
        
        # --- HEIC to JPG Section State Variables ---
        self.heic_file_paths = []
        self.heic_output_dir = tk.StringVar(value=os.getcwd()) # Default to current dir
        self.heic_quality_var = tk.IntVar(value=90) # Default quality
        self.heic_listbox = None
        self.heic_preview_frame = None
        self.heic_thumbnails = {}  # Store thumbnail PhotoImage objects to prevent garbage collection

        # Main frame with grid configuration
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(expand=True, fill=tk.BOTH)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)  # Give weight to the notebook frame
        main_frame.rowconfigure(2, weight=0)  # Status bar row (fixed height)
        
        # Add a title label with proper grid configuration
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, sticky='nsew', pady=(0, 15))
        title_frame.columnconfigure(0, weight=1)  # Allow title to expand
        
        title_label = ttk.Label(
            title_frame,
            text="Comprehensive Image Manipulator",
            font=('Segoe UI', 16, 'bold'),
            foreground='#2c3e50',
            anchor='center',
            padding=(0, 0, 0, 5)  # Add padding below the title
        )
        title_label.grid(row=0, column=0, sticky='ew')
        
        # Add a separator
        separator = ttk.Separator(title_frame, orient='horizontal')
        separator.grid(row=1, column=0, sticky='ew', pady=5)

        # Feature Notebook (Tabs) with grid configuration
        notebook_frame = ttk.Frame(main_frame, style='Card.TFrame')
        notebook_frame.grid(row=1, column=0, sticky='nsew', pady=5)
        notebook_frame.columnconfigure(0, weight=1)
        notebook_frame.rowconfigure(0, weight=1)
        
        self.feature_notebook = ttk.Notebook(notebook_frame)
        self.feature_notebook.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        
        # Configure notebook to expand
        self.feature_notebook.columnconfigure(0, weight=1)
        self.feature_notebook.rowconfigure(0, weight=1)
        
        # Add a subtle border around the notebook
        self.style.configure('Card.TFrame', background='#e0e0e0', relief='solid', borderwidth=1)

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

        # Populate the "HEIC to JPG" tab.
        self.setup_heic_to_jpg_tab()

        # Status bar
        status_bar_frame = ttk.Frame(main_frame)
        status_bar_frame.grid(row=2, column=0, sticky='ew')
        status_bar_frame.columnconfigure(0, weight=1)
        
        self.status_bar_text = tk.StringVar()
        self.status_bar_text.set(" Ready")
        
        status_bar = ttk.Label(
            status_bar_frame,
            textvariable=self.status_bar_text,
            style='Status.TLabel',
            anchor=tk.W,
            padding=(10, 5, 10, 5)
        )
        status_bar.grid(row=0, column=0, sticky='ew')
        
        # Add a resize grip for better UX
        resize_grip = ttk.Sizegrip(status_bar_frame)
        resize_grip.grid(row=0, column=1, sticky='se')

    def create_feature_tab(self, tab_name):
        """Creates a new tab in the notebook and returns it."""
        tab = ttk.Frame(self.feature_notebook, padding="10")
        self.feature_notebook.add(tab, text=tab_name)
        
        # Configure tab to expand
        tab.columnconfigure(0, weight=1)
        tab.rowconfigure(0, weight=1)
        
        return tab

    def setup_crop_tab(self):
        """Sets up the UI for the Enhanced Image Cropper tab."""
        for widget in self.tab_crop.winfo_children(): 
            widget.destroy()

        # Main content frame for the cropper tab with grid configuration
        self.tab_crop.columnconfigure(0, weight=1)
        self.tab_crop.rowconfigure(0, weight=1)
        
        cropper_content_frame = ttk.Frame(self.tab_crop)
        cropper_content_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        cropper_content_frame.columnconfigure(0, weight=1)
        cropper_content_frame.rowconfigure(1, weight=1)  # Middle frame with canvas gets extra space

        # Top: File selection and info
        top_frame = ttk.Frame(cropper_content_frame)
        top_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        top_frame.columnconfigure(1, weight=1)  # Allow the file label to expand
        
        # Use grid for better control
        load_button = ttk.Button(top_frame, text="Select Image...", command=self.load_image_for_cropping)
        load_button.grid(row=0, column=0, padx=(0, 10), sticky='w')
        
        selected_file_label = ttk.Label(top_frame, textvariable=self.selected_crop_file_var, anchor=tk.W)
        selected_file_label.grid(row=0, column=1, sticky='ew')

        # Middle: Canvas and Controls
        middle_frame = ttk.Frame(cropper_content_frame)
        middle_frame.grid(row=1, column=0, sticky='nsew')
        middle_frame.columnconfigure(0, weight=1)  # Canvas frame expands
        middle_frame.columnconfigure(1, weight=0)  # Controls have fixed width
        middle_frame.rowconfigure(0, weight=1)     # Row with canvas expands

        # Canvas Frame (Left part of middle_frame)
        canvas_frame = ttk.Frame(middle_frame, relief=tk.SUNKEN, borderwidth=1)
        canvas_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # Create a container frame for the canvas with scrollbars
        canvas_container = ttk.Frame(canvas_frame)
        canvas_container.pack(expand=True, fill=tk.BOTH)
        
        # Add scrollbars
        y_scroll = ttk.Scrollbar(canvas_container, orient=tk.VERTICAL)
        x_scroll = ttk.Scrollbar(canvas_container, orient=tk.HORIZONTAL)
        
        self.crop_canvas = tk.Canvas(
            canvas_container,
            bg='gray75',
            highlightthickness=0,
            yscrollcommand=y_scroll.set,
            xscrollcommand=x_scroll.set
        )
        
        # Configure scrollbars
        y_scroll.config(command=self.crop_canvas.yview)
        x_scroll.config(command=self.crop_canvas.xview)
        
        # Grid layout for canvas and scrollbars
        self.crop_canvas.grid(row=0, column=0, sticky='nsew')
        y_scroll.grid(row=0, column=1, sticky='ns')
        x_scroll.grid(row=1, column=0, sticky='ew')
        
        # Configure grid weights for the container
        canvas_container.columnconfigure(0, weight=1)
        canvas_container.rowconfigure(0, weight=1)
        
        # Make the canvas frame expand with the window
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)
        
        # Bind mouse events
        self.crop_canvas.bind("<ButtonPress-1>", self._on_crop_canvas_press)
        self.crop_canvas.bind("<B1-Motion>", self._on_crop_canvas_drag)
        self.crop_canvas.bind("<ButtonRelease-1>", self._on_crop_canvas_release)
        self.crop_canvas.bind("<Motion>", self._on_crop_canvas_motion) # For cursor changes
        self.crop_canvas.bind("<Configure>", self._on_canvas_configure) # For handling canvas resize

        # Controls Frame (Right part of middle_frame)
        controls_frame = ttk.Frame(middle_frame, width=220) 
        controls_frame.grid(row=0, column=1, sticky='nsew', padx=(0, 5))
        controls_frame.columnconfigure(0, weight=1)
        controls_frame.rowconfigure(1, weight=1)  # For the controls frame to fill space

        # Cropper Controls Frame (Select, Aspect Ratio, Crop, Save, Undo)
        cropper_controls_frame = ttk.LabelFrame(controls_frame, text="Controls", padding=10)
        cropper_controls_frame.grid(row=0, column=0, sticky='nsew', padx=5, pady=5)
        cropper_controls_frame.columnconfigure(0, weight=1)  # Make controls expand to fill frame

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
        """Display or refresh an image on the main crop canvas.

        This method scales and centers the provided `image_to_display` (or
        `self.original_crop_image_pil` if None) onto `self.crop_canvas`.
        The image is resized to fit within the canvas dimensions (or fallback
        to `PREVIEW_MAX_WIDTH`/`HEIGHT` if canvas is not yet sized) while
        maintaining aspect ratio using `Image.Resampling.LANCZOS`.
        
        Also updates the scroll region to ensure the entire image is accessible.
        
        Key actions:
        - Stores the scaled Pillow image as `self.display_crop_image_pil`.
        - Stores the PhotoImage for Tkinter as `self.display_crop_image_tk`.
        - Calculates and stores `self.crop_image_scale_factor` (actual image to displayed image).
        - Calculates and stores `self.crop_canvas_image_offset_x` and `_y` (for centering).
        - Clears the canvas (`"all"`) and draws the new image.
        - Resets `self.crop_rect_id`, `self.crop_current_rect_coords`, and updates
          the crop area details display to "N/A".
        
        Args:
            image_to_display: The Pillow image object to display. Defaults to 
                           `self.original_crop_image_pil`.
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
        self.crop_canvas.config(scrollregion=self.crop_canvas.bbox("all"))

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

    def _on_canvas_configure(self, event=None):
        """Handle canvas resizing events.
        
        This method is called when the canvas is resized. It ensures the image
        is properly scaled and centered when the window is resized.
        """
        if not self.original_crop_image_pil:
            return
            
        # Only redraw if the canvas size has actually changed
        canvas_width = self.crop_canvas.winfo_width()
        canvas_height = self.crop_canvas.winfo_height()
        
        if canvas_width > 1 and canvas_height > 1:  # Ensure valid canvas size
            # Store the current crop state
            had_rect = self.crop_rect_id is not None
            
            # Redraw the image
            self._display_image_on_crop_canvas()
            
            # If we had a rectangle before, redraw it with the same aspect ratio
            if had_rect and self.fixed_aspect_active and self.current_aspect_ratio_val:
                self._draw_default_fixed_aspect_rectangle()
            # If we had a rectangle but not fixed aspect, clear it
            elif had_rect:
                self._reset_cropper_selection_state(clear_rect_only=True)

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

    def setup_heic_to_jpg_tab(self):
        """Sets up the UI for the HEIC to JPG Converter tab."""
        for widget in self.tab_heic_to_jpg.winfo_children():
            widget.destroy()

        # Configure grid for the tab
        self.tab_heic_to_jpg.columnconfigure(0, weight=1)
        self.tab_heic_to_jpg.rowconfigure(0, weight=1)
        
        # Main content frame for the HEIC to JPG tab with grid configuration
        heic_content_frame = ttk.Frame(self.tab_heic_to_jpg)
        heic_content_frame.grid(row=0, column=0, sticky='nsew')
        heic_content_frame.columnconfigure(0, weight=1)
        heic_content_frame.rowconfigure(1, weight=1)  # Give weight to the middle frame

        # Top: File selection and list clearing
        top_frame = ttk.Frame(heic_content_frame)
        top_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))

        select_files_button = ttk.Button(top_frame, text="Select HEIC/HEIF Files...", command=self._heic_select_files)
        select_files_button.pack(side=tk.LEFT, padx=(0, 10))

        clear_list_button = ttk.Button(top_frame, text="Clear List", command=self._heic_clear_list)
        clear_list_button.pack(side=tk.LEFT, padx=(0, 10))

        # Middle: Split view between listbox and preview
        middle_frame = ttk.PanedWindow(heic_content_frame, orient=tk.HORIZONTAL)
        middle_frame.grid(row=1, column=0, sticky='nsew', pady=(0,10))
        
        # Left side: Listbox frame
        list_frame = ttk.Frame(middle_frame)
        middle_frame.add(list_frame, weight=2)
        
        # Right side: Preview frame
        preview_frame = ttk.Frame(middle_frame)
        middle_frame.add(preview_frame, weight=3)
        
        # Listbox for selected files
        self.heic_listbox = tk.Listbox(list_frame, selectmode=tk.EXTENDED)
        self.heic_listbox.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=(0,5))
        self.heic_listbox.bind('<<ListboxSelect>>', self._update_heic_preview)
        
        heic_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.heic_listbox.yview)
        heic_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.heic_listbox.config(yscrollcommand=heic_scrollbar.set)
        
        # Preview area
        preview_label = ttk.Label(preview_frame, text="Preview", font=('Segoe UI', 10, 'bold'))
        preview_label.pack(pady=(0, 5))
        
        # Canvas for preview with scrollbars
        preview_canvas_frame = ttk.Frame(preview_frame)
        preview_canvas_frame.pack(expand=True, fill=tk.BOTH)
        
        self.heic_preview_canvas = tk.Canvas(preview_canvas_frame, bg='white', bd=1, relief=tk.SOLID)
        preview_v_scroll = ttk.Scrollbar(preview_canvas_frame, orient=tk.VERTICAL, command=self.heic_preview_canvas.yview)
        preview_h_scroll = ttk.Scrollbar(preview_canvas_frame, orient=tk.HORIZONTAL, command=self.heic_preview_canvas.xview)
        
        self.heic_preview_canvas.configure(yscrollcommand=preview_v_scroll.set, xscrollcommand=preview_h_scroll.set)
        
        preview_v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        preview_h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.heic_preview_canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)
        
        # Frame inside canvas to hold preview images
        self.heic_preview_frame = ttk.Frame(self.heic_preview_canvas)
        self.heic_preview_canvas.create_window((0, 0), window=self.heic_preview_frame, anchor='nw')
        
        # Bind canvas to update scroll region
        self.heic_preview_frame.bind('<Configure>', lambda e: self.heic_preview_canvas.configure(
            scrollregion=self.heic_preview_canvas.bbox('all')
        ))

        # Bottom: Controls (Output dir, Quality, Convert)
        bottom_frame = ttk.Frame(heic_content_frame)
        bottom_frame.grid(row=2, column=0, sticky='ew', pady=(5,0))
        
        output_dir_frame = ttk.Frame(bottom_frame)
        output_dir_frame.pack(fill=tk.X, pady=(0,5))
        ttk.Label(output_dir_frame, text="Output Directory:").pack(side=tk.LEFT, padx=(0,5))
        output_dir_entry = ttk.Entry(output_dir_frame, textvariable=self.heic_output_dir, width=50)
        output_dir_entry.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        select_output_button = ttk.Button(output_dir_frame, text="Browse...", command=self._heic_select_output_dir)
        select_output_button.pack(side=tk.LEFT)

        quality_frame = ttk.Frame(bottom_frame)
        quality_frame.pack(fill=tk.X, pady=(0,10))
        ttk.Label(quality_frame, text="JPG Quality (1-100):").pack(side=tk.LEFT, padx=(0,5))
        quality_scale = ttk.Scale(quality_frame, from_=1, to=100, orient=tk.HORIZONTAL, variable=self.heic_quality_var, length=200)
        quality_scale.pack(side=tk.LEFT, padx=(0,5))
        quality_label_val = ttk.Label(quality_frame, text=str(self.heic_quality_var.get())) # Initial value
        quality_label_val.pack(side=tk.LEFT)
        self.heic_quality_var.trace_add("write", lambda *args: quality_label_val.config(text=f"{self.heic_quality_var.get():.0f}"))


        convert_button = ttk.Button(bottom_frame, text="Convert Selected to JPG", command=self._heic_convert_files)
        convert_button.pack(pady=(5,0))

    def _create_thumbnail(self, image_path, size=(200, 200)):
        """Create a thumbnail from an image file."""
        try:
            img = Image.open(image_path)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Convert to RGB if necessary (for HEIC with alpha channel)
            if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'RGBA':
                    background.paste(img, mask=img.split()[3])  # 3 is the alpha channel
                else:
                    background.paste(img, (0, 0), img)
                img = background
            
            photo = ImageTk.PhotoImage(img)
            return photo
        except Exception as e:
            print(f"Error creating thumbnail for {image_path}: {e}")
            # Return a blank image with error text
            error_img = Image.new('RGB', size, (240, 240, 240))
            try:
                from PIL import ImageDraw, ImageFont
                draw = ImageDraw.Draw(error_img)
                # Try to use a default font, fallback to default if not available
                try:
                    font = ImageFont.truetype("arial.ttf", 12)
                except:
                    font = ImageFont.load_default()
                text = "Preview not available"
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                position = ((size[0] - text_width) // 2, (size[1] - text_height) // 2)
                draw.text(position, text, fill="black", font=font)
                return ImageTk.PhotoImage(error_img)
            except:
                return ImageTk.PhotoImage(error_img)

    def _remove_preview_item(self, file_path):
        """Remove an item from the preview and file list."""
        if file_path in self.heic_file_paths:
            # Find and remove the file path
            index = self.heic_file_paths.index(file_path)
            self.heic_file_paths.pop(index)
            
            # Update the listbox
            self.heic_listbox.delete(index)
            
            # Update the preview
            selected_indices = self.heic_listbox.curselection()
            self._update_heic_preview()
            
            # Try to maintain selection
            if selected_indices:
                try:
                    self.heic_listbox.selection_set(selected_indices[0])
                except:
                    pass
            
            self.status_bar_text.set(f"Removed: {os.path.basename(file_path)}")

    def _update_heic_preview(self, event=None):
        """Update the preview area with selected thumbnails."""
        # Clear previous previews
        for widget in self.heic_preview_frame.winfo_children():
            widget.destroy()
        
        # Clear previous thumbnails to prevent memory leaks
        self.heic_thumbnails.clear()
        
        selected_indices = self.heic_listbox.curselection()
        if not selected_indices and self.heic_listbox.size() > 0:
            # If nothing is selected but there are items, select the first one
            self.heic_listbox.selection_set(0)
            selected_indices = (0,)
        
        if not selected_indices:
            return
            
        # Configure grid for preview items
        cols = 2  # Number of columns for the grid
        for i, idx in enumerate(selected_indices):
            if 0 <= idx < len(self.heic_file_paths):
                file_path = self.heic_file_paths[idx]
                
                # Create a frame for each preview item
                item_frame = ttk.Frame(self.heic_preview_frame, padding=5, relief='groove', borderwidth=1)
                item_frame.grid(row=i//cols, column=i%cols, padx=5, pady=5, sticky='nsew')
                
                # Create a frame for the header (filename + delete button)
                header_frame = ttk.Frame(item_frame)
                header_frame.pack(fill=tk.X, pady=(0, 5))
                
                # Display filename
                filename = os.path.basename(file_path)
                display_name = filename[:20] + '...' if len(filename) > 25 else filename
                label_text = ttk.Label(header_frame, text=display_name, wraplength=120, justify='left')
                label_text.pack(side=tk.LEFT, fill=tk.X, expand=True, anchor='w')
                
                # Add delete button
                delete_btn = ttk.Button(
                    header_frame, 
                    text="✕", 
                    width=2,
                    command=lambda f=file_path: self._remove_preview_item(f)
                )
                delete_btn.pack(side=tk.RIGHT, padx=(5, 0))
                
                # Create thumbnail
                thumbnail = self._create_thumbnail(file_path)
                if thumbnail:
                    # Store reference to prevent garbage collection
                    self.heic_thumbnails[file_path] = thumbnail
                    
                    # Display thumbnail
                    label_img = ttk.Label(item_frame, image=thumbnail)
                    label_img.pack()
                    
                    # Add tooltip with full filename
                    ToolTip(label_img, text=filename, delay=500)
        
        # Configure grid weights
        rows = (len(selected_indices) + cols - 1) // cols
        for i in range(rows):
            self.heic_preview_frame.grid_rowconfigure(i, weight=1)
        for i in range(cols):
            self.heic_preview_frame.grid_columnconfigure(i, weight=1)
        
        # Update scroll region
        self.heic_preview_frame.update_idletasks()
        self.heic_preview_canvas.configure(scrollregion=self.heic_preview_canvas.bbox('all'))

    def _heic_select_files(self):
        """Select HEIC/HEIF files and add them to the listbox."""
        filetypes = [("HEIC/HEIF files", "*.heic *.heif"), ("All files", "*.*")]
        selected_files = filedialog.askopenfilenames(
            title="Select HEIC/HEIF Files",
            filetypes=filetypes
        )
        if selected_files:
            for f_path in selected_files:
                if f_path not in self.heic_file_paths:
                    self.heic_file_paths.append(f_path)
                    self.heic_listbox.insert(tk.END, os.path.basename(f_path))
            self.status_bar_text.set(f"{len(self.heic_file_paths)} file(s) selected.")
            # Select the newly added files and update preview
            if len(selected_files) > 0:
                first_new = len(self.heic_file_paths) - len(selected_files)
                self.heic_listbox.selection_clear(0, tk.END)
                for i in range(first_new, len(self.heic_file_paths)):
                    self.heic_listbox.selection_set(i)
                self._update_heic_preview()
        else:
            self.status_bar_text.set("No files selected.")

    def _heic_select_output_dir(self):
        """Select the output directory for converted JPG files."""
        directory = filedialog.askdirectory(
            title="Select Output Directory",
            initialdir=self.heic_output_dir.get() # Start from current or previously selected
        )
        if directory:
            self.heic_output_dir.set(directory)
            self.status_bar_text.set(f"Output directory set to: {directory}")

    def _heic_clear_list(self):
        """Clear the list of selected HEIC files and the listbox."""
        self.heic_file_paths.clear()
        self.heic_listbox.delete(0, tk.END)
        # Clear preview
        for widget in self.heic_preview_frame.winfo_children():
            widget.destroy()
        self.heic_thumbnails.clear()
        self.status_bar_text.set("File list cleared.")
    
    def _heic_convert_files(self):
        """Convert selected HEIC/HEIF files to JPG format."""
        if not self.heic_file_paths:
            messagebox.showwarning("No Files", "Please select HEIC/HEIF files to convert.")
            self.status_bar_text.set("Conversion failed: No files selected.")
            return

        output_dir = self.heic_output_dir.get()
        if not output_dir or not os.path.isdir(output_dir):
            messagebox.showerror("Invalid Directory", "Please select a valid output directory.")
            self.status_bar_text.set("Conversion failed: Invalid output directory.")
            return

        quality = self.heic_quality_var.get()
        converted_count = 0
        error_count = 0
        error_files = []

        self.status_bar_text.set(f"Starting conversion of {len(self.heic_file_paths)} files...")
        self.root.update_idletasks() # Update UI to show starting message

        for i, file_path in enumerate(self.heic_file_paths):
            base_name = os.path.splitext(os.path.basename(file_path))[0]
            output_jpg_path = os.path.join(output_dir, base_name + ".jpg")
            self.status_bar_text.set(f"Converting ({i+1}/{len(self.heic_file_paths)}): {os.path.basename(file_path)}...")
            self.root.update_idletasks()

            try:
                # Pillow uses pillow-heif automatically if registered
                img = Image.open(file_path)

                # Handle alpha channel for JPG conversion
                if img.mode == 'RGBA' or img.mode == 'PA' or (isinstance(img.info.get('icc_profile'), bytes) and b'CMYK' in img.info.get('icc_profile')):
                    # If RGBA or PA, paste on a white background
                    # Some HEIC might also be CMYK, which JPG supports, but transparency needs handling
                    if img.mode == 'RGBA' or img.mode == 'PA':
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        # The mask is the alpha channel itself
                        try:
                            mask = img.split()[-1] # Get the alpha channel
                            if mask.mode != 'L': # Ensure mask is 'L' mode
                                mask = mask.convert('L')
                            background.paste(img, (0,0), mask=mask)
                            img = background
                        except IndexError: # In case split doesn't return enough channels (e.g. for 'P' with alpha in palette)
                            # Fallback for images like 'P' mode with transparency
                            img = img.convert("RGBA")
                            mask = img.split()[-1]
                            if mask.mode != 'L': 
                                mask = mask.convert('L')
                            background.paste(img, (0,0), mask=mask)
                            img = background

                # Ensure final image is RGB for JPG saving
                if img.mode != 'RGB':
                    img = img.convert('RGB')

                img.save(output_jpg_path, "JPEG", quality=quality, optimize=True)
                converted_count += 1
            except UnidentifiedImageError:
                error_files.append(f"{os.path.basename(file_path)} (Unrecognized format or not an image)")
                error_count += 1
            except FileNotFoundError:
                error_files.append(f"{os.path.basename(file_path)} (File not found during conversion)")
                error_count += 1
            except Exception as e:
                error_files.append(f"{os.path.basename(file_path)} ({type(e).__name__}: {e})")
                error_count += 1
                print(f"Error converting {file_path}: {e}") # Log to console for debugging

        final_message = f"{converted_count} file(s) converted successfully."
        if error_count > 0:
            final_message += f" {error_count} file(s) failed."
            messagebox.showerror("Conversion Errors", 
                                 f"{error_count} file(s) failed to convert:\n\n" + "\n".join(error_files) + 
                                 "\n\nSee console for detailed error messages if any.")
        else:
            messagebox.showinfo("Conversion Complete", final_message)
        
        self.status_bar_text.set(final_message)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageManipulatorApp(root)
    root.mainloop()