'''
This script checks the specified folder for the files older than 7 days.
If there are some files with this condition satisfied, it creates an zip archive of them
and deletes them. Those archives are stored in computer for another 90 days, after that
are uploaded to Google Drive folder and deleted from computer.

Example:
python3 auto_archive.py /home/user/Downloads 11MKhCt4VfWMuAyeyThx94xjfwyST0FKd

It works best when scheduled with cron.
For more info on how to set google authentication visit:
https://d35mpxyw7m7k7g.cloudfront.net/bigdata_1/Get+Authentication+for+Google+Service+API+.pdf
'''

import datetime as dt
import os
import sys
from zipfile import ZipFile

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive


class FileFilter:
    def __init__(self, folder):
        self.folder = folder

    def get_filenames(self, ext=''):
        filenames = list(filter(lambda file: os.path.isfile(os.path.join(self.folder, file)), os.listdir(self.folder)))
        if ext != '':
            filenames = [file for file in filenames if file.endswith(ext)]
        return filenames

    def filter_filenames(self, filenames, delta_days):
        today_sec = dt.datetime.now().timestamp()
        delta_sec = dt.timedelta(days = delta_days).total_seconds()
        files_to_archive = []
        for file in filenames:
            time_of_creation = os.stat(os.path.join(self.folder, file)).st_ctime
            if today_sec - time_of_creation >= delta_sec:
                files_to_archive.append(file)

        return files_to_archive


class FileZipper:
    def __init__(self, folder, prefix='_backup'):
        self.folder = folder
        self.zipfile_name = f'{prefix}-{dt.datetime.now().strftime("%y%m%d")}.zip'
        self.zipfile_path = os.path.join(self.folder, self.zipfile_name)

    def create_archive(self, files_to_archive, remove=False):
        with ZipFile(self.zipfile_path, 'w') as zip_file:
            for file in files_to_archive:
                file_path = os.path.join(self.folder, file)
                zip_file.write(file_path, os.path.basename(file_path))

                if remove:
                    os.remove(os.path.join(self.folder, file))


class FileUploader:
    def __init__(self, source_folder, upload_folder):
        self.folder = source_folder
        self.gauth = GoogleAuth()
        self.drive = GoogleDrive(self.gauth)
        self.upload_folder = upload_folder

    def upload_to_cloud(self, filenames, remove=False):
        for file in filenames:
            gfile = self.drive.CreateFile({'parents': [{'id': self.upload_folder}], 'title': file})
            file_path = os.path.join(self.folder, file)
            gfile.SetContentFile(file_path)
            gfile.Upload()
            gfile = None
            if remove:
                self.remove(file)

    def remove(self, file):
        os.remove(os.path.join(self.folder, file))


if __name__ == '__main__':

    try:
        # get a name of the folder to watch
        FOLDER = sys.argv[1]
        UPLOAD_FOLDER = sys.argv[2]
    except IndexError:
        print('You have to provide full path to folder you want to watch and the ID of google drive folder.\n' + 
            'Example: python3 auto_archive.py /home/user/Downloads 11MKhCt4VfWMuAyeyThx94xjfwyST0FKd\n')
        sys.exit()
    
    FILE_FILTER = FileFilter(folder=FOLDER)

    # find all files in the folder 
    filenames = FILE_FILTER.get_filenames()

    # filter the files that are older than 1 week
    files_to_archive = FILE_FILTER.filter_filenames(filenames, 7)

    # create new zip archive with those files
    if len(files_to_archive) > 0:
        file_zipper = FileZipper(FOLDER)
        file_zipper.create_archive(files_to_archive, remove=False)

    # check for all zip files that are older than 3 months
    zipfiles = FILE_FILTER.get_filenames(ext='zip')
    zipfiles_to_upload = FILE_FILTER.filter_filenames(zipfiles, 90)
    
    # delete (or upload to cloud) those files
    if len(zipfiles_to_upload) > 0:
        file_uploader = FileUploader(FOLDER, UPLOAD_FOLDER)
        file_uploader.upload_to_cloud(zipfiles_to_upload, remove=False)
