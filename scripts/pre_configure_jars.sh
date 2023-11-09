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

dynamic_configs=/root/scripts/dynamic_configs.env
echo "source $dynamic_configs" >> /etc/bash.bashrc

python3 -m pip install --upgrade "pip>=23.2.1"
spark_version=$(cat $SPARK_HOME/python/pyspark/version.py | grep -o "[0-9][.][0-9][.][0-9]")
pip_resolver=$(python3 -m pip install pyspark==$spark_version delta-spark --dry-run)
delta_version=$(echo $pip_resolver | grep -oP "delta-spark-\K([0-9.]*)")
python3 -m pip cache purge

echo "export SPARK_VERSION=${spark_version}" >> $dynamic_configs
echo "export DELTA_VERSION=${delta_version}" >> $dynamic_configs

# Remove the version suffix from the jars example for ease of use.
example_path=/opt/spark/examples/jars/spark-examples_2.12
mv $example_path-$spark_version.jar $example_path.jar

# Delta changed the package name from `core` to `spark` in version 3.0.0.
if [ "${delta_version:0:1}" -lt "3" ]; then
    delta_package_name="core"
else
    delta_package_name="spark"
fi

# Store the delta package name in the environment variable DELTA_JAR_PACKAGE
# that will be included in the `spark.jars.packages` property of the
# `spark-defaults.conf` file in runtime.
delta_package=io.delta:delta-${delta_package_name}_2.12:${delta_version}
echo "export DELTA_JAR_PACKAGE=${delta_package}" >> $dynamic_configs

# Store extra cloud jars in the `EXTRA_CLOUD_JARS_PACKAGES` environment
# variable that will be set to the `spark-defaults.conf` file if configured.
extra_jars="org.apache.spark:spark-sql-kafka-0-10_2.12:${spark_version}"
echo "export EXTRA_BASE_JARS_PACKAGES=${extra_jars}" >> $dynamic_configs

azure_jars="com.microsoft.azure:azure-eventhubs-spark_2.12:2.3.22"
azure_jars="$azure_jars,org.apache.hadoop:hadoop-azure:3.3.0"
echo "export EXTRA_AZURE_JARS_PACKAGES=${azure_jars}" >> $dynamic_configs

aws_jars="org.apache.spark:spark-streaming-kinesis-asl_2.12:jar:${spark_version}"
aws_jars="$aws_jars,org.apache.hadoop:hadoop-aws:3.3.0"
echo "export EXTRA_AWS_JARS_PACKAGES=${aws_jars}" >> $dynamic_configs
