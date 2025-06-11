import unittest
import os
import shutil
import tempfile
from file_processor import FileProcessor

class TestFileProcessorSplitFileStrict(unittest.TestCase): # Renaming slightly for clarity if we add another class

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.fp = FileProcessor(log_callback=print)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_input_file(self, filename="input.txt", content=""):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    # MODIFIED HELPER: chapter_filename_num argument is removed, filename based on chapter_folder_name
    def _assert_chapter_exists(self, base_output_folder_name, chapter_folder_name, suffix, expected_content):
        base_output_path = os.path.join(self.test_dir, base_output_folder_name)
        chapter_folder_path = os.path.join(base_output_path, chapter_folder_name)
        self.assertTrue(os.path.isdir(chapter_folder_path),
                        f"Chapter folder '{chapter_folder_name}' not found in '{base_output_path}'. Found: {os.listdir(base_output_path) if os.path.exists(base_output_path) else 'None'}")

        # Filename is now based on the folder name itself
        chapter_filename = f"{chapter_folder_name}_{suffix}.txt"
        chapter_filepath = os.path.join(chapter_folder_path, chapter_filename)
        self.assertTrue(os.path.isfile(chapter_filepath), f"Chapter file '{chapter_filepath}' not found.")

        with open(chapter_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, expected_content, f"Content mismatch for chapter file {chapter_filename} in folder {chapter_folder_name}")

    # --- VALID STRUCTURE TESTS (split_file) ---
    def test_valid_single_chapter_no_name(self):
        content = "This is chapter one.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        # Folder "Chapter_1", File "Chapter_1_test.txt"
        self._assert_chapter_exists("input_chapters", "Chapter_1", "test", "This is chapter one.")

    def test_valid_single_chapter_with_name(self):
        content = "This is chapter one.DELIM(ChapterAlpha)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        # Folder "ChapterAlpha", File "ChapterAlpha_test.txt"
        self._assert_chapter_exists("input_chapters", "ChapterAlpha", "test", "This is chapter one.")

    def test_valid_multiple_chapters_mixed_names_regex_mode(self):
        content = "Content Alpha===SEP(Name1)Content Beta===SEPContent Gamma===SEP(Name3)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "regex", "===SEP", 0, "mix")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        self._assert_chapter_exists("input_chapters", "Name1", "mix", "Content Alpha")
        self._assert_chapter_exists("input_chapters", "Chapter_0", "mix", "Content Beta")
        self._assert_chapter_exists("input_chapters", "Name3", "mix", "Content Gamma")

    def test_user_scenario_prologue_then_sequential_chapters(self):
        content = "This is the Prologue.DELIM(Prologue)This is Chapter One Content.DELIMThis is Chapter Two Content.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "user")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        self._assert_chapter_exists("input_chapters", "Prologue", "user", "This is the Prologue.")
        self._assert_chapter_exists("input_chapters", "Chapter_1", "user", "This is Chapter One Content.")
        self._assert_chapter_exists("input_chapters", "Chapter_2", "user", "This is Chapter Two Content.")

    def test_valid_content_with_empty_custom_name_parentheses(self):
        content = "Data.SPLIT()More Data.SPLIT(Final)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 10, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)
        self._assert_chapter_exists("input_chapters", "Chapter_10", "test", "Data.")
        self._assert_chapter_exists("input_chapters", "Final", "test", "More Data.")

    # Error condition tests remain the same as they check for None or specific error logs,
    # not specific file paths usually.
    def test_error_empty_input_file(self):
        input_file = self._create_input_file(content="")
        self.assertIsNone(self.fp.split_file(input_file, "string", "SPLIT", 1, "test"))

    def test_error_whitespace_only_input_file(self):
        input_file = self._create_input_file(content="""
	   """) # Whitespace only
        self.assertIsNone(self.fp.split_file(input_file, "string", "SPLIT", 1, "test"))

    def test_error_starts_with_delimiter(self):
        content = "DELIMText after first delimiter.DELIM"
        input_file = self._create_input_file(content=content)
        self.assertIsNone(self.fp.split_file(input_file, "string", "DELIM", 1, "test"))

    def test_error_not_ending_with_delimiter(self):
        content = "Text segment 1.DELIMText segment 2"
        input_file = self._create_input_file(content=content)
        self.assertIsNone(self.fp.split_file(input_file, "string", "DELIM", 1, "test"))

    def test_error_no_delimiter_at_all_just_text(self):
        content = "This is a single block of text"
        input_file = self._create_input_file(content=content)
        self.assertIsNone(self.fp.split_file(input_file, "string", "DELIM", 1, "test"))

    def test_error_empty_text_segment_between_delimiters(self):
        content = "Text 1.DELIMDELIM(WithName)Text 2.DELIM"
        input_file = self._create_input_file(content=content)
        self.assertIsNone(self.fp.split_file(input_file, "string", "DELIM", 1, "test"))

    def test_error_only_delimiter(self):
        content = "DELIM"
        input_file = self._create_input_file(content=content)
        self.assertIsNone(self.fp.split_file(input_file, "string", "DELIM", 1, "test"))

    def test_valid_sanitized_folder_names_strict(self):
        content = "Content with bad:name.DELIM(Chapter: The Forbidden <Name>?)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 0, "sanitize")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        # Expected sanitized folder name: "Chapter_ The Forbidden _Name__"
        # File: "Chapter_ The Forbidden _Name___sanitize.txt"
        self._assert_chapter_exists("input_chapters", "Chapter_ The Forbidden _Name__", "sanitize", "Content with bad:name.")

    def test_valid_delimiter_with_regex_chars_string_mode(self):
        content = "Chapter 1.DATA*.(Name1)Chapter 2.DATA*."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", ".DATA*.", 1, "s_esc")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)
        self._assert_chapter_exists("input_chapters", "Name1", "s_esc", "Chapter 1")
        self._assert_chapter_exists("input_chapters", "Chapter_1", "s_esc", "Chapter 2")

    def test_valid_complex_regex_delimiter_regex_mode(self):
        content = r"Text A123SEP(NumName)Text B45SEPText C789SEP(EndName)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "regex", r"\d+SEP", 0, "r_comp")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        self._assert_chapter_exists("input_chapters", "NumName", "r_comp", "Text A")
        self._assert_chapter_exists("input_chapters", "Chapter_0", "r_comp", "Text B")
        self._assert_chapter_exists("input_chapters", "EndName", "r_comp", "Text C")

