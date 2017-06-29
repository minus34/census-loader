FROM python:3.6
MAINTAINER Alex Leith <aleith@crcsi.com.au>


ADD ./ /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD python3 server.py \
	
