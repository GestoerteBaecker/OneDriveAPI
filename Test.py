from OneDrive_API import *

def main():
    with open("Settings.json", encoding="utf-8") as file:
        settings = json.load(file)

    try:
        # Initialize
        onedrive = OneDrive(settings)

        # Fetching
        onedrive_path = "Test/download_test/"
        found_files, found_folders = onedrive.FetchAllFiles(onedrive_path)
        print("Found files in " + onedrive_path + ":", list(found_files.keys()))
        print("Found folders in " + onedrive_path + ":", list(found_folders.keys()))

        # Downloading files (all available files in 'onedrive_path')
        onedrive_path = "Test/download_test"
        local_path = "download_test"
        onedrive.Download(onedrive_path, local_path)

        # Uploading files
        files = os.listdir("upload_test")
        files = ["upload_test/" + file for file in files]
        onedrive_path = "Test/upload_test"
        onedrive.Upload(files, onedrive_path)

        # Creating directories
        onedrive_path = "Test/"
        new_foldername = "move_test"
        onedrive.MakeDir(onedrive_path,
                         new_foldername)  # Note: Creating a none existent folder 'move_test' before moving files to it is not necessary. The folder is created on the fly

        # Moving files
        onedrive_path_dest = "Test/move_test"
        onedrive_path_src = "Test/download_test/"
        onedrive.MoveAllFiles(onedrive_path_dest, onedrive_path_src)

        return 0

    except Exception as ex:
        print(ex)
        return -1

if __name__ == "__main__":
    main()