# New Test Class for duplicate_and_modify_chapters
class TestFileProcessorDuplicateAndModify(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.fp = FileProcessor(log_callback=print)
        self.input_chapters_base = os.path.join(self.test_dir, "input_chapters") # Base for chapters created by split_file

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _assert_file_exists(self, chapter_folder_path, filename_no_ext, suffix, expected_content=None):
        filepath = os.path.join(chapter_folder_path, f"{filename_no_ext}{suffix}") # suffix includes dot, e.g. ".txt" or "_wrapped.txt"
        self.assertTrue(os.path.isfile(filepath), f"File not found: {filepath}")
        if expected_content is not None:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            self.assertEqual(content, expected_content)

    def test_duplicate_and_modify_with_new_filenames(self):
        # 1. Setup: Create some chapter files using split_file (which now uses new naming)
        orig_suffix = "orig"
        content = "Prologue Content.DELIM(Prologue)Chapter 1 Content.DELIM"
        input_file = os.path.join(self.test_dir, "test_input.txt")
        with open(input_file, 'w') as f: f.write(content)

        # These paths will be like ".../input_chapters/Prologue/Prologue_orig.txt", ".../input_chapters/Chapter_1/Chapter_1_orig.txt"
        chapter_paths_from_split = self.fp.split_file(input_file, "string", "DELIM", 1, orig_suffix)
        self.assertIsNotNone(chapter_paths_from_split)
        self.assertEqual(len(chapter_paths_from_split), 2)

        # 2. Call duplicate_and_modify_chapters
        text_to_add = "POST_TEXT"
        empty_suffix = "empty" # This is the empty_file_suffix_text for the function
        self.fp.duplicate_and_modify_chapters(chapter_paths_from_split, text_to_add, empty_suffix)

        # 3. Assertions
        # Determine the actual base output folder from one of the created chapter paths
        # e.g. /path/to/temp/test_dir/test_input_chapters/Prologue/Prologue_orig.txt
        # os.path.dirname() twice gets /path/to/temp/test_dir/test_input_chapters
        actual_chapters_base_folder = os.path.dirname(os.path.dirname(chapter_paths_from_split[0]))

        # For "Prologue"
        prologue_folder_path = os.path.join(actual_chapters_base_folder, "Prologue")
        self.assertTrue(os.path.isdir(prologue_folder_path), f"Prologue folder not found at {prologue_folder_path}")
        # Wrapped: Prologue_orig_wrapped.txt
        self._assert_file_exists(prologue_folder_path, "Prologue_orig", "_wrapped.txt", f"```\nPrologue Content.\n```\n{text_to_add}")
        # Empty: Prologue_empty.txt
        self._assert_file_exists(prologue_folder_path, "Prologue", f"_{empty_suffix}.txt", "") # Empty content

        # For "Chapter_1"
        chapter_1_folder_path = os.path.join(actual_chapters_base_folder, "Chapter_1")
        self.assertTrue(os.path.isdir(chapter_1_folder_path), f"Chapter_1 folder not found at {chapter_1_folder_path}")
        # Wrapped: Chapter_1_orig_wrapped.txt
        self._assert_file_exists(chapter_1_folder_path, "Chapter_1_orig", "_wrapped.txt", f"```\nChapter 1 Content.\n```\n{text_to_add}")
        # Empty: Chapter_1_empty.txt
        self._assert_file_exists(chapter_1_folder_path, "Chapter_1", f"_{empty_suffix}.txt", "")

    def test_duplicate_and_modify_filename_without_assumed_suffix(self):
        # Test case where the input filename to duplicate_and_modify might not end with "_orig"
        # Create a dummy chapter file manually that doesn't end with _orig
        custom_folder_path = os.path.join(self.test_dir, "MyManualChapter")
        os.makedirs(custom_folder_path, exist_ok=True)
        manual_chapter_filename_no_ext = "MyFileWithoutOrig"
        manual_chapter_filepath = os.path.join(custom_folder_path, f"{manual_chapter_filename_no_ext}.txt")
        manual_content = "Manual file content."
        with open(manual_chapter_filepath, 'w') as f: f.write(manual_content)

        chapter_paths = [manual_chapter_filepath]
        text_to_add = "AppendedText"
        empty_suffix_text = "alt_empty"
        self.fp.duplicate_and_modify_chapters(chapter_paths, text_to_add, empty_suffix_text)

        # Wrapped file should be MyFileWithoutOrig_wrapped.txt
        self._assert_file_exists(custom_folder_path, manual_chapter_filename_no_ext, "_wrapped.txt", f"```\n{manual_content}\n```\n{text_to_add}")
        # Empty file should use full MyFileWithoutOrig as stem because "_orig" was not found
        self._assert_file_exists(custom_folder_path, manual_chapter_filename_no_ext, f"_{empty_suffix_text}.txt", "")


if __name__ == '__main__':
    # This allows running tests from both classes if this file is executed directly
    # However, typically tests are run by a test runner discovering them.
    # For simplicity here, just running the first class's tests if run directly.
    # A proper runner would find both TestFileProcessorSplitFileStrict and TestFileProcessorDuplicateAndModify
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestFileProcessorSplitFileStrict))
    suite.addTest(unittest.makeSuite(TestFileProcessorDuplicateAndModify))
    runner = unittest.TextTestRunner()
    runner.run(suite)
