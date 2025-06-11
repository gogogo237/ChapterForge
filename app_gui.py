import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from file_processor import FileProcessor
from f_mover import FileMoverLogic # Added FileMoverLogic import

DEFAULT_SPLIT_STRING = "=======----JGFLKG==57483==="
DEFAULT_DUPLICATE_APPEND_TEXT = "Split the above text into seperate sentences. And append the Chinese translation of each sentence after each English sentence. Each English and Chinese sentence should be put into separate line. just give me the answer directly, no other response phrase."
DEFAULT_CHAPTER_SUFFIX = "orig"

class ChapterSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chapter Splitter Pro")
        self.root.geometry("700x750") 

        self.file_processor = FileProcessor(log_callback=self.log_message)
        self.file_mover_logic = FileMoverLogic() # Instantiate FileMoverLogic
        self.chapter_file_paths = []

        # --- UI Variables ---
        # For Chapter Splitter Tab
        self.input_filepath_var = tk.StringVar()
        self.split_method_var = tk.StringVar(value="string")
        self.split_string_var = tk.StringVar(value=DEFAULT_SPLIT_STRING)
        self.split_regex_var = tk.StringVar()
        self.start_number_var = tk.StringVar(value="1")
        self.chapter_suffix_var = tk.StringVar(value=DEFAULT_CHAPTER_SUFFIX)
        # self.duplicate_append_text_var is removed, ScrolledText will be used directly
        self.empty_file_suffix_var = tk.StringVar(value="bi")

        # For File Mover Tab
        self.source_folder_fm_var = tk.StringVar()
        self.dest_folder_fm_var = tk.StringVar()
        
        self.initial_source_files_full_paths_fm = [] # Loaded from disk, sorted
        self.current_source_files_full_paths_fm = [] # Reflects listbox order, used for moving
        
        self.initial_dest_subfolders_full_paths_fm = [] # Loaded from disk, sorted
        self.current_dest_subfolders_full_paths_fm = [] # Reflects listbox order (though not reordered by user now)

        self.drag_start_index_fm = None # For drag-and-drop

        # --- Main UI Setup with Tabs ---
        self.notebook = ttk.Notebook(root)
        
        # Tab 1: Chapter Splitter
        self.splitter_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.splitter_tab_frame, text='Chapter Splitter')
        self._init_splitter_tab(self.splitter_tab_frame) # Encapsulate splitter UI

        # Tab 2: File Mover
        self.fm_tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.fm_tab_frame, text='File Mover')
        self._init_fm_tab(self.fm_tab_frame) # Initialize File Mover tab UI

        self.notebook.pack(expand=True, fill='both')
        
        self.toggle_split_input() # Initial state for splitter tab

    def _init_splitter_tab(self, tab_frame):
        # All frames previously in main_frame are now children of tab_frame
        input_frame = ttk.LabelFrame(tab_frame, text="Input File", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        ttk.Label(input_frame, text="Select TXT File:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.input_file_entry = ttk.Entry(input_frame, textvariable=self.input_filepath_var, width=60, state="readonly")
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.browse_button = ttk.Button(input_frame, text="Browse...", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)

        split_options_frame = ttk.LabelFrame(tab_frame, text="Splitting Options", padding="10")
        split_options_frame.pack(fill=tk.X, pady=5)
        self.string_radio = ttk.Radiobutton(split_options_frame, text="Split by String:", variable=self.split_method_var, value="string", command=self.toggle_split_input)
        self.string_radio.grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.split_string_entry = ttk.Entry(split_options_frame, textvariable=self.split_string_var, width=50)
        self.split_string_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.regex_radio = ttk.Radiobutton(split_options_frame, text="Split by Regex:", variable=self.split_method_var, value="regex", command=self.toggle_split_input)
        self.regex_radio.grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.split_regex_entry = ttk.Entry(split_options_frame, textvariable=self.split_regex_var, width=50, state="disabled")
        self.split_regex_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        split_options_frame.columnconfigure(1, weight=1)

        naming_frame = ttk.LabelFrame(tab_frame, text="Chapter Naming", padding="10")
        naming_frame.pack(fill=tk.X, pady=5)
        ttk.Label(naming_frame, text="Start Numbering From:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_number_entry = ttk.Entry(naming_frame, textvariable=self.start_number_var, width=10)
        self.start_number_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(naming_frame, text="Chapter Filename Suffix:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.chapter_suffix_entry = ttk.Entry(naming_frame, textvariable=self.chapter_suffix_var, width=20)
        self.chapter_suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        action_frame = ttk.Frame(tab_frame, padding="5") # Changed parent to tab_frame
        action_frame.pack(fill=tk.X, pady=10)
        self.split_button = ttk.Button(action_frame, text="Split File", command=self.perform_split)
        self.split_button.pack(side=tk.LEFT, padx=5)
        
        duplication_frame = ttk.LabelFrame(tab_frame, text="Duplication & Modification (after splitting)", padding="10") # Changed parent
        duplication_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duplication_frame, text="Text to add after ```:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW)
        self.duplicate_append_text_area = scrolledtext.ScrolledText(duplication_frame, wrap=tk.WORD, height=5, width=50)
        self.duplicate_append_text_area.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.duplicate_append_text_area.insert(tk.END, DEFAULT_DUPLICATE_APPEND_TEXT) 

        ttk.Label(duplication_frame, text="Suffix for empty file names (e.g., 'notes'):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.empty_file_suffix_entry = ttk.Entry(duplication_frame, textvariable=self.empty_file_suffix_var, width=50)
        self.empty_file_suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        duplication_frame.columnconfigure(1, weight=1)

        self.duplicate_button = ttk.Button(action_frame, text="Duplicate & Modify Chapters", command=self.perform_duplication, state="disabled")
        self.duplicate_button.pack(side=tk.LEFT, padx=5)

        # Log area common to both? Or per tab? For now, keep it as part of splitter tab for simplicity of diff.
        # A shared log could be outside the notebook.
        log_frame = ttk.LabelFrame(tab_frame, text="Log", padding="10") # Changed parent
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, width=80)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')

    def _init_fm_tab(self, tab_frame):
        # Source Folder Selection
        source_frame_fm = ttk.LabelFrame(tab_frame, text="Source Folder (Contains files to move)", padding="10")
        source_frame_fm.pack(fill=tk.X, pady=5)
        ttk.Label(source_frame_fm, text="Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.source_folder_entry_fm = ttk.Entry(source_frame_fm, textvariable=self.source_folder_fm_var, width=60, state="readonly")
        self.source_folder_entry_fm.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.browse_source_fm_button = ttk.Button(source_frame_fm, text="Browse...", command=self._browse_source_folder_fm)
        self.browse_source_fm_button.grid(row=0, column=2, padx=5, pady=5)
        source_frame_fm.columnconfigure(1, weight=1)

        # Destination Folder Selection
        dest_frame_fm = ttk.LabelFrame(tab_frame, text="Main Destination Folder (Contains subfolders)", padding="10")
        dest_frame_fm.pack(fill=tk.X, pady=5)
        ttk.Label(dest_frame_fm, text="Folder:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.dest_folder_entry_fm = ttk.Entry(dest_frame_fm, textvariable=self.dest_folder_fm_var, width=60, state="readonly")
        self.dest_folder_entry_fm.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.browse_dest_fm_button = ttk.Button(dest_frame_fm, text="Browse...", command=self._browse_dest_folder_fm)
        self.browse_dest_fm_button.grid(row=0, column=2, padx=5, pady=5)
        dest_frame_fm.columnconfigure(1, weight=1)

        # Listbox Frame
        listbox_main_frame_fm = ttk.Frame(tab_frame, padding="10")
        listbox_main_frame_fm.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Source Files Listbox
        source_list_frame_fm = ttk.LabelFrame(listbox_main_frame_fm, text="Source Files (Drag to Reorder)", padding="5")
        source_list_frame_fm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.source_files_listbox_fm = tk.Listbox(source_list_frame_fm, height=15, exportselection=False)
        self.source_files_listbox_fm.pack(fill=tk.BOTH, expand=True)
        self.source_files_listbox_fm.bind("<ButtonPress-1>", self._on_source_lb_drag_start_fm)
        self.source_files_listbox_fm.bind("<B1-Motion>", self._on_source_lb_drag_motion_fm)
        self.source_files_listbox_fm.bind("<ButtonRelease-1>", self._on_source_lb_drag_release_fm)

        # Destination Folders Listbox
        dest_list_frame_fm = ttk.LabelFrame(listbox_main_frame_fm, text="Destination Subfolders (Sorted - Target Order)", padding="5")
        dest_list_frame_fm.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        self.dest_folders_listbox_fm = tk.Listbox(dest_list_frame_fm, height=15)
        self.dest_folders_listbox_fm.pack(fill=tk.BOTH, expand=True)

        # Action/Status Frame
        action_status_frame_fm = ttk.Frame(tab_frame, padding="5")
        action_status_frame_fm.pack(fill=tk.X, pady=5)

        self.move_button_fm = ttk.Button(action_status_frame_fm, text="Move Files", command=self._execute_move_files_fm, state="disabled")
        self.move_button_fm.pack(side=tk.LEFT, padx=10)
        
        self.status_label_fm_var = tk.StringVar(value="Status: Select source and destination folders.")
        self.status_label_fm = ttk.Label(action_status_frame_fm, textvariable=self.status_label_fm_var, relief=tk.SUNKEN, padding=5)
        self.status_label_fm.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)


    def log_message(self, message):
        # Ensure log_area is available before trying to use it.
        # This might be called by FileProcessor before UI fully initialized if not careful.
        if hasattr(self, 'log_area') and self.log_area:
            self.log_area.configure(state='normal')
            self.log_area.insert(tk.END, message + "\n")
            self.log_area.configure(state='disabled')
            self.log_area.see(tk.END)
        else: # Fallback if log_area isn't ready (e.g. during early init)
            print(f"LOG: {message}")


    # --- Methods for Chapter Splitter Tab ---
    def browse_file(self):
        filepath = filedialog.askopenfilename(
            title="Select Input TXT File",
            filetypes=(("Text files", "*.txt"), ("All files", "*.*"))
        )
        if filepath:
            self.input_filepath_var.set(filepath)
            self.log_message(f"Selected input file: {filepath}")
            self.duplicate_button.config(state="disabled")
            self.chapter_file_paths = []

    def toggle_split_input(self):
        if self.split_method_var.get() == "string":
            self.split_string_entry.config(state="normal")
            self.split_regex_entry.config(state="disabled")
        else:
            self.split_string_entry.config(state="disabled")
            self.split_regex_entry.config(state="normal")

    def validate_split_inputs(self):
        if not self.input_filepath_var.get():
            messagebox.showerror("Error", "Please select an input TXT file.")
            return False
        if not os.path.exists(self.input_filepath_var.get()):
            messagebox.showerror("Error", "Input file does not exist.")
            return False
        
        try:
            int(self.start_number_var.get())
        except ValueError:
            messagebox.showerror("Error", "Start number must be an integer.")
            return False

        split_method = self.split_method_var.get()
        if split_method == "string" and not self.split_string_var.get():
            messagebox.showerror("Error", "Split string cannot be empty.")
            return False
        if split_method == "regex" and not self.split_regex_var.get():
            messagebox.showerror("Error", "Split regex cannot be empty.")
            return False
        return True

    def perform_split(self):
        if not self.validate_split_inputs():
            return

        filepath = self.input_filepath_var.get()
        split_method = self.split_method_var.get()
        split_value = self.split_string_var.get() if split_method == "string" else self.split_regex_var.get()
        start_number = int(self.start_number_var.get())
        chapter_suffix = self.chapter_suffix_var.get()

        self.log_message(f"Starting split process for: {filepath}")
        self.log_message(f"Mode: {split_method}, Value: '{split_value}', Start #: {start_number}, Suffix: '{chapter_suffix}'")
        
        self.split_button.config(state="disabled")
        self.duplicate_button.config(state="disabled")
        self.root.update_idletasks()

        try:
            self.chapter_file_paths = self.file_processor.split_file(
                filepath, split_method, split_value, start_number, chapter_suffix
            )
            if self.chapter_file_paths:
                messagebox.showinfo("Success", f"File split successfully into {len(self.chapter_file_paths)} chapters.")
                self.duplicate_button.config(state="normal")
            else:
                messagebox.showerror("Error", "Splitting failed. Check log for details.")
        except Exception as e:
            self.log_message(f"An unexpected error occurred during split: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.split_button.config(state="normal")
            self.root.update_idletasks()

    def perform_duplication(self):
        if not self.chapter_file_paths:
            messagebox.showwarning("Warning", "No chapters have been split yet, or splitting failed.", parent=self.root)
            return

        append_text = self.duplicate_append_text_area.get("1.0", tk.END).strip() 
        empty_suffix = self.empty_file_suffix_var.get()

        if not empty_suffix:
             messagebox.showerror("Error", "Suffix for empty file names cannot be blank.", parent=self.root)
             return

        self.log_message(f"Starting duplication process for {len(self.chapter_file_paths)} chapters.")
        self.log_message(f"Text to add: '{append_text}', Empty file name suffix part: '{empty_suffix}'")

        self.duplicate_button.config(state="disabled")
        self.split_button.config(state="disabled")
        self.root.update_idletasks()

        try:
            self.file_processor.duplicate_and_modify_chapters(
                self.chapter_file_paths, append_text, empty_suffix
            )
            messagebox.showinfo("Success", "Chapters duplicated and modified successfully.", parent=self.root)
        except Exception as e:
            self.log_message(f"An unexpected error occurred during duplication: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}", parent=self.root)
        finally:
            self.duplicate_button.config(state="normal")
            self.split_button.config(state="normal")
            self.root.update_idletasks()

    # --- Methods for File Mover Tab ---
    def _browse_source_folder_fm(self):
        folder_path = filedialog.askdirectory(title="Select Source Folder (contains files)")
        if folder_path:
            self.source_folder_fm_var.set(folder_path)
            self.log_message(f"File Mover: Selected source folder: {folder_path}")
            self._load_folder_contents_fm()

    def _browse_dest_folder_fm(self):
        folder_path = filedialog.askdirectory(title="Select Main Destination Folder (contains subfolders)")
        if folder_path:
            self.dest_folder_fm_var.set(folder_path)
            self.log_message(f"File Mover: Selected destination folder: {folder_path}")
            self._load_folder_contents_fm()

    def _clear_listboxes_fm(self):
        self.source_files_listbox_fm.delete(0, tk.END)
        self.dest_folders_listbox_fm.delete(0, tk.END)
        
        self.initial_source_files_full_paths_fm = []
        self.current_source_files_full_paths_fm = []
        self.initial_dest_subfolders_full_paths_fm = []
        self.current_dest_subfolders_full_paths_fm = []
        self.drag_start_index_fm = None


    def _load_folder_contents_fm(self):
        self._clear_listboxes_fm()
        self.move_button_fm.config(state="disabled")

        source_path = self.source_folder_fm_var.get()
        dest_path = self.dest_folder_fm_var.get()

        if not source_path or not dest_path:
            # One or both paths are not set yet, just ensure UI is clear.
            self.status_label_fm_var.set("Status: Select source and destination folders.")
            return

        self.log_message(f"File Mover: Loading contents for Source: '{source_path}' and Dest: '{dest_path}'")
        contents = self.file_mover_logic.get_folder_contents(source_path, dest_path)

        if contents['error_message']:
            self.log_message(f"File Mover Error: {contents['error_message']}")
            messagebox.showerror("Folder Error", contents['error_message'], parent=self.fm_tab_frame)
            self.status_label_fm_var.set(f"Status: Error - {contents['error_message']}")
            return

        for f_name in contents['source_files']:
            self.source_files_listbox_fm.insert(tk.END, f_name)
            self.initial_source_files_full_paths_fm.append(os.path.join(source_path, f_name))
        self.current_source_files_full_paths_fm = list(self.initial_source_files_full_paths_fm)
            
        for d_name in contents['dest_subfolders']:
            self.dest_folders_listbox_fm.insert(tk.END, d_name)
            self.initial_dest_subfolders_full_paths_fm.append(os.path.join(dest_path, d_name))
        self.current_dest_subfolders_full_paths_fm = list(self.initial_dest_subfolders_full_paths_fm)

        num_source_files = len(self.current_source_files_full_paths_fm)
        num_dest_subfolders = len(self.current_dest_subfolders_full_paths_fm)

        if num_source_files == 0 and num_dest_subfolders == 0:
            self.status_label_fm_var.set("Status: No source files or destination subfolders found.")
        elif num_source_files == 0:
            self.status_label_fm_var.set("Status: No source files found.")
        elif num_dest_subfolders == 0:
            self.status_label_fm_var.set("Status: No destination subfolders found.")
        elif num_source_files == num_dest_subfolders:
            self.status_label_fm_var.set(f"Status: Ready to move {num_source_files} file(s).")
            self.move_button_fm.config(state="normal")
        else:
            mismatch_msg = f"Mismatch: {num_source_files} source files, {num_dest_subfolders} destination subfolders."
            self.status_label_fm_var.set(f"Status: {mismatch_msg}")
            messagebox.showwarning("Count Mismatch", mismatch_msg + "\n\nPlease ensure counts match for moving.", parent=self.fm_tab_frame)
            self.log_message(f"File Mover: {mismatch_msg}")


    def _on_source_lb_drag_start_fm(self, event):
        widget = event.widget
        index = widget.nearest(event.y)
        if index == -1: # Clicked outside any item
            return
        
        sel = widget.curselection()
        if not sel or index != sel[0]: # if selection is empty or different from nearest item
             widget.selection_clear(0, tk.END)
             widget.selection_set(index)
             widget.activate(index)

        self.drag_start_index_fm = index
        # self.log_message(f"Drag Start: Index {self.drag_start_index_fm}, Item: {widget.get(index)}")


    def _on_source_lb_drag_motion_fm(self, event):
        if self.drag_start_index_fm is None:
            return
        widget = event.widget
        current_index = widget.nearest(event.y)
        if current_index != -1 and current_index != widget.curselection()[0]:
            widget.activate(current_index) # Visual feedback for potential drop target
            # self.log_message(f"Drag Motion: Over Index {current_index}, Item: {widget.get(current_index)}")


    def _on_source_lb_drag_release_fm(self, event):
        if self.drag_start_index_fm is None:
            return
        
        widget = event.widget
        drop_index = widget.nearest(event.y)
        
        start_idx = self.drag_start_index_fm
        self.drag_start_index_fm = None # Reset drag state first

        if drop_index == -1 or drop_index == start_idx : # Dropped outside or on itself
            widget.selection_clear(0, tk.END) # Clear selection if dropped outside
            # self.log_message(f"Drag Release: Invalid drop index {drop_index} or same as start {start_idx}.")
            return

        # Move the item in the listbox display
        item_to_move_display = widget.get(start_idx)
        widget.delete(start_idx)
        widget.insert(drop_index, item_to_move_display)
        widget.selection_set(drop_index) # Select the moved item
        widget.activate(drop_index)

        # Move the item in the internal list of full paths
        item_path_to_move = self.current_source_files_full_paths_fm.pop(start_idx)
        self.current_source_files_full_paths_fm.insert(drop_index, item_path_to_move)
        
        self.log_message(f"File Mover: Reordered source file '{os.path.basename(item_path_to_move)}' from index {start_idx} to {drop_index}.")


    def _execute_move_files_fm(self):
        self.log_message("File Mover: Initiating file move operation.")
        
        source_files_to_move = self.current_source_files_full_paths_fm
        dest_folders_for_move = self.current_dest_subfolders_full_paths_fm # Using current, though not reorderable by user yet

        if not source_files_to_move or not dest_folders_for_move:
            messagebox.showerror("Move Error", "Source files or destination folders list is empty.", parent=self.fm_tab_frame)
            return

        if len(source_files_to_move) != len(dest_folders_for_move):
            messagebox.showerror("Move Error", "Mismatch between the number of source files and destination folders. Cannot proceed.", parent=self.fm_tab_frame)
            self.move_button_fm.config(state="disabled") # Should already be, but good to ensure
            return

        preview_lines = []
        for i in range(min(len(source_files_to_move), 5)): # Show preview for up to 5 files
            src_name = os.path.basename(source_files_to_move[i])
            dest_name = os.path.basename(dest_folders_for_move[i])
            preview_lines.append(f"Move '{src_name}'  ->  '{dest_name}/'")
        if len(source_files_to_move) > 5:
            preview_lines.append("...")
        preview_message = "\n".join(preview_lines)

        confirm = messagebox.askyesno("Confirm Move Operation", 
                                      f"Are you sure you want to move {len(source_files_to_move)} file(s)?\n\nPreview:\n{preview_message}",
                                      parent=self.fm_tab_frame)
        if not confirm:
            self.log_message("File Mover: Move operation cancelled by user.")
            return

        self.move_button_fm.config(state="disabled")
        self.browse_source_fm_button.config(state="disabled")
        self.browse_dest_fm_button.config(state="disabled")
        self.status_label_fm_var.set("Status: Moving files...")
        self.root.update_idletasks()

        results = self.file_mover_logic.move_files_to_folders(source_files_to_move, dest_folders_for_move)
        
        success_count = 0
        error_count = 0
        detailed_messages = ["Move Operation Results:"]

        for res in results:
            log_entry = f"File: {res['file']}, Status: {res['status']}, Message: {res['message']}"
            self.log_message(log_entry) # Log each operation
            detailed_messages.append(log_entry)
            if res['status'] == 'Success':
                success_count += 1
            else:
                error_count += 1
        
        summary_message = f"Move complete. Success: {success_count}, Errors: {error_count}."
        self.log_message(summary_message)
        
        if error_count > 0:
            messagebox.showwarning("Move Partially Failed", summary_message + "\n\nCheck log for details.", parent=self.fm_tab_frame)
        else:
            messagebox.showinfo("Move Successful", summary_message, parent=self.fm_tab_frame)

        # Refresh folder contents and UI state
        self._load_folder_contents_fm() 
        self.browse_source_fm_button.config(state="normal")
        self.browse_dest_fm_button.config(state="normal")
        # The move_button_fm state will be reset by _load_folder_contents_fm based on new counts.


if __name__ == "__main__":
    root = tk.Tk()
    app = ChapterSplitterApp(root)
    root.mainloop()