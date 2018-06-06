import socket
import requests
import subprocess
from getpass import getuser, getpass
import argparse
import platform
from binascii import hexlify, unhexlify
from sys import stdin
from simplecrypt import encrypt, decrypt

# SETTINGS
SERVER_NAME = 'http://localhost:8000'


def decryptCreds(salt, cipher):
    plaintext = decrypt(salt, unhexlify(cipher))
    return plaintext.decode('utf8')


def encryptCreds(salt, password):
    # encrypt the plaintext.  we explicitly convert to bytes first (optional)
    ciphertext = encrypt(salt, password.encode('utf8'))
    return hexlify(ciphertext).decode('utf8')


'''
2018-03-08
JRK - Login module for tracking status of desktops
        and whether or not users are logged on
'''


def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


# Logger function (activity=Login / Logoff)
def logger(activity=None):
    if activity is None:
        # parse activity from command line argument
        ap = argparse.ArgumentParser()
        ap.add_argument('-a', '--action', required=False,
                        help='Login | Logout | BadgeRead | other')
        args = vars(ap.parse_args())
        activity = args['action']
    else:
        # Activity passed in via external function
        pass
    # get desktop fully qualified domain name
    desktop = socket.getfqdn()
    # get user name
    user = getuser()
    # get IP address
    ip = get_ip()
    # get platform
    os = platform.system() + platform.version()

    url = SERVER_NAME + '/connectlog/'
    # known issue - presently writing to the log table requires no permissions
    post_req = {"activity": activity, "fqdn": desktop, "ip_addr": ip, "os": os,
                "user": user}
    resp = requests.post(url, json=post_req)
    if resp.status_code != 201:
        raise ApiError('POST /connectlog/'.format(resp.status_code), json=task)
    print('Logged ID: {}'.format(resp.json()["id"]))


def registerBadge(badgeHex):
    # found unregistered badge. Let's tie it to a user.
    print("Please enter username: ")
    username = input("Username: ")
    print(username)
    password = getpass("Password: ")

    resp = requests.get(SERVER_NAME + '/profile/?user=' + str(username))
    if resp.status_code != 200:
        # This means something went wrong.
        raise ApiError('GET /profile/ {}'.format(resp.status_code))
    for profile_item in resp.json()['results']:
        profile_url = format(profile_item['url'])
        print(profile_url)

    put_req = {"badge": badgeHex, "pw": password}
    resp = requests.put(profile_url, auth=(username, password), json=put_req)
    if resp.status_code != 200:
        raise ApiError('PUT /profile/'.format(resp.status_code), json=task)
    print('Modified profile. ID: {}'.format(resp.json()["id"]))


def authenticate(user):
    resp = requests.get(SERVER_NAME + '/profile/?user='
                        + str(user['username']),
                        auth=(user['username'], user['pw']))
    if resp.status_code != 200:
        user['desktop'] = ''
        return user
        # raise ApiError('PUT /profile/'.format(resp.status_code), json=task)
    else:
        for profile_item in resp.json()['results']:
            user['desktop'] = format(profile_item['desktop'])
            return user


def registerDesktop(url, creds):
    # found user, no desktop set
    print("Please enter your desktop name: ")
    desktop = input("Desktop: ")
    put_req = {"desktop": desktop}
    resp = requests.put(url, auth=creds, json=put_req)
    if resp.status_code != 200:
        raise ApiError('PUT /profile/'.format(resp.status_code), json=task)
    print('Modified profile. ID: {}'.format(resp.json()["id"]))
    return desktop
# call function for testing
# registerBadge('0x02dd43a2')


def rdpConnect(user):
    print(user['desktop'])
    if (user['desktop'] is None or user['desktop'] == ""):
        print("No desktop defined!")
    else:
        commandstring = ("xfreerdp /cert-ignore /u:%s /p:%s /f /v:%s"
                         " -wallpaper -themes"
                         % (user['username'], user['pw'], user['desktop']))
        print(commandstring)
        p = subprocess.Popen(commandstring, shell=True, stdout=subprocess.PIPE)
        stdout, stderr = p.communicate()


'''
# test stuff
user = {'username': 'administrator', 'pw': '',
            'desktop': 'mcmcspiceworks.mcmh.local'}
rdpConnect(user)
'''


def badgeRead(badge_hex, badge_num):
    if badge_num > 0:
        logger("badgeread")
        resp = requests.get(SERVER_NAME + '/profile/?badge=' + str(badge_num))
        if resp.status_code != 200:
            # This means something went wrong.
            raise ApiError('GET /profile/ {}'.format(resp.status_code))

        print(resp.json())
        if resp.json()['count'] == 0:
            print("Hey, this badge isn't registered. Let's register it!")
            registerBadge(badge_hex)

        for profile_item in resp.json()['results']:
            # print(snippet_item)
            # print(resp.json())
            print('{} {} {}'.format(profile_item['id'],
                                    profile_item['user'], profile_item['url']))
            pw = str(profile_item['pw'])
            # print(pw)
            # print(badge_hex)
            plain_pw = decryptCreds(badge_hex, pw)
            # print(plain_pw)
            desktop = profile_item['desktop']
            if desktop == '':
                desktop = registerDesktop(profile_item['url'],
                                          (profile_item['user'], plain_pw))
            user = {'username': profile_item['user'],
                    'pw': plain_pw, 'desktop': desktop}
            rdpConnect(user)
            logger("disconnect")


def authenticate_and_connect(user):
    authenticate(user)
    if user['desktop'] == '':
        return False
    else:
        rdpConnect(user)
        return True
