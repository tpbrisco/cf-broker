
from flask import (
    Flask,
    Blueprint)

# minimum broker version supported
X_BROKER_API_MAJOR_VERSION = 2
X_BROKER_API_MINOR_VERSION = 10
X_BROKER_API_VERSION_NAME = 'X-Broker-Api-Version'

content_headers = {'Content-Type': 'text/json'}
