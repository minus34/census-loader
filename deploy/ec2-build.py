
import boto3
import logging
import os

BLUEPRINT = "ubuntu_16_04_1"
BUILDID = "nano_1_2"
# KEY_PAIR_NAME = "Default"
AVAILABILITY_ZONE = "ap-southeast-2a"  # Sydney, AU


def main():

    # get AWS credentials (required to copy pg_dump files from S3)
    aws_access_key_id = ""
    aws_secret_access_key = ""
    cred_array = open("/Users/hugh.saalmans/.aws/credentials", 'r').read().split("\n")

    for line in cred_array:
        bits = line.split("=")
        if bits[0].lower() == "aws_access_key_id":
            aws_access_key_id = bits[1]
        if bits[0].lower() == "aws_secret_access_key":
            aws_secret_access_key = bits[1]

    # load bash script
    bash_file = os.path.abspath(__file__).replace(".py", ".sh")
    bash_script = open(bash_file, 'r').read().format(aws_access_key_id, aws_secret_access_key)

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
        instanceNames=['census_loader_instance'],
        availabilityZone=AVAILABILITY_ZONE,
        blueprintId=BLUEPRINT,
        bundleId=BUILDID,
        userData=bash_script
    )

    logger.info(response_dict)

    return True


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
