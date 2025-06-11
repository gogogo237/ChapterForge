import unittest
import os
import shutil
import tempfile
from file_processor import FileProcessor

class TestFileProcessorSplitFileStrict(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Noisy logs can be helpful for debugging tests, or use lambda: None to suppress
        self.fp = FileProcessor(log_callback=print)
        # self.fp = FileProcessor(log_callback=lambda x: None)


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_input_file(self, filename="input.txt", content=""):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def _assert_chapter_exists(self, base_output_folder_name, chapter_folder_name, chapter_filename_num, suffix, expected_content):
        # Construct path to the _chapters folder e.g. "input_chapters"
        base_output_path = os.path.join(self.test_dir, base_output_folder_name)

        chapter_folder_path = os.path.join(base_output_path, chapter_folder_name)
        self.assertTrue(os.path.isdir(chapter_folder_path),
                        f"Chapter folder '{chapter_folder_name}' not found in '{base_output_path}'. Found: {os.listdir(base_output_path) if os.path.exists(base_output_path) else 'None'}")

        chapter_filename = f"{chapter_filename_num}_{suffix}.txt"
        chapter_filepath = os.path.join(chapter_folder_path, chapter_filename)
        self.assertTrue(os.path.isfile(chapter_filepath), f"Chapter file '{chapter_filepath}' not found.")

        with open(chapter_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, expected_content, f"Content mismatch for chapter {chapter_filename_num} in folder {chapter_folder_name}")

    # --- VALID STRUCTURE TESTS ---
    def test_valid_single_chapter_no_name(self):
        content = "This is chapter one.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")

        self.assertIsNotNone(chapter_paths, "Expected successful split for valid structure.")
        self.assertEqual(len(chapter_paths), 1)
        self._assert_chapter_exists("input_chapters", "Chapter_1", 1, "test", "This is chapter one.")

    def test_valid_single_chapter_with_name(self):
        content = "This is chapter one.DELIM(ChapterAlpha)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        self._assert_chapter_exists("input_chapters", "ChapterAlpha", 1, "test", "This is chapter one.")

    def test_valid_multiple_chapters_mixed_names_regex_mode(self):
        # Using === as delimiter parts
        content = "Content Alpha===SEP(Name1)Content Beta===SEPContent Gamma===SEP(Name3)"
        input_file = self._create_input_file(content=content)
        # Regex split_value: "===SEP"
        chapter_paths = self.fp.split_file(input_file, "regex", "===SEP", 0, "mix")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        self._assert_chapter_exists("input_chapters", "Name1", 0, "mix", "Content Alpha")
        self._assert_chapter_exists("input_chapters", "Chapter_1", 1, "mix", "Content Beta") # Default name
        self._assert_chapter_exists("input_chapters", "Name3", 2, "mix", "Content Gamma")

    def test_valid_content_with_empty_custom_name_parentheses(self):
        content = "Data.SPLIT()More Data.SPLIT(Final)" # DELIM() means use default name
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 10, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)
        self._assert_chapter_exists("input_chapters", "Chapter_10", 10, "test", "Data.")
        self._assert_chapter_exists("input_chapters", "Final", 11, "test", "More Data.")


    # --- ERROR CONDITION TESTS ---
    def test_error_empty_input_file(self):
        input_file = self._create_input_file(content="") # Empty
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test")
        self.assertIsNone(chapter_paths, "Should return None for empty file.")

    def test_error_whitespace_only_input_file(self):
        input_file = self._create_input_file(content="""
	   """) # Whitespace only
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test")
        self.assertIsNone(chapter_paths, "Should return None for whitespace-only file.")

    def test_error_starts_with_delimiter(self):
        content = "DELIMText after first delimiter.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: starts with delimiter.")

    def test_error_starts_with_delimiter_and_name(self):
        content = "DELIM(StartName)Text after first delimiter.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: starts with delimiter with name.")

    def test_error_not_ending_with_delimiter(self):
        content = "Text segment 1.DELIMText segment 2" # No DELIM after "segment 2"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: does not end with delimiter.")

    def test_error_no_delimiter_at_all_just_text(self):
        content = "This is a single block of text without any delimiters."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "NOT_FOUND_DELIMITER", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: no delimiters found, and must end with one.")

    def test_error_empty_text_segment_between_delimiters(self):
        content = "Text 1.DELIMDELIM(WithName)Text 2.DELIM" # Empty segment between first and second DELIM
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: empty text segment between delimiters.")

    def test_error_empty_text_segment_leading_to_empty_custom_name(self):
        content = "Text 1.DELIM(Name1)DELIM()Text 2.DELIM" # Empty segment between DELIM(Name1) and DELIM()
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: empty text segment between named delimiters.")

    def test_error_only_delimiter(self):
        content = "DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: file is only a delimiter.")

    def test_error_only_delimiter_with_name(self):
        content = "DELIM(ChapterName)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: file is only a delimiter with a name.")

    def test_error_text_after_final_delimiter(self):
        # This is essentially the same as "not ending with delimiter" if the parser is strict.
        # The current logic `raw_parts[len(raw_parts) - 1].strip()` checks this.
        content = "Text1.DELIMText after what should be final delimiter."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths, "Should fail: text found after the supposed final delimiter implies it wasn't final.")

    def test_valid_sanitized_folder_names_strict(self):
        content = "Content with bad:name.DELIM(Chapter: The Forbidden <Name>?)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 0, "sanitize")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        self._assert_chapter_exists("input_chapters", "Chapter_ The Forbidden _Name__", 0, "sanitize", "Content with bad:name.")

    def test_valid_delimiter_with_regex_chars_string_mode(self):
        # String mode should escape regex chars in delimiter
        content = "Chapter 1.DATA*.(Name1)Chapter 2.DATA*."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", ".DATA*.", 1, "s_esc")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)
        self._assert_chapter_exists("input_chapters", "Name1", 1, "s_esc", "Chapter 1")
        self._assert_chapter_exists("input_chapters", "Chapter_2", 2, "s_esc", "Chapter 2")

    def test_valid_complex_regex_delimiter_regex_mode(self):
        # User provides actual regex for delimiter part
        # Delimiter: one or more digits, then "SEP"
        content = r"Text A123SEP(NumName)Text B45SEPText C789SEP(EndName)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "regex", r"\d+SEP", 0, "r_comp") # \d+SEP is the base delimiter

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        self._assert_chapter_exists("input_chapters", "NumName", 0, "r_comp", "Text A")
        self._assert_chapter_exists("input_chapters", "Chapter_1", 1, "r_comp", "Text B") # Default name
        self._assert_chapter_exists("input_chapters", "EndName", 2, "r_comp", "Text C")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
