# census-map-deploy
Deploys the CensusMap to AWS with single Python script.

Architecture is a single AWS Lightsail (e.g simple EC2) server with:
* Postgres 9.6 with PostGIS 2.3
* A Python/Flask app using gunicorn 

### Pre-requisites
- Python 3.x with Boto3 and Paramiko packages installed

### Process
1. Install AWS CLI tools
2. Set your AWS key and secret key in the default AWS credentials file (see the AWS CLI doco for more info)
3. Edit ec2-build.py for your: server type & size, certificate file, AWS region and server name
4. Run ec2-build.py
5. When finished (~20 mins): SSH into your new AWS server and run these commands
- cd ~/git/census-loader/web
- sudo gunicorn -w 4 -b 0.0.0.0:80 single_server:app &
6. Test the app's running at your server's IP address 

### Notes
* Haven't worked out how to run gunicorn through Python & Paramiko (hence the 2 manually run commands at the end)
* NGINX should be running on top of gunicorn for improved security (pull request anyone?)

### Data License

Source: [Australian Bureau of Statistics](http://www.abs.gov.au/websitedbs/d3310114.nsf/Home/Attributing+ABS+Material)
