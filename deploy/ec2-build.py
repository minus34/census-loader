
import boto3
import logging
import os
import paramiko
import time
import uuid

from datetime import datetime

logging.getLogger("paramiko").setLevel(logging.INFO)

BLUEPRINT = "ubuntu_16_04_1"
# BUILDID = "nano_1_2"
BUILDID = "medium_1_2"
# KEY_PAIR_NAME = "Default"
AVAILABILITY_ZONE = "ap-southeast-2a"  # Sydney, AU
PEM_FILE = "/Users/hugh.saalmans/.aws/LightsailDefaultPrivateKey-ap-southeast-2.pem"
INSTANCE_NAME = "census_loader_instance_v2"


def main():
    full_start_time = datetime.now()

    # get uuid based passwords
    password_array = str(uuid.uuid4()).split("-")
    admin_password = password_array[1] + password_array[4].upper() + password_array[0] + password_array[3].upper()
    password_array = str(uuid.uuid4()).split("-")
    readonly_password = password_array[3] + password_array[2].upper() + password_array[4] + password_array[0].upper()

    # create lightsail client
    lightsail_client = boto3.client('lightsail')

    # blueprints = lightsail_client.get_blueprints()
    # for bp in blueprints['blueprints']:
    #     if bp['isActive']:
    #         print('{} : {}'.format(bp['blueprintId'], bp['description']))

    # bundles = lightsail_client.get_bundles(includeInactive=False)
    # for bundle in bundles['bundles']:
    #     for k, v in bundle.items():
    #         print('{} : {}'.format(k, v))

    response_dict = lightsail_client.create_instances(
        instanceNames=[INSTANCE_NAME],
        availabilityZone=AVAILABILITY_ZONE,
        blueprintId=BLUEPRINT,
        bundleId=BUILDID
        # userData=initial_script
    )
    logger.info("\t\t{0}".format(response_dict))

    # wait until instance is running
    instance_dict = get_lightsail_instance(lightsail_client, INSTANCE_NAME)

    while instance_dict["state"]["name"] != 'running':
        logger.info('\t\tWaiting 15 seconds... instance is %s' % instance_dict["state"]["name"])
        time.sleep(15)
        instance_dict = get_lightsail_instance(lightsail_client, INSTANCE_NAME)

        # open the Postgres port on the instance
        response_dict = lightsail_client.open_instance_public_ports(
            portInfo={
                'fromPort': 5432,
                'toPort': 5432,
                'protocol': "tcp"
            },
            instanceName=INSTANCE_NAME
        )
        logger.info("\t\t{0}".format(response_dict))

    logger.info('\t\tWaiting 30 seconds... instance is booting')
    time.sleep(30)

    instance_ip = instance_dict["publicIpAddress"]
    cpu_count = instance_dict["hardware"]["cpuCount"]
    logger.info("\t\tPublic IP address: {0}".format(instance_ip))

    # create SSH client
    key = paramiko.RSAKey.from_private_key_file(PEM_FILE)
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh_client.connect(hostname=instance_ip, username="ubuntu", pkey=key)

    logger.info("Connected to new server via SSH : {0}".format(datetime.now() - full_start_time))
    logger.info("")

    # run each bash command
    bash_file = os.path.abspath(__file__).replace(".py", ".sh")
    bash_commands = open(bash_file, 'r').read().split("\n")

    for cmd in bash_commands:
        if cmd[:1] != "#" and cmd[:1].strip(" ") != "":  # ignore comments and blank lines
            # replace text with passwords if required
            if "<postgres-password>" in cmd:
                cmd = cmd.replace("<postgres-password>", admin_password)
            if "<rouser-password>" in cmd:
                cmd = cmd.replace("<rouser-password>", readonly_password)

            run_ssh_command(ssh_client, cmd, admin_password)

    # data and code loaded - run the thing using gunicorn!
    cmd = "sudo gunicorn -w {0} -D --pythonpath ~/git/census-loader/web/ -b 0.0.0.0:80 single_server:app"\
        .format(cpu_count * 2)
    run_ssh_command(ssh_client, cmd, admin_password)

    # TODO: Put NGINX in front of gunicorn as a reverse proxy"

    ssh_client.close()

    logger.info("Public IP address : {}".format(instance_ip))
    logger.info("")
    logger.info("Admin password    : {}".format(admin_password))
    logger.info("Readonly password : {}".format(readonly_password))
    logger.info("")
    logger.info("Total time : : {0}".format(datetime.now() - full_start_time))
    logger.info("")
    return True


def get_lightsail_instance(lightsail_client, name):
    response = lightsail_client.get_instance(instanceName=name)

    return response["instance"]


def run_ssh_command(ssh_client, cmd, admin_password):
    start_time = datetime.now()
    logger.info("START : {0}".format(cmd))

    # run command
    # try:
    stdin, stdout, stderr = ssh_client.exec_command(cmd)

    # send Postgres user password when running pg_restore
    if "pg_restore" in cmd:
        stdin.write(admin_password + '\n')
        stdin.flush()

    # log everything

    # for line in stdin.read().splitlines():
    #     if line:
    #         logger.info(line)
    stdin.close()

    for line in stdout.read().splitlines():
        pass
        # if line:
        #     logger.info("\t\t{0}".format(line))
    stdout.close()

    for line in stderr.read().splitlines():
        if line:
            logger.info("\t\t{0}".format(line))
    stderr.close()

    logger.info("END   : {0} : {1}".format(cmd, datetime.now() - start_time))

    # except:
    #     logger.warning("FAILED! : {0} : {1}".format(cmd, datetime.now() - start_time))

    logger.info("")


if __name__ == '__main__':
    logger = logging.getLogger()

    # set logger
    log_file = os.path.abspath(__file__).replace(".py", ".log")
    logging.basicConfig(filename=log_file, level=logging.DEBUG, format="%(asctime)s %(message)s",
                        datefmt="%m/%d/%Y %I:%M:%S %p")

    # setup logger to write to screen as well as writing to log file
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logger.info("")
    logger.info("Start ec2-build")

    if main():
        logger.info("Finished successfully!")
    else:
        logger.fatal("Something bad happened!")

    logger.info("")
    logger.info("-------------------------------------------------------------------------------")
