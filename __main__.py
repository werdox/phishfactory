"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pyAesCrypt
import json
import smtplib
import os
import getpass
import re
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate
from email.mime.application import MIMEApplication


class Colors:
    if os.name == "posix":
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'

    else:
        HEADER = ''
        BLUE = ''
        GREEN = ''
        YELLOW = ''
        RED = ''
        ENDC = ''
        BOLD = ''


def red(text):
    return Colors.RED + text + Colors.ENDC


def yellow(text):
    return Colors.YELLOW + text + Colors.ENDC


def green(text):
    return Colors.GREEN + text + Colors.ENDC


def blue(text):
    return Colors.BLUE + text + Colors.ENDC


def bold(text):
    return Colors.BOLD + text + Colors.ENDC


if os.getuid() > 0:
    print(red(bold("Run as root :)")))
    exit()

BASE = os.path.dirname(__file__)

SETUP_FILE = open(BASE + "/setups.json", "r")
SETUP = json.load(SETUP_FILE)
SETUP_FILE.close()

SERVER = "smtp.gmail.com"
PORT = 587

html_body = None
subject = None
attachments = None

flag = 0


def clean():
    os.system("rm -rf {0}/data.json".format(BASE))


KEY_FILE = open(BASE + "/.key", "r")
KEY = KEY_FILE.read()
KEY_FILE.close()

bufferSize = 64 * 1024
DATA_PATH = BASE + "/data.json"
DATA_PATH_E = BASE + "/data.json.aes"
pyAesCrypt.decryptFile(DATA_PATH_E, DATA_PATH, KEY, bufferSize)
DT = open(DATA_PATH, "r")
DATA = json.load(DT)
DT.close()
clean()


def valid_number(text):
    while True:
        question = input(green(bold(text)) + blue(bold("> ")))
        try:
            question = int(question.replace(" ", ""))
            return question

        except ValueError:
            print(red("Please submit a number!"))


def placeholder_filler(text):
    placeholders = re.findall("{[aA-zZ]*}", text)
    placeholders = list(dict.fromkeys(placeholders))

    for placeholder in placeholders:
        if placeholder != "{TARGET}":
            print(yellow(bold("Found placeholder {0}".format(placeholder))))
            new = input(green(bold("New value for {0}".format(placeholder))) + blue(bold("> ")))
            text = text.replace(placeholder, new)

    return text


def encrypt():
    pyAesCrypt.encryptFile(DATA_PATH, DATA_PATH_E, KEY, bufferSize)
    os.system("rm -rf {0}".format(DATA_PATH))


def update(dct):
    dtf = open(DATA_PATH, "w")
    data = json.dumps(dct)
    dtf.write(data)
    dtf.close()
    encrypt()


if not DATA["email"] and not DATA["alias"] and not DATA["password"]:
    flag = 1
    account = input(green(bold("Sender's email address (g-mail)")) + blue(bold("> ")))
    alias = input(green(bold("Nickname")) + blue(bold("> ")))
    pw = getpass.getpass()
    print(yellow(bold(':.: Validating e-mail :.:')))

else:
    account = DATA["email"]
    alias = DATA["alias"]
    pw = DATA["password"]

SMTP = smtplib.SMTP(SERVER, PORT)

try:
    SMTP.starttls()
    SMTP.login(account, pw)
    SMTP.quit()

except Exception as e:
    print(red("[ERR] {}".format(str(e))))

if flag:
    save = input(green(bold("Save credentials for later use?")) + blue(bold(" [Y/n] "))).replace(" ", "")

    if save in "Yy":
        DATA["email"] = account
        DATA["alias"] = alias
        DATA["password"] = pw
        print(yellow(bold("encrypting credentials file...")), end="")
        update(DATA)
        print(yellow(bold("done")))

use_setup = input(green(bold("Use existing setup?")) + blue(bold(" [Y/n] "))).replace(" ", "")
if use_setup in "Yy":
    setups = SETUP.keys()
    for setup in setups:
        s = SETUP[setup]
        print(blue(bold("\n{0}) ".format(int(setup) + 1))) + bold("{0}".format(s["name"])))
        print(blue(bold("\tSubject: ")) + bold("{0}".format(s["subject"])))
        print(blue(bold("\tTemplate: ")) + bold("{0}".format(s["template"])))
        print()

    choice = str(valid_number("Setup number") - 1)
    if choice in setups:
        subject = SETUP[choice]["subject"]
        html = open("{0}/templates/{1}".format(
            BASE, SETUP[choice]["template"]
        ), "r")
        html_body = html.read()
        html_body = placeholder_filler(html_body)
        html.close()

else:
    subject = input(green(bold("Subject")) + blue(bold("> ")))
    attachments = input(green(bold("Path to attachment(s) (use , to separate multiple files)")) + blue(bold("> ")))
    while True:
        templates_dirs = os.popen("ls {0}/templates".format(BASE)).read().split("\n")[:-1]
        print(green(bold("HTML Templates")))
        counter = 1
        for td in templates_dirs:
            print("{0}) {1}".format(counter, td))
            counter += 1

        section_number = valid_number("Template type number") - 1

        templates = os.popen(
            "ls {0}/templates/{1}".format(BASE, templates_dirs[section_number])).read().split(
            "\n")[:-1]
        counter = 1

        print(templates_dirs[section_number])
        for template in templates:
            print(str(counter) + ") " + template)
            templates[counter - 1] = template
            counter += 1

        template_number = valid_number("HTML template number") - 1

        try:
            html = open("{0}/templates/{1}/{2}".format(
                BASE, templates_dirs[section_number], templates[template_number]
            ), "r")
            html_body = html.read()
            html_body = placeholder_filler(html_body)

        except FileNotFoundError:
            print(red(bold("File not found!")))
            continue

        break

target = input(green(bold("Target email address")) + blue(bold("> ")))
html_body = html_body.replace("{TARGET}", target)

print(yellow(bold("logging in...")), end="")
SMTP.connect(SERVER, PORT)
SMTP.starttls()
SMTP.login(account, pw)
print(yellow(bold("done")))

print(yellow(bold("sending email...")), end="")

message = MIMEMultipart('alternative')
message['From'] = "{} <{}>".format(alias, account)
message['To'] = target
message['Date'] = formatdate(localtime=True)

message['Subject'] = subject

html = MIMEText(html_body, 'html')
message.attach(html)

if attachments:
    for att in attachments.split(","):
        f = open(att, "rb")
        attachment = MIMEApplication(f.read(), _subtype=att.split('.')[-1])
        attachment.add_header('Content-Disposition', 'attachment', filename=att.split('/')[-1])
        message.attach(attachment)
        f.close()

SMTP.sendmail(alias, target, message.as_string())
SMTP.quit()

print(yellow(bold("done")))
