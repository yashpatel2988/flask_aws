import requests
import zipfile
import os
import time

class mysq:
    def __init__(self):
        self.BASE_URL = str("https://api-009.bhatol.in")

        # client
        upload_path = "upload"
        download_path = "download"

        # admin
        admin_upload_path = "admin_upload"
        admin_download_path = "admin_download"

        print("[1] UPLOAD")
        print("[2] DOWNLOAD")
        print("[3] EXIT")
        print("[4] Admin Mode")
        user_input = int(input("SELECT CHOICE: "))

        if user_input == 1:
            self.upload(upload_path)
        elif user_input == 2:
            self.download(download_path)
        elif user_input == 4:
            self.BASE_URL = self.BASE_URL + "/admin"

            while True:
                print("\n\n-----------------------------------------------")
                print("\t\t ADMIN MODE")
                print("-----------------------------------------------")
                print("\n|------\t|---------------------------------------|")
                print("|CHOICE\t| \t\tOPTION\t\t\t|")
                print("|------\t|---------------------------------------|")
                print("|  [1] \t| UPLOAD FILES FROM ADMIN_UPLOAD\t|")
                print("|  [2] \t| DOWNLOAD FILES TO ADMIN_DOWNLOAD\t|")
                print("|  [3] \t| FORCE DELETE SEND FOLDER\t\t|")
                print("|  [4] \t| FROCE DELETE RECIVE FOLDER\t\t|")
                print("|  [5] \t| FROCE DELETE TEMP FOLDER\t\t|")
                print("|  [6] \t| SIMULATE CLIENT UPLOAD \t\t|")
                print("|  [7] \t| SIMULATE CLIENT DOWNLOAD\t\t|")
                print("|  [0] \t| EXIT \t\t\t\t\t|")
                print("|------\t|---------------------------------------|\n")

                user_input = int(input("Enter Choice: "))

                if user_input == 0:
                    break
                elif user_input == 1:
                    self.upload(admin_upload_path)
                elif user_input == 2:
                    self.download(admin_download_path)
                elif user_input == 3:
                    self.force_delete_send()
                elif user_input == 4:
                    self.force_delete_recived()
                elif user_input == 5:
                    self.force_delete_temp()
                elif user_input == 6:
                    self.upload(upload_path)
                elif user_input == 7:
                    self.download(download_path)
                else:
                    continue

                time.sleep(2)


        else:
            exit()

    def __upload_to_server(self, file_path):

        upload_url = self.BASE_URL + '/upload'  # Update with your API URL

        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(upload_url, files=files)
        print(response.json())

    def create_zip_entire_folder(self, folder_path, output_zip_path):
        """
        Compresses a folder and its subdirectories into a ZIP file.

        Parameters:
        - folder_path (str): The path to the folder to be compressed.
        - output_zip_path (str): The path for the output ZIP file.

        Returns:
        - None
        """
        with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Calculate the relative path for the file within the ZIP file
                    relative_path = os.path.relpath(file_path, os.path.dirname(folder_path))
                    zipf.write(file_path, relative_path)
        return None

    def upload(self, upload_path):
        # variables
        temp_folder = 'temp'

        # creating folders
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)
        if not os.path.exists(upload_path):
            os.mkdir(upload_path)

        # compressing to zip file
        zip_location = os.path.join(temp_folder, "send.zip")
        self.create_zip_entire_folder(upload_path + "/", zip_location)

        # uplod zip file to server
        self.__upload_to_server(zip_location)

        # removing zip_file, temp folder
        try:
            os.remove(zip_location)
            os.rmdir(temp_folder)
        except:
            print("unable to  remove temporary files")

    def download(self, download_path):
        output_dir = download_path
        temp_folder = "temp"
        
        ## creating temp folder
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        if not os.path.exists(temp_folder):
            os.mkdir(temp_folder)

        # downloading zip to temp folder
        zip_location = os.path.join(temp_folder, "download.zip")
        response = requests.get(f'{self.BASE_URL}/download')
        with open(zip_location, 'wb') as f:
            f.write(response.content)

        ## extractig zip to output folder
        with zipfile.ZipFile(zip_location, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        ## removing temp file and zip file
        try:
            os.remove(zip_location)
            os.removedirs(temp_folder)
        except:
            pass

        print("DOWNLOAD SUCCESS")

    ## admin 
    
    def force_delete_recived(self):
        response = requests.get(f'{self.BASE_URL}/clean/download_location')
        print(response.json())

    def force_delete_send(self):
        response = requests.get(f'{self.BASE_URL}/clean/upload_location')
        print(response.json())

    def force_delete_temp(self):
        response = requests.get(f'{self.BASE_URL}/clean/temp')
        print(response.json())

mysq = mysq()