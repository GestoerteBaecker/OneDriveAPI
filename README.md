# OneDriveAPI

This is a really simple Python API to communicate to OneDrive (Download, Upload, Fetch). It only uses the authentication with access and refresh tokens. For first usage, leave the variable 'refresh_token' in the Settings.json empty. After trying to connect to OneDrive you are prompted to grant access (enter your username and password). Afterwards the refresh token is generated and could be saved for later usage (it is valid for 3 months; after this period you are prompted again to grant access).

## Prerequisites
For the usage it is necessary to allow the connection of OneDrive to your app. Please follow the steps below. A detailed description could be found at the end of this readme.
- Register an application in the Azure portal: You will need to create a new application in the Azure portal and obtain the application ID and secret (see https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
- Grant permissions: You will need to grant your application the necessary permissions to access OneDrive. You can do this in the Azure portal by selecting your application and then clicking on "API permissions".
- After that you can clone the repository. Replace all values marked with "XXX" in the settings.json according to your setup. 
- For usage see Test.py

## Usage
Please see Test.py for the usage.
The error handling is done by throwing exceptions, so ensure to always use try-catches. 
Since all the other SDKs are deprecated i tried to do my own. If you feel the need to adapt, extend or improve something, let me know and contribute. Thank you :)

## Register your app to the Azure portal
Following you will find detailed instructions on how to register your app within the Azure portal and how else to prepare your app to be connected to the OneDrive API. Please note that these steps are only valid for a certain configuration of authorization type ("code"), account type, scopes of the APIs etc. Feel free to modify specific points within it. You then also might alter the Settings.json or authorization process, too.
- On the Azure portal search for the App "App registrations". Click "new registration". 
- Under the menu "Supported account types" choose "Accounts in any organizational directory (Any Azure AD directory - Multitenant) and personal Microsoft accounts (e.g. Skype, Xbox)".Click "Register".

- Now the overview of your new registered app should be showed. Obtain the value under "Application (client) ID" and save it in the Settings.json under the tag "client_id"
- On the overview go to "Client credentials" and click "Add a certificate or secret".
	- Click "New client secret" and enter your validity as you whish. Dont leave the page after creating the secret as you have to copy the secret value. It will only be displayed immediately after the secret creation. Paste the secret value in the Settings.json under the tag "client_secret".
- Go back to the overview and click "Add a Redirect URI" under the menu "Redirect URIs".
	- Under "Platform configurations" click "Add a platform", within this dialog click "Mobile and desktop application".
	- Under "Redirect URIs" enable all redirect URLs listed and click the button "Configure".
- On the side menu on the left, under the point "Manage", click the category "API permissions".
	- Click "Add a permission" and choose "Microsoft Graph" in the dialog. 
	- Choose "Application permissions" and check the following permissions (you can search for them in the entry dialog):
		- files.readwrite
		- User.Read
		- Please ensure in the "Settings.json" under key "permissions" the value "offline_access" is given, otherwise no refresh token could be generated
	- Click button "Add permissions".
- On the left side menu, click the entry "Expose an API". Click the link next to the text "Application ID URI" right on top. Leave the default application ID URI and save it. 
	- Under this entry, click "Add a scope". Fill in the mandatory entry boxes (like "Files.ReadWrite.All"). Before saving, make sure to change the "Who can consent?" to "Admins and users" and "State" to "enabled".
	- On the same page, click "Add a client application" and insert the application ID (it should be identical to the one you just used in the step before). Enable the check box "Authorized scopes" before saving. 
