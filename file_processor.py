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

        raw_parts = []
        if split_mode == "string":
            if not split_value:
                self.log_callback("Error: Split string cannot be empty.")
                return None
            # Escape split_value for regex, then use capturing group
            raw_parts = re.split(f'({re.escape(split_value)})', content)
        elif split_mode == "regex":
            if not split_value:
                self.log_callback("Error: Split regex cannot be empty.")
                return None
            try:
                # Use capturing group for regex mode
                raw_parts = re.split(f'({split_value})', content)
            except re.error as e:
                self.log_callback(f"Error in regex pattern: {e}")
                return None
        else:
            self.log_callback("Error: Invalid split mode.")
            return None

        processed_chapters = []
        current_chapter_id_counter = 0 # Tracks the number of chapters identified

        # Handle content before the first delimiter (raw_parts[0])
        if raw_parts and raw_parts[0].strip():
            first_part_content = raw_parts[0].strip()
            chapter_id = start_number + current_chapter_id_counter
            processed_chapters.append({
                "name": f"Chapter_{chapter_id}",
                "content": first_part_content,
                "id_for_filename": chapter_id
            })
            current_chapter_id_counter += 1

        # Process parts starting from the first delimiter
        # Loop takes delimiter at raw_parts[i] and content_after at raw_parts[i+1]
        for i in range(1, len(raw_parts), 2):
            # raw_parts[i] is the delimiter. We are interested in raw_parts[i+1].
            if (i + 1) < len(raw_parts):
                text_after_delimiter = raw_parts[i+1]

                # Regex to find custom name: e.g., "(My Chapter) actual content"
                # Changed ([^)]+) to ([^)]*) to allow empty names like ()
                custom_name_match = re.match(r'^\s*\(([^)]*)\)\s*', text_after_delimiter)

                chapter_id = start_number + current_chapter_id_counter
                chapter_name_to_use = f"Chapter_{chapter_id}" # Default name
                actual_chapter_content = text_after_delimiter # Default content

                if custom_name_match:
                    # Always update content to be what's after the matched parentheses pattern
                    actual_chapter_content = text_after_delimiter[custom_name_match.end():]
                    custom_name = custom_name_match.group(1).strip()
                    if custom_name: # Use custom name if it's not empty
                        chapter_name_to_use = custom_name
                    # Else, chapter_name_to_use remains the default (e.g., "Chapter_X")

                actual_chapter_content = actual_chapter_content.strip()

                # Add chapter only if there's actual content OR if a non-empty custom name was specified
                # This prevents creating "Chapter_X" for empty sections after a delimiter,
                # but ensures custom-named chapters are created even if their content is empty.
                if actual_chapter_content or (custom_name_match and custom_name_match.group(1).strip()):
                    processed_chapters.append({
                        "name": chapter_name_to_use,
                        "content": actual_chapter_content,
                        "id_for_filename": chapter_id
                    })
                    current_chapter_id_counter += 1 # Increment for each chapter added

        if not processed_chapters:
            self.log_callback("No chapters found after splitting. Check your split string/regex and content structure.")
            return None

        input_dir = os.path.dirname(input_filepath)
        input_filename_no_ext = os.path.splitext(os.path.basename(input_filepath))[0]
        base_output_folder_name = f"{input_filename_no_ext}_chapters"
        base_output_path = os.path.join(input_dir, base_output_folder_name)
        
        os.makedirs(base_output_path, exist_ok=True)

        chapter_file_paths = []
        for chapter_data in processed_chapters:
            chapter_num_for_filename = chapter_data["id_for_filename"]

            # Sanitize folder name
            sanitized_folder_name = re.sub(r'[<>:"/\|?*]', '_', chapter_data["name"])
            sanitized_folder_name = re.sub(r'^\.+|^\s+|\.+$|\s+$', '', sanitized_folder_name).strip() # leading/trailing dots/spaces
            if not sanitized_folder_name: # Fallback if name becomes empty after sanitization
                sanitized_folder_name = f"Chapter_{chapter_num_for_filename}"

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
        
        if chapter_file_paths:
            self.log_callback(f"Successfully split into {len(chapter_file_paths)} chapters.")
        else:
            # This may occur if input is empty or only delimiters with no content.
            self.log_callback("Processing complete, but no chapter files were created.")

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
            
            match = re.match(r"(\d+)", original_filename_no_ext) # Extracts number from "1_orig"
            if match:
                base_chapter_num_str = match.group(1)
                empty_filename_base = f"{base_chapter_num_str}"
            else:
                self.log_callback(f"Warning: Could not parse base chapter number from '{original_filename_no_ext}'. Using it as base for empty file name.")
                empty_filename_base = original_filename_no_ext # Fallback
            
            empty_filename = f"{empty_filename_base}_{empty_file_suffix_text}.txt"
            empty_filepath = os.path.join(chapter_dir, empty_filename)
            try:
                with open(empty_filepath, 'w', encoding='utf-8') as ef:
                    pass # Create an empty file
                self.log_callback(f"Created empty file: {empty_filepath}")
                modified_count += 1
            except Exception as e:
                self.log_callback(f"Error creating empty file {empty_filepath}: {e}")
        
        if modified_count > 0:
            self.log_callback(f"Successfully duplicated and modified {modified_count} chapters.")
        else:
            self.log_callback("No chapters were duplicated or modified (This might be expected if input was empty or no paths provided).")