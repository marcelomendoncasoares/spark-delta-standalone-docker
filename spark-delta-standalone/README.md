<h1> Spark + Delta Docker Standalone</h1>
<p>
  <a href="https://github.com/marcelomendoncasoares/spark-delta-standalone-docker/tree/main/spark-delta-standalone">
    <img alt="GitHub" src="https://img.shields.io/badge/GitHub-marcelomendoncasoares-181717.svg?style=flat&logo=github" />
  </a>
  <a href="https://hub.docker.com/r/marcelomendoncasoares/spark-delta-standalone/">
    <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/marcelomendoncasoares/spark-delta-standalone.svg" />
  </a>
  <a href="http://www.apache.org/licenses/LICENSE-2.0.html">
    <img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache 2.0-blue.svg" target="_blank" />
  </a>
</p>

Based on the [spark-delta](../spark-delta/Dockerfile) image, provides a
dynamically configurable standalone Spark cluster. It can be used in a
`docker-compose` in combination with an application container, such as the
example in the [docker-compose.yml](docker-compose.yml) file in this folder, or
directly as a standalone cluster. Exposes several optional environment
variables for configuration of the driver and executors.

- [Configuring the cluster](#configuring-the-cluster)
- [Docker compose example](#docker-compose-example)
- [Docker run example](#docker-run-example)
- [Building](#building)
- [License](#license)

## Configuring the cluster

Configure a Spark standalone cluster based on the available resources and the
instructions provided by the user through environment variables.The cluster
will contain a master and one worker with several executors, as is recommended
by Spark documentation (https://issues.apache.org/jira/browse/SPARK-30978).

The worker memory and cores will default to the sum of the configured memory
and cores for all executors, so it does not need to be directly configured. The
following environment variables can be used to configure the cluster:

    - FREE_CORES: Default: '1'
        Number of cores to be left free for the OS or other apps.

    - DRIVER_CORES: Default: '1'
        Number of cores to be used by the driver.

    - MIN_EXECUTOR_CORES: Default: '1'
        Minimum number of cores to be used by each executor. The actual number
        of cores used by each executor will be the minimum between this value
        and the number of cores available divided by the number of executors.

    - FREE_MEMORY: Default: '10%, 1GB' (the "GB" symbol is required)
        Memory to be left free for the OS or other apps. Can be provided in one
        of the following formats:
            * Percentage only: "10%" or "0.1"
            * Percentage and minimum value in GB: "10%, 1GB"
            * Exact value in GB: "1GB"

    - DRIVER_MEMORY: Default: '10%, 1GB'
        Percentage of memory to be used by the driver. Same format and
        specification possibilities as `FREE_MEMORY`.

    - EXECUTOR_MEMORY: Default: '16GB'
        Memory to be used by each executor. Will divide the available memory to
        calculate the number of executors, if `NUM_EXECUTORS` is not provided.
        Only the exact value in GB is accepted and the "GB" symbol is required.

    - NUM_EXECUTORS: Default: '0'
        Number of executors to be started. If < 1, will determine the number of
        executors will be calculated based on the available memory and the
        memory to be used by each executor.

    - AUTO_SCALE: Default: 'true'
        Whether to enable the Spark 'dynamic allocation' feature. If enabled,
        the number of executors will start from `NUM_EXECUTORS` and use this as
        maximum after scaling down and up according to the workload. Other
        executor configs (memory and cores) will still be respected when
        spawning new executors during scale up.

All configuration is optional. If no configuration is provided, the cluster
will be started with the default configurations.

> Note that, beside all memory configurations requiring the `GB` symbol, _it is
> not possible to use other units besides GB_.

## Docker compose example

To start the cluster, run the following command:

```bash
docker-compose up
```

This will start a spark cluster on the host machine at `localhost:7077` that
can be accessed by any SparkSession. A submit example is already present on the
[`docker-compose.yml`](docker-compose.yml) file that will compute the `pi`
number and can be observer in the [Spark UI](http://localhost:8080).

The running cluster can also be used to back a SparkSession in a Python
application, for example:

```python
from pyspark.sql import SparkSession

spark = (
    SparkSession.builder
    .appName("test")
    .master("spark://localhost:7077")
    .getOrCreate()
)

spark.range(1, 100).write.format("delta").save("delta_table")
spark.read.load("delta_table").show()
spark.sql("drop table delta_table")
```

## Docker run example

As the cluster is contained inside a single container, it can also be started
directly with `docker run`, by simply running:

```bash
docker run -i --rm \
    -p 4040:4040 -p 7077:7077 -p 8080:8080 -p 8081:8081 \
    -t marcelomendoncasoares/spark-delta:latest
```

## Building

To build the image, run the following command:

```bash
docker build -t marcelomendoncasoares/spark-delta-standalone --build-arg SPARK_VERSION="3.3.3" .
```

The build argument `SPARK_VERSION` is optional and will defaults to `latest` if
not provided. It maps to the `spark-delta` image version and will fail if such
version is not available. In such cases, be sure to build the base version
first. See the [spark-delta building](../spark-delta/README.md#building)
section for more details.

---

## License

Copyright &copy; 2023 Marcelo Soares.

Licensed under the
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
