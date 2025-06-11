import unittest
import os
import shutil
import tempfile
from file_processor import FileProcessor

class TestFileProcessorSplitFileStrict(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.fp = FileProcessor(log_callback=print) # Using print for test debug visibility
        # self.fp = FileProcessor(log_callback=lambda x: None)


    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def _create_input_file(self, filename="input.txt", content=""):
        filepath = os.path.join(self.test_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return filepath

    def _assert_chapter_exists(self, base_output_folder_name, chapter_folder_name, chapter_filename_num, suffix, expected_content):
        base_output_path = os.path.join(self.test_dir, base_output_folder_name)
        chapter_folder_path = os.path.join(base_output_path, chapter_folder_name)
        self.assertTrue(os.path.isdir(chapter_folder_path),
                        f"Chapter folder '{chapter_folder_name}' not found in '{base_output_path}'. Found: {os.listdir(base_output_path) if os.path.exists(base_output_path) else 'None'}")

        chapter_filename = f"{chapter_filename_num}_{suffix}.txt" # Filename uses its own sequential counter
        chapter_filepath = os.path.join(chapter_folder_path, chapter_filename)
        self.assertTrue(os.path.isfile(chapter_filepath), f"Chapter file '{chapter_filepath}' not found.")

        with open(chapter_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertEqual(content, expected_content, f"Content mismatch for chapter file {chapter_filename} in folder {chapter_folder_name}")

    # --- VALID STRUCTURE TESTS (Focus on numbering changes) ---
    def test_valid_single_chapter_no_name(self):
        content = "This is chapter one.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        # Folder: Chapter_1 (from default_naming_sequence_counter starting at 1)
        # File: 1_test.txt (from filename_id_counter starting at 1)
        self._assert_chapter_exists("input_chapters", "Chapter_1", 1, "test", "This is chapter one.")

    def test_valid_single_chapter_with_name(self):
        content = "This is chapter one.DELIM(ChapterAlpha)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        # Folder: ChapterAlpha (custom)
        # File: 1_test.txt (filename_id_counter starts at 1)
        # default_naming_sequence_counter remains at 1 (not used)
        self._assert_chapter_exists("input_chapters", "ChapterAlpha", 1, "test", "This is chapter one.")

    def test_valid_multiple_chapters_mixed_names_regex_mode(self):
        content = "Content Alpha===SEP(Name1)Content Beta===SEPContent Gamma===SEP(Name3)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "regex", "===SEP", 0, "mix") # start_number = 0

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        # Chapter 1: Custom Name "Name1", File ID 0
        #   filename_id_counter becomes 1
        #   default_naming_sequence_counter remains 0
        self._assert_chapter_exists("input_chapters", "Name1", 0, "mix", "Content Alpha")

        # Chapter 2: Default Name "Chapter_0", File ID 1
        #   filename_id_counter becomes 2
        #   default_naming_sequence_counter becomes 1 (used 0)
        self._assert_chapter_exists("input_chapters", "Chapter_0", 1, "mix", "Content Beta")

        # Chapter 3: Custom Name "Name3", File ID 2
        #   filename_id_counter becomes 3
        #   default_naming_sequence_counter remains 1
        self._assert_chapter_exists("input_chapters", "Name3", 2, "mix", "Content Gamma")

    def test_user_scenario_prologue_then_sequential_chapters(self):
        content = "This is the Prologue.DELIM(Prologue)This is Chapter One Content.DELIMThis is Chapter Two Content.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "user") # start_number = 1

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)

        # Expected:
        # 1. Folder "Prologue", File "1_user.txt" (Content: "This is the Prologue.")
        #    filename_id_counter becomes 2. default_naming_sequence_counter remains 1.
        self._assert_chapter_exists("input_chapters", "Prologue", 1, "user", "This is the Prologue.")

        # 2. Folder "Chapter_1", File "2_user.txt" (Content: "This is Chapter One Content.")
        #    filename_id_counter becomes 3. default_naming_sequence_counter becomes 2 (used 1).
        self._assert_chapter_exists("input_chapters", "Chapter_1", 2, "user", "This is Chapter One Content.")

        # 3. Folder "Chapter_2", File "3_user.txt" (Content: "This is Chapter Two Content.")
        #    filename_id_counter becomes 4. default_naming_sequence_counter becomes 3 (used 2).
        self._assert_chapter_exists("input_chapters", "Chapter_2", 3, "user", "This is Chapter Two Content.")

    def test_valid_content_with_empty_custom_name_parentheses(self):
        # DELIM() means use default name
        content = "Data.SPLIT()More Data.SPLIT(Final)"
        input_file = self._create_input_file(content=content)
        # start_number = 10
        # File IDs: 10, 11
        # Default Name IDs: 10 (used for first chapter), then 11 (not used)
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 10, "test")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)
        self._assert_chapter_exists("input_chapters", "Chapter_10", 10, "test", "Data.")
        self._assert_chapter_exists("input_chapters", "Final", 11, "test", "More Data.")


    # --- ERROR CONDITION TESTS (Should largely remain unchanged by numbering logic) ---
    def test_error_empty_input_file(self):
        input_file = self._create_input_file(content="")
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_whitespace_only_input_file(self):
        input_file = self._create_input_file(content="""
	   """) # Whitespace only
        chapter_paths = self.fp.split_file(input_file, "string", "SPLIT", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_starts_with_delimiter(self):
        content = "DELIMText after first delimiter.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_starts_with_delimiter_and_name(self):
        content = "DELIM(StartName)Text after first delimiter.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_not_ending_with_delimiter(self):
        content = "Text segment 1.DELIMText segment 2"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_no_delimiter_at_all_just_text(self):
        content = "This is a single block of text without any delimiters."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "NOT_FOUND_DELIMITER", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_empty_text_segment_between_delimiters(self):
        content = "Text 1.DELIMDELIM(WithName)Text 2.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_empty_text_segment_leading_to_empty_custom_name(self):
        content = "Text 1.DELIM(Name1)DELIM()Text 2.DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_only_delimiter(self):
        content = "DELIM"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_only_delimiter_with_name(self):
        content = "DELIM(ChapterName)"
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_error_text_after_final_delimiter(self):
        content = "Text1.DELIMText after what should be final delimiter."
        input_file = self._create_input_file(content=content)
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 1, "test")
        self.assertIsNone(chapter_paths)

    def test_valid_sanitized_folder_names_strict(self):
        content = "Content with bad:name.DELIM(Chapter: The Forbidden <Name>?)"
        input_file = self._create_input_file(content=content)
        # File ID: 0. Default Name ID: 0 (not used).
        chapter_paths = self.fp.split_file(input_file, "string", "DELIM", 0, "sanitize")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 1)
        self._assert_chapter_exists("input_chapters", "Chapter_ The Forbidden _Name__", 0, "sanitize", "Content with bad:name.")

    def test_valid_delimiter_with_regex_chars_string_mode(self):
        content = "Chapter 1.DATA*.(Name1)Chapter 2.DATA*."
        input_file = self._create_input_file(content=content)
        # start_number = 1
        # Ch1: Name1, FileID 1. DefaultNameID remains 1.
        # Ch2: Chapter_1, FileID 2. DefaultNameID becomes 2.
        chapter_paths = self.fp.split_file(input_file, "string", ".DATA*.", 1, "s_esc")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 2)
        self._assert_chapter_exists("input_chapters", "Name1", 1, "s_esc", "Chapter 1")
        self._assert_chapter_exists("input_chapters", "Chapter_1", 2, "s_esc", "Chapter 2")

    def test_valid_complex_regex_delimiter_regex_mode(self):
        content = r"Text A123SEP(NumName)Text B45SEPText C789SEP(EndName)"
        input_file = self._create_input_file(content=content)
        # start_number = 0
        # Ch1: NumName, FileID 0. DefaultNameID remains 0.
        # Ch2: Chapter_0, FileID 1. DefaultNameID becomes 1.
        # Ch3: EndName, FileID 2. DefaultNameID remains 1.
        chapter_paths = self.fp.split_file(input_file, "regex", r"\d+SEP", 0, "r_comp")

        self.assertIsNotNone(chapter_paths)
        self.assertEqual(len(chapter_paths), 3)
        self._assert_chapter_exists("input_chapters", "NumName", 0, "r_comp", "Text A")
        self._assert_chapter_exists("input_chapters", "Chapter_0", 1, "r_comp", "Text B")
        self._assert_chapter_exists("input_chapters", "EndName", 2, "r_comp", "Text C")

if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
