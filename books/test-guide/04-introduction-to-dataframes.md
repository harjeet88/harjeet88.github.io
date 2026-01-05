---
title: "Chapter 4: Intoduction to dataframes"
desc: "Understanding Spark dataframes"
order: 4
---
# Chapter 4 : Spark's Data Abstractions – RDDs and DataFrames

Welcome to the core of Apache Spark's data processing capabilities. In this chapter, we'll explore Spark's primary data structures: **Resilient Distributed Datasets (RDDs)** and **DataFrames**. These abstractions allow Spark to handle massive datasets across a cluster of machines efficiently and fault-tolerantly.

We'll start with a brief introduction to RDDs—the foundational, low-level API—then move to DataFrames, the modern, high-level structured API that's recommended for most use cases in current Spark versions (as of January 2026, the latest is Apache Spark 4.1.0). By understanding both, you'll appreciate Spark's evolution and know when to use each.

This chapter assumes you've read the introductory overview of Spark's architecture (driver, executors, cluster managers). We'll use PySpark examples throughout for accessibility, as it's the most popular language for new users.








*The illustrations above compare RDDs and DataFrames, highlighting key differences in structure, optimization, and use cases.*

## Resilient Distributed Datasets (RDDs): The Foundation

RDDs were Spark's original data abstraction, introduced in the first versions of Spark. An **RDD** is an immutable, partitioned collection of elements that can be operated on in parallel across a cluster.

### Key Characteristics of RDDs
- **Resilient**: Fault-tolerant through "lineage" — Spark tracks how the RDD was created, so lost partitions can be recomputed.
- **Distributed**: Data is split into partitions across cluster nodes for parallel processing.
- **Immutable**: Once created, RDDs can't be changed; operations return new RDDs.
- **Lazy Evaluation**: Transformations (e.g., map, filter) build a logical plan but don't compute immediately—only when an action (e.g., collect, count) is called.
- **Low-Level API**: You work directly with objects (e.g., Python lists or custom classes), giving fine-grained control.

RDDs are great for unstructured or semi-structured data where you need custom processing logic.

### Creating and Using RDDs
Here's a simple example:

```python
from pyspark.sql import SparkSession

spark = SparkSession.builder.appName("RDD Example").getOrCreate()
sc = spark.sparkContext  # Access the underlying SparkContext

# Create an RDD from a Python list
data = [1, 2, 3, 4, 5]
rdd = sc.parallelize(data, numSlices=4)  # 4 partitions

# Transformations: build a plan
squared_rdd = rdd.map(lambda x: x * x)
filtered_rdd = squared_rdd.filter(lambda x: x > 10)

# Action: trigger computation
result = filtered_rdd.collect()
print(result)  # Output: [16, 25]

spark.stop()
```

RDDs also support reading from files:

```python
text_rdd = sc.textFile("path/to/large_text_file.txt")
word_counts = text_rdd.flatMap(lambda line: line.split(" ")) \
                     .map(lambda word: (word, 1)) \
                     .reduceByKey(lambda a, b: a + b)
```

### Limitations of RDDs
- No built-in schema or structure → Less efficient for columnar operations.
- No automatic optimization → You manually manage performance (e.g., partitioning).
- Verbose code for common tasks like joins or aggregations.

RDDs are still useful for legacy code or when you need maximum control (e.g., custom partitioning in machine learning pipelines).

## DataFrames: Structured Data Processing Made Easy

Introduced in Spark 1.3 and unified as the primary API in Spark 2.0+, **DataFrames** are distributed collections of data organized into named columns, much like a table in a relational database or a pandas DataFrame in Python.

DataFrames build on RDDs but add a **schema** (column names and types) and leverage Spark's powerful optimizations.








*The diagrams above show how DataFrames integrate with Spark's Catalyst optimizer (for query planning) and Tungsten execution engine (for efficient memory/CPU use).*

### Why DataFrames? Key Advantages
- **Structured and Schema-Enforced**: Columns have names and types → Easier debugging and optimization.
- **High-Level API**: Expressive operations (select, filter, groupBy, join) similar to SQL or pandas.
- **Performance Optimizations**:
  - **Catalyst Optimizer**: Analyzes your code and generates an efficient physical execution plan.
  - **Tungsten Engine**: Off-heap memory management, code generation, and whole-stage codegen for faster execution (often 2-10x faster than RDDs).
- **Interoperable with Spark SQL**: Register a DataFrame as a temporary view and query with SQL.
- **Wide Data Source Support**: Read/write JSON, CSV, Parquet, Avro, JDBC, etc., seamlessly.
- **Lazy Evaluation**: Like RDDs, transformations are lazy for efficient planning.

