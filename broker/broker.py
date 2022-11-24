
# broker requirements are outlined at
# https://github.com/openservicebrokerapi/servicebroker/blob/v2.12/spec.md#provisioning

from flask import (Blueprint,
                   request,
                   abort,
                   url_for,
                   send_file,
                   make_response,
                   current_app)
from functools import wraps
import json
import uuid

broker_bp = Blueprint('broker_bp',
                      __name__,
                      template_folder='templates',
                      static_folder='static',
                      static_url_path='assets')

x_broker_api_major_version = 2
x_broker_api_minor_version = 10
x_broker_api_version_name = 'X-Broker-Api-Version'

content_headers = {'Content-Type': 'text/json'}

# broker plans
big_dreams = {
    "id": str(uuid.uuid4()),  # note that this will change with each restart
    "name": "big_dreams",
    "description": "A Big Dream",
    "plan_updateable": True,
    "metadata": {
        "bullets": [
            "Dreams are cheap",
            "Even big dreams",
        ],
    },
    "free": False,
}
small_dreams = {
    "id": str(uuid.uuid4()),  # note that this will change with each restart
    "name": "small_dreams",
    "description": "A Small Dream",
    "plan_updateable": True,
    "metadata": {
        "bullets": [
            "Small dreams are barely worth having",
        ],
    },
    "free": True,
}

# define the service
dream_service = {
    "id": str(uuid.uuid4()),  # note that this will change with each restart
    "name": "dream",
    "description": "Imaginary Service",
    "bindable": True,
    "plan_updateable": True,
    "plans": [big_dreams, small_dreams],
    "dashboard_client": {
        "id": "user",
        "secret": "pass",
        "redirect_uri": 'overwritten_later',
    },
    "metadata": {
        "listing": {
            "imageUrl": "",  # while this is documented as here, see below
            "blurb": "dreams are cheap",
            "longDescription": "Dream services ranging from free to cheap",
            },
        "bullets": [
            "Dreams of all sizes",
        ],
        "imageUrl": "",  # where the imageUrl actually works (see above)
        "displayName": "Broker of dreams",
        },
}

# full service definition
services = {"services": [dream_service]}

service_template = {
    'id': '',
    'space_guid': '',
    'plan_id': '',
    'bindings': {},
}

# fake database of services
instances = dict()

# utility functions


def find_instance(id):
    '''find service instance by id'''
    current_app.config['LOG'].debug("find_instance: {}".format(id))
    if id in instances.keys():
        return instances[id]
    return None


def delete_instance(id):
    '''delete instance by instance id'''
    current_app.config['LOG'].debug("delete_instance: {}".format(
        json.dumps(instances, indent=2)))
    if id in instances.keys():
        del instances[id]
    return {}

#
# define error handling for checking api version
#


def api_version_is_valid(api_version):
    '''verify if version number is compatible'''
    version_data = api_version.split('.')
    if (float(version_data[0]) != x_broker_api_major_version or
        (float(version_data[0]) == x_broker_api_major_version and
         float(version_data[1]) < x_broker_api_minor_version)):
        return False
    return True


