"""
Configure a Spark standalone cluster based on the available resources and the
instructions provided by the user through environment variables. The cluster
will contain a master and one worker with several executors, as is recommended
by Spark documentation (https://issues.apache.org/jira/browse/SPARK-30978). The
worker memory and cores will default to the sum of the configured memory and
cores for all executors, so it does not need to be directly configured.

The following environment variables can be used to configure the cluster:

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

> Note that, beside all memory configurations requiring the `GB` symbol, *it is
> not possible to use other units besides GB*.

"""

import os
import subprocess

from dataclasses import dataclass
from functools import lru_cache
from multiprocessing import cpu_count
from pathlib import Path
from typing import Literal, TypedDict


SPARK_CONF_PATH = Path(os.environ['SPARK_HOME']) / "conf" / "spark-defaults.conf"
"""Spark configuration file path."""


@lru_cache()
def total_mem_gb() -> float:
    """
    Total memory available in GB. If the container have its memory limited,
    will return this limit. Otherwise, will return the total host memory.
    """

    def _get_mem_from_cmd(cmd: str, divide_by: int) -> float:
        get_cmd = subprocess.run(cmd, shell=True, capture_output=True)
        return int(get_cmd.stdout.decode("utf-8").strip()) / divide_by

    echo_vmstat_cmd = "echo $(vmstat -s | grep -i 'total memory' | grep -Eo [0-9]+)"
    host_mem_gb = _get_mem_from_cmd(echo_vmstat_cmd, 1024 ** 2)

    try:
        container_mem_cmd = "echo $(cat /sys/fs/cgroup/memory/memory.limit_in_bytes)"
        container_mem_gb = _get_mem_from_cmd(container_mem_cmd, 1024 ** 3)

    # The container memory limit file does not always exist. In these cases,
    # the container memory is the same as the host memory.
    except:
        container_mem_gb = host_mem_gb

    return min(host_mem_gb, container_mem_gb)


def mem_to_str(mem_gb: float) -> str:
    """
    Convert memory in GB to a string in GB or MB with the appropriate symbol.
    """
    if round(mem_gb) > 0 and mem_gb % round(mem_gb) <= 0.01:
        return f"{int(mem_gb)}GB"
    return f"{int(mem_gb * 1024)}MB"


@dataclass
class MemoryConfig:
    """
    Memory configuration. Store the percentage of memory to be used and the
    minimum value in GB. The percentage is relative to the total memory
    available in the host. If exact is True, the percentage will be ignored
    and the min value will be used as the exact value in GB.
    """

    pct: float
    min: int
    exact: bool = False

    @classmethod
    def from_env_var(cls, name: str, default: "MemoryConfig") -> "MemoryConfig":
        """
        Create a MemoryConfig object from an environment variable according to
        the rules described in the module docstring.

        Args:
            name (str): Name of the environment variable.
            default (MemoryConfig): Default value to be used if the environment
                variable is not provided or incomplete.
        """

        env_var = os.environ.get(name)
        if env_var is None:
            return default

        elements = env_var.split(",")
        if len(elements) == 1 and elements[0].upper().endswith("GB"):
            return cls(0.0, float(elements[0][:-2]), exact=True)

        spec = elements[0].strip()
        float_spec = float(spec[:-1])/100 if spec.endswith("%") else float(spec)
        if float_spec > 1:
            raise ValueError(
                f"Invalid value for {name!r} env var. Percentage must be "
                f"between 0 and 100. Got {float_spec}."
            )

        if len(elements) == 1:
            return cls(float_spec, default.min)
        if len(elements) == 2:
            return cls(float_spec, int(elements[1]))

        raise ValueError(
            f"Too many elements in {name} env var. Only 2 allowed, to "
            f"represent percentage, minimum value. Got {len(elements)} "
            f"with values {elements}."
        )

    def as_gb(self) -> float:
        """
        The memory configuration parsed as GB.
        """
        if self.exact:
            return self.min
        return max(self.pct * total_mem_gb(), self.min)

    def to_str(self) -> str:
        """
        The memory configuration parsed as a string with the "GB" symbol, if
        the memory is greater than 1GB, or "MB" otherwise.
        """
        return mem_to_str(self.as_gb())


class ClusterSpec(TypedDict):
    """
    Final cluster specification. Will determine the configurations to be set on
    the `spark-defaults.conf` file. Each key must be correspondent to a Spark
    configuration if prefixed with `spark.` (e.g. `spark.driver.cores`).
    """

    driver_cores: int
    driver_memory: str
    worker_cores: int
    worker_memory: str
    executor_instances: int
    executor_cores: int
    executor_memory: str


