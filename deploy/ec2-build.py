
import boto3
import logging
import os

BLUEPRINT = "ubuntu_16_04_1"
BUILDID = "nano_1_2"
KEY_PAIR_NAME = "Default"
AVAILABILITY_ZONE = "ap-southeast-2"  # Sydney, AU

# AWS_ACCESS_KEY = 'yourAccessKey'
# AWS_SECRET_ACCESS_KEY = 'yourSecretKey'

def main():

    # load bash script
    bash_file = os.path.abspath(__file__).replace(".py", ".sh")
    bash_script = open(bash_file, 'r').read()

    lightsail_client = boto3.client('lightsail')

    # blueprints = lightsail_client.get_blueprints()
    # for bp in blueprints['blueprints']:
    #     if bp['isActive']:
    #         print('{} : {}'.format(bp['blueprintId'], bp['description']))

    # bundles = lightsail_client.get_bundles(includeInactive=False)
    # for bundle in bundles['bundles']:
    #     for k, v in bundle.items():
    #         print('{} : {}'.format(k, v))

    lightsail_client.create_instances(
        instanceNames=['python_generated_census_loader_instance'],
        availabilityZone='us-east-1a',
        blueprintId=BLUEPRINT,
        bundleId=BUILDID,
        userData=bash_script,
        keyPairName=KEY_PAIR_NAME
    )

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