def requires_api_version(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_version = request.headers.get(x_broker_api_version_name)
        if (not api_version or not api_version_is_valid(api_version)):
            abort(412)
        return f(*args, **kwargs)
    return decorated


@broker_bp.errorhandler(412)
def version_mismatch(error):
    '''return precondition failed "http code 412" on incorrect broker version'''
    return 'version mismatch.  expected {}: {}.{}'.format(
        x_broker_api_version_name,
        x_broker_api_major_version,
        x_broker_api_minor_version), 412

# enforce authentication from the marketplace


def check_auth(username, password):
    if not (username == 'user' and password == 'pass'):
        current_app.config['LOG'].warning('marketplace auth failed')
        return False
    else:
        current_app.config['LOG'].info('marketplace auth ok')
    return True


def authenticate():
    return make_response(
        json.dumps({'www-authenticate': 'basic realm="login required"'},
                   indent=2), 401)


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated

#
# define broker endpoints
#


@broker_bp.route('/image', methods=['GET'])
@broker_bp.route('/image/', methods=['GET'])
def service_image():
    current_app.config['LOG'].info("service_image called")
    return send_file('assets/batman.png',
                     attachment_file='logo.png',
                     mimetype='image/png')


@broker_bp.route('/console', methods=['GET'])
def service_console():
    current_app.config['LOG'].info("service_console called")
    resp_dict = {'dream_service': dream_service,
                 'instances': instances}
    return make_response(json.dumps(resp_dict, indent=2),
                         200, content_headers)


@broker_bp.route('/catalog')
@requires_api_version
@requires_auth
def catalog():
    """Create and return catalog item"""
    current_app.config['LOG'].info("catalog called")
    dream_service['dashboard_client']['redirect_uri'] = \
        request.url_root + url_for('broker_bp.service_console')[1:]
    dream_service['metadata']['imageUrl'] = \
        request.url_root + url_for('broker_bp.service_image')[1:]
    return make_response(json.dumps(services, indent=2), 200, content_headers)


@broker_bp.route('/service_instances/<instance_id>',
                 methods=['PUT', 'PATCH', 'DELETE'])
def service_instances(instance_id):
    if request.method == 'PUT':
        return service_instances_put(instance_id)
    elif request.method == 'PATCH':
        return service_instances_patch(instance_id)
    elif request.method == 'DELETE':
        return service_instances_delete(instance_id)
    err = {"description":
           "services instances {} unknown method {}".format(
               instance_id, request.method)}
    return make_response(json.dumps(err, indent=2), 404, content_headers)


def service_instances_put(instance_id):
    '''create a service instance, with service and plan'''
    current_app.config['LOG'].info("service_instances PUT {}".format(
        instance_id))
    config = request.get_json()
    if not config and not (
            (config['service_id'] == dream_service['id']) and
            ((config['plan_id'] == big_dreams['id'] or
              config['plan_id'] == small_dreams['id']))):
        current_app.config['LOG'].debug("service/plan mismatch")
        err = {'description': "PUT service({}) or plan ({}) not me".format(
            config['service_id'], config['plan_id'])}
        return make_response(json.dumps(err, indent=2), 404, content_headers)
    current_app.config['LOG'].debug("config: {}".format(
        json.dumps(config, indent=2)))
    svc = service_template.copy()
    svc['id'] = instance_id
    for k in config.keys():
        svc[k] = config[k]
    instances[instance_id] = svc
    return make_response(json.dumps(svc), 201, content_headers)


def service_instances_patch(instance_id):
    '''patch an existing service plan with new config'''
    current_app.config['LOG'].info("service_instances PATCH {}".format(
        instance_id))
    config = request.json()
    current_app.config['LOG'].info("config: {}".format(json.dumps(config,
                                                                indent=2)))
    if not config and not (
            (config['service_id'] == dream_service['id']) and
            ((config['plan_id'] == big_dreams['id'] or
              config['plan_id'] == small_dreams['id']))):
        current_app.config['LOG'].debug("service/plan mismatch")
        err = {'description': "PATCH service({}) or plan ({}) not me".format(
            config['service_id'], config['plan_id'])}
        return make_response(json.dumps(err, indent=2), 404, content_headers)
    if instance_id not in instances:
        err = {"description":
               "{} not a valid service instance for PATCH".format(instance_id)}
        return make_response(json.dumps(err, indent=2), 404, content_headers)
    for k in config.keys():
        instances[instance_id][k] = config[k]
    return make_response(json.dumps(instances[instance_id], indent=2),
                         201, content_headers)


def service_instances_delete(instance_id):
    '''delete an existing service instance'''
    current_app.config['LOG'].info("services_instances DEL {}".format(
        instance_id))
    delete_instance(instance_id)
    return make_response(json.dumps({}), 200, content_headers)


@broker_bp.route('/service_instances/<instance_id>/service_bindings/<binding_id>',
                 methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def service_bindings(instance_id, binding_id):
    if request.method == 'GET':
        return service_bindings_get(instance_id, binding_id)
    elif request.method == 'PUT' or request.method == 'PATCH':
        return service_bindings_putch(instance_id,binding_id)
    elif request.method == 'DELETE':
        return service_bindings_delete(instance_id, binding_id)
    err = {"description":
           "services instances {} binding {} unknown method {}".format(
               instance_id, binding_id, request.method)}
    return make_response(json.dumps(err, indent=2), 404, content_headers)


def service_bindings_get(instance_id, binding_id):
    current_app.config['LOG'].info(
        "service_bindings GET instance {} binding {}".format(
            instance_id, binding_id))
    x = find_instance(instance_id)
    if x is None:
        rcode = {'description':
                 "service instance {} not found".format(instance_id)}
        return make_response(json.dumps(rcode), 410, content_headers)
    if binding_id in x['bindings'].keys():
        return make_response(json.dumps(x.bindings[binding_id], indent=2),
                             200, content_headers)
    rcode = {'description':
             "service binding {} not found".format(binding_id)}
    return make_response(json.dumps(rcode), 404, content_headers)


def service_bindings_putch(instance_id, binding_id):
    config = request.get_json()
    current_app.config['LOG'].info(
        "service_bindings_putch {} {} config {}".format(
            instance_id, binding_id, json.dumps(config, indent=2)))
    x = find_instance(instance_id)
    if x is None:
        rcode = {'description':
                 "service instance {} not found".format(instance_id)}
        return make_response(json.dumps(rcode), 410, content_headers)
    creds = {'username': 'user', 'password': 'pass'}
    x['bindings'][binding_id] = config
    x['bindings']['credentials'] = creds
    r_ok = 201
    if request.method == 'PATCH':
        r_ok = 200
    return make_response(json.dumps(creds, indent=2),
                         r_ok, content_headers)


def service_bindings_delete(instance_id, binding_id):
    current_app.config['LOG'].info(
        "service_bindings_delete {} {}".format(
            instance_id, binding_id))
    x = find_instance(instance_id)
    if binding_id in x['bindings'].keys():
        del x['bindings'][binding_id]
        return make_response(json.dumps(x), 200, content_headers)
    err = {"description":
           "service instance {} binding {} not found, cannot delete".format(
               instance_id, binding_id)}
    return make_response(json.dumps(err, indent=2), 404, content_headers)