DataFrames are the recommended abstraction for 95% of use cases in modern Spark (4.x series).

### Creating DataFrames
There are many ways to create a DataFrame. Here are common ones:

```python
from pyspark.sql import SparkSession
from pyspark.sql.types import *

spark = SparkSession.builder.appName("DataFrame Example").getOrCreate()

# 1. From a Python list of Rows
from pyspark.sql import Row
rows = [Row(name="Alice", age=30), Row(name="Bob", age=25)]
df = spark.createDataFrame(rows)

# 2. With explicit schema
schema = StructType([
    StructField("name", StringType(), True),
    StructField("age", IntegerType(), True)
])
df = spark.createDataFrame(rows, schema)

# 3. From a pandas DataFrame (great for prototyping)
import pandas as pd
pandas_df = pd.DataFrame({"name": ["Alice", "Bob"], "age": [30, 25]})
df = spark.createDataFrame(pandas_df)

# 4. Reading from files (most common in production)
df = spark.read.csv("path/to/employees.csv", header=True, inferSchema=True)
# Or Parquet (recommended for performance)
df = spark.read.parquet("path/to/data.parquet")

df.show(5)  # Display first 5 rows
```








*Examples of PySpark code for creating and working with DataFrames.*

### Basic Operations on DataFrames
DataFrames shine with intuitive, SQL-like operations:

```python
# Select columns
df.select("name", "age").show()

# Filter rows
df.filter(df.age > 25).show()

# Aggregations
from pyspark.sql.functions import avg, count
df.groupBy("department").agg(avg("salary"), count("*")).show()

# Joins
df2 = spark.read.csv("path/to/departments.csv", header=True, inferSchema=True)
joined_df = df.join(df2, "dept_id", "inner")

# SQL queries
df.createOrReplaceTempView("employees")
spark.sql("SELECT department, AVG(salary) FROM employees GROUP BY department").show()
```

### Converting Between RDDs and DataFrames
You can move freely between them:

```python
# DataFrame to RDD
rdd_from_df = df.rdd

# RDD to DataFrame (with schema)
df_from_rdd = rdd_from_df.toDF(schema)
```

## RDD vs. DataFrame: Detailed Comparison

| Feature                  | RDD                                      | DataFrame                                      |
|--------------------------|------------------------------------------|------------------------------------------------|
| **Introduction**        | Spark 1.0 (core API)                    | Spark 1.3 (structured API)                     |
| **Data Structure**      | Unstructured collection of objects      | Tabular with named columns and schema           |
| **Type Safety**         | Compile-time (in Scala/Java)             | Runtime (but schema helps)                     |
| **Optimization**        | Manual (no optimizer)                   | Automatic via Catalyst + Tungsten              |
| **Performance**         | Good for custom logic                   | Often 2-10x faster for structured operations   |
| **Ease of Use**         | Verbose, low-level                      | High-level, SQL-like, concise                  |
| **Use Cases**           | Unstructured data, custom algorithms    | Structured/semi-structured data, analytics, ETL|
| **API Languages**       | All (Java, Scala, Python, R)            | All, but best in Python/Scala                  |
| **Current Recommendation** | Legacy or fine control                | Default for new projects                       |

In Spark 4.1.0+, DataFrames (via SparkSession) are the unified entry point, and RDDs are accessible underneath.

## Best Practices for Working with DataFrames
- **Prefer DataFrames**: Use them unless you need RDD-level control.
- **Define Schemas Explicitly**: Avoid `inferSchema` on large datasets for speed.
- **Use Columnar Formats**: Read/write Parquet or ORC for compression and efficiency.
- **Cache Wisely**: `df.cache()` for reused DataFrames, but monitor memory.
- **Minimize Shuffles**: Avoid wide operations (e.g., groupBy on high-cardinality keys).
- **Leverage Built-in Functions**: Use `pyspark.sql.functions` instead of UDFs when possible.
- **Broadcast Small Tables**: For joins with small DataFrames.
- **Monitor with Spark UI**: Check http://localhost:4040 during development.

## Conclusion

RDDs provide the robust foundation of Spark's distributed computing, while DataFrames elevate it with structure, optimizations, and usability. For most modern applications—from ETL pipelines to machine learning preprocessing—start with DataFrames.

In the next chapter, we'll cover creating and configuring SparkSession—the entry point that gives you access to DataFrames and the underlying RDDs when needed.

Practice these examples locally, and experiment with your own datasets. The official Spark documentation (spark.apache.org/docs/latest) is an excellent resource for the latest updates.

Happy data processing!
