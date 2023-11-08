<h1 align="center">Spark + Delta Standalone Docker</h1>
<p align="center">
  <a href="https://github.com/marcelomendoncasoares">
    <img alt="GitHub" src="https://img.shields.io/badge/GitHub-marcelomendoncasoares-181717.svg?style=flat&logo=github" />
  </a>
  <a href="http://www.apache.org/licenses/LICENSE-2.0.html">
    <img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache 2.0-blue.svg" target="_blank" />
  </a>
</p>

> This repo contains a complete container solution for running **_Apache
> Spark_** on _standalone_ mode with [delta.io](https://delta.io/) native
> support and able to read/write to Apache Kafka, AWS S3, Azure Storage
> Accounts and Azure Eventhubs. Standalone mode is the simplest way to deploy a
> Spark application, with both driver and its single worker running on the same
> system.

The custom images extend the official Apache Spark image, available at
[official Apache Spark Docker Hub](hhttps://hub.docker.com/r/apache/spark). The
base `spark-delta` image includes all necessary jars to use delta and other
connectors. It can be used in a `docker-compose` to build a cluster or the
`spark-delta-standalone` image can be used to run a single container with a
dynamically configurable standalone Spark cluster.

---

## License

Copyright &copy; 2023 Marcelo Soares.

Licensed under the
[Apache License, Version 2.0](http://www.apache.org/licenses/LICENSE-2.0).
