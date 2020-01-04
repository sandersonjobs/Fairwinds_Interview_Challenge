#!/bin/python3

import boto3
import time
from fabric import Connection
import os


symfony_install_script = """
cd ~
sudo dnf -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm
sudo dnf -y install https://rpms.remirepo.net/enterprise/remi-release-8.rpm
sudo yum -y --enablerepo=remi,epel install wget git php php-mysqlnd php-intl php-json php-xml php-dom php-posix php-mbstring
wget https://get.symfony.com/cli/installer -O - | bash
echo "export PATH="$HOME/.symfony/bin:$PATH"" >> ~/.bash_profile
source ~/.bash_profile
cd /var/www/html
sudo /home/ec2-user/.symfony/bin/symfony new --full sanderson_interview
cd sanderson_interview
sudo /home/ec2-user/.symfony/bin/symfony server:start > /dev/null 2>&1 &
"""
test_script = """
ls ~
sudo cat /etc/hosts
"""

aws_access_key = os.environ["AWS_ACCESS_KEY"]
aws_secret_key = os.environ["AWS_SECRET_KEY"]
pem_key = os.environ["PEM_KEY"]
client = boto3.client(
    'ec2',
    region_name='eu-west-1',
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
)

def build_server():
    response = client.run_instances(
        ImageId='ami-04facb3ed127a2eb6',
        MinCount=1,
        MaxCount=1,
        KeyName='sanderson_key',
        SecurityGroups=['launch-wizard-1'],
        InstanceType='t2.micro',
    )

instances = client.describe_instances(Filters=[
    {
        'Name': 'instance-state-name',
        'Values': ['running']
    }
])

try:
    check_for_active_server = instances["Reservations"][0]["Instances"]
except:
    build_server()


find_new_server = False
retry_count=0

while find_new_server is False:
    instances = client.describe_instances(Filters=[
        {
            'Name': 'instance-state-name',
            'Values': ['running']
        }
    ])
    try:
        find_new_server = instances["Reservations"][0]["Instances"]
        find_new_server = True
        print("Found new server")
    except:
        find_new_server = False
        print("Server not up yet...")
        time.sleep(15)
        retry_count += 1
        if retry_count >= 5:
            build_server()

ip_address = instances['Reservations'][0]['Instances'][0]['PublicIpAddress']

server_up = False
while server_up is False:
    try:
        conn = Connection(host=ip_address, user= "ec2-user", connect_kwargs={"key_filename":pem_key},)
        server_up = True
        print("Connected!")
        print("Building symfony node...")
    except:
        server_up = False
        print("Unable to connect to Server...")

conn.run(symfony_install_script)

try:
    time.sleep(10)
    conn.run("sudo /home/ec2-user/.symfony/bin/symfony server:list | grep 8000 > /dev/null 2>&1")
    print("Congrats, your symfony web app is accessible at http://{ipaddress}:8000".format(ipaddress=ip_address))
except:
    print("Symfony web app is not running...")
