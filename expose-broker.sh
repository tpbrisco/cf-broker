set -e
# set broker URL if defined
if [[ -z "$BROKER_URL" ]]; then
    echo "set BROKER_URL for the broker"
    exit 1
fi
echo "Using broker URL ${BROKER_URL}"

# use "--space-scoped" if not admin
cf create-service-broker dream user pass ${BROKER_URL}
cf enable-service-access dream
