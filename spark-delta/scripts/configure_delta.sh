#!/bin/bash
#
# Use pip dependency resolver to define which delta version to install and
# preserves the version in the environment variables for other commands and
# for any usage in the container.
#
# The spark version must be extracted because it can be `latest` and it is
# needed for the jars download. The delta version is bounded to the spark
# version, so pip dependency resolution is used to check which is the delta
# version for the current spark version. Newer pip is needed to support the
# `--dry-run` flag.

python3 -m pip install --upgrade "pip>=23.2.1"
spark_version=$(cat $SPARK_HOME/python/pyspark/version.py | grep -o "[0-9][.][0-9][.][0-9]")
pip_resolver=$(python3 -m pip install pyspark==$spark_version delta-spark --dry-run)
delta_version=$(echo $pip_resolver | grep -oP "delta-spark-\K([0-9.]*)")
python3 -m pip cache purge

echo "export SPARK_VERSION=${spark_version}" >> /etc/bash.bashrc
echo "export DELTA_VERSION=${delta_version}" >> /etc/bash.bashrc

# Delta changed the package name from `core` to `spark` in version 3.0.0.
if [ "${delta_version:0:1}" -lt "3" ]; then
    delta_package_name="core"
else
    delta_package_name="spark"
fi

# Dynamically set the spark.jars.packages property to include the jars needed
# according to the spark, hadoop and delta versions.
jars="org.apache.spark:spark-sql-kafka-0-10_2.12:${spark_version}"
jars="$jars,com.microsoft.azure:azure-eventhubs-spark_2.12:2.3.21"
jars="$jars,com.microsoft.azure:azure-eventhubs:3.3.0"
jars="$jars,io.delta:delta-${delta_package_name}_2.12:${delta_version}"
jars="$jars,org.apache.hadoop:hadoop-aws:3.3.0"
jars="$jars,org.apache.hadoop:hadoop-azure:3.3.0"
echo "spark.jars.packages $jars" >> ${SPARK_HOME}/conf/spark-defaults.conf
