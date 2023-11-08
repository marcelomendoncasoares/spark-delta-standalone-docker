# Spark + Delta image.
#
# An extension of the official Spark image ready to run Delta Lake jobs and
# to connect to Azure resources (Event Hubs, Blob Storage, etc.) or AWS S3.
# Uses Delta as the default file format for Spark catalog tables.

ARG SPARK_VERSION=latest
FROM apache/spark:${SPARK_VERSION} AS base

# We will be running our Spark jobs as `root` user.
USER root

COPY spark_conf/ $SPARK_HOME/conf/
ENV PATH=$SPARK_HOME/bin:$SPARK_HOME/sbin:$PATH

COPY scripts/ /root/scripts/
RUN chmod +x /root/scripts/*.sh
RUN /root/scripts/configure_delta.sh

# Working directory is set to the home folder of `root` user.
WORKDIR /root

# Expose ports for monitoring.
# - 4040: SparkContext Web UI
# - 7077: Spark Master.
# - 8080: Spark Master Web UI.
# - 8081: Spark Worker Web UI.
EXPOSE 4040 7077 8080 8081

CMD ["/bin/bash"]
