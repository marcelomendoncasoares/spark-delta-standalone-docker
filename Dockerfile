# Spark + Delta Standalone image.
#
# An extension of the official Spark image ready to run Delta Lake jobs and
# to connect to Azure resources (Event Hubs, Blob Storage, etc.) or AWS S3.
# Uses delta as the default file format for Spark catalog tables. The other
# extra jars can be enabled by setting the `EXTRA_CLOUD_JARS` environment
# variable to `true`.
#
# If the `START_SPARK_CLUSTER` environment variable is set to `true`, the
# container will start a standalone Spark cluster with the master and a worker
# with its executors configured according to the environment variables exposed
# on the `scripts/start_cluster.py` script. See the README.md file for more
# information on the available variables.

ARG SPARK_VERSION=latest
FROM apache/spark:${SPARK_VERSION} AS base

# We will be running our Spark jobs as `root` user.
USER root

# Add the Spark binaries to the PATH for simplicity.
COPY spark_conf/ $SPARK_HOME/conf/
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH
ENV SPARK_LOCAL_DIRS=/root/data

# Prepare delta jars and other extras for later configuration.
COPY scripts/ /root/scripts/
RUN chmod +x /root/scripts/*.sh
RUN /root/scripts/pre_configure_jars.sh

WORKDIR /root

# The entrypoint script will be executed when the container is started to start
# a standalone cluster with the master and the configured number of executors.
ENTRYPOINT ["/root/scripts/entrypoint.sh"]

# Expose ports for monitoring.
# - 4040: SparkContext Web UI
# - 7077: Spark Master.
# - 8080: Spark Master Web UI.
# - 8081: Spark Worker Web UI.
EXPOSE 4040 7077 8080 8081

CMD ["/bin/bash"]
