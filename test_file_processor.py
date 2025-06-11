import unittest
import os
import shutil
import tempfile
from file_processor import FileProcessor # Assuming file_processor.py is in the same directory or PYTHONPATH

class TestFileProcessorSplitFile(unittest.TestCase):

    def setUp(self):
        # Create a temporary directory to store test inputs and outputs
        self.test_dir = tempfile.mkdtemp()
        self.fp = FileProcessor(log_callback=lambda x: None) # Suppress logging during tests

    def tearDown(self):
        # Remove the temporary directory after the test
        shutil.rmtree(self.test_dir)

    def _create_input_file(self, filename="input.txt", content=""):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def _assert_chapter_exists(self, base_output_folder, chapter_folder_name, chapter_filename_num, suffix, expected_content):
        chapter_folder_path = os.path.join(base_output_folder, chapter_folder_name)
        self.assertTrue(os.path.isdir(chapter_folder_path), f"Chapter folder '{chapter_folder_name}' not found.")

        chapter_filename = f"{chapter_filename_num}_{suffix}.txt"
        chapter_filepath = os.path.join(chapter_folder_path, chapter_filename)
        self.assertTrue(os.path.isfile(chapter_filepath), f"Chapter file '{chapter_filepath}' not found.")

        with open(chapter_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, expected_content, f"Content mismatch for chapter {chapter_filename_num} in folder {chapter_folder_name}")

    def test_split_with_custom_name_string_mode(self):
        content = "IntroductionSPLIT_HERE(Chapter One)This is chapter one.SPLIT_HERE(Chapter Two)This is chapter two."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT_HERE", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_1", 1, "test", "Introduction")
        self._assert_chapter_exists(output_folder_base, "Chapter One", 2, "test", "This is chapter one.")
        self._assert_chapter_exists(output_folder_base, "Chapter Two", 3, "test", "This is chapter two.")

    def test_split_with_custom_name_regex_mode(self):
        content = "Intro===DELIMITER===(First Chapter)Content 1===DELIMITER===(Second Chapter)Content 2"
        input_file = self._create_input_file(content=content)
        # Regex delimiter might need escaping if it has special characters, but here "===" is fine.
        chapter_paths = self.fp.split_file(input_file, "regex", "===DELIMITER===", 0, "doc")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_0", 0, "doc", "Intro")
        self._assert_chapter_exists(output_folder_base, "First Chapter", 1, "doc", "Content 1")
        self._assert_chapter_exists(output_folder_base, "Second Chapter", 2, "doc", "Content 2")

    def test_split_default_naming_string_mode(self):
        content = "Part 1---Part 2---Part 3"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "---", 10, "seg")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_10", 10, "seg", "Part 1")
        self._assert_chapter_exists(output_folder_base, "Chapter_11", 11, "seg", "Part 2")
        self._assert_chapter_exists(output_folder_base, "Chapter_12", 12, "seg", "Part 3")

    def test_split_starts_with_delimiter_custom_name(self):
        content = "SPLIT(CustomStart)Content of first chapter."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "frag")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1) # No content before first split

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "CustomStart", 1, "frag", "Content of first chapter.")

        # Check that no "Chapter_1" (default for empty first part) folder was created if input starts with delimiter
        # The current logic for raw_parts[0] means if it's empty after strip, no initial chapter.
        # If "SPLIT" is the delimiter, raw_parts[0] is empty.
        default_first_part_folder = os.path.join(output_folder_base, "Chapter_1") # default name for first part if it existed
        self.assertFalse(os.path.exists(default_first_part_folder), "Folder for empty initial part should not be created when starting with delimiter.")


    def test_split_mixed_naming_and_empty_segments(self):
        content = "First part.SPLIT(Custom One)Content1SPLITSPLIT(Custom Two)Content2SPLIT  SPLIT(Empty Custom)  "
        input_file = self._create_input_file(content=content)
        # Note: "SPLIT SPLIT" will result in one "Chapter_X" with empty content if not handled.
        # The current code: if actual_chapter_content.strip() is empty AND no custom name, it's skipped.
        # If custom name exists, it's created even if content is empty.
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 0, "mix")

        self.assertIsNotNone(chapter_paths)
        # Expected:
        # 1. "First part." (Chapter_0)
        # 2. "(Custom One)Content1" (Custom One)
        # 3. "" (empty content after second SPLIT, no custom name -> should be skipped by current logic)
        # 4. "(Custom Two)Content2" (Custom Two)
        # 5. "  " (empty content after fourth SPLIT, no custom name -> should be skipped)
        # 6. "(Empty Custom)  " (Empty Custom, content "  " -> stripped to "" but custom name folder created)
        self.assertEqual(len(chapter_paths), 4)


        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_0", 0, "mix", "First part.")
        self._assert_chapter_exists(output_folder_base, "Custom One", 1, "mix", "Content1")
        self._assert_chapter_exists(output_folder_base, "Custom Two", 2, "mix", "Content2")
        self._assert_chapter_exists(output_folder_base, "Empty Custom", 3, "mix", "") # Content is stripped

    def test_split_empty_custom_name_parentheses(self):
        content = "DataSPLIT()Empty name content."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_1", 1, "test", "Data")
        # Empty custom name "()" should fall back to default naming "Chapter_ID"
        self._assert_chapter_exists(output_folder_base, "Chapter_2", 2, "test", "Empty name content.")

    def test_split_delimiter_at_end_of_file(self):
        content = "Some data then SPLIT"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "endtest")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1) # Only "Some data then"

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_1", 1, "endtest", "Some data then")
        # The logic `if (i + 1) < len(raw_parts):` handles trailing delimiters.
        # `raw_parts` would be `['Some data then ', 'SPLIT', '']`
        # The loop for `i=1` (delimiter 'SPLIT') has `i+1 = 2`. `raw_parts[2]` is `''`.
        # `text_after_delimiter` is `''`. `custom_name_match` is None. `actual_chapter_content` is `''`.
        # `actual_chapter_content.strip()` is `''`. `custom_name_match` is `None`. So, it's skipped. Correct.

    def test_no_delimiter_found(self):
        content = "This is a single block of text without any delimiters."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "NOT_FOUND_DELIMITER", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1) # The whole content as one chapter

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        self._assert_chapter_exists(output_folder_base, "Chapter_1", 1, "test", content)

    def test_empty_input_file(self):
        input_file = self._create_input_file(content="")
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test")
        self.assertIsNone(chapter_paths, "Should return None for empty file leading to no chapters.")
        # The current code returns None if processed_chapters is empty.
        # If content is "", raw_parts can be ['']. first_part_content is "". No initial chapter.
        # Loop for i=1 doesn't run. processed_chapters is empty. Returns None. Correct.

    def test_sanitized_folder_names(self):
        content = "SPLIT(Chapter: The Forbidden <Name>?)Content"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 0, "sanitize")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        # Expected sanitized name: "Chapter_ The Forbidden _Name__" (or similar based on exact regex)
        # Current sanitization: re.sub(r'[<>:"/\|?*]', '_', chapter_data["name"])
        # "Chapter: The Forbidden <Name>?" -> "Chapter_ The Forbidden _Name__"
        # Then re.sub(r'^\.+|^\s+|\.+$|\s+$', '', sanitized_folder_name).strip()
        # This should be "Chapter_ The Forbidden _Name__"
        self._assert_chapter_exists(output_folder_base, "Chapter_ The Forbidden _Name__", 0, "sanitize", "Content")

    def test_split_with_spaces_around_custom_name(self):
        content = "SPLIT (  My Spaced Out Chapter  )  Spaced content.  "
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test_space")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)

        output_folder_base = os.path.join(self.test_dir, "input_chapters")
        # Custom name regex `^\s*\(([^)]+)\)\s*` should handle spaces around parentheses
        # and `strip()` on group(1) handles spaces inside.
        # Content is also stripped.
        self._assert_chapter_exists(output_folder_base, "My Spaced Out Chapter", 1, "test_space", "Spaced content.")


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
