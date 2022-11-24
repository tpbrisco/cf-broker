
import os
import logging
import uuid
from flask import Flask
from broker import broker

logger = logging.getLogger('dream_broker')
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

app = Flask(__name__)
app.config['LOG'] = logger
app.config['JSON_AS_ASCII'] = True
app.config['SECRET_KEY'] = uuid.uuid4().hex
app.register_blueprint(broker.broker_bp, url_prefix='/v2')
app.add_url_rule('/console', view_func=broker.service_console)


def main():
    port = int(os.getenv('VCAP_APP_PORT', '8000'))
    print("port={}".format(port))
    app.run(host='0.0.0.0', port=port)


if __name__ == "__main__":
    main()
