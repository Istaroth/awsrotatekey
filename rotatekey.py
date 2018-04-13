#!/usr/bin/env python

"""
Short script to rotate access keys in AWS. To be used inside automation (e.g. Jenkins)
"""

from __future__ import print_function

# should the script write stuff to output?
talkative = False


def external_call(command, error=""):
    """Wrapper for calls to external commands, returnig the result of the call"""
    import subprocess

    cmdlist = command.split()
    try:
        result = subprocess.check_output(cmdlist, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as err:
        if err.returncode != 0:
            if talkative and error != "":
                print(error)
            exit(1)

    return result


def get_current_key():
    """remember the currently used key"""
    result = external_call("aws configure get aws_access_key_id",
                           "Could not get current access key ID from CLI, not safe to proceed")
    currentKey = result.decode("utf-8").rstrip()

    return currentKey


def disable_keys_but(currentKey):
    """check the list of exsting keys and disable all other than current"""
    import json

    result = external_call("aws iam list-access-keys",
                           "Not able to access AWS access keys, exiting")
    accessKeys = json.loads(result)
    
    if len(accessKeys["AccessKeyMetadata"]) != 1:
        # delete all unused access keys
        for key in accessKeys["AccessKeyMetadata"]:
            keyid = key["AccessKeyId"]
            if keyid != currentKey:
                external_call("aws iam delete-access-key --access-key-id %s" % keyid)


def create_key_and_activate():    
    import json

    """create a new key and make it current"""
    result = external_call("aws iam create-access-key",
                           "Unable to create new access key, nothing changed")
    newKey = json.loads(result)
    
    keyid = newKey['AccessKey']['AccessKeyId']
    secret = newKey['AccessKey']['SecretAccessKey']

    return (keyid, secret)
    

def switch_active_keys(oldKey, newKey, secret):
    """deactivate old access key and switch CLI to new"""
    result = external_call("aws iam update-access-key --access-key-id %s --status Inactive" % oldKey,
                           "Old access key disabled. Can be reenabled manually if problems occur.")
    
    external_call("aws configure set aws_access_key_id %s" % newKey)
    external_call("aws configure set aws_secret_access_key %s" % secret)    


if __name__=='__main__':
    current = get_current_key()
    if talkative: print("current key is %s" % current)

    disable_keys_but(current)
    (newkey, secret) = create_key_and_activate()
    if talkative: print("new key is %s" % newkey)

    switch_active_keys(current, newkey, secret)
    if talkative: print("Access key rotated! Have a nice day")

    exit(0)
