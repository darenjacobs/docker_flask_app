import os
from flask import Flask, request, jsonify
import logging
from logging.handlers import RotatingFileHandler
import redis
import hashlib

app = Flask(__name__)


# helper method that logs the error and then returns the JSON to be returned as the response
def log_error_and_return(message, http_code):
    app.logger.error("%s", message)
    return jsonify(
        err_msg=message
    ), http_code


try:
    cache = redis.StrictRedis(host=os.environ['MESSAGES_REDIS_HOST'], port=6379, db=0)
    cache.ping()
except Exception as err:
    app.logger.error('ERROR: %s', err)
    exit('Failed to connect, terminating.')


@app.route('/messages', methods=['POST'])
def add_message():
    if 'message' not in request.get_json():
        return log_error_and_return("I was expecting to receive a POST param called 'message'.", 400)

    data = request.get_json()
    message = data['message']

    hash = hashlib.sha256(message.encode('ascii')).hexdigest()
    if hash:
        cache.set(hash, message)
        app.logger.info("Added new message: %s", message)
        return jsonify(
                digest=hash
        ), 201

    # just in case we failed to get a SHA256 hash in line 32
    return log_error_and_return("Something bad happened to me:(", 500)


@app.route('/messages/<hash>', methods=['GET'])
def get_message(hash):
    message = cache.get(hash)
    if not message:
        return log_error_and_return("Message not found for hash: " + hash, 404)

    return jsonify(
            message=message.decode('utf-8')
    ), 200


if __name__ == '__main__':

    LOG_DIR = '/opt/messages/logs'
    CERT_DIR = '/opt/messages/certs'
    CERT_FILE = '/localhost.crt'
    CERT_KEY = '/localhost.key'

    formatter = logging.Formatter(
                    "[%(asctime)s] {%(pathname)s:%(lineno)d} %(levelname)s - %(message)s")

    # app log
    app_handler = RotatingFileHandler(LOG_DIR+'/app.log', maxBytes=100000000, backupCount=5)
    app.logger.setLevel(logging.INFO)
    app_handler.setFormatter(formatter)
    app.logger.addHandler(app_handler)

    # access log
    access_logger = logging.getLogger('werkzeug')
    access_handler = RotatingFileHandler(LOG_DIR+'/access.log', maxBytes=100000000, backupCount=5)
    access_logger.addHandler(access_handler)

    app.run(host='0.0.0.0', ssl_context=(CERT_DIR+CERT_FILE, CERT_DIR+CERT_KEY))
