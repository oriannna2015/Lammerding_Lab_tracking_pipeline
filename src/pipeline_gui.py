"""
GUI Application for Lammerding Lab Cell Tracking Support

A graphical user interface for the cell tracking pipeline.
Author: Oriana Chen
"""
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import threading
import sys
import os
from pathlib import Path
import json

# Add src folder to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from folder_utils import scan_data_folder_structure
from channel_splitter import ChannelSplitter
from segmentation import Segmentator
from fluorescence_analyzer import FluorescenceAnalyzer
from subtrack_lineage_analysis import batch_analyze_all_locations
from tracking_output_relocator import TrackingOutputRelocator


class PipelineGUI:
    """GUI for the Integrated Cell Tracking Pipeline."""
    
    def __init__(self, root):
        """Initialize the GUI."""
        self.root = root
        self.root.title("Lammerding Lab - Cell Tracking Support")
        self.root.geometry("1000x700")
        
        # Configuration
        self.config = ConfigManager()
        self.locations = []
        self.current_step = 0
        self.processing = False
        
        # Setup GUI
        self._create_widgets()
        self._load_config_if_exists()
    
    def _create_widgets(self):
        """Create all GUI widgets."""
        # Header
        header_frame = ttk.Frame(self.root, padding="10")
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Label(header_frame, text="Lammerding Lab - Cell Tracking Support", 
                 font=('Arial', 16, 'bold')).pack()
        ttk.Label(header_frame, text="Integrated Processing Platform v2.0 | by Oriana Chen",
                 font=('Arial', 10)).pack()
        
        # Main content area with notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=5)
        
        # Tab 1: Configuration
        self.config_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.config_tab, text="⚙️ Configuration")
        self._create_config_tab()
        
        # Tab 2: Pipeline Execution
        self.pipeline_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.pipeline_tab, text="▶️ Pipeline")
        self._create_pipeline_tab()
        
        # Tab 3: Log
        self.log_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.log_tab, text="📋 Log")
        self._create_log_tab()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
    
    def _create_config_tab(self):
        """Create configuration tab."""
        # Input Data Folder
        row = 0
        ttk.Label(self.config_tab, text="Input Data Folder:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.input_folder_var = tk.StringVar()
        ttk.Entry(self.config_tab, textvariable=self.input_folder_var, width=60).grid(
            row=row, column=1, padx=5, pady=5)
        ttk.Button(self.config_tab, text="Browse...", 
                  command=self._browse_input_folder).grid(row=row, column=2, padx=5)
        
        # Working Directory
        row += 1
        ttk.Label(self.config_tab, text="Working Directory:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.working_dir_var = tk.StringVar()
        ttk.Entry(self.config_tab, textvariable=self.working_dir_var, width=60).grid(
            row=row, column=1, padx=5, pady=5)
        ttk.Button(self.config_tab, text="Browse...", 
                  command=self._browse_working_dir).grid(row=row, column=2, padx=5)
        ttk.Label(self.config_tab, text="(TrackMate outputs should be in: working_dir/OutputTracks)",
                 font=('Arial', 8), foreground='gray').grid(
            row=row+1, column=1, sticky=tk.W, padx=5)
        row += 1
        
        # StarDist Model
        row += 1
        ttk.Label(self.config_tab, text="StarDist Model Path:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.model_path_var = tk.StringVar()
        ttk.Entry(self.config_tab, textvariable=self.model_path_var, width=60).grid(
            row=row, column=1, padx=5, pady=5)
        ttk.Button(self.config_tab, text="Browse...", 
                  command=self._browse_model_path).grid(row=row, column=2, padx=5)
        
        # Channel Names
        row += 1
        ttk.Label(self.config_tab, text="Channel Names:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        channel_frame = ttk.Frame(self.config_tab)
        channel_frame.grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        self.channel_vars = []
        default_channels = ['Green', 'Phase', 'Red']
        for i, ch in enumerate(default_channels):
            var = tk.StringVar(value=ch)
            self.channel_vars.append(var)
            ttk.Entry(channel_frame, textvariable=var, width=15).grid(row=0, column=i, padx=2)
        
        # QC Parameters
        row += 1
        ttk.Separator(self.config_tab, orient='horizontal').grid(
            row=row, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        
        row += 1
        ttk.Label(self.config_tab, text="QC Parameters", 
                 font=('Arial', 10, 'bold')).grid(row=row, column=0, columnspan=3, sticky=tk.W)
        
        row += 1
        ttk.Label(self.config_tab, text="Max Splits Allowed:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.max_splits_var = tk.IntVar(value=3)
        ttk.Spinbox(self.config_tab, from_=0, to=10, textvariable=self.max_splits_var, 
                   width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        
        row += 1
        ttk.Label(self.config_tab, text="Min Track Duration:").grid(
            row=row, column=0, sticky=tk.W, pady=5)
        self.min_duration_var = tk.IntVar(value=20)
        ttk.Spinbox(self.config_tab, from_=1, to=100, textvariable=self.min_duration_var, 
                   width=10).grid(row=row, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(self.config_tab, text="frames").grid(row=row, column=1, sticky=tk.W, padx=80)
        
        # Buttons
        row += 1
        button_frame = ttk.Frame(self.config_tab)
        button_frame.grid(row=row, column=0, columnspan=3, pady=20)
        
        # First row: Save and Load buttons
        first_row = ttk.Frame(button_frame)
        first_row.pack(pady=5)
        ttk.Button(first_row, text="Save Config", 
                  command=self._save_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(first_row, text="Load Config", 
                  command=self._load_config).pack(side=tk.LEFT, padx=5)
        
        # Second row: Apply Config button
        second_row = ttk.Frame(button_frame)
        second_row.pack(pady=5)
        ttk.Button(second_row, text="Apply Config", 
                  command=self._validate_config).pack(padx=5)
    
    def _create_pipeline_tab(self):
        """Create pipeline execution tab."""
        # Info section
        info_frame = ttk.LabelFrame(self.pipeline_tab, text="Project Info", padding="10")
        info_frame.pack(fill=tk.X, pady=5)
        
        self.location_count_var = tk.StringVar(value="Please load the files first!")
        ttk.Label(info_frame, text="Detected Locations:").pack(side=tk.LEFT)
        self.location_count_label = ttk.Label(info_frame, textvariable=self.location_count_var, 
                 font=('Arial', 10, 'bold'), foreground='red')
        self.location_count_label.pack(side=tk.LEFT, padx=10)
        
        ttk.Button(info_frame, text="🔍 Scan Data Folder", 
                  command=self._scan_locations).pack(side=tk.RIGHT, padx=5)
        
        # Pipeline steps
        steps_frame = ttk.LabelFrame(self.pipeline_tab, text="Pipeline Steps", padding="10")
        steps_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create a canvas with scrollbar
        canvas = tk.Canvas(steps_frame, height=400)
        scrollbar = ttk.Scrollbar(steps_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Define pipeline steps
        self.steps = [
            ("1️⃣ Channel Splitting", "Automated", self._run_step1),
            ("2️⃣ Image Stabilization", "Script + Manual", self._run_step2),
            ("3️⃣ Cell Segmentation", "Automated", self._run_step3),
            ("4️⃣ TrackMate Tracking", "Manual", self._run_step4),
            ("4.5️⃣ Result Relocation", "Automated (Optional)", self._run_step4_5),
            ("5️⃣ Subtrack Analysis", "Automated", self._run_step5),
            ("6️⃣ Fluorescence Analysis", "Automated", self._run_step6),
        ]
        
        self.step_buttons = []
        self.step_status_vars = []
        
        for i, (name, method, func) in enumerate(self.steps):
            step_frame = ttk.Frame(scrollable_frame)
            step_frame.pack(fill=tk.X, pady=5, padx=5)
            
            # Step label
            ttk.Label(step_frame, text=name, font=('Arial', 10, 'bold')).pack(side=tk.LEFT)
            ttk.Label(step_frame, text=f"({method})", 
                     font=('Arial', 9), foreground='gray').pack(side=tk.LEFT, padx=5)
            
            # Status
            status_var = tk.StringVar(value="⏸️ Pending")
            self.step_status_vars.append(status_var)
            ttk.Label(step_frame, textvariable=status_var).pack(side=tk.RIGHT, padx=10)
            
            # Button - all steps enabled for flexible execution
            btn = ttk.Button(step_frame, text="▶️ Run", command=func)
            btn.pack(side=tk.RIGHT)
            self.step_buttons.append(btn)
        
        # Control buttons
        control_frame = ttk.Frame(self.pipeline_tab)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="▶️ Run All Steps", 
                  command=self._run_all_steps, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="⏹️ Stop", 
                  command=self._stop_processing).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="🔄 Reset", 
                  command=self._reset_pipeline).pack(side=tk.LEFT, padx=5)
    
    def _create_log_tab(self):
        """Create log tab."""
        self.log_text = scrolledtext.ScrolledText(self.log_tab, wrap=tk.WORD, 
                                                   height=30, width=100)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Button frame
        button_frame = ttk.Frame(self.log_tab)
        button_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(button_frame, text="Clear Log", 
                  command=lambda: self.log_text.delete(1.0, tk.END)).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Save Log", 
                  command=self._save_log).pack(side=tk.LEFT, padx=5)
    
    def log(self, message, level="INFO"):
        """Add message to log."""
        timestamp = ""
        prefix = ""
        if level == "INFO":
            prefix = "ℹ️"
        elif level == "SUCCESS":
            prefix = "✅"
        elif level == "ERROR":
            prefix = "❌"
        elif level == "WARNING":
            prefix = "⚠️"
        
        self.log_text.insert(tk.END, f"{prefix} {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def _browse_input_folder(self):
        """Browse for input folder."""
        folder = filedialog.askdirectory(title="Select Input Data Folder")
        if folder:
            self.input_folder_var.set(folder)
    
    def _browse_working_dir(self):
        """Browse for working directory."""
        folder = filedialog.askdirectory(title="Select Working Directory")
        if folder:
            self.working_dir_var.set(folder)
    
    def _browse_model_path(self):
        """Browse for StarDist model."""
        folder = filedialog.askdirectory(title="Select StarDist Model Folder")
        if folder:
            self.model_path_var.set(folder)
    
    def _save_config(self):
        """Save configuration to file."""
        try:
            self.config.set('input_data_folder', self.input_folder_var.get())
            self.config.set('working_directory', self.working_dir_var.get())
            self.config.set('stardist_model_path', self.model_path_var.get())
            self.config.set('channel_names', [var.get() for var in self.channel_vars])
            self.config.set('max_splits_allowed', self.max_splits_var.get())
            self.config.set('min_track_duration_frames', self.min_duration_var.get())
            
            # Ask for save location
            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="pipeline_config.json"
            )
            
            if file_path:
                self.config.save_config(file_path)
                self.log(f"Config saved to: {file_path}", "SUCCESS")
                messagebox.showinfo("Success", "Configuration saved!")
        except Exception as e:
            self.log(f"Failed to save config: {e}", "ERROR")
            messagebox.showerror("Error", f"Failed to save config: {e}")
    
    def _load_config(self):
        """Load configuration from file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                self.config.load_config(file_path)
                self._update_gui_from_config()
                self.log(f"Config loaded: {file_path}", "SUCCESS")
                messagebox.showinfo("Success", "Configuration loaded!")
            except Exception as e:
                self.log(f"Failed to load config: {e}", "ERROR")
                messagebox.showerror("Error", f"Failed to load config: {e}")
    
    def _load_config_if_exists(self):
        """Load config if default file exists."""
        default_path = Path("pipeline_config.json")
        if default_path.exists():
            try:
                self.config.load_config(str(default_path))
                self._update_gui_from_config()
                self.log("Loaded default configuration", "INFO")
            except:
                pass
    
    def _update_gui_from_config(self):
        """Update GUI fields from config."""
        self.input_folder_var.set(self.config.get('input_data_folder', ''))
        self.working_dir_var.set(self.config.get('working_directory', ''))
        self.model_path_var.set(self.config.get('stardist_model_path', ''))
        
        channels = self.config.get('channel_names', ['Green', 'Phase', 'Red'])
        for i, var in enumerate(self.channel_vars):
            if i < len(channels):
                var.set(channels[i])
        
        self.max_splits_var.set(self.config.get('max_splits_allowed', 3))
        self.min_duration_var.set(self.config.get('min_track_duration_frames', 20))
    
    def _validate_config(self):
        """Validate current configuration."""
        try:
            # Update config from GUI
            self.config.set('input_data_folder', self.input_folder_var.get())
            self.config.set('working_directory', self.working_dir_var.get())
            self.config.set('stardist_model_path', self.model_path_var.get())
            
            errors = []
            
            # Check paths
            if not self.config.get('input_data_folder'):
                errors.append("Input data folder not set")
            elif not os.path.exists(self.config.get('input_data_folder')):
                errors.append("Input data folder does not exist")
            
            if not self.config.get('working_directory'):
                errors.append("Working directory not set")
            
            model_path = self.config.get('stardist_model_path')
            if model_path and not os.path.exists(model_path):
                errors.append("StarDist model path does not exist")
            
            if errors:
                self.log("Validation failed:", "ERROR")
                for err in errors:
                    self.log(f"  - {err}", "ERROR")
                messagebox.showwarning("Validation Failed", "\n".join(errors))
            else:
                # Setup working directories
                self.config.setup_working_directories()
                self.log("Configuration validated successfully!", "SUCCESS")
                messagebox.showinfo("Success", "Configuration is valid!\nWorking directories created.")
                
        except Exception as e:
            self.log(f"Validation error: {e}", "ERROR")
            messagebox.showerror("Error", f"Validation error: {e}")
    
    def _scan_locations(self):
        """Scan data folder for locations."""
        def scan():
            try:
                self.log("Scanning data folder...", "INFO")
                input_folder = self.input_folder_var.get()
                
                if not input_folder or not os.path.exists(input_folder):
                    self.log("Invalid input folder", "ERROR")
                    return
                
                self.locations = scan_data_folder_structure(input_folder)
                
                if self.locations:
                    self.location_count_var.set(f"{len(self.locations)} locations")
                    self.location_count_label.config(foreground='green')
                    self.log(f"✓ Found {len(self.locations)} locations", "SUCCESS")
                    
                    # Show sample
                    self.log("Sample locations:", "INFO")
                    for i, loc in enumerate(self.locations[:5]):
                        self.log(f"  {i+1}. {loc['rep']}/{loc['timepoint']}/{loc['datatype']}/{loc['location']}", "INFO")
                    if len(self.locations) > 5:
                        self.log(f"  ... and {len(self.locations) - 5} more", "INFO")
                else:
                    self.location_count_var.set("0 locations")
                    self.location_count_label.config(foreground='orange')
                    self.log("No locations found", "WARNING")
                    
            except Exception as e:
                self.log(f"Scan failed: {e}", "ERROR")
        
        threading.Thread(target=scan, daemon=True).start()
    
    def _update_step_status(self, step_idx, status, message=""):
        """Update step status."""
        if status == "running":
            self.step_status_vars[step_idx].set("⏳ Running...")
        elif status == "success":
            self.step_status_vars[step_idx].set("✅ Complete")
        elif status == "error":
            self.step_status_vars[step_idx].set("❌ Failed")
        elif status == "manual":
            self.step_status_vars[step_idx].set("👉 Manual Action")
        
        if message:
            self.log(message, "SUCCESS" if status == "success" else "ERROR" if status == "error" else "INFO")
    
    def _enable_next_step(self, step_idx):
        """Enable next step button."""
        if step_idx + 1 < len(self.step_buttons):
            self.step_buttons[step_idx + 1].config(state='normal')
    
    def _run_step1(self):
        """Run step 1: Channel Splitting."""
        def run():
            try:
                self._update_step_status(0, "running", "[Step 1] Starting channel splitting...")
                
                # Update config
                self.config.set('input_data_folder', self.input_folder_var.get())
                self.config.set('channel_names', [var.get() for var in self.channel_vars])
                
                if not self.locations:
                    self.log("Please scan data folder first", "ERROR")
                    self._update_step_status(0, "error")
                    return
                
                channel_names = self.config.get_channel_names()
                splitter = ChannelSplitter(channel_names)
                
                # Redirect output
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    stats = splitter.batch_split(self.locations)
                
                output = f.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log(line, "INFO")
                
                if stats['success'] > 0:
                    self._update_step_status(0, "success", f"✓ Step 1 Complete: {stats['success']}/{stats['total']} successful")
                else:
                    self._update_step_status(0, "error", "Step 1 Failed")
                    
            except Exception as e:
                self.log(f"Step 1 Error: {e}", "ERROR")
                self._update_step_status(0, "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def _run_step2(self):
        """Run step 2: Generate stabilization macro."""
        try:
            self._update_step_status(1, "running", "[Step 2] Generating Image Stabilization script...")
            
            # Generate macro directly
            macro_path = self._generate_stabilization_macro()
            
            if macro_path:
                self.log(f"✓ Script generated: {macro_path}", "SUCCESS")
                self.log("", "INFO")
                self.log("📋 Please follow these steps:", "INFO")
                self.log("  1. Open Fiji/ImageJ", "INFO")
                self.log("  2. Plugins → Macros → Run...", "INFO")
                self.log(f"  3. Select file: {macro_path}", "INFO")
                self.log("  4. Wait for batch processing to complete", "INFO")
                self.log("  5. Click 'Verify' button below when done", "INFO")
                
                self._update_step_status(1, "manual")
                
                # Show verification dialog
                self.root.after(100, self._show_step2_verification_dialog)
            else:
                self._update_step_status(1, "error", "Failed to generate script")
                
        except Exception as e:
            self.log(f"Step 2 Error: {e}", "ERROR")
            self._update_step_status(1, "error")
    
    def _show_step2_verification_dialog(self):
        """Show dialog to verify step 2 completion."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Image Stabilization - Waiting for Manual Operation")
        dialog.geometry("500x300")
        
        ttk.Label(dialog, text="⏳ Waiting for ImageJ Processing", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        msg = """
Please run the generated macro script in Fiji/ImageJ.

After processing completes, click the 'Verify Results' button below.

The pipeline will automatically check if all stabilized files were generated.
        """
        ttk.Label(dialog, text=msg, justify=tk.LEFT).pack(pady=10, padx=20)
        
        def verify():
            verified = self._verify_stabilization()
            if verified['success'] == verified['total']:
                self.log(f"✓ Verification passed: {verified['success']}/{verified['total']} locations", "SUCCESS")
                self._update_step_status(1, "success", "Step 2 Complete")
                dialog.destroy()
                messagebox.showinfo("Success", f"Verification passed!\n{verified['success']}/{verified['total']} locations complete")
            else:
                self.log(f"⚠ Verification found issues: {verified['missing']}/{verified['total']} locations missing files", "WARNING")
                result = messagebox.askyesno("Verification Failed", 
                    f"{verified['missing']}/{verified['total']} locations are missing stabilized files.\n\nContinue anyway?")
                if result:
                    self._update_step_status(1, "success", "Step 2 Complete (partial)")
                    dialog.destroy()
        
        ttk.Button(dialog, text="✓ Verify Results", command=verify).pack(pady=10)
        ttk.Button(dialog, text="⏸️ Verify Later", command=dialog.destroy).pack()
    
    def _run_step3(self):
        """Run step 3: Segmentation."""
        def run():
            try:
                self._update_step_status(2, "running", "[Step 3] Starting cell segmentation...")
                
                model_path = self.model_path_var.get()
                if not model_path or not os.path.exists(model_path):
                    self.log("StarDist model path invalid", "ERROR")
                    self._update_step_status(2, "error")
                    return
                
                working_dir = self.config.get('working_directory')
                input_mask_folder = str(Path(working_dir) / "InputMask")
                
                # Use original locations (in-place processing)
                # No need to update paths as they already point to input data folder
                segmentator = Segmentator(model_path)
                
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    stats = segmentator.batch_segment(self.locations, input_mask_folder)
                
                output = f.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log(line, "INFO")
                
                if stats['success'] > 0:
                    self._update_step_status(2, "success", f"✓ Step 3 Complete: {stats['success']}/{stats['total']} successful")
                else:
                    self._update_step_status(2, "error", "Step 3 Failed")
                    
            except Exception as e:
                self.log(f"Step 3 Error: {e}", "ERROR")
                import traceback
                self.log(traceback.format_exc(), "ERROR")
                self._update_step_status(2, "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def _run_step4(self):
        """Run step 4: Verify TrackMate tracking."""
        try:
            self._update_step_status(3, "manual", "[Step 4] Waiting for TrackMate tracking...")
            
            self.log("", "INFO")
            self.log("📋 Please complete TrackMate tracking in Fiji", "INFO")
            self.log("  1. Open Fiji and load your segmented images", "INFO")
            self.log("  2. Run TrackMate and configure tracking parameters", "INFO")
            self.log("  3. Export tracking results to CSV files", "INFO")
            self.log("  4. Click 'Verify' button below when done", "INFO")
            self.log("", "INFO")
            
            # Show verification dialog
            self.root.after(100, self._show_step4_verification_dialog)
                
        except Exception as e:
            self.log(f"Step 4 Error: {e}", "ERROR")
            self._update_step_status(3, "error")
    
    def _show_step4_verification_dialog(self):
        """Show dialog to verify step 4 completion."""
        dialog = tk.Toplevel(self.root)
        dialog.title("TrackMate Tracking - Waiting for Manual Operation")
        dialog.geometry("500x300")
        
        ttk.Label(dialog, text="⏳ Waiting for TrackMate Processing", 
                 font=('Arial', 12, 'bold')).pack(pady=10)
        
        msg = """
Please complete TrackMate tracking in Fiji for all locations.

After all tracking is complete and CSV files are exported,
click the 'Verify Results' button below.

The pipeline will automatically check if all CSV files have been exported.
        """
        ttk.Label(dialog, text=msg, justify=tk.LEFT).pack(pady=10, padx=20)
        
        def verify():
            verified = self._verify_trackmate()
            if verified['success'] == verified['total']:
                self.log(f"✓ Verification passed: {verified['success']}/{verified['total']} locations", "SUCCESS")
                self._update_step_status(3, "success", "Step 4 Complete")
                dialog.destroy()
                messagebox.showinfo("Success", f"Verification passed!\n{verified['success']}/{verified['total']} locations complete")
            else:
                self.log(f"⚠ Verification found issues: {verified['missing']}/{verified['total']} locations missing data", "WARNING")
                result = messagebox.askyesno("Verification Failed", 
                    f"{verified['missing']}/{verified['total']} locations are missing tracking results.\n\nContinue anyway?")
                if result:
                    self._update_step_status(3, "success", "Step 4 Complete (partial)")
                    dialog.destroy()
        
        ttk.Button(dialog, text="✓ Verify Results", command=verify).pack(pady=10)
        ttk.Button(dialog, text="⏸️ Verify Later", command=dialog.destroy).pack()
    
    def _run_step4_5(self):
        """Run step 4.5: Relocate tracking outputs from working directory."""
        def run():
            try:
                # Get working directory and construct output tracks path
                working_dir = self.config.get('working_directory')
                if not working_dir:
                    result = messagebox.askyesno(
                        "Working Directory Not Set",
                        "Working directory is not configured.\n\n"
                        "This step relocates TrackMate outputs from working_dir/OutputTracks back to input data folders.\n\n"
                        "Skip this step?"
                    )
                    if result:
                        self.log("Step 4.5 skipped (working directory not set)", "INFO")
                        self._update_step_status(4, "success", "✓ Step 4.5 Skipped")
                    else:
                        self._update_step_status(4, "error", "Working directory not configured")
                    return
                
                output_tracks = Path(working_dir) / "OutputTracks"
                
                if not output_tracks.exists():
                    result = messagebox.askyesno(
                        "OutputTracks Folder Not Found",
                        f"OutputTracks folder not found at:\n{output_tracks}\n\n"
                        "This step is optional and only needed if TrackMate results were exported to OutputTracks.\n\n"
                        "Skip this step?"
                    )
                    if result:
                        self.log("Step 4.5 skipped (OutputTracks folder not found)", "INFO")
                        self._update_step_status(4, "success", "✓ Step 4.5 Skipped")
                    else:
                        self._update_step_status(4, "error", "OutputTracks folder not found")
                    return
                
                self._update_step_status(4, "running", "[Step 4.5] Relocating tracking outputs...")
                self.log("", "INFO")
                self.log(f"Source: {output_tracks}", "INFO")
                
                input_data_folder = self.config.get('input_data_folder')
                self.log(f"Target: {input_data_folder}", "INFO")
                self.log("", "INFO")
                
                import io
                from contextlib import redirect_stdout
                
                relocator = TrackingOutputRelocator(str(output_tracks), input_data_folder)
                
                f = io.StringIO()
                with redirect_stdout(f):
                    stats = relocator.relocate_all()
                
                output = f.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log(line, "INFO")
                
                if stats['moved'] > 0:
                    self._update_step_status(4, "success", 
                        f"✓ Step 4.5 Complete: {stats['moved']} files relocated to {stats['locations_updated']} locations")
                elif stats['total_files'] == 0:
                    self.log("No files found to relocate", "WARNING")
                    self._update_step_status(4, "success", "✓ Step 4.5 Complete (no files)")
                else:
                    self._update_step_status(4, "error", "Step 4.5 Failed")
                    
            except Exception as e:
                self.log(f"Step 4.5 Error: {e}", "ERROR")
                self._update_step_status(4, "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def _run_step5(self):
        """Run step 5: Subtrack Analysis."""
        def run():
            try:
                self._update_step_status(5, "running", "[Step 5] Starting subtrack analysis...")
                
                # Use input data folder where tracking results are located
                input_data_folder = self.config.get('input_data_folder')
                max_splits = self.max_splits_var.get()
                min_duration = self.min_duration_var.get()
                
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    results = batch_analyze_all_locations(
                        Path(input_data_folder),
                        max_splits=max_splits,
                        min_duration=min_duration
                    )
                
                output = f.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log(line, "INFO")
                
                success_count = sum(1 for v in results.values() if v)
                if success_count > 0:
                    self._update_step_status(5, "success", f"✓ Step 5 Complete: {success_count}/{len(results)} successful")
                else:
                    self._update_step_status(5, "error", "Step 5 Failed")
                    
            except Exception as e:
                self.log(f"Step 5 Error: {e}", "ERROR")
                self._update_step_status(5, "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def _run_step6(self):
        """Run step 6: Fluorescence Analysis."""
        def run():
            try:
                self._update_step_status(6, "running", "[Step 6] Starting fluorescence analysis...")
                
                working_dir = self.config.get('working_directory')
                input_mask_folder = str(Path(working_dir) / "InputMask")
                
                # Use original locations (in-place processing)
                # Locations already have correct 'path' field pointing to input data folder
                analyzer = FluorescenceAnalyzer(input_mask_folder)
                
                import io
                from contextlib import redirect_stdout
                
                f = io.StringIO()
                with redirect_stdout(f):
                    stats = analyzer.batch_analyze(self.locations)
                
                output = f.getvalue()
                for line in output.split('\n'):
                    if line.strip():
                        self.log(line, "INFO")
                
                if stats['success'] > 0:
                    self._update_step_status(6, "success", f"✓ Step 6 Complete: {stats['success']}/{stats['total']} successful")
                    self.log("", "INFO")
                    self.log("🎉 All steps complete!", "SUCCESS")
                else:
                    self._update_step_status(6, "error", "Step 6 Failed")
                    
            except Exception as e:
                self.log(f"Step 6 Error: {e}", "ERROR")
                self._update_step_status(6, "error")
        
        threading.Thread(target=run, daemon=True).start()
    
    def _run_all_steps(self):
        """Run all pipeline steps."""
        messagebox.showinfo("Info", "Auto-run will execute all steps sequentially.\nManual steps (Step 2 and 4) need manual verification after completion.")
        # This would need more complex orchestration
        self.log("Please execute each step manually", "INFO")
    
    def _stop_processing(self):
        """Stop processing."""
        self.processing = False
        self.log("Processing stopped", "WARNING")
    
    def _reset_pipeline(self):
        """Reset pipeline state."""
        result = messagebox.askyesno("Confirm", "Reset all step statuses?")
        if result:
            for var in self.step_status_vars:
                var.set("⏸️ Pending")
            # All steps remain enabled for flexible execution
            self.log("Pipeline reset", "INFO")
    
    def _save_log(self):
        """Save log to file."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile="pipeline_log.txt"
        )
        
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"Log saved to: {file_path}", "SUCCESS")
    
    def _generate_stabilization_macro(self):
        """Generate ImageJ macro for image stabilization."""
        try:
            working_dir = Path(self.config.get('working_directory'))
            input_folder = Path(self.config.get('input_data_folder'))
            
            # Read template
            template_path = Path(__file__).parent.parent / "three_channel_stabilize_bulk.txt"
            if not template_path.exists():
                # Try alternative location
                template_path = Path(__file__).parent / "three_channel_stabilize_bulk.txt"
            
            if not template_path.exists():
                self.log("Warning: Template file not found, generating basic macro", "WARNING")
                macro_content = self._generate_basic_stabilization_macro()
            else:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                
                # Extract unique reps, timepoints, and datatypes from locations
                reps = sorted(set([loc['rep'] for loc in self.locations]))
                timepoints = sorted(set([loc['timepoint'] for loc in self.locations]))
                datatypes = sorted(set([loc['datatype'] for loc in self.locations]))
                
                # Convert to ImageJ array format
                reps_array = ', '.join([f'"{r}"' for r in reps])
                times_array = ', '.join([f'"{t}"' for t in timepoints])
                types_array = ', '.join([f'"{d}"' for d in datatypes])
                
                # Replace root path (convert to forward slashes for ImageJ)
                root_path = str(input_folder).replace('\\', '/') + '/'
                
                # Replace placeholders in template
                macro_content = template_content.replace(
                    'root = "D:/Lammerding Lab/Final Tracking Data/";',
                    f'root = "{root_path}";'
                )
                macro_content = macro_content.replace(
                    'reps = newArray("Rep 1", "Rep 3", "Rep 4");',
                    f'reps = newArray({reps_array});'
                )
                macro_content = macro_content.replace(
                    'times = newArray("0-24h", "24-48h", "48-72h", "72-96h");',
                    f'times = newArray({times_array});'
                )
                macro_content = macro_content.replace(
                    'types = newArray("Dense", "5um", "10um");',
                    f'types = newArray({types_array});'
                )
            
            # Save macro to working directory
            output_path = working_dir / "image_stabilization_macro.ijm"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(macro_content)
            
            self.log(f"Generated macro with:", "INFO")
            self.log(f"  Reps: {reps if 'reps' in locals() else 'N/A'}", "INFO")
            self.log(f"  Timepoints: {timepoints if 'timepoints' in locals() else 'N/A'}", "INFO")
            self.log(f"  Datatypes: {datatypes if 'datatypes' in locals() else 'N/A'}", "INFO")
            
            return str(output_path)
            
        except Exception as e:
            self.log(f"Failed to generate stabilization macro: {e}", "ERROR")
            return None
    
    def _generate_basic_stabilization_macro(self):
        """Generate a basic stabilization macro if template is not available."""
        return """// Basic Image Stabilization Macro
print("Image stabilization macro generated by pipeline");
print("Please configure according to your data structure");
"""
    
    def _verify_stabilization(self):
        """Verify that stabilization has been completed for all locations."""
        try:
            # Check if locations have been scanned
            if not self.locations:
                self.log("Please scan data folder first!", "ERROR")
                messagebox.showerror("Error", "No locations loaded. Please click 'Scan Data Folder' first.")
                return {'total': 0, 'success': 0, 'missing': 0}
            
            input_folder = Path(self.config.get('input_data_folder'))
            stats = {'total': len(self.locations), 'success': 0, 'missing': 0}
            
            for location in self.locations:
                location_path = Path(location['path'])
                
                # Check for stabilized files (typically have '_stabilized' or similar suffix)
                # This is a basic check - adjust based on actual file naming
                stabilized_files = list(location_path.glob("*_cropped*.tif"))
                
                if stabilized_files:
                    stats['success'] += 1
                else:
                    stats['missing'] += 1
                    self.log(f"  Missing stabilized files: {location['name']}", "WARNING")
            
            return stats
            
        except Exception as e:
            self.log(f"Verification error: {e}", "ERROR")
            return {'total': 0, 'success': 0, 'missing': 0}
    
    def _verify_trackmate(self):
        """Verify that TrackMate tracking has been completed for all locations."""
        try:
            # Check if locations have been scanned
            if not self.locations:
                self.log("Please scan data folder first!", "ERROR")
                messagebox.showerror("Error", "No locations loaded. Please click 'Scan Data Folder' first.")
                return {'total': 0, 'success': 0, 'missing': 0}
            
            stats = {'total': len(self.locations), 'success': 0, 'missing': 0}
            
            for location in self.locations:
                location_path = Path(location['path'])
                tracking_result = location_path / "Tracking Result"
                
                if not tracking_result.exists():
                    stats['missing'] += 1
                    self.log(f"  Missing Tracking Result folder: {location['name']}", "WARNING")
                    continue
                
                # Check for required CSV files
                spots_files = list(tracking_result.glob("*-spots.csv")) or list(tracking_result.glob("*-all-spots.csv"))
                edges_files = list(tracking_result.glob("*-edges.csv"))
                tracks_files = list(tracking_result.glob("*-tracks.csv"))
                
                if spots_files and edges_files and tracks_files:
                    stats['success'] += 1
                else:
                    stats['missing'] += 1
                    missing = []
                    if not spots_files:
                        missing.append("spots.csv")
                    if not edges_files:
                        missing.append("edges.csv")
                    if not tracks_files:
                        missing.append("tracks.csv")
                    self.log(f"  Missing files in {location['name']}: {', '.join(missing)}", "WARNING")
            
            return stats
            
        except Exception as e:
            self.log(f"Verification error: {e}", "ERROR")
            return {'total': 0, 'success': 0, 'missing': 0}


def main():
    """Main entry point."""
    root = tk.Tk()
    app = PipelineGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