@dataclass
class ClusterConfig:
    """
    Cluster configuration. Extracts the configurations from the environment
    variables and calculates the final cluster specification to be started.
    The configurations are described in the module docstring.
    """

    free_cores: int = 1
    driver_cores: int = 1
    min_executor_cores: int = 1
    free_mem: MemoryConfig = MemoryConfig(0.1, 1)
    driver_mem: MemoryConfig = MemoryConfig(0.1, 1)
    executor_mem: float = 16.0
    num_executors: int = 0
    auto_scale: bool = True

    @classmethod
    def from_env_vars(cls) -> "ClusterConfig":
        """
        Create a ClusterConfig object from the environment variables.
        """
        return cls(
            free_cores=int(os.environ.get("FREE_CORES", 1)),
            driver_cores=int(os.environ.get("DRIVER_CORES", 1)),
            min_executor_cores=int(os.environ.get("MIN_EXECUTOR_CORES", 1)),
            free_mem=MemoryConfig.from_env_var("FREE_MEMORY", MemoryConfig(0.1, 1)),
            driver_mem=MemoryConfig.from_env_var("DRIVER_MEMORY", MemoryConfig(0.1, 1)),
            executor_mem=float(os.environ.get("EXECUTOR_MEMORY", "16").replace("GB", "")),
            num_executors=int(os.environ.get("NUM_EXECUTORS", 0)),
            auto_scale=os.environ.get("AUTO_SCALE", "true").lower() == "true",
        )

    def calculate(self) -> ClusterSpec:
        """
        Calculate the cluster specification based on provided configs.
        """

        remaining_mem = total_mem_gb() - self.free_mem.as_gb() - self.driver_mem.as_gb()
        num_executors = self.num_executors

        if num_executors < 1:
            num_executors = int(max(remaining_mem // self.executor_mem, 1))
        executor_mem = remaining_mem / num_executors

        remaining_cores = cpu_count() - self.free_cores - self.driver_cores
        executor_cores = max(remaining_cores // num_executors, self.min_executor_cores)

        return ClusterSpec(
            driver_cores=self.driver_cores,
            driver_memory=self.driver_mem.to_str(),
            worker_cores=max(remaining_cores, executor_cores),
            worker_memory=mem_to_str(remaining_mem),
            executor_instances=num_executors,
            executor_cores=executor_cores,
            executor_memory=mem_to_str(executor_mem),
        )

    def _apply_to_conf(self, spark_conf: ClusterSpec) -> None:
        """
        Idempotently apply the cluster specifications to the conf file.
        """

        if self.auto_scale:
            max_executors = spark_conf["executor_instances"]
            spark_conf = {
                **spark_conf,
                "shuffle.service.enabled": "true",
                "dynamicAllocation.enabled": "true",
                "dynamicAllocation.minExecutors": min(max_executors, 2),
                "dynamicAllocation.maxExecutors": max_executors,
                "dynamicAllocation.executorIdleTimeout": "180s",
            }

        conf_lines = SPARK_CONF_PATH.read_text().splitlines()
        for conf, value in spark_conf.items():
            conf = f"spark.{conf.replace('_', '.')}"
            for i, line in enumerate(conf_lines):
                if line.startswith(conf):
                    conf_lines[i] = f"{conf} {value}"
                    break
            if not line.startswith(conf):
                conf_lines.append(f"{conf} {value}")

        SPARK_CONF_PATH.write_text("\n".join(conf_lines))

    def start(self) -> None:
        """
        Start the calculated cluster.
        """
        conf = self.calculate()
        self._apply_to_conf(conf)

        start_prefix = "/opt/spark/sbin/start"
        print(f"Starting master...")
        subprocess.run([f"{start_prefix}-master.sh"], check=True)

        print(f"Starting worker...")
        worker_command = [f"{start_prefix}-worker.sh", "spark://0.0.0.0:7077"]
        worker_mem = ["--memory", conf["worker_memory"]]
        worker_cores = ["--cores", str(conf["worker_cores"])]
        subprocess.run([*worker_command, *worker_mem, *worker_cores], check=True)

        print(
            f"# \n"
            f"# Spark standalone cluster started with success.\n"
            f"# The cluster have been configured to preserve {self.free_cores} core(s) "
            f"and {self.free_mem.to_str()} of memory for \n"
            f"# the OS and other apps, using the following resources:\n"
            f"# \n"
            f"#   * Driver: {conf['driver_cores']} cores / {conf['driver_memory']} RAM\n"
            f"#   * Worker: {conf['worker_cores']} cores / {conf['worker_memory']} RAM\n"
            f"# \n"
            f"# The worker will spawn {conf['executor_instances']} executor(s) with "
            f"{conf['executor_cores']} cores and {conf['executor_memory']} RAM. "
            f"{'Auto scale is enabled.' if self.auto_scale else ''}\n"
            f"# "
        )


if __name__ == "__main__":
    start_spark_cluster = os.environ.get("START_SPARK_CLUSTER", "").lower() == "true"
    extra_cloud_jars_flag = os.environ.get("EXTRA_CLOUD_JARS", "false").lower()

    # Add the delta package and extra cloud jars to the config file. Extra jars
    # provided through the `EXTRA_JARS_PACKAGES` env var will also be added.
    spark_jars = os.environ["DELTA_JAR_PACKAGE"]
    if extra_cloud_jars_flag != "false":
        spark_jars += "," + os.environ["EXTRA_BASE_JARS_PACKAGES"]
        if extra_cloud_jars_flag in ("azure", "true"):
            spark_jars += "," + os.environ["EXTRA_AZURE_JARS_PACKAGES"]
        if extra_cloud_jars_flag in ("aws", "true"):
            spark_jars += "," + os.environ["EXTRA_AWS_JARS_PACKAGES"]
    if dynamic_extra_jars := os.environ.get("EXTRA_JARS_PACKAGES"):
        spark_jars += "," + dynamic_extra_jars.replace(" ", "").strip(",")
    with SPARK_CONF_PATH.open("a") as conf_file:
        conf_file.write(f"spark.jars.packages {spark_jars}\n")

    # Start the cluster if configured.
    if start_spark_cluster:
        cluster_config = ClusterConfig.from_env_vars()
        cluster_config.start()
