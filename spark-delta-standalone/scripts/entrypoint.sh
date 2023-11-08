#!/bin/sh
#
# Call all runtime scripts and then the CMD from the Dockerfile.

# Dyanmically configure and start the local cluster.
python3 /root/scripts/start_cluster.py

# This will exec the CMD from your Dockerfile
exec "$@"
