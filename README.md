# Project Title
broker - a trivial but complete broker for Cloud Foundry in python/Flask

## Introduction

The current version of "broker" is a rewrite of "pybroker", and
intended to use more pythonic flask-y constructs - including
blueprints, as well as be more natural to the flask command line.

"broker" is a complete but minimal cloud foundry broker written in
python using the Flask framework.

It implements a service "Dream" that provides large dreams (for a fee)
or small dreams (for free).  It merely maintains an internal data
structure with instances that have created and bound.

The data stored at the instance creation and binding are the data
POSTed into the broker endpoints -- os it may be used to test what is
in the data structures.

# Creating the broker
A simple "cf push" by admin will run the broker/app.py application, it
is probably best if this is pushed into a system space/org

The shell scripts "expose-broker.sh" and "hide-broker.sh" are cf-cli
scripts taht will (respectively) instantiate the broker application as
a service, and place it in the marketplace.  The "hide-broker" will
remove it from the marketplace.

Note that re-pushing the application destroys the "data structure" and
GUIDs in the application -- which will confuse the marketplace if
bindings are already in place.  The hide-broker/expose-broker are
intended to mitigate issues that will arise from re-pushes.
Investigate the cf-cli purge-service-binding/purge-service-offering to
recover from re-pushes.

## Known working functionality
- create-service - service and plans work
- service - show service information
- un/bind-service - binding/unbinding works as expected
- upgrade-service - a no-op, but succeeds
- rename-service - rename service instance
- update-service - switch between plans
- service-key - fixed, null values
- service-keys - fixed, null values
- delete-service-key - works
- delete-service - remove service entry
- purge-service-offering - handy when you upgrade the broker without deleting service instance

## Testing
A simple "test-broker.sh" script is intended to verify correct
operation of the broker.  More contributions here are welcome.

## Dependencies
"broker" uses Flask and logger (and see requirements.txt)

## Development
"broker" is a simple flask app.  To test from the command line:
```bash
% FLASK_DEBUG=1 FLASK_APP='broker.app' flask run
```

## To Do
Contributions welcome here.

I've tried to make this as complete as possible, contributions to make
it more complete are welcome!
