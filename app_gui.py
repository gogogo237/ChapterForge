import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import os
from file_processor import FileProcessor

DEFAULT_SPLIT_STRING = "=======----JGFLKG==57483==="
DEFAULT_DUPLICATE_APPEND_TEXT = "Split the above text into seperate sentences. And append the Chinese translation of each sentence after each English sentence. Each English and Chinese sentence should be put into separate line. just give me the answer directly, no other response phrase."
DEFAULT_CHAPTER_SUFFIX = "orig"

class ChapterSplitterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Chapter Splitter Pro")
        self.root.geometry("700x750") # Increased height a bit more for the new text area

        self.file_processor = FileProcessor(log_callback=self.log_message)
        self.chapter_file_paths = []

        # --- UI Variables ---
        self.input_filepath_var = tk.StringVar()
        self.split_method_var = tk.StringVar(value="string")
        self.split_string_var = tk.StringVar(value=DEFAULT_SPLIT_STRING)
        self.split_regex_var = tk.StringVar()
        self.start_number_var = tk.StringVar(value="1")
        self.chapter_suffix_var = tk.StringVar(value=DEFAULT_CHAPTER_SUFFIX)
        # self.duplicate_append_text_var is removed, ScrolledText will be used directly
        self.empty_file_suffix_var = tk.StringVar(value="bi")

        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        input_frame = ttk.LabelFrame(main_frame, text="Input File", padding="10")
        input_frame.pack(fill=tk.X, pady=5)
        ttk.Label(input_frame, text="Select TXT File:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.input_file_entry = ttk.Entry(input_frame, textvariable=self.input_filepath_var, width=60, state="readonly")
        self.input_file_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.browse_button = ttk.Button(input_frame, text="Browse...", command=self.browse_file)
        self.browse_button.grid(row=0, column=2, padx=5, pady=5)
        input_frame.columnconfigure(1, weight=1)

        split_options_frame = ttk.LabelFrame(main_frame, text="Splitting Options", padding="10")
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

        naming_frame = ttk.LabelFrame(main_frame, text="Chapter Naming", padding="10")
        naming_frame.pack(fill=tk.X, pady=5)
        ttk.Label(naming_frame, text="Start Numbering From:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        self.start_number_entry = ttk.Entry(naming_frame, textvariable=self.start_number_var, width=10)
        self.start_number_entry.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        
        ttk.Label(naming_frame, text="Chapter Filename Suffix:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.chapter_suffix_entry = ttk.Entry(naming_frame, textvariable=self.chapter_suffix_var, width=20)
        self.chapter_suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

        action_frame = ttk.Frame(main_frame, padding="5")
        action_frame.pack(fill=tk.X, pady=10)
        self.split_button = ttk.Button(action_frame, text="Split File", command=self.perform_split)
        self.split_button.pack(side=tk.LEFT, padx=5)
        
        duplication_frame = ttk.LabelFrame(main_frame, text="Duplication & Modification (after splitting)", padding="10")
        duplication_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(duplication_frame, text="Text to add after ```:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.NW) # Sticky NW for better alignment with multiline text
        self.duplicate_append_text_area = scrolledtext.ScrolledText(duplication_frame, wrap=tk.WORD, height=5, width=50) # Replaced Entry with ScrolledText
        self.duplicate_append_text_area.grid(row=0, column=1, padx=5, pady=5, sticky=tk.EW)
        self.duplicate_append_text_area.insert(tk.END, DEFAULT_DUPLICATE_APPEND_TEXT) # Set default text

        ttk.Label(duplication_frame, text="Suffix for empty file names (e.g., 'notes'):").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        self.empty_file_suffix_entry = ttk.Entry(duplication_frame, textvariable=self.empty_file_suffix_var, width=50)
        self.empty_file_suffix_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.EW)
        duplication_frame.columnconfigure(1, weight=1)

        self.duplicate_button = ttk.Button(action_frame, text="Duplicate & Modify Chapters", command=self.perform_duplication, state="disabled")
        self.duplicate_button.pack(side=tk.LEFT, padx=5)

        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=10, width=80)
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.configure(state='disabled')

        self.toggle_split_input()

    def log_message(self, message):
        self.log_area.configure(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.configure(state='disabled')
        self.log_area.see(tk.END)

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
            messagebox.showwarning("Warning", "No chapters have been split yet, or splitting failed.")
            return

        append_text = self.duplicate_append_text_area.get("1.0", tk.END).strip() # Get text from ScrolledText
        empty_suffix = self.empty_file_suffix_var.get()

        if not empty_suffix:
             messagebox.showerror("Error", "Suffix for empty file names cannot be blank.")
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
            messagebox.showinfo("Success", "Chapters duplicated and modified successfully.")
        except Exception as e:
            self.log_message(f"An unexpected error occurred during duplication: {e}")
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        finally:
            self.duplicate_button.config(state="normal")
            self.split_button.config(state="normal")
            self.root.update_idletasks()

if __name__ == "__main__":
    root = tk.Tk()
    app = ChapterSplitterApp(root)
    root.mainloop()