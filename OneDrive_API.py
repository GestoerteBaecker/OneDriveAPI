from datetime import datetime
import json
import os
import requests
from threading import Thread, Lock
import time
from typing import Any, Type


class OneDrive:


    def __init__(self, connection_parameters: dict) -> None:
        """
        Constructor.
        :param connection_parameters: Holds all parameters necessary for connecting to OneDrive
        """
        # the following variables are set with a settings file
        self.mutex = Lock() # mutex
        self.threads = [] # here the running threads are saved
        self.max_threads: int = 0 # maximum number of threads used for communicating to OneDrive
        self.refresh_token: str = "" # used for granting a new access token
        self.url: str = "" # browse URL of OneDrive
        self.auth_url: str = "" # authentication URL
        self.client_id: str = "" # ID if the registered application
        self.permissions: list = [] # permissions as str
        self.redirect_uri: str = "" # redirect URL
        self.scope = '' # holds the permissions
        self.refresh_interval: int = 0 # interval (in seconds) after which the API connection has to be refreshed
        self.number_retry_connection: int = 0 # number of retrys to be executed to connect to the API

        # the following variables are dependent on the previous ones or are derived from them
        self.token: str = "" # actual token
        self.last_updated: float = 0.0 # timestamp since last connection check
        self.headers: dict = dict() # holds the token
        self.errors: list = [] # error descriptions
        self.is_connected = False # specifies if a connection to OneDrive is available

        self._SetParameters(connection_parameters)
        self._CheckConnected()


    def __del__(self) -> None:
        """
        Destructor. Ensures all running threads are joined.
        """
        self._JoinThreads()


    def _SetsAndChecksVariable(self, parameters: dict, var: str, var_type: Type, member_var_name: str) -> None:
        """
        Checks if the given variable is of the given type and sets the specified member variable to the value of var if it is True.
        :param parameters: Holds all available parameters.
        :param var: The key of 'parameters' to get the variable to check.
        :param var_type: The type to check against.
        :param member_var_name: The name of the member variable to set.
        """
        if not var in parameters.keys():
            raise Exception("The variable \"" + var + "\" is not given in the settings-json-file.")
        if isinstance(parameters[var], var_type):
            setattr(self, member_var_name, parameters[var])
            return None
        raise Exception("The variable \"" + var + "\" did not match the specified data type")


    def _SetsAndChecksVariableWithDefaultValue(self, parameters: dict, var: str, default_value: Any, var_type: Type, member_var_name: str) -> None:
        """
        Checks if the given variable is of the given type and sets the specified member variable to the value of var if it is True. Sets the default value, if the key is not given.
        :param parameters: Holds all available parameters.
        :param var: The key of 'parameters' to get the variable to check.
        :param default_value: The default value to set, when the key is not given in 'parameters'
        :param var_type: The type to check against.
        :param member_var_name: The name of the member variable to set.
        """
        try:
            self._SetsAndChecksVariable(parameters, var, var_type, member_var_name)
        except:
            setattr(self, member_var_name, default_value)


    def _SetParameters(self, parameters: dict) -> None:
        """
        Sets all parameters necessary for connecting to OneDrive
        :param parameters: holds all parameters
        """
        try:
            self._SetsAndChecksVariable(parameters, "max_threads", int, "max_threads")
            self._SetsAndChecksVariable(parameters, "refresh_token", str, "refresh_token")
            self._SetsAndChecksVariable(parameters, "browse_url", str, "url")
            self._SetsAndChecksVariable(parameters, "auth_url", str, "auth_url")
            self._SetsAndChecksVariable(parameters, "client_id", str, "client_id")
            self._SetsAndChecksVariable(parameters, "permissions", list, "permissions")
            self._SetsAndChecksVariable(parameters, "redirect_uri", str, "redirect_uri")

            self._SetsAndChecksVariableWithDefaultValue(parameters, "refresh_interval", 3600, int, "refresh_interval")
            self._SetsAndChecksVariableWithDefaultValue(parameters, "number_retry_connection", 50, int, "number_retry_connection")

            self.scope = ''
            for items in range(len(self.permissions)):
                self.scope = self.scope + self.permissions[items]
                if items < len(self.permissions) - 1:
                    self.scope = self.scope + '+'
        except Exception as ex:
            raise Exception("Could not initialize parameters: " + str(ex))


    def _SaveRequest(func: callable) -> callable:
        """
        Decorator for all functions usable in public scope.
        """
        def Wrapper(*args, **kw):
            try:
                return func(*args, **kw)
            except Exception as ex:
                if str(ex) == "":
                    raise Exception("Unknown exception. Check internet connection")
                raise ex
        return Wrapper


    @_SaveRequest
    def _Connect(self) -> None:
        """
        Connects to the OneDriveAPI
        """
        self._RefreshToken()
        response = requests.get(self.url + 'me/drive/', headers=self.headers)
        if response.status_code == 200:
            self.is_connected = True
        else:
            self.is_connected = False


    @_SaveRequest
    def _RefreshToken(self) -> None:
        """
        Acquires a new access token.
        """
        data = {
            "client_id": self.client_id,
            "scope": self.permissions,
            "refresh_token": self.refresh_token,
            "redirect_uri": self.redirect_uri,
            "grant_type": 'refresh_token'
        }
        response = requests.post(self.auth_url, data=data)
        self.token = json.loads(response.text)["access_token"]
        self.refresh_token = json.loads(response.text)["refresh_token"]
        self.last_updated = time.mktime(datetime.today().timetuple())
        self.headers = {'Authorization': 'Bearer ' + self.token}


    def _CheckLastHeartbeat(self) -> None:
        """
        Checks if the connection has to be refreshed
        """
        now = time.mktime(datetime.today().timetuple())
        if now - self.last_updated > self.refresh_interval:
            self._RefreshToken()


    def _CheckConnected(self) -> None:
        """
        Checks if the connection to the API is active
        """
        attempts = 0
        if not self.is_connected:
            while not self.is_connected:
                attempts += 1
                if attempts == self.number_retry_connection:
                    raise Exception("Could not connect to OneDrive")
                self._Connect()
                time.sleep(0.5)
        self._CheckLastHeartbeat()
        self._CheckRequestsCompleted()


    def _CheckError(self, error_text: str, response: Any) -> bool:
        """
        Checks if an error occurred and saves the error
        :param error_text: Potential error message
        :param response: http-response to evaluate
        :return: True, if an error occurred
        """
        error_occurred = False
        if type(response).__name__ == "Response":
            error_occurred = not response.ok
        elif type(response).__name__ == "dict":
            for key in response:
                if "error" in key:
                    error_occurred = True
                    error_text = error_text + " (Code: " + response["error"]["code"] + ")"
        else:
            error_occurred = True
        if error_occurred:
            with self.mutex:
                self.errors.append(error_text)
        return error_occurred


    def _FetchErrors(self, prefix: str = "") -> None:
        """
        Fetches all error messages saved in 'CheckError'
        :param prefix: Prefix to be prepended to the error messages saved
        """
        with self.mutex:
            if len(self.errors) != 0:
                error_text = ". ".join(self.errors)
                self.errors = []
                error_text = prefix + error_text
                raise Exception(error_text)


    def _JoinThreads(self) -> None:
        """
        Joins all active threads
        """
        number_threads = len(self.threads)
        for i in range(number_threads):
            thread = self.threads[0]
            thread.join()
            self.threads.pop(0)


    def _CheckRequestsCompleted(self) -> None:
        """
        Lets the main thread wait, until all worker threads are completed
        """
        while len(self.threads) > 0:
            time.sleep(0.1)


    @_SaveRequest
    def _FetchFolderID(self, path_onedrive: str) -> str:
        """
        Fetches the OneDrive-ID of a specific folder
        :param path_onedrive: directory from which the OneDrive-ID shall be fetched (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :return: OneDrive-ID
        """
        self._CheckConnected()
        path_onedrive = path_onedrive.lstrip("/").rstrip("/")
        url = self.url + "me/drive/root:/" + path_onedrive + "/"
        response = json.loads(requests.get(url, headers=self.headers).text)
        error_message = "Could not fetch the folder ID of " + path_onedrive
        self._CheckError(error_message, response)
        self._FetchErrors()
        return response["id"]


    @_SaveRequest
    def FetchAllFiles(self, path_onedrive: str) -> tuple:
        """
        Fetches all files and folders of a specific folder in OneDrive
        :param path_onedrive: directory from which all files and folders are fetched (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :return: tuple: first element: dictionary of all files (key: filename, value: OneDrive-ID), second element: dictionary of all folders (key: foldername, value: OneDrive-ID)
        """
        self._CheckConnected()
        path_onedrive = path_onedrive.lstrip("/").rstrip("/")
        url = self.url + "me/drive/root:/" + path_onedrive + ":/children"
        response = json.loads(requests.get(url, headers=self.headers).text)
        results_files = dict()
        results_folder = dict()
        error_message = "Could not fetch all files from " + path_onedrive
        self._CheckError(error_message, response)
        self._FetchErrors()
        for item in response["value"]:
            if "folder" in item.keys():
                results_folder[item["name"]] = item["id"]
            else:
                results_files[item["name"]] = item["id"]
        return results_files, results_folder


    @_SaveRequest
    def MakeDir(self, path_onedrive: str, new_folder_name: str) -> None:
        """
        Creates a new directory
        :param path_onedrive: directory wherein a new folder shall be created (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :param new_folder_name: new folder name
        """
        self._CheckConnected()
        path_onedrive = path_onedrive.lstrip("/").rstrip("/")
        url = self.url + "me/drive/root:/" + path_onedrive + ":/children"
        body = {
            "name": new_folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }
        response = json.loads(requests.post(url, headers=self.headers, json=body).text)
        error_message = "Could not create the directory " + new_folder_name
        self._CheckError(error_message, response)
        self._FetchErrors()


    @_SaveRequest
    def MoveFile(self, dest_path_onedrive: str, src_path_onedrive: str, arg_filename: str) -> None:
        """
        Moves files between directorys in OneDrive
        :param dest_path_onedrive: directory to move the file to (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :param src_path_onedrive: directory where the file is located (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :param arg_filename: filename to be moved
        """
        self._CheckConnected()
        dest_path_onedrive = dest_path_onedrive.lstrip("/").rstrip("/")
        src_path_onedrive = src_path_onedrive.lstrip("/").rstrip("/")
        files_ids, _ = self.FetchAllFiles(src_path_onedrive)
        dest_path_id = self._FetchFolderID(dest_path_onedrive)
        for filename in files_ids:
            if filename == arg_filename:
                file_id = files_ids[filename]
                url = self.url + 'me/drive/items/' + file_id
                body = {
                    "parentReference": {
                        "id": dest_path_id
                    },
                }
                response = json.loads(requests.patch(url, headers=self.headers, json=body).text)
                error_message = "Could not move file " + src_path_onedrive
                self._CheckError(error_message, response)
                self._FetchErrors()
                return


    @_SaveRequest
    def MoveAllFiles(self, dest_path_onedrive: str, src_path_onedrive: str) -> None:
        """
        Moves all files of a given directory in OneDrive to another directory. E.g.: after calling MoveAllFiles("root/dest", "root/src") the folder structure is "root/dest/src" and "root/src" does not exist anymore
        :param dest_path_onedrive: directory to move the files to (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :param src_path_onedrive: directory where all file are located (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        """
        self._CheckConnected()
        dest_path_onedrive = dest_path_onedrive.lstrip("/").rstrip("/")
        src_path_onedrive = src_path_onedrive.lstrip("/").rstrip("/")
        src_path_id = self._FetchFolderID(src_path_onedrive)
        dest_path_id = self._FetchFolderID(dest_path_onedrive)
        url = self.url + 'me/drive/items/' + src_path_id
        body = {
            "parentReference": {
                "id": dest_path_id
            },
        }
        response = json.loads(requests.patch(url, headers=self.headers, json=body).text)
        error_message = "Could not move all files from " + src_path_onedrive
        self._CheckError(error_message, response)
        self._FetchErrors()


    @_SaveRequest
    def Upload(self, filenames: list, path_onedrive: str, log: bool = True) -> None:
        """
        Uploads several files to one specific directory in OneDrive
        :param filenames: list of files to upload (given as local paths)
        :param path_onedrive: directory to upload to (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :param log: writes to console, if files are uploaded
        """

        def UploadIntern(filename, url, header, log, CheckError):
            if not os.path.isfile(filename):
                error_message = "Could not upload " + filename + ": File does not exist"
                CheckError(error_message, None)
                return True
            content = open(filename, 'rb')
            response = json.loads(requests.put(url, headers=header, data=content).text)
            error_message = "Could not upload " + filename
            error_occured = CheckError(error_message, response)
            if log and not error_occured:
                print("File " + filename + " has been uploaded")
            return error_occured

        self._CheckConnected()
        if path_onedrive[0] != "/":
            path_onedrive = "/" + path_onedrive
        if path_onedrive[-1] != "/":
            path_onedrive = path_onedrive + "/"
        url_pre = self.url + 'me/drive/root:'
        url_post = ':/content'
        index = len(filenames)
        while index > 0:
            number_threads = self.max_threads
            if index < self.max_threads:
                number_threads = index
            for i in range(number_threads):
                index -= 1
                filename = filenames[index]
                filename = filename.replace("\\", "/")
                url = url_pre + path_onedrive + filename.split("/")[-1] + url_post
                thread = Thread(target=UploadIntern, args=(filename, url, self.headers, log, self._CheckError,), daemon=True)
                thread.start()
                self.threads.append(thread)
            self._JoinThreads()
            self._FetchErrors("Could not upload all files: ")


    @_SaveRequest
    def Download(self, path_onedrive: str, path_local: str, specific_file: str = "", log: bool = True) -> None:
        """
        Downloads all files or a specific file from a OneDrive directory to a specific directory.
        :param path_onedrive: directory to download from (e.g. if there is a directory 'Test' on the main page of OneDrive (=root), let 'path_onedrive' be 'Test/')
        :param path_local: local directory to download to
        :param specific_file: downloads only the given file; downloads all files from 'path_onedrive', when empty string is given
        :param log: writes to console, if files are downloaded
        """

        def DownloadIntern(path_local, filename, url, header, log, CheckError):
            data = requests.get(url, headers=header)
            error_message = "Could not download " + filename
            if CheckError(error_message, data):
                return True
            try:
                with open(path_local + "/" + filename, 'wb') as f:
                    f.write(data.content)
                if log:
                    print("File " + filename + " has been downloaded")
                return False
            except:
                error_message = "Could not write " + path_local + " to drive"
                CheckError(error_message, None)
                return True

        self._CheckConnected()
        if not os.path.exists(path_local):
            os.makedirs(path_local)
        path_onedrive = path_onedrive.lstrip("/").rstrip("/")
        all_files, _ = self.FetchAllFiles(path_onedrive)
        keys = list(all_files.keys())
        index = len(keys)
        while index > 0:
            number_threads = self.max_threads
            if index < self.max_threads:
                number_threads = index
            for i in range(number_threads):
                index -= 1
                filename = keys[index]
                if (specific_file != "" and specific_file == filename) or specific_file == "":
                    url = self.url + 'me/drive/items/' + all_files[filename] + "/content"
                    thread = Thread(target=DownloadIntern, args=(path_local, filename, url, self.headers, log, self._CheckError,), daemon=True)
                    thread.start()
                    self.threads.append(thread)
            self._JoinThreads()
            self._FetchErrors("Could not download all files: ")
