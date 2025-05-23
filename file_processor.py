import os
import re
import shutil

class FileProcessor:
    def __init__(self, log_callback=print):
        self.log_callback = log_callback

    def split_file(self, input_filepath, split_mode, split_value, start_number, chapter_filename_suffix="orig"):
        """
        Splits the input text file into chapters.

        Args:
            input_filepath (str): Path to the input .txt file.
            split_mode (str): "string" or "regex".
            split_value (str): The string or regex pattern to split by.
            start_number (int): The starting number for chapter filenames.
            chapter_filename_suffix (str): Suffix to add before the .txt extension for chapter files.

        Returns:
            list: A list of paths to the created chapter files, or None on failure.
        """
        if not os.path.exists(input_filepath):
            self.log_callback(f"Error: Input file not found: {input_filepath}")
            return None
        if not input_filepath.lower().endswith(".txt"):
            self.log_callback("Error: Input file must be a .txt file.")
            return None

        try:
            with open(input_filepath, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.log_callback(f"Error reading input file: {e}")
            return None

        if split_mode == "string":
            if not split_value:
                self.log_callback("Error: Split string cannot be empty.")
                return None
            parts = content.split(split_value)
        elif split_mode == "regex":
            if not split_value:
                self.log_callback("Error: Split regex cannot be empty.")
                return None
            try:
                parts = re.split(split_value, content)
            except re.error as e:
                self.log_callback(f"Error in regex pattern: {e}")
                return None
        else:
            self.log_callback("Error: Invalid split mode.")
            return None

        chapters_content = [part.strip() for part in parts if part.strip()]

        if not chapters_content:
            self.log_callback("No chapters found after splitting. Check your split string/regex.")
            return None

        input_dir = os.path.dirname(input_filepath)
        input_filename_no_ext = os.path.splitext(os.path.basename(input_filepath))[0]
        
        base_output_folder_name = f"{input_filename_no_ext}_chapters"
        base_output_path = os.path.join(input_dir, base_output_folder_name)
        
        os.makedirs(base_output_path, exist_ok=True)
        self.log_callback(f"Created base output folder: {base_output_path}")

        chapter_file_paths = []
        for i, chapter_text in enumerate(chapters_content):
            chapter_num = start_number + i
            chapter_folder_name = f"Chapter_{chapter_num}"
            chapter_folder_path = os.path.join(base_output_path, chapter_folder_name)
            os.makedirs(chapter_folder_path, exist_ok=True)

            chapter_filename = f"{chapter_num}_{chapter_filename_suffix}.txt" 
            chapter_filepath = os.path.join(chapter_folder_path, chapter_filename)

            try:
                with open(chapter_filepath, 'w', encoding='utf-8') as cf:
                    cf.write(chapter_text)
                self.log_callback(f"Created chapter: {chapter_filepath}")
                chapter_file_paths.append(chapter_filepath)
            except Exception as e:
                self.log_callback(f"Error writing chapter file {chapter_filepath}: {e}")
        
        if chapter_file_paths:
            self.log_callback(f"Successfully split into {len(chapter_file_paths)} chapters.")
        return chapter_file_paths

    def duplicate_and_modify_chapters(self, chapter_paths, text_to_add_after_codeblock, empty_file_suffix_text):
        """
        Duplicates chapter files, wraps content in ```, appends text, and creates empty files.

        Args:
            chapter_paths (list): List of paths to the chapter .txt files.
            text_to_add_after_codeblock (str): Text to append after ``` in duplicated files.
            empty_file_suffix_text (str): Suffix to append to the name of the new empty files.
                                           (e.g., if "bi", and chapter is "1", empty file is "1_bi.txt")
        """
        if not chapter_paths:
            self.log_callback("No chapter paths provided for duplication.")
            return

        modified_count = 0
        for original_chapter_path in chapter_paths:
            if not os.path.exists(original_chapter_path):
                self.log_callback(f"Warning: Chapter file not found, skipping: {original_chapter_path}")
                continue

            chapter_dir = os.path.dirname(original_chapter_path)
            original_filename = os.path.basename(original_chapter_path) # e.g., "1_orig.txt"
            # original_filename_no_ext includes the chapter suffix, e.g., "1_orig"
            original_filename_no_ext = os.path.splitext(original_filename)[0] 

            try:
                with open(original_chapter_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except Exception as e:
                self.log_callback(f"Error reading chapter file {original_chapter_path} for duplication: {e}")
                continue

            # 1. Create wrapped duplicate
            # Name: [original_filename_no_ext]_wrapped.txt (e.g., "1_orig_wrapped.txt")
            wrapped_content = f"```\n{original_content}\n```\n{text_to_add_after_codeblock}"
            duplicate_filename = f"{original_filename_no_ext}_wrapped.txt" 
            duplicate_filepath = os.path.join(chapter_dir, duplicate_filename)
            try:
                with open(duplicate_filepath, 'w', encoding='utf-8') as df:
                    df.write(wrapped_content)
                self.log_callback(f"Created wrapped duplicate: {duplicate_filepath}")
            except Exception as e:
                self.log_callback(f"Error creating wrapped duplicate {duplicate_filepath}: {e}")
                continue

            # 2. Create empty file
            # Name: [base_chapter_num]_[empty_file_suffix_text].txt (e.g., "1_bi.txt")
            
            # Extract the base chapter number (the initial numeric part of the filename)
            match = re.match(r"(\d+)", original_filename_no_ext)
            if match:
                base_chapter_num_str = match.group(1) # e.g., "1" from "1_orig" or "1" from "1"
                empty_filename_base = f"{base_chapter_num_str}"
            else:
                # Fallback: if somehow the original filename doesn't start with a number,
                # use the full original_filename_no_ext. This shouldn't happen with current logic.
                self.log_callback(f"Warning: Could not parse base chapter number from '{original_filename_no_ext}'. Using it as base for empty file.")
                empty_filename_base = original_filename_no_ext
            
            empty_filename = f"{empty_filename_base}_{empty_file_suffix_text}.txt"
            empty_filepath = os.path.join(chapter_dir, empty_filename)
            try:
                with open(empty_filepath, 'w', encoding='utf-8') as ef:
                    pass
                self.log_callback(f"Created empty file: {empty_filepath}")
                modified_count += 1
            except Exception as e:
                self.log_callback(f"Error creating empty file {empty_filepath}: {e}")
        
        if modified_count > 0:
            self.log_callback(f"Successfully duplicated and modified {modified_count} chapters.")
        else:
            self.log_callback("No chapters were duplicated or modified.")