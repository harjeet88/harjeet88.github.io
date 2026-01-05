---
title: "Chapter 3: Pyspark Architecture"
desc: "Understanding PySpark Architecture "
order: 3
---
# Understanding PySpark Architecture

PySpark is the Python API for Apache Spark, enabling Python developers to leverage Spark's powerful distributed data processing capabilities. While the core Apache Spark engine is written in Scala and runs on the JVM (Java Virtual Machine), PySpark bridges the gap by allowing Python code to interact with this JVM-based system.

This tutorial explains the PySpark architecture in depth, highlighting key differences from pure Spark (Scala/Java) applications. It is based on concepts from the video ["PySpark vs Spark Architecture | Spark Interview Questions"](https://www.youtube.com/watch?v=OHwSOaDqiZk) by Data Savvy, which visually compares standard Spark architecture with PySpark's unique Python-JVM interactions.

## Core Apache Spark Architecture (Foundation for PySpark)

Before diving into PySpark specifics, understand the underlying Spark cluster architecture, which PySpark inherits.

**Key Components:**
- **Driver Program**: The main process running your application code. It creates the SparkSession/SparkContext, defines transformations/actions, and coordinates job execution.
- **Cluster Manager**: Allocates resources across the cluster. Supported types include Standalone, YARN, Mesos, or Kubernetes.
- **Worker Nodes**: Machines in the cluster that host Executors.
- **Executors**: JVM processes on worker nodes that run tasks, store data in memory/disk, and report results back to the driver.

**Execution Flow (in standard Spark):**
1. Driver connects to Cluster Manager to request resources (Executors).
2. Cluster Manager launches Executors on workers.
3. Driver sends code and tasks to Executors.
4. Executors perform computations in parallel.
5. Results are sent back to the Driver.

This master-worker model ensures fault tolerance and scalability.

## PySpark-Specific Architecture: The Python-JVM Bridge

PySpark introduces additional layers because Python code cannot run directly on the JVM. The referenced video emphasizes that **only custom Python logic (e.g., UDFs, lambdas) runs in Python processes**—all core Spark operations (planning, optimization, shuffling, caching) happen in the JVM.

### Driver Side in PySpark

**Flow on the Driver:**
1. Your Python script starts and creates a `SparkSession` (or `SparkContext`).
2. Internally, PySpark launches a **JVM Driver process** via `spark-submit`.
3. The JVM Driver starts a **Py4J Gateway Server** for bidirectional communication between Python and JVM.
4. Connection details (e.g., port) are shared via a temporary file or environment.
5. Python code sends high-level operations (e.g., `df.filter(...)`) to the JVM via Py4J.
6. The JVM Driver:
   - Builds a logical plan.
   - Optimizes it using the Catalyst Optimizer.
   - Generates a physical execution plan (DAG of stages/tasks).
7. All planning and optimization occur in the JVM—no Python involvement here.

This setup adds slight overhead but allows seamless Python syntax.

### Worker Side in PySpark

The behavior differs based on whether custom Python code is involved.

#### Case 1: Standard Spark Operations (No Python UDFs/Lambdas)
- Examples: `df.filter(col("age") > 18)`, `groupBy`, `join`.
- Tasks run entirely in JVM Executors.
- No Python processes are spawned.
- Fast and efficient, identical to Scala/Java Spark.

#### Case 2: Python UDFs or Lambda Functions
- Example: `df.withColumn("new_col", udf(my_python_func)(col("old_col")))`.
- When a task encounters Python logic:
  1. The JVM Executor spawns a separate **Python subprocess** (Python interpreter) on the worker node.
  2. Data is serialized and sent to the Python process via **pipes** (stdin/stdout).
  3. Python executes the custom logic.
  4. Results are serialized back to the JVM Executor.
  5. Executor continues with the rest of the task.
- **Overhead**: Serialization, process spawning, and data transfer introduce latency. Python UDFs are not optimized by Catalyst.

**Important Notes from the Video:**
- Data shuffling and DataFrame/RDD caching always happen in the JVM.
- PySpark performance is best when minimizing Python UDFs (prefer built-in Spark functions or pandas UDFs in newer versions).

## Overall PySpark Execution Flow

1. Python Driver → Py4J → JVM Driver: Submit transformations (lazy).
2. Action triggers job submission.
3. JVM Driver → DAG Scheduler → Task Scheduler.
4. Tasks sent to Executors via Cluster Manager.
5. Executors run tasks (JVM or spawn Python for UDFs).
6. Results → JVM Driver → Py4J → Python Driver.

## Performance Implications and Best Practices

- **Pros of PySpark**: Easy for Python data scientists; integrates with pandas, NumPy.
- **Cons**: Overhead from Py4J and Python subprocesses for UDFs.
- **Tips**:
  - Use built-in Spark SQL functions instead of Python UDFs.
  - Leverage Vectorized/Pandas UDFs (Arrow-based) for better performance (available since Spark 2.3+).
  - Monitor via Spark UI to spot Python-related bottlenecks.

## Conclusion

PySpark extends Apache Spark's robust JVM-based architecture to Python by using Py4J for driver communication and pipes for worker-side Python execution. This enables productive development but requires awareness of the Python-JVM boundary to optimize performance.

For a clear visual explanation of these concepts, including side-by-side comparisons of Spark vs. PySpark flows, watch the source video:  
[PySpark vs Spark Architecture | Spark Interview Questions](https://www.youtube.com/watch?v=OHwSOaDqiZk)

Experiment with simple PySpark scripts and observe the Spark UI to see these components in action!
