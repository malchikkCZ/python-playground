'''
This script works as automated sender of log files from selenium tests.
You have to provide an email address to send logs to as an argument of the script.

Example:
python3 log_sender.py some.email@gmail.com

It works best when scheduled with cron.
'''

import datetime as dt
import os
import smtplib
import sys
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


class FileFinder:
    def __init__(self):
        self.now = dt.datetime.now()
        self.basedir = None

    def get_previous_date(self, delta_days):
        delta = dt.timedelta(days=delta_days)
        return (self.now - delta).strftime('%Y-%m-%d')

    def get_directory(self, delta_days, contains):
        
        date_str = self.get_previous_date(delta_days)
        self.basedir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'logs', date_str)
        listdir = os.listdir(self.basedir)
        return [dir for dir in listdir if contains in dir]

    def get_files(self, delta_days, file_contains='', dir_contains=''):
        output_files = []
        for folder in self.get_directory(delta_days=delta_days, contains=dir_contains):
            dirpath = os.path.join(self.basedir, folder)
            logs = [file for file in os.listdir(dirpath) if file_contains in file]
            logs.sort()
            output_files.append(os.path.join(dirpath, logs.pop()))
        return output_files


class MailSender:
    def __init__(self, mailfrom, password):
        self.mailfrom = mailfrom
        self.password = password

    def build_message(self, mailto, subject, text, files_to_send={}):
        new_msg = MIMEMultipart()
        new_msg['From'] = self.mailfrom
        new_msg['To'] = mailto
        new_msg['Subject'] = subject
        new_msg['X-Priority'] = '1'
        new_msg.attach(MIMEText(f'\n\n{text}', 'plain'))

        for filename in files_to_send.keys():
            payload = MIMEBase('application', 'octate-stream')

            with open(files_to_send[filename], 'rb') as file:
                payload.set_payload(file.read())
                encoders.encode_base64(payload)
                payload.add_header('Content-Disposition', 'attachement', filename=filename)
                new_msg.attach(payload)
        return new_msg.as_string()

    def send(self, mailto, message):
        with smtplib.SMTP('smtp.gmail.com') as mailserver:
            mailserver.starttls()
            mailserver.login(user=self.mailfrom, password=self.password)
            mailserver.sendmail(
                from_addr=self.mailfrom,
                to_addrs=mailto,
                msg=message
            )


class Engine:
    def __init__(self, mailfrom, password, mailto):
        self.mailfrom = mailfrom
        self.password = password
        self.mailto = mailto

    def run(self):
        file_finder = FileFinder()

        # get yesterday's date
        # find all folders with 'delivery' in title
        # find most recent files with 'out' in title
        files = file_finder.get_files(delta_days=1, file_contains='out', dir_contains='delivery')

        # change files list to dictionary with filenames and paths
        files_to_send = {}
        for file in files:
            filename = f'{file.split("/")[-2].replace("_delivery_options", "")}.txt'
            files_to_send[filename] = file

        if len(files_to_send) > 0:
            mail_sender = MailSender(self.mailfrom, self.password)

            # build a message with all files as attachements
            message = mail_sender.build_message(
                mailto=self.mailto,
                subject='SELENIUM: Delivery options log files',
                text='Automated report on Delivery Options log files. See attachements for more.',
                files_to_send=files_to_send
            )

            # send the message via email
            mail_sender.send(self.mailto, message)


if __name__ == '__main__':
    MAILFROM = os.environ.get('MAILFROM')
    PASSWORD = os.environ.get('PASSWORD')

    if not MAILFROM or not PASSWORD:
        print('You need to save your gmail credentials in environment variables, eg.\n\n' + 
            'export MAILFROM="your.email@gmail.com"\n' +
            'export PASSWORD="0ad9b813"\n')
        sys.exit()

    try:
        MAILTO = str(sys.argv[1])
    except IndexError:
        print('You have to provide an email address to send logs to as an argument of the script.\n' +
            'Example: python3 log_sender.py some.email@gmail.com\n')
        sys.exit()

    engine = Engine(MAILFROM, PASSWORD, MAILTO)
    engine.run()
