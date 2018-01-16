# Dockerized Paxos web service submission


### DEPLOYMENT
```
$ tar zxvf docker_flask_app.tar.gz
$ cd docker_flask_app
$ docker-compose up -d
```

APP ROOT DIR: /opt/messages
CERT DIR: /opt/messages/certs
LOG DIR: /opt/messages/logs

### ENV VARS
MESSAGES_REDIS_HOST is an ENV variable read in app.py to determine the Redis host to connect to.

By default, it is set to 'redis' which is the label assigned to the Redis container.
This can be changed by editing ```docker-compose.yml```:
```
  app:
    ...
    ...
    environment:
      - MESSAGES_REDIS_HOST=NEW_REDIS_HOST
```

### LOGS
The app creates two logs:

- /opt/messages/logs/app.log
- /opt/messages/logs/access.log

```maxBytes``` and ```backupCount``` values allow the files to rollover at a predetermined size. When the size is about to be exceeded, the file is closed and a new file is silently opened for output.
Rollover occurs whenever the current log file is nearly maxBytes in length.
If backupCount is non-zero, the system will save old log files by appending the extensions ‘.1’, ‘.2’ etc., to the filename.

The default values set in app.py are:
```
maxBytes: 100000000
backupCount: 5
```


To view the app and access logs:
```
$ CONTAINER_ID=$(docker ps |grep dockerflaskapp_app |cut -f 1 -d' ')

$ docker exec -it $CONTAINER_ID cat /opt/messages/logs/app.log /opt/messages/logs/access.log
```
or:
```
$ docker cp $CONTAINER_ID:/opt/messages/logs/app.log /path/to/dest
$ docker cp $CONTAINER_ID:/opt/messages/logs/access.log /path/to/dest
```

### APP WATCHDOG

Add the following to the crontab:
```
* * * * * /path/to/service_test.sh
```
This will check whether the app is alive and well at one minute intervals and restart the containers in the event the test failed.

```
$ cat service_test.sh
#!/bin/sh
python /path/to/test.py --port 5000 --cert-path /path/to/localhost.crt
RC=$?
if [ $RC -ne 0 ]
then
  echo `date` | mail -s "Message containers restarted" devops@example.com
  docker-compose restart
fi
```

### CERT and KEY

This archive includes a self signed certificate and key issued for 'localhost'.
These can easily be replaced with valid ones. Place the cert and key under docker_flask_app/certs and set the new file names in app.py.

### DEFAULT USER

For better security, the application runs with the non privileged user ```daemon```.  You can easily change the user by editing the Dockerfile.
To create a different user and run the app with it, add the following line to the Dockerfile, where USERNAME is the name of the desired user:
```
RUN useradd -ms /bin/false USERNAME
```
Then adjust these lines accordingly:
```
RUN chown USERNAME /opt/messages/logs
RUN chown root.USERNAME /opt/messages/certs/*
USER USERNAME
CMD ["python3", "/opt/messages/app.py"]
```

### TESTING

Use the [test script](https://github.com/paxos-bankchain/devops-test-script)
```
$ python /path/to/test.py --port 5000 --cert-path /path/to/localhost.crt
```

Sample output:
```
https://localhost:5000/messages/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa correctly not found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found
https://localhost:5000/messages POSTed successfully
https://localhost:5000/messages/fcde2b2edba56bf408601fb721fe9b5c338d10ee429ea04fae5511b68fbf8fb9 correctly found
https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae correctly found

***************************************************************************
All tests passed!
***************************************************************************
```

You can also test using curl as follows:
```
$ curl -X POST -H "Content-Type: application/json" -d '{"message":"foo"}' --cacert /path/to/localhost.crt https://localhost:5000/messages

{
  "digest": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae"
}

$ curl --cacert /path/to/localhost.crt https://localhost:5000/messages/2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae
{
  "message": "foo"
}

$ curl --cacert /path/to/localhost.crt https://localhost:5000/messages/aaaaaaaaaaaaaaaaaaa
{
  "err_msg": "Message not found for hash: aaaaaaaaaaaaaaaaaaa"
}
```

### SCALING

For scaling we could deploy replicas of the docker_flask_app and could scale the reads/writes of Redis. For Redis we could create read slaves for the GET requests. However, it is important to test performance before scaling. With Redis we could create additional servers and slaves, enable caching and consider data compression. We should also consider writing to and increasing memory per server. If this application becomes more complex we'd need to ensure write concise functions that we are scaling queries.

Ref: https://redislabs.com/ebook/part-3-next-steps/chapter-10-scaling-redis/

### NOTE ABOUT HTTP RETURN CODES

When successfully inserting a new message, the /messages endpoint returns [HTTP 201](https://httpstatuses.com/201) since it creates a new record. The specification should clarify that that is the HTTP code to return.
