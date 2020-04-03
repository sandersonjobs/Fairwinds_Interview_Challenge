#!/bin/python3

import winrm
import xml.etree.ElementTree as ET
from subprocess import Popen, PIPE
import shlex
import os
import random
from gepy.external.mysqlclient import mysql_conn


usernames={"non_ec":("lg777957sv","lg782967sv"),"ec":("lg788403sv","lg788424sv")}


def aim_cmd(action):
    return "/etc/rc.d/init.d/aimprv {action}".format(action=action)

def delete_cred_file():
    return "find / -type f -name 'appprovideruser.cred' -delete"

def create_server_pool(ec_status,non_ec_status):

    os.environ["RD_CONFIG_ASSET_WIN"]="true"
    os.environ["RD_CONFIG_ASSET_NIX"]="false"
    os.environ["RD_CONFIG_ASSET_NETWORK"]="false"
    os.environ["RD_CONFIG_ENV_PROD"]="true"
    os.environ["RD_CONFIG_ENV_DEV"]="false"
    os.environ["RD_CONFIG_ENV_STAGE"]="flase"
    os.environ["RD_CONFIG_ENV_QA"]="false"
    os.environ["RD_CONFIG_ENV_OTHER"]="false"
    os.environ["RD_CONFIG_EC"]=ec_status
    os.environ["RD_CONFIG_NONEC"]=non_ec_status

    cmd="ge-resource-model"
    server_dict =[]
    ret_object = Popen(cmd, stdout=PIPE, stderr=PIPE)
    stdout = ret_object.communicate()[0].decode("utf-8").strip('\n')
    xml_output = stdout
    root = ET.fromstring(xml_output)
    i=1

    for node in root.findall('node'):
        domain = node.get('DnsDomain')
        domain = str(domain)
        if "logon" in domain:
            ip = node.get('IpAddress')
            if ip != "None" and i<6:
                server_dict.append(ip)
                i += 1

    return server_dict

def get_passwd(username):

    cmd="/opt/CARKaim/sdk/clipasswordsdk"\
        " GetPassword -p AppDescs.AppID=CTAUTO -p Query='Safe=0200_02_WND_CE_CTAUTO;"\
        "Folder=Root;Object=WinDomain_C#logon.ds.ge.com#{name}' -o password".format(name=username)

    ret_object = Popen(shlex.split(cmd), stdout=PIPE, stderr=PIPE)
    stdout = ret_object.communicate()[0].decode("utf-8").strip('\n')
    retcode = ret_object.returncode
    passwd=stdout
    return passwd

def get_winrm_result(name,passwd,server):
    re = winrm.Session(
        target=server,
        auth=(name, passwd),
        transport='ntlm',
        server_cert_validation='ignore',
        message_encryption='always',
        read_timeout_sec=20,
        operation_timeout_sec=15,
    )
    answer = re.run_cmd('hostname')
    return answer


def main():
    non_ec_result=0
    ec_result=0
    
    # Uncomment the server pools below in order to get your server pool via the Asset Model
    # non_ec_server_pool = create_server_pool(ec_status="false",non_ec_status="true")
    # ec_server_pool = create_server_pool(ec_status="true",non_ec_status="false")

    # Uncomment the server pools below in order to use the static pool defined as an attribute
    # in the cta_scripts cookbook
    non_ec_server_pool = <%= node['cta_scripts']['windows_check_nonec_server_pool'] %>
    ec_server_pool = <%= node['cta_scripts']['windows_check_ec_server_pool'] %>

    random.shuffle(non_ec_server_pool)
    random.shuffle(ec_server_pool)

    for server in non_ec_server_pool:
        try:
            result = os.system("ping -qc 1 {server} > /dev/null".format(server=server))
            if result == 0:
                non_ec_target_server = server
                break
        except:
            pass
    for server in ec_server_pool:
        try:
            result = os.system("ping -qc 1 {server} > /dev/null".format(server=server))
            if result == 0:
                ec_target_server = server
                break
        except:
            pass

    # Uncomment these to test the script manually. Sensu does not need this part, so it should stay commented out unless testing
    # os.environ["no_proxy"] = os.environ["no_proxy"] + ',' + non_ec_target_server + ',' + ec_target_server
    # os.environ["NO_PROXY"] = os.environ["NO_PROXY"] + ',' + non_ec_target_server + ',' + ec_target_server

    print("\nTarget non_ec server: {server}".format(server=non_ec_target_server))
    for name in usernames["non_ec"]:
        passwd=get_passwd(name)
        try:
            response = get_winrm_result(name,passwd,non_ec_target_server)
            if response.status_code == 0:
                print("{name}: OK non_ec access".format(name=name))
        except:
            print("{name}: FAILED non_ec access".format(name=name))
            non_ec_result += 1
    print("Target ec server: {server}".format(server=ec_target_server))
    for name in usernames["ec"]:
        passwd = get_passwd(name)
        try:
            response = get_winrm_result(name,passwd,ec_target_server)
            if response.status_code == 0:
                print("{name}: OK ec access".format(name=name))
        except:
            print("{name}: FAILED ec access".format(name=name))
            non_ec_result += 1

    if (non_ec_result or ec_result) != 0:
        program_return = 2
    else:
        program_return = 0

    exit(program_return)


if __name__ == '__main__':
    aim_object = Popen(aim_cmd('status'), stdout=PIPE, stderr=PIPE, shell=True)
    stdout = aim_object.communicate()[0].decode("utf-8").strip('\n')

    try:
        mysqlclient = mysql_conn()
    except ConnectionError as error:
        print (error)
        exit(2)

    if 'running' in stdout:
        if mysqlclient.record_exists():
            if mysqlclient.expired_record():
                mysqlclient.delete_record()
                mysqlclient.insert_record()
            else:
                pass
        else:
            mysqlclient.insert_record()
        mysqlclient.close()
        main()
    else:
        aim_object = Popen(aim_cmd('start'), stdout=PIPE, stderr=PIPE, shell=True)
        stdout = aim_object.communicate()[0].decode("utf-8").strip('\n')
        if aim_object.returncode is not 0:
            if mysqlclient.record_exists():
                print ('Server has already been whitelisted. Node may need to be reset')
            else:
                ## In the future, add API call to GE Forms to generate ticket requesting whitelisting
                print('Server needs to be whitelisted!')
            delete_cred_object = Popen(delete_cred_file(), stdout=PIPE, stderr=PIPE, shell=True)
            stdout = delete_cred_object.communicate()[0].decode("utf-8").strip('\n')
            mysqlclient.close()
            exit(2)
        else:
            if mysqlclient.record_exists():
                if mysqlclient.expired_record():
                    mysqlclient.delete_record()
                    mysqlclient.insert_record()
                else:
                    pass
            else:
                mysqlclient.insert_record()
            mysqlclient.close()
            main()
