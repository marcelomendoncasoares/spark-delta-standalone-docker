<h1> Spark + Delta Docker</h1>
<p>
  <a href="https://github.com/marcelomendoncasoares/spark-delta-standalone-docker/tree/main/spark-delta">
    <img alt="GitHub" src="https://img.shields.io/badge/GitHub-marcelomendoncasoares-181717.svg?style=flat&logo=github" />
  </a>
  <a href="https://hub.docker.com/r/marcelomendoncasoares/spark-delta/">
    <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/marcelomendoncasoares/spark-delta.svg" />
  </a>
  <a href="http://www.apache.org/licenses/LICENSE-2.0.html">
    <img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache 2.0-blue.svg" target="_blank" />
  </a>
</p>

Base image that extends the official Apache Spark image, available at
[official Apache Spark Docker Hub](hhttps://hub.docker.com/r/apache/spark).
Includes all necessary jars to use delta and other connectors. It can be used
in a `docker-compose` to build a cluster, such as the example in the
[docker-compose.yml](docker-compose.yml) file in this folder.

In this image, any Spark application will automatically use `delta` as default
file format for `load/save` operations, and as table catalog. Bear in mind that
the dependencies provision can take a while on the first run, but it will be
cached for future runs. So, in case of dispatching multiple jobs, it is
recommended to start the container and reuse it for all jobs.

If needed, the image provides an environment variable `SPARK_VERSION` and
another `DELTA_VERSION` for any necessary inspection.

- [Starting the cluster with docker compose](#starting-the-cluster-with-docker-compose)
- [Manually starting a cluster](#manually-starting-a-cluster)
- [Building](#building)
- [License](#license)

## Starting the cluster with docker compose

To start the cluster, run the following command:

```bash
docker-compose up
```

If running the [`docker-compose.yml`](docker-compose.yml) file as is, it will
spawn the cluster and a separate container with a job to compute the `pi`
number. The job can be seen in the [Spark UI](http://localhost:8080).

## Manually starting a cluster

If desired to start a cluster manually inside a single container, simply start
the container and the run the `start-master.sh` and `start-worker.sh` scripts:

```bash
docker run -i --rm \
    -p 4040:4040 -p 7077:7077 -p 8080:8080 -p 8081:8081 \
    -t marcelomendoncasoares/spark-delta:latest
```

After the container starts:

```bash
# The `$SPARK_HOME/sbin` folder is already in the `$PATH` env var.
start-master.sh
start-worker.sh spark://0.0.0.0:7077
```

To test if the cluster is running, check if the process opened up correctly:

```bash
root@4ebdfdcc1562:~# ps -ax | grep java
 19 pts/0    Sl     0:05 /opt/java/openjdk/bin/java -cp /opt/spark/conf/:/opt/spark/jars/* -Xmx1g org.apache.spark.deploy.master.Master --host 8f7f7bb5d931 --port 7077 --webui-port 8080
290 pts/0    Sl     0:05 /opt/java/openjdk/bin/java -cp /opt/spark/conf/:/opt/spark/jars/* -Xmx1g org.apache.spark.deploy.worker.Worker --webui-port 8081 spark://0.0.0.0:7077
363 pts/0    S+     0:00 grep --color=auto java
```

Now submit a test job to see if the cluster is responsive:

```bash
# The `$SPARK_HOME/bin` folder is already in the `$PATH` env var.
spark-submit \
    --master spark://0.0.0.0:7077 \
    --class org.apache.spark.examples.SparkPi \
    /opt/spark/examples/jars/spark-examples_2.12-$SPARK_VERSION.jar
```

> Note that is is when the job is called that all jar dependencies are
> downloaded and provided to the session. This can take a while on the first
> run, but it will be cached for future runs.

## Building

To build the image, run the following command:

```bash
docker build -t marcelomendoncasoares/spark-delta --build-arg SPARK_VERSION="3.3.3" .
```

The build argument `SPARK_VERSION` is optional and will defaults to `latest` if
not provided, which will use the latest Spark version available at the official
Apache Spark Docker Hub. This option is useful to target a specific Spark
version (with its compatible delta version).

> The image was developed and tested with Spark greater than 3.0.0. If using
> Spark 2.x, it is possible that the build fails due to `delta` version
> incompatibilities.

---

## License

Copyright &copy; 2023 Marcelo Soares.

Licensed under the
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
