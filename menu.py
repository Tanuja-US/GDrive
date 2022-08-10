from operations import *

end = False
#Menu for choosing the operation
logger.info("\n\n\n-------------Sesion started---------------")
while not end:
    print("\n\n\t\t\tMenu\n\n")
    print(" \t 1.Backup \n\n \t 2.Restore \n\n \t 3.Create folder \n\n \t 4.List files \n\n \t 5.Exit \n\n")
    option = input("Enter the option: ")
    match option:
        case "1":
            folder_path = input("Enter folder path to be backed up: ")
            gDrive_loc = input("Enter the Google Drive location: ")
            logger.info("Request for backup of {} folder to {}".format(folder_path,gDrive_loc))
            backup_folder(folder_path,gDrive_loc)
        case "2":
            gDrive_loc = input("Enter the Google Drive location: ")
            logger.info("Request for downloading of {} folder".format(gDrive_loc))
            download_folder(gDrive_loc)
        case "3":
            folder_name = input("Enter the folder name to create: ")
            gDrive_loc = input("Enter the Google Drive location: ")
            logger.info("Request for creating {} folder at {}".format(folder_name,gDrive_loc))
            create_folder(folder_name,gDrive_loc)
        case "4":
            print("\t 1.List files at the given location \n\n \t 2.List files recursively")
            opt = input("Enter the option: ")
            gDrive_loc = input("Enter the Google Drive location: ")                        
            match opt:
                case "1":
                    logger.info("Request for listing the files at {}".format(gDrive_loc))
                    list_files(gDrive_loc)
                case "2":
                    logger.info("Request for recursively listing the files at {}".format(gDrive_loc))
                    list_rec(gDrive_loc)
                case default:
                    print("Invalid option. Please try again")
        case "5":
            logger.info("Request for ending the sesion")
            end_session()
            end = True
        case default:
            print("Invalid option. Please try again")
        
logger.info("---------------Session ended--------------")
