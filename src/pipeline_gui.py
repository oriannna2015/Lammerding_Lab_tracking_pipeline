"""
GUI Application for Lammerding Lab Cell Tracking Support (Web Edition)

A modern graphical user interface for the cell tracking pipeline.
Serves HTML UI via a local web server and opens in the system browser.
Author: Oriana Chen
"""
import threading
import sys
import os
import json
import io
import time
import traceback
import webbrowser
import socket
from pathlib import Path
from contextlib import redirect_stdout

from bottle import Bottle, request, response, static_file, template

# Add src folder to path
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from folder_utils import scan_data_folder_structure
from channel_splitter import ChannelSplitter
from segmentation import Segmentator
from fluorescence_analyzer import FluorescenceAnalyzer
from subtrack_lineage_analysis import batch_analyze_all_locations
from tracking_output_relocator import TrackingOutputRelocator


class PipelineServer:
    """Local web server for the cell tracking pipeline GUI."""

    def __init__(self):
        self.app = Bottle()
        self.config = ConfigManager()
        self.locations = []
        self.processing = False
        self.log_entries = []

        self._setup_routes()

    def _setup_routes(self):
        """Register all routes."""
        self.app.route('/', 'GET', self._index)
        self.app.route('/api/browse', 'POST', self._api_browse)
        self.app.route('/api/config/default', 'GET', self._api_get_default_config)
        self.app.route('/api/config/save', 'POST', self._api_save_config)
        self.app.route('/api/config/load', 'POST', self._api_load_config)
        self.app.route('/api/config/apply', 'POST', self._api_apply_config)
        self.app.route('/api/scan', 'POST', self._api_scan)
        self.app.route('/api/step/run', 'POST', self._api_run_step)
        self.app.route('/api/step/verify', 'POST', self._api_verify_step)
        self.app.route('/api/stop', 'POST', self._api_stop)
        self.app.route('/api/log', 'GET', self._api_get_log)
        self.app.route('/api/log/save', 'POST', self._api_save_log)
        self.app.route('/api/documentation', 'POST', self._api_open_documentation)
        self.app.route('/api/shutdown', 'POST', self._api_shutdown)

    def _json_response(self, data):
        """Return JSON response."""
        response.content_type = 'application/json'
        return json.dumps(data)

    def _add_log(self, message, level="info"):
        """Add a log entry."""
        entry = {
            'time': time.strftime('%H:%M:%S'),
            'message': message,
            'level': level
        }
        self.log_entries.append(entry)

    # ==================== ROUTES ====================

    def _index(self):
        """Serve the main HTML page."""
        template_path = Path(__file__).parent / "templates" / "index.html"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()

    def _api_browse(self):
        """Handle browse folder request - returns instruction for tkinter dialog."""
        import tkinter as tk
        from tkinter import filedialog

        target = request.json.get('target', '')

        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        folder = filedialog.askdirectory(
            title=f"Select folder",
            parent=root
        )

        root.destroy()

        if folder:
            return self._json_response({'success': True, 'path': folder})
        return self._json_response({'success': False})

    def _api_get_default_config(self):
        """Get default configuration."""
        default_path = Path(__file__).parent.parent / "pipeline_config.json"
        if default_path.exists():
            try:
                self.config.load_config(str(default_path))
            except Exception:
                pass
        return self._json_response(self.config.config)

    def _api_save_config(self):
        """Save configuration to file."""
        import tkinter as tk
        from tkinter import filedialog

        try:
            config_data = request.json
            for key, value in config_data.items():
                self.config.set(key, value)

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                initialfile="pipeline_config.json",
                parent=root
            )

            root.destroy()

            if file_path:
                self.config.save_config(file_path)
                self._add_log(f"Config saved to: {file_path}", "success")
                return self._json_response({'success': True, 'path': file_path})
            return self._json_response({'success': False, 'error': 'Cancelled'})
        except Exception as e:
            return self._json_response({'success': False, 'error': str(e)})

    def _api_load_config(self):
        """Load configuration from file."""
        import tkinter as tk
        from tkinter import filedialog

        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            file_path = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                parent=root
            )

            root.destroy()

            if file_path:
                self.config.load_config(file_path)
                self._add_log(f"Config loaded from: {file_path}", "success")
                return self._json_response({'success': True, 'config': self.config.config})
            return self._json_response({'success': False, 'error': None})
        except Exception as e:
            return self._json_response({'success': False, 'error': str(e)})

    def _api_apply_config(self):
        """Validate and apply configuration."""
        try:
            config_data = request.json
            for key, value in config_data.items():
                self.config.set(key, value)

            errors = []
            input_folder = self.config.get('input_data_folder')
            working_dir = self.config.get('working_directory')
            model_path = self.config.get('stardist_model_path')

            if not input_folder:
                errors.append("Input data folder not set")
            elif not os.path.exists(input_folder):
                errors.append("Input data folder does not exist")

            if not working_dir:
                errors.append("Working directory not set")

            if model_path and not os.path.exists(model_path):
                errors.append("StarDist model path does not exist")

            if errors:
                return self._json_response({'success': False, 'errors': errors})

            self.config.setup_working_directories()

            # Save as default
            default_path = Path(__file__).parent.parent / "pipeline_config.json"
            self.config.save_config(str(default_path))

            self._add_log("Configuration validated and applied", "success")
            return self._json_response({
                'success': True,
                'message': 'All paths validated. Working directories created.'
            })
        except Exception as e:
            return self._json_response({'success': False, 'errors': [str(e)]})

    def _api_scan(self):
        """Scan data folder for locations."""
        try:
            input_folder = self.config.get('input_data_folder')
            if not input_folder or not os.path.exists(input_folder):
                return self._json_response({
                    'success': False,
                    'error': 'Invalid input folder. Please apply configuration first.'
                })

            self.locations = scan_data_folder_structure(input_folder)

            samples = []
            if self.locations:
                for loc in self.locations[:5]:
                    samples.append(f"{loc['rep']}/{loc['timepoint']}/{loc['datatype']}/{loc['location']}")
                if len(self.locations) > 5:
                    samples.append(f"... and {len(self.locations) - 5} more")

            self._add_log(f"Scan complete: {len(self.locations)} locations found", "success")
            return self._json_response({
                'success': True,
                'count': len(self.locations),
                'samples': samples
            })
        except Exception as e:
            return self._json_response({'success': False, 'error': str(e)})

    def _api_run_step(self):
        """Run a pipeline step."""
        index = request.json.get('index', -1)
        try:
            if index == 0:
                result = self._run_step_channel_splitting()
            elif index == 1:
                result = self._run_step_stabilization()
            elif index == 2:
                result = self._run_step_segmentation()
            elif index == 3:
                result = self._run_step_tracking()
            elif index == 4:
                result = self._run_step_relocation()
            elif index == 5:
                result = self._run_step_subtrack()
            elif index == 6:
                result = self._run_step_fluorescence()
            else:
                result = {'status': 'error', 'message': 'Unknown step'}
            return self._json_response(result)
        except Exception as e:
            return self._json_response({'status': 'error', 'message': str(e)})

    def _api_verify_step(self):
        """Verify a manual step."""
        index = request.json.get('index', -1)
        try:
            if index == 1:
                result = self._verify_stabilization()
            elif index == 3:
                result = self._verify_trackmate()
            else:
                result = {'success': True, 'message': 'Verified'}
            return self._json_response(result)
        except Exception as e:
            return self._json_response({'success': False, 'message': str(e)})

    def _api_stop(self):
        """Stop processing."""
        self.processing = False
        self._add_log("Processing stop requested", "warning")
        return self._json_response({'success': True})

    def _api_get_log(self):
        """Get all log entries."""
        return self._json_response(self.log_entries)

    def _api_save_log(self):
        """Save log to file."""
        import tkinter as tk
        from tkinter import filedialog

        try:
            text = request.json.get('text', '')

            root = tk.Tk()
            root.withdraw()
            root.attributes('-topmost', True)

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialfile="pipeline_log.txt",
                parent=root
            )

            root.destroy()

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                return self._json_response({'success': True, 'path': file_path})
            return self._json_response({'success': False})
        except Exception as e:
            return self._json_response({'success': False, 'error': str(e)})

    def _api_open_documentation(self):
        """Open documentation."""
        doc_path = Path(__file__).parent.parent / "DATA_DOCUMENTATION.md"
        if doc_path.exists():
            os.startfile(str(doc_path))
        return self._json_response({'success': True})

    def _api_shutdown(self):
        """Shutdown the server."""
        self._add_log("Server shutting down...", "info")

        def shutdown():
            time.sleep(0.5)
            os._exit(0)

        threading.Thread(target=shutdown, daemon=True).start()
        return self._json_response({'success': True})

    # ==================== STEP IMPLEMENTATIONS ====================

    def _run_step_channel_splitting(self):
        """Step 1: Channel Splitting."""
        if not self.locations:
            return {'status': 'error', 'message': 'Please scan data folder first'}

        try:
            channel_names = self.config.get('channel_names', ['Green', 'Phase', 'Red'])
            splitter = ChannelSplitter(channel_names)

            f = io.StringIO()
            with redirect_stdout(f):
                stats = splitter.batch_split(self.locations)

            output = f.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self._add_log(line, "info")

            if stats['success'] > 0:
                msg = f"{stats['success']}/{stats['total']} locations processed"
                self._add_log(f"Step 1 Complete: {msg}", "success")
                return {'status': 'success', 'message': msg}
            else:
                return {'status': 'error', 'message': 'No locations processed successfully'}
        except Exception as e:
            self._add_log(f"Step 1 Error: {traceback.format_exc()}", "error")
            return {'status': 'error', 'message': str(e)}

    def _run_step_stabilization(self):
        """Step 2: Generate stabilization macro."""
        try:
            macro_path = self._generate_stabilization_macro()
            if macro_path:
                self._add_log(f"Script generated: {macro_path}", "success")
                self._add_log("Please run in Fiji: Plugins > Macros > Run...", "info")
                return {
                    'status': 'manual',
                    'message': f'Macro generated at: {macro_path}. Run in Fiji then verify.'
                }
            else:
                return {'status': 'error', 'message': 'Failed to generate stabilization script'}
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def _run_step_segmentation(self):
        """Step 3: Cell Segmentation."""
        if not self.locations:
            return {'status': 'error', 'message': 'Please scan data folder first'}

        try:
            model_path = self.config.get('stardist_model_path')
            if not model_path or not os.path.exists(model_path):
                return {'status': 'error', 'message': 'StarDist model path invalid'}

            working_dir = self.config.get('working_directory')
            input_mask_folder = str(Path(working_dir) / "InputMask")

            segmentator = Segmentator(model_path)

            f = io.StringIO()
            with redirect_stdout(f):
                stats = segmentator.batch_segment(self.locations, input_mask_folder)

            output = f.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self._add_log(line, "info")

            if stats['success'] > 0:
                msg = f"{stats['success']}/{stats['total']} locations segmented"
                self._add_log(f"Step 3 Complete: {msg}", "success")
                return {'status': 'success', 'message': msg}
            else:
                return {'status': 'error', 'message': 'Segmentation failed'}
        except Exception as e:
            self._add_log(f"Step 3 Error: {traceback.format_exc()}", "error")
            return {'status': 'error', 'message': str(e)}

    def _run_step_tracking(self):
        """Step 4: TrackMate Tracking (Manual)."""
        self._add_log("Please complete TrackMate tracking in Fiji", "info")
        self._add_log("  1. Open Fiji and load segmented images", "info")
        self._add_log("  2. Run TrackMate with your parameters", "info")
        self._add_log("  3. Export results to CSV", "info")
        self._add_log("  4. Click Verify when done", "info")
        return {'status': 'manual', 'message': 'Complete TrackMate tracking in Fiji, then verify.'}

    def _run_step_relocation(self):
        """Step 4.5: Result Relocation."""
        try:
            working_dir = self.config.get('working_directory')
            if not working_dir:
                self._add_log("Working directory not set - skipping", "warning")
                return {'status': 'success', 'message': 'Skipped (no working directory)'}

            output_tracks = Path(working_dir) / "OutputTracks"
            if not output_tracks.exists():
                self._add_log("OutputTracks folder not found - skipping", "warning")
                return {'status': 'success', 'message': 'Skipped (no OutputTracks folder)'}

            input_data_folder = self.config.get('input_data_folder')
            relocator = TrackingOutputRelocator(str(output_tracks), input_data_folder)

            f = io.StringIO()
            with redirect_stdout(f):
                stats = relocator.relocate_all()

            output = f.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self._add_log(line, "info")

            if stats['moved'] > 0:
                msg = f"{stats['moved']} files relocated"
                self._add_log(f"Step 4.5 Complete: {msg}", "success")
                return {'status': 'success', 'message': msg}
            else:
                return {'status': 'success', 'message': 'No files to relocate'}
        except Exception as e:
            self._add_log(f"Step 4.5 Error: {traceback.format_exc()}", "error")
            return {'status': 'error', 'message': str(e)}

    def _run_step_subtrack(self):
        """Step 5: Subtrack Analysis."""
        try:
            input_data_folder = self.config.get('input_data_folder')
            max_splits = self.config.get('max_splits_allowed', 3)
            min_duration = self.config.get('min_track_duration_frames', 20)

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
                    self._add_log(line, "info")

            success_count = sum(1 for v in results.values() if v)
            if success_count > 0:
                msg = f"{success_count}/{len(results)} locations analyzed"
                self._add_log(f"Step 5 Complete: {msg}", "success")
                return {'status': 'success', 'message': msg}
            else:
                return {'status': 'error', 'message': 'Subtrack analysis failed'}
        except Exception as e:
            self._add_log(f"Step 5 Error: {traceback.format_exc()}", "error")
            return {'status': 'error', 'message': str(e)}

    def _run_step_fluorescence(self):
        """Step 6: Fluorescence Analysis."""
        if not self.locations:
            return {'status': 'error', 'message': 'Please scan data folder first'}

        try:
            working_dir = self.config.get('working_directory')
            input_mask_folder = str(Path(working_dir) / "InputMask")

            analyzer = FluorescenceAnalyzer(input_mask_folder)

            f = io.StringIO()
            with redirect_stdout(f):
                stats = analyzer.batch_analyze(self.locations)

            output = f.getvalue()
            for line in output.split('\n'):
                if line.strip():
                    self._add_log(line, "info")

            if stats['success'] > 0:
                msg = f"{stats['success']}/{stats['total']} locations analyzed"
                self._add_log(f"Step 6 Complete: {msg}", "success")
                return {'status': 'success', 'message': msg}
            else:
                return {'status': 'error', 'message': 'Fluorescence analysis failed'}
        except Exception as e:
            self._add_log(f"Step 6 Error: {traceback.format_exc()}", "error")
            return {'status': 'error', 'message': str(e)}

    # ==================== VERIFICATION ====================

    def _verify_stabilization(self):
        """Verify stabilization results."""
        if not self.locations:
            return {'success': False, 'message': 'No locations loaded'}

        stats = {'total': len(self.locations), 'success': 0, 'missing': 0}

        for location in self.locations:
            location_path = Path(location['path'])
            stabilized_files = list(location_path.glob("*_cropped*.tif"))
            if stabilized_files:
                stats['success'] += 1
            else:
                stats['missing'] += 1

        if stats['success'] == stats['total']:
            return {'success': True, 'message': f"{stats['success']}/{stats['total']} locations verified"}
        else:
            msg = f"{stats['success']}/{stats['total']} verified, {stats['missing']} missing"
            return {'success': False, 'message': msg, 'continue_anyway': True}

    def _verify_trackmate(self):
        """Verify TrackMate results."""
        if not self.locations:
            return {'success': False, 'message': 'No locations loaded'}

        stats = {'total': len(self.locations), 'success': 0, 'missing': 0}

        for location in self.locations:
            location_path = Path(location['path'])
            tracking_result = location_path / "Tracking Result"

            if not tracking_result.exists():
                stats['missing'] += 1
                continue

            spots = list(tracking_result.glob("*-spots.csv")) or list(tracking_result.glob("*-all-spots.csv"))
            edges = list(tracking_result.glob("*-edges.csv"))
            tracks = list(tracking_result.glob("*-tracks.csv"))

            if spots and edges and tracks:
                stats['success'] += 1
            else:
                stats['missing'] += 1

        if stats['success'] == stats['total']:
            return {'success': True, 'message': f"{stats['success']}/{stats['total']} locations verified"}
        else:
            msg = f"{stats['success']}/{stats['total']} verified, {stats['missing']} missing"
            return {'success': False, 'message': msg, 'continue_anyway': True}

    # ==================== UTILITY ====================

    def _generate_stabilization_macro(self):
        """Generate ImageJ macro for image stabilization."""
        try:
            working_dir = Path(self.config.get('working_directory'))
            input_folder = Path(self.config.get('input_data_folder'))

            template_path = Path(__file__).parent / "three_channel_stabilize_bulk.txt"
            if not template_path.exists():
                template_path = Path(__file__).parent.parent / "three_channel_stabilize_bulk.txt"

            if not template_path.exists():
                macro_content = '// Basic Image Stabilization Macro\nprint("Please configure manually");\n'
            else:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()

                reps = sorted(set([loc['rep'] for loc in self.locations]))
                timepoints = sorted(set([loc['timepoint'] for loc in self.locations]))
                datatypes = sorted(set([loc['datatype'] for loc in self.locations]))

                reps_array = ', '.join([f'"{r}"' for r in reps])
                times_array = ', '.join([f'"{t}"' for t in timepoints])
                types_array = ', '.join([f'"{d}"' for d in datatypes])

                root_path = str(input_folder).replace('\\', '/') + '/'

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

            output_path = working_dir / "image_stabilization_macro.ijm"
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(macro_content)

            return str(output_path)
        except Exception as e:
            self._add_log(f"Failed to generate macro: {e}", "error")
            return None

    def find_free_port(self):
        """Find a free port on localhost."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', 0))
            return s.getsockname()[1]

    def run(self):
        """Start the server and open browser."""
        port = self.find_free_port()
        url = f'http://127.0.0.1:{port}'

        self._add_log("CellTracker Pro initialized. Ready for configuration.", "info")

        # Open browser after a short delay
        def open_browser():
            time.sleep(1.0)
            webbrowser.open(url)

        threading.Thread(target=open_browser, daemon=True).start()

        print(f"\n{'='*50}")
        print(f"  CellTracker Pro - Pipeline Studio")
        print(f"  Running at: {url}")
        print(f"  Press Ctrl+C to quit")
        print(f"{'='*50}\n")

        self.app.run(host='127.0.0.1', port=port, quiet=True)


def main():
    """Main entry point."""
    server = PipelineServer()
    server.run()


if __name__ == "__main__":
    main()
