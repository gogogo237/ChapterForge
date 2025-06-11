import os
import shutil

class FileMoverLogic:
    def get_folder_contents(self, source_folder_path, dest_folder_path):
        '''
        Lists files in the source folder and immediate subdirectories in the destination folder.
        Returns a dictionary with 'source_files', 'dest_subfolders', and 'error_message'.
        '''
        source_files = []
        dest_subfolders = []
        error_message = None

        if not source_folder_path or not os.path.isdir(source_folder_path):
            error_message = "Invalid or missing source folder path."
            return {'source_files': [], 'dest_subfolders': [], 'error_message': error_message}
        
        try:
            for item in os.listdir(source_folder_path):
                if os.path.isfile(os.path.join(source_folder_path, item)):
                    source_files.append(item)
            source_files.sort() 
        except Exception as e:
            error_message = f"Error reading source folder: {e}"
            return {'source_files': [], 'dest_subfolders': [], 'error_message': error_message}

        if not dest_folder_path or not os.path.isdir(dest_folder_path):
            error_message = "Invalid or missing main destination folder path."
            return {'source_files': source_files, 'dest_subfolders': [], 'error_message': error_message}

        try:
            for item in os.listdir(dest_folder_path):
                if os.path.isdir(os.path.join(dest_folder_path, item)):
                    dest_subfolders.append(item)
            dest_subfolders.sort()
        except Exception as e:
            error_message = f"Error reading destination folder: {e}"
            return {'source_files': source_files, 'dest_subfolders': [], 'error_message': error_message}
            
        return {'source_files': source_files, 'dest_subfolders': dest_subfolders, 'error_message': error_message}

    def move_files_to_folders(self, ordered_source_files_with_paths, ordered_dest_subfolders_with_paths):
        '''
        Moves source files to their corresponding destination subfolders.
        Assumes lists are of the same length and in the desired order.
        Returns a list of status messages.
        '''
        results = []
        if len(ordered_source_files_with_paths) != len(ordered_dest_subfolders_with_paths):
            results.append({'file': 'N/A', 'status': 'Error', 'message': 'Mismatch between number of source files and destination folders.'})
            return results

        for i in range(len(ordered_source_files_with_paths)):
            source_file_full_path = ordered_source_files_with_paths[i]
            dest_subfolder_full_path = ordered_dest_subfolders_with_paths[i]
            
            source_filename = os.path.basename(source_file_full_path)
            dest_folder_name = os.path.basename(dest_subfolder_full_path)

            try:
                if not os.path.exists(source_file_full_path):
                    results.append({'file': source_filename, 'status': 'Error', 'message': f"Source file not found: {source_file_full_path}"})
                    continue
                if not os.path.isdir(dest_subfolder_full_path):
                    results.append({'file': source_filename, 'status': 'Error', 'message': f"Destination folder not found: {dest_subfolder_full_path}"})
                    continue

                final_dest_path = os.path.join(dest_subfolder_full_path, source_filename)
                
                if os.path.exists(final_dest_path):
                    results.append({'file': source_filename, 
                                    'status': 'Error', 
                                    'message': f"File '{source_filename}' already exists in destination '{dest_folder_name}'."})
                    continue

                shutil.move(source_file_full_path, final_dest_path)
                results.append({'file': source_filename, 'status': 'Success', 'message': f"Moved to '{dest_folder_name}'."})
            except Exception as e:
                results.append({'file': source_filename, 'status': 'Error', 'message': f"Failed to move to '{dest_folder_name}': {e}"})
        
        return results

if __name__ == '__main__':
    # This block is for standalone testing of file_mover.py
    # It will not be executed when imported by app_gui.py
    print("Running file_mover.py standalone for testing...")
    logic = FileMoverLogic()
    
    # Setup dummy directories and files
    test_root = "_test_fm_temp"
    source_folder = os.path.join(test_root, "test_source_folder")
    dest_folder = os.path.join(test_root, "test_dest_folder")
    sub1 = os.path.join(dest_folder, "sub1_alpha") # Use sorted names
    sub2 = os.path.join(dest_folder, "sub2_beta")

    if os.path.exists(test_root): shutil.rmtree(test_root)
    os.makedirs(source_folder)
    os.makedirs(sub1)
    os.makedirs(sub2)
    
    with open(os.path.join(source_folder, "fileA.txt"), "w") as f: f.write("fileA content")
    with open(os.path.join(source_folder, "fileB.txt"), "w") as f: f.write("fileB content")
    with open(os.path.join(source_folder, "fileC.txt"), "w") as f: f.write("fileC content") # Extra file initially

    print("\n--- Testing get_folder_contents ---")
    contents = logic.get_folder_contents(source_folder, dest_folder)
    print(f"Source Files: {contents['source_files']}") # Expected: ['fileA.txt', 'fileB.txt', 'fileC.txt']
    print(f"Dest Subfolders: {contents['dest_subfolders']}") # Expected: ['sub1_alpha', 'sub2_beta']
    print(f"Error: {contents['error_message']}")
    
    # Test with one file removed to match subfolder count for move operation
    os.remove(os.path.join(source_folder, "fileC.txt"))
    print("\n--- Testing move_files_to_folders (after removing fileC.txt) ---")
    
    # Re-fetch contents to reflect the change
    contents_after_remove = logic.get_folder_contents(source_folder, dest_folder)
    print(f"Source Files (after remove): {contents_after_remove['source_files']}")


    source_file_paths_for_move = [
        os.path.join(source_folder, contents_after_remove['source_files'][0]), # Should be fileA.txt
        os.path.join(source_folder, contents_after_remove['source_files'][1])  # Should be fileB.txt
    ]
    dest_subfolder_paths_for_move = [
        os.path.join(dest_folder, contents_after_remove['dest_subfolders'][0]), # Should be sub1_alpha
        os.path.join(dest_folder, contents_after_remove['dest_subfolders'][1])  # Should be sub2_beta
    ]

    move_results = logic.move_files_to_folders(source_file_paths_for_move, dest_subfolder_paths_for_move)
    print("Move Results:")
    for res in move_results:
        print(f"  File: {res['file']}, Status: {res['status']}, Message: {res['message']}")

    # Verify files are moved
    print("\nVerifying file locations after move:")
    print(f"File A in sub1_alpha: {os.path.exists(os.path.join(sub1, 'fileA.txt'))}")
    print(f"File B in sub2_beta: {os.path.exists(os.path.join(sub2, 'fileB.txt'))}")
    print(f"File A still in source: {os.path.exists(os.path.join(source_folder, 'fileA.txt'))}")
    print(f"File B still in source: {os.path.exists(os.path.join(source_folder, 'fileB.txt'))}")

    # Test conflict
    print("\n--- Testing move_files_to_folders (with conflict) ---")
    # Recreate fileA in source and in sub1_alpha to test conflict
    with open(os.path.join(source_folder, "fileA.txt"), "w") as f: f.write("fileA content - new")
    with open(os.path.join(sub1, "fileA.txt"), "w") as f: f.write("fileA content - existing in dest")

    source_conflict_paths = [os.path.join(source_folder, "fileA.txt")]
    dest_conflict_paths = [os.path.join(dest_folder, "sub1_alpha")]
    
    conflict_results = logic.move_files_to_folders(source_conflict_paths, dest_conflict_paths)
    print("Conflict Move Results:")
    for res in conflict_results:
        print(f"  File: {res['file']}, Status: {res['status']}, Message: {res['message']}")


    # Clean up
    print("\nCleaning up test directory...")
    shutil.rmtree(test_root)
    print(f"Removed {test_root}")
