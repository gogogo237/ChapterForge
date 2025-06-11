import os
import re
import shutil

class FileProcessor:
    def __init__(self, log_callback=print):
        self.log_callback = log_callback

    def split_file(self, input_filepath, split_mode, split_value, start_number, chapter_filename_suffix="orig"):
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

        if not content.strip():
            self.log_callback("Input file is empty or contains only whitespace. No chapters to split.")
            return None

        base_delimiter_pattern_for_regex = ""
        if split_mode == "string":
            if not split_value:
                self.log_callback("Error: Split string cannot be empty for 'string' mode.")
                return None
            base_delimiter_pattern_for_regex = re.escape(split_value)
        elif split_mode == "regex":
            if not split_value:
                self.log_callback("Error: Split regex cannot be empty for 'regex' mode.")
                return None
            base_delimiter_pattern_for_regex = split_value
        else:
            self.log_callback("Error: Invalid split mode.")
            return None

        delimiter_capturing_regex = f"({base_delimiter_pattern_for_regex}(?:\s*\(([^)]*)\))?)"

        try:
            raw_parts = re.split(delimiter_capturing_regex, content)
        except re.error as e:
            self.log_callback(f"Error in splitting regex pattern: {e}")
            return None

        processed_chapters = []
        # Initialize the two counters
        filename_id_counter = start_number
        default_naming_sequence_counter = start_number

        # --- Structural Validations ---
        if not raw_parts[0].strip() and len(raw_parts) > 1:
            self.log_callback("Error: File structure invalid. Content cannot start with a delimiter.")
            return None

        if len(raw_parts) == 1:
            if raw_parts[0].strip():
                self.log_callback("Error: File structure invalid. No delimiters found, or file does not end with a delimiter as required.")
                return None
            else:
                self.log_callback("Input file is effectively empty after attempting to split. No chapters.")
                return None

        if (len(raw_parts) - 1) % 3 != 0:
            self.log_callback(f"Error: Invalid file structure. Segment count ({len(raw_parts)}) from splitting is unexpected. Expected TEXT, DELIMITER_INFO, TEXT... structure. Does it end with a delimiter?")
            return None

        if raw_parts[len(raw_parts) - 1].strip():
            self.log_callback("Error: File structure invalid. There is text content after the final delimiter.")
            return None

        num_chapters = (len(raw_parts) - 1) // 3
        if num_chapters == 0 :
            self.log_callback("No chapters to process based on parsed structure (e.g. file was just a delimiter).")
            return None

        for i in range(num_chapters):
            text_segment_content = raw_parts[i * 3].strip()
            custom_name_from_group = raw_parts[i * 3 + 2]

            if not text_segment_content:
                self.log_callback(f"Error: File structure invalid. Empty text segment found before delimiter for chapter {i + 1}.")
                return None

            current_filename_id = filename_id_counter # Use current filename_id_counter for this chapter's file

            chapter_name_to_use = ""

            if custom_name_from_group is not None and custom_name_from_group.strip():
                chapter_name_to_use = custom_name_from_group.strip()
                # default_naming_sequence_counter is NOT incremented
            else:
                chapter_name_to_use = f"Chapter_{default_naming_sequence_counter}"
                default_naming_sequence_counter += 1 # Increment only for default names

            processed_chapters.append({
                "name": chapter_name_to_use,
                "content": text_segment_content,
                "id_for_filename": current_filename_id # This is the sequential ID for the filename
            })
            filename_id_counter += 1 # Always increment for the next file's ID

        if not processed_chapters:
            self.log_callback("No valid chapters were processed.")
            return None

        input_dir = os.path.dirname(input_filepath)
        input_filename_no_ext = os.path.splitext(os.path.basename(input_filepath))[0]
        base_output_folder_name = f"{input_filename_no_ext}_chapters"
        base_output_path = os.path.join(input_dir, base_output_folder_name)
        os.makedirs(base_output_path, exist_ok=True)

        chapter_file_paths = []
        for chapter_data in processed_chapters:
            # Use 'id_for_filename' from chapter_data for the actual filename number
            chapter_num_for_filename = chapter_data["id_for_filename"]

            sanitized_folder_name = re.sub(r'[<>:"/\|?*]', '_', chapter_data["name"])
            sanitized_folder_name = re.sub(r'^\.+|^\s+|\.+$|\s+$', '', sanitized_folder_name).strip()
            if not sanitized_folder_name: # Should not happen if default naming is robust
                sanitized_folder_name = f"Chapter_{chapter_num_for_filename}" # Fallback, but logic aims to prevent empty names

            chapter_folder_path = os.path.join(base_output_path, sanitized_folder_name)
            os.makedirs(chapter_folder_path, exist_ok=True)

            chapter_filename = f"{chapter_num_for_filename}_{chapter_filename_suffix}.txt"
            chapter_filepath = os.path.join(chapter_folder_path, chapter_filename)

            try:
                with open(chapter_filepath, 'w', encoding='utf-8') as cf:
                    cf.write(chapter_data["content"])
                self.log_callback(f"Created chapter: '{chapter_filepath}' in folder '{sanitized_folder_name}'")
                chapter_file_paths.append(chapter_filepath)
            except Exception as e:
                self.log_callback(f"Error writing chapter file {chapter_filepath}: {e}")
                return None

        if not chapter_file_paths and num_chapters > 0 :
             self.log_callback("Error: Chapters were processed but no files were written (unexpected).")
             return None

        self.log_callback(f"Successfully split into {len(chapter_file_paths)} chapters.")
        return chapter_file_paths

    def duplicate_and_modify_chapters(self, chapter_paths, text_to_add_after_codeblock, empty_file_suffix_text):
        # This method remains unchanged.
        if not chapter_paths:
            self.log_callback("No chapter paths provided for duplication.")
            return

        modified_count = 0
        for original_chapter_path in chapter_paths:
            if not os.path.exists(original_chapter_path):
                self.log_callback(f"Warning: Chapter file not found, skipping: {original_chapter_path}")
                continue

            chapter_dir = os.path.dirname(original_chapter_path)
            original_filename = os.path.basename(original_chapter_path)
            original_filename_no_ext = os.path.splitext(original_filename)[0] 

            try:
                with open(original_chapter_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except Exception as e:
                self.log_callback(f"Error reading chapter file {original_chapter_path} for duplication: {e}")
                continue

            wrapped_content = f"""```
{original_content}
```
{text_to_add_after_codeblock}"""
            duplicate_filename = f"{original_filename_no_ext}_wrapped.txt" 
            duplicate_filepath = os.path.join(chapter_dir, duplicate_filename)
            try:
                with open(duplicate_filepath, 'w', encoding='utf-8') as df:
                    df.write(wrapped_content)
                self.log_callback(f"Created wrapped duplicate: {duplicate_filepath}")
            except Exception as e:
                self.log_callback(f"Error creating wrapped duplicate {duplicate_filepath}: {e}")
                continue
            
            match = re.match(r"(\d+)", original_filename_no_ext)
            if match:
                base_chapter_num_str = match.group(1)
                empty_filename_base = f"{base_chapter_num_str}"
            else:
                self.log_callback(f"Warning: Could not parse base chapter number from '{original_filename_no_ext}'. Using it as base for empty file name.")
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