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
import os
import json
from random import randint

if os.getuid() > 0:
    print("Run as root :)")
    exit()

CONFIG_FILE = open("config.json", "r")
CONFIG = json.load(CONFIG_FILE)
CMD_PATH = CONFIG["cmd_dir"] + CONFIG["name"]
BASE = CONFIG["install_dir"] + CONFIG["name"]


def create_dir():
    print("creating {0}...".format(BASE), end="")
    os.system("mkdir " + BASE)
    print("done")


if not os.path.exists(BASE):
    create_dir()

else:
    print(BASE + " already exists")
    choice = input("Delete and recreate? [Y/n] ")
    if choice in "Yy":
        print("deleting {0}...".format(BASE))
        os.system("rm -rf " + BASE)
        print("done")
        create_dir()

print("copying this directory to {0}...".format(BASE), end="")
os.system("cp -rf . " + BASE)
print("done")

chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890.,/+-*_-<>"
KEY = ""

print("generating key...", end="")
for i in range(len(chars)):
    KEY += chars[randint(0, len(chars)-1)]

print("done")

key_file = open(BASE + "/.key", "w")
key_file.write(KEY)
key_file.close()

DATA_FILE = open(BASE + "/data.json", "w")
d = {
    "email": 0,
    "alias": 0,
    "password": 0
}

json.dump(d, DATA_FILE)
DATA_FILE.close()
bufferSize = 64 * 1024
pyAesCrypt.encryptFile(BASE + "/data.json", BASE + "/data.json.aes", KEY, bufferSize)
os.system("rm -rf {0}".format(BASE + "/data.json"))

print("creating command {0}...".format(CMD_PATH), end="")
f = open(CMD_PATH, "w")
f.write("""
#! /bin/bash

python3 {0}

""".format(BASE))
f.close()
print("done")

print("executing: chmod ugo+x {0}...".format(CMD_PATH), end="")
os.system("chmod +x " + CMD_PATH)
print("done")
