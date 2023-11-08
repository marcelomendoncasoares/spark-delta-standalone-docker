ARG SPARK_VERSION=latest
FROM marcelomendoncasoares/spark-delta:${SPARK_VERSION} AS base

# Working directory is set to the home folder of `root` user.
WORKDIR /root

# Expose ports for monitoring.
# - 4040: SparkContext Web UI
# - 7077: Spark Master.
# - 8080: Spark Master Web UI.
# - 8081: Spark Worker Web UI.
EXPOSE 4040 7077 8080 8081

# The entrypoint script will be executed when the container is started to start
# a standalone cluster with the master and the configured number of workers.
COPY scripts/ /root/scripts/
RUN chmod +x /root/scripts/*.sh
ENTRYPOINT ["/root/scripts/entrypoint.sh"]

CMD ["/bin/bash"]
