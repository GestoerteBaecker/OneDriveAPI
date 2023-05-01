# OneDriveAPI

This is a really simple Python API to communicate to OneDrive (Download, Upload, Fetch). It only uses the authentication with access and refresh tokens. For first usage, leave the variable 'refresh_token' in the Settings.json empty. After trying to connect to OneDrive you are prompted to grant access (enter your username and password). Afterwards the refresh token is generated and could be saved for later usage (it is valid for 3 months; after this period you are prompted again to grant access).

## Prerequisites
For the usage it is necessary to allow the connection of OneDrive to your app. Please follow the steps below:
- Register an application in the Azure portal: You will need to create a new application in the Azure portal and obtain the application ID and secret (see https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
- Grant permissions: You will need to grant your application the necessary permissions to access OneDrive. You can do this in the Azure portal by selecting your application and then clicking on "API permissions".
- After that you can clone the repository. Replace all values marked with "XXX" in the settings.json according to your setup. 
- For usage see Test.py

## Usage
Please see Test.py for the usage.
The error handling is done by throwing exceptions, so ensure to always use try-catches. 
Since all the other SDKs are deprecated i tried to do my own. If you feel the need to adapt, extend or improve something, let me know and contribute. Thank you :)
