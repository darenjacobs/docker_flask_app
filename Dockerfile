FROM debian:9
# skip install suggested and recommended packages to keep the container as small as possible
RUN apt-get update && apt-get install --no-install-recommends --no-install-suggests  -y \
  vim-nox \
  python3 \
  python3-pip \
  python3-setuptools

# deploy needed Python modules
RUN pip3 install flask redis

# root dir for the app will be /opt/messages
ADD messages/* /opt/messages/
RUN mkdir /opt/messages/logs
RUN chown daemon /opt/messages/logs

# copy self signed cert and key and set proper permissions
ADD certs/* /opt/messages/certs/
RUN chown root.daemon /opt/messages/certs/*
RUN chmod 640 /opt/messages/certs/*

# run the app with the daemon user for better security
USER daemon
CMD ["python3", "/opt/messages/app.py"]

EXPOSE 5000
