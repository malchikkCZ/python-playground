'''
This script helps to monitor available storage space on server.
You have to provide the percentage of free space to be alerted at and
an email address to send alert to as arguments of the script.

Example:
python3 check_storage.py 10 some.email@gmail.com

It works best when scheduled with cron.
'''

import os
import shutil
import smtplib
import socket
import sys

from netifaces import AF_INET, ifaddresses, interfaces


class StorageChecker:
    def __init__(self, perc):
        self.perc = perc / 100

    def check(self):
        total, used, free = shutil.disk_usage('/')

        print(free/total)
        if free / total <= self.perc:
            message = f'There is less than {(free / total * 100):.2f} % of free space on server: \n'

            for ifaceName in interfaces():
                addresses = [i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':'No IP addr'}] )]
                for address in addresses:
                    message += f'\n{address}'
            message += f'\n{socket.gethostname()}'

            return True, message

        return False, ''


class EmailSender:
    def __init__(self, mailfrom, password):
        self.mailfrom = mailfrom
        self.password = password

    def send(self, mailto, subject, message):
        with smtplib.SMTP('smtp.gmail.com') as mailserver:
            mailserver.starttls()
            mailserver.login(user=self.mailfrom, password=self.password)
            mailserver.sendmail(
                from_addr=self.mailfrom,
                to_addrs=mailto,
                msg=f'Subject:{subject}\n\n{message}'
            )


if __name__ == '__main__':
    MAILFROM = os.environ.get("MAILFROM")
    PASSWORD = os.environ.get("PASSWORD")

    if not MAILFROM or not PASSWORD:
        print('You have to set environment variables for gmail username and password\n\n' +
            'export MAILFROM="your.mail@gmail.com"\n' +
            'export PASSWORD="your_password"\n')
        sys.exit()

    try:
        PERC = int(sys.argv[1])
        MAILTO = str(sys.argv[2])
    except IndexError:
        print('You have to provide percentage of storage left and email to send alert to.\n' + 
            'Example: python3 check_storage.py 10 some.email@gmail.com\n')
        sys.exit()

    storage_checker = StorageChecker(PERC)
    is_alert, message = storage_checker.check()

    if is_alert:
        email_sender = EmailSender(MAILFROM, PASSWORD)
        email_sender.send(MAILTO, 'ALERT: Low server storage space', message)
