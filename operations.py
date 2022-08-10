from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
from googleapiclient.http import MediaIoBaseDownload
import os
import zipfile
import io
import logging


SCOPES = ['https://www.googleapis.com/auth/drive']

#creating a logger for logging the details 
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler('log_file.log')
logger.addHandler(file_handler)
formatter = logging.Formatter("%(levelname)s:%(message)s:%(asctime)s")
file_handler.setFormatter(formatter)


#function used to authenticate a account before calling the service
def authenticate():
    creds = None
    # The file token.json stores the user's access it is created automatically when the authorization flow completes for the first  time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next time
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
            logger.info("token.json file created")
    return creds


def backup_folder(folder_path,gDrive_loc):
    creds = authenticate()
    try:
        #creating a service
        service = build('drive', 'v3', credentials = creds)
        local_folder_path = folder_path
        folder_paths = local_folder_path.split("\\")
        local_folder_name = folder_paths[-1]
        gDrive_loc = gDrive_loc
        folders = gDrive_loc.split('/')
        destination_dir = folders[-1]
        length_gDrive_path = len(folders)
        check_folder_exists = None

        #calling the service to get the parent id
        results = service.files().list(q="name='{}'".format(folders[0]), fields="nextPageToken, files(id,name,mimeType)").execute()
        items = results.get('files', [])
        for item in items:
            folder_id = item['id']

        if length_gDrive_path == 1:
            if len(items):
                check_folder_exists = True
            else:
                file_metadata = { 'name': destination_dir, 'mimeType': 'application/vnd.google-apps.folder'}
                folder = service.files().create(body=file_metadata).execute()
                folder_id = folder.get('id')
                check_folder_exists = True
        #calling the service to list the folder names
        else:
            for i in range(length_gDrive_path-1):
                    results = service.files().list(q="parents = '{}'".format(folder_id), fields="nextPageToken, files(id, name,mimeType)").execute()
                    items.clear()
                    items = results.get('files', [])
                    for item in items:
                        if i == length_gDrive_path-2:
                            if item['name'] == folders[i+1]:
                                folder_id = item['id']
                                check_folder_exists = True
                                break
                            else:
                                check_folder_exists = False
                        elif item['name'] == folders[i+1]:
                            folder_id = item['id']
        
        #creating a new folder if one dosent exist
        if not check_folder_exists:
            file_metadata = { 'name': destination_dir, 'mimeType': 'application/vnd.google-apps.folder', 'parents':[folder_id]}
            folder = service.files().create(body=file_metadata).execute()
            folder_id = folder.get('id')

        #checks if the folder_path provided is a directory if it is creates a zip file of the dir and uplodes it 
        if os.path.isdir(local_folder_path):
            zipf = zipfile.ZipFile("{}.zip".format(local_folder_name),'w',zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(local_folder_path):
                for file in files:
                    zipfile.ZipFile("{}.zip".format(local_folder_name),'w',zipfile.ZIP_DEFLATED)
                    zipf.write(os.path.join(root, file))
            zipf.close()
            file_name = '{}.zip'.format(local_folder_name)
            file_metadata = {'name':file_name, 'parents': [folder_id] }
            media = MediaFileUpload('{}'.format('./{}'.format(file_name)))
            service.files().create(body=file_metadata, media_body = media, fields = 'id').execute()
            print("File {} created at {}".format(file_name,gDrive_loc))

        #uploades the given file into the GDrive location 
        else:
            files = local_folder_path.split("\\")
            file_name = files[-1]
            file_metadata = {'name':file_name, 'parents': [folder_id] }
            media = MediaFileUpload('{}'.format(local_folder_path))
            service.files().create(body=file_metadata, media_body = media, fields = 'id').execute()
            print("File {} created at {}".format(file_name,gDrive_loc))

    except HttpError as error:
        print("An error occurred: {}".format(error))
        logger.error("An error occurred: {}".format(error))
    except FileNotFoundError as error:
        print("An error occurred: {}".format(error))
        logger.error("An error occurred: {}".format(error))


def download_folder(gDrive_loc):
    creds = authenticate()
    try:
        #creating a service
        service = build('drive', 'v3', credentials = creds)
        gDrive_loc = gDrive_loc
        folders = gDrive_loc.split('/')
        length_gDrive_path = len(folders)
        file_ids = []
        file_names = []
        folder_exist = False

        #cheching if its no input is provided for GDrive location
        if len(gDrive_loc) == 0:
            results = service.files().list(fields="nextPageToken, files(id,name,mimeType)").execute()
            items = results.get('files', [])
            for item in items:
                if item['mimeType'] != 'application/vnd.google-apps.folder':
                    file_ids.append(item['id'])
                    file_names.append(item['name'])

        else:
            #calling the service to get the parent id
            results = service.files().list(q="name='{}'".format(folders[0]), fields="nextPageToken, files(id,name,mimeType)").execute()
            items = results.get('files', [])
            for item in items:
                folder_id = item['id']
            if len(items) == 0:
                print("{} folder dosent exist".format(folders[0]))
                logger.error("{} folder dosent exist".format(folders[0]))
                return 

            #calling the service to list the folder names
            for i in range(length_gDrive_path):
                if item['name'] == folders[-1]:
                    folder_exist = True
                results = service.files().list(q="parents = '{}'".format(folder_id), fields="nextPageToken, files(id, name,mimeType)").execute()
                items.clear()
                items = results.get('files', [])
                for item in items:
                    if i == length_gDrive_path-1:
                        if item['mimeType'] != 'application/vnd.google-apps.folder':
                            file_ids.append(item['id'])
                            file_names.append(item['name'])
                        folder_id = item['id']
                    elif item['name'] == folders[i+1]:
                        folder_id = item['id']
                    if item['name'] == folders[-1]:
                        folder_exist = True
        
        if not folder_exist:
            print("{} path dosent exist".format(gDrive_loc))
            logger.error("{} path dosent exist".format(gDrive_loc))
            return
        elif len(file_ids) == 0:
            print("{} Folder empty".format(gDrive_loc))
            logger.error("{} Folder empty".format(gDrive_loc))
            return

        # downloading the required files 
        for file_id, file_name in zip(file_ids, file_names):
            request = service.files().get_media(fileId=file_id)
            file_handler = io.BytesIO()
            download = MediaIoBaseDownload(fd = file_handler, request=request)
            download_done = False
            while not download_done:
                download_done = download.next_chunk()
            file_handler.seek(0)
            with open(os.path.join('./',file_name), 'wb') as f:
                f.write(file_handler.read())
                f.close()
                print("File {} downloaded".format(file_name))
                logger.info("File {} downloaded".format(file_name))

    except HttpError as error:
        print("An error occurred: {}".format(error))
        logger.error("An error occurred: {}".format(error))


def create_folder(folder_name, gDrive_loc):
    creds = authenticate()
    try:
        #creating a service
        service = build('drive', 'v3', credentials = creds)
        folder_name = folder_name
        gDrive_loc = gDrive_loc
        folders = gDrive_loc.split('/')
        destination_dir = folders[-1]
        length_gDrive_path = len(folders)
        folder_exist = False
        
        #cheching if its no input is provided for GDrive location
        if len(gDrive_loc) == 0:
            file_metadata = { 'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}
            service.files().create(body=file_metadata).execute()
            print("Folder {} created at MyDrive".format(folder_name))
            logger.info("Folder {} created at MyDrive".format(folder_name))
        else:
            #calling the service to get the parent id
            results = service.files().list(q="name='{}'".format(folders[0]), fields="nextPageToken, files(id,name,mimeType)").execute()
            items = results.get('files', [])
            for item in items:
                folder_id = item['id']
            if len(items) == 0:
                print("{} folder dosent exist".format(folders[0]))
                logger.error("{} folder dosent exist".format(folders[0]))
                return 
            if length_gDrive_path == 1:
                if item['name'] == folders[-1]:
                    folder_exist = True

            #calling the service to list the folder names
            for i in range(length_gDrive_path-1):
                if item['name'] == folders[-1]:
                        folder_exist = True
                results = service.files().list(q="parents = '{}'".format(folder_id), fields="nextPageToken, files(id, name,mimeType)").execute()
                items.clear()
                items = results.get('files', [])
                for item in items:
                    if item['name'] == folders[-1]:
                        folder_exist = True
                        folder_id = item['id']
                    if item['name'] == folders[i+1]:
                        folder_id = item['id']
            

            if not folder_exist:
                print("{} path dosent exist".format(gDrive_loc))
                logger.error("{} path dosent exist".format(gDrive_loc))
                return

            #creating the folder at the given gDrive location
            file_metadata = { 'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents':[folder_id]}
            service.files().create(body=file_metadata).execute()
            print("Folder {} created at {}".format(folder_name,gDrive_loc))
            logger.info("Folder {} created at {}".format(folder_name,gDrive_loc))

    except HttpError as error:
        print("An error occurred: {}".format(error))
        logger.error("An error occurred: {}".format(error))


def list_files(gDrive_loc):
    creds = authenticate()
    try:
        #creating a service        
        service = build('drive', 'v3', credentials = creds)
        gDrive_loc = gDrive_loc
        folders = gDrive_loc.split('/')
        length_gDrive_path = len(folders)
        i = 0
        
        #cheching if its no input is provided 
        if len(gDrive_loc) == 0:
            results = service.files().list(fields="nextPageToken, files(id, name, mimeType)").execute()
            items = results.get('files', [])
            for item in items:
                if item['mimeType'] == 'application/vnd.google-apps.folder':
                    print('{}/'.format(item['name']))
                else:
                    print('{}'.format(item['name']))

        else:    
            for folder in folders:
                #calling the serive to list the folder names
                results = service.files().list(q="name='{}'".format(folder), fields="nextPageToken, files(id, name, mimeType)").execute()
                items = results.get('files', [])
                if len(items) == 0:
                    print("{} folder dosent exist".format(folder))
                    logger.error("{} folder dosent exist".format(gDrive_loc))
                    break
                for item in items:
                    folder_id = item['id']
                results = service.files().list(q="parents = '{}'".format(folder_id), fields="nextPageToken, files(id, name, mimeType)").execute()
                items = results.get('files', [])
                i+=1
                #listing all the files at the given gDrive location 
                if i == length_gDrive_path:
                    for item in items:
                        if item['mimeType'] == 'application/vnd.google-apps.folder':
                            print('{}/'.format(item['name']))
                        else:
                            print('{}'.format(item['name']))
                    if len(items) == 0:
                        print("The folder is empty")
    except HttpError as error:
        print("An error occurred: {}".format(error))
        logger.error("An error occurred: {}".format(error))


def list_rec(gDrive_loc):
    creds = authenticate()
    try:
        def recrscive(id,name):
            # print('{}'.format(name), end='/')
            results = service.files().list(q="parents = '{}'".format(id), fields="nextPageToken, files(id, name,mimeType)").execute()
            files = results.get('files', [])
            if len(files) == 0:
                print('{}'.format(name), end='/')
            else:
                for file in files:
                    print('{}'.format(name), end='/')
                    if file['mimeType'] != 'application/vnd.google-apps.folder':
                        print('{}'.format(file['name']))
                    else:
                        recrscive(file['id'],file['name'])
            print()
        #creating a service        
        service = build('drive', 'v3', credentials = creds)
        gDrive_loc = gDrive_loc
        folders = gDrive_loc.split('/')
        length_gDrive_path = len(folders)
        i = 0
        for folder in folders:
            #calling the serive to list the folder names
            results = service.files().list(q="name='{}'".format(folder), fields="nextPageToken, files(id, name,mimeType)").execute()
            items = results.get('files', [])
            if len(items) == 0:
                print("{} folder dosent exist".format(folder))
                break
            for item in items:
                folder_id = item['id']
            results = service.files().list(q="parents = '{}'".format(folder_id), fields="nextPageToken, files(id, name,mimeType)").execute()
            items = results.get('files', [])
            i+=1
            #listing all the files at the given gDrive location 
            if i == length_gDrive_path:
                for item in items:
                    if item['mimeType'] != 'application/vnd.google-apps.folder':
                        print('{}'.format(item['name']), end=',')
                    else:
                        print()
                        recrscive(item['id'],item['name'])
    except HttpError as error:
        print("An error occurred: {}".format(error))
        logger.error("An error occurred: {}".format(error))

def end_session():
    #deleting the token.json file 
    if os.path.exists('token.json'):
        os.remove('token.json')
        logger.info("token.json file deleted")
    