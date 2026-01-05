
# Chapter 6: Basic DataFrame Operations and Spark SQL

In previous chapters, we explored Spark's data abstractions and how to create **DataFrames**. This chapter dives deeper into foundational operations that form the building blocks of most Spark applications. We'll cover inspecting data, selecting and manipulating columns, filtering and sorting rows, adding or modifying columns, handling missing values, distinct and duplicate removal, sampling, limiting results, and more.

We've intentionally kept **aggregations** and **joins** out of this chapter—they deserve their own dedicated treatment in upcoming chapters due to their complexity and performance implications. Here, we focus on operations that typically involve narrow transformations (no shuffling of data across the cluster), making them efficient and straightforward.

All examples use **PySpark** with Apache Spark 4.x (current as of January 2026). We'll continue with the employee dataset from before, expanded slightly for richer examples.












*The illustrations above show common DataFrame operations like selecting columns, filtering rows, adding new columns via `withColumn`, and sorting results.*

## 6.1 Setting Up the SparkSession and Sample Data

```python
from pyspark.sql import SparkSession
from pyspark.sql import Row
from pyspark.sql.functions import col, lit, when, expr

spark = SparkSession.builder \
    .appName("Chapter 6 - Basic DataFrame Operations") \
    .master("local[*]") \
    .getOrCreate()

# Expanded employee data with more variety (including duplicates and nulls)
employee_data = [
    Row(id=1, name="Alice", age=34, salary=75000, dept_id=101, country="USA"),
    Row(id=2, name="Bob", age=45, salary=92000, dept_id=102, country="USA"),
    Row(id=3, name="Charlie", age=29, salary=62000, dept_id=101, country="Canada"),
    Row(id=4, name="Diana", age=38, salary=88000, dept_id=103, country="USA"),
    Row(id=5, name="Eve", age=27, salary=55000, dept_id=102, country="USA"),
    Row(id=6, name="Frank", age=41, salary=98000, dept_id=101, country="UK"),
    Row(id=7, name="Grace", age=33, salary=72000, dept_id=None, country="Canada"),
    Row(id=8, name="Alice", age=34, salary=75000, dept_id=101, country="USA"),  # Duplicate
    Row(id=9, name="Henry", age=None, salary=68000, dept_id=102, country="USA")
]

employees = spark.createDataFrame(employee_data)
employees.show(truncate=False)
```








*Typical output of `df.show()` in PySpark—note the truncated columns and row formatting.*

## 6.2 Inspecting Your DataFrame

Before transforming data, always inspect it.

```python
# Schema and data types
employees.printSchema()

# Number of rows and columns
print(f"Rows: {employees.count()}, Columns: {len(employees.columns)}")

# Quick statistical summary (for numeric columns)
employees.describe("age", "salary").show()

# Summary with more stats
employees.summary("count", "mean", "stddev", "min", "25%", "50%", "75%", "max").show()

# Display first few rows
employees.show(10, truncate=False)  # No truncation
employees.head(5)  # Returns list of Row objects
employees.take(5)  # Similar to head
employees.tail(5)  # Last 5 rows (Spark 3.4+)
```

**Tip**: Use `show(n, truncate=False, vertical=True)` for wide rows to display as key-value pairs.

## 6.3 Selecting and Projecting Columns

Projection means choosing specific columns.

```python
# Simple column selection
employees.select("name", "salary", "country").show()

# Using col() for programmatic access
employees.select(col("name"), col("age") + 10).show()

# Select with expressions
employees.selectExpr("name", "salary * 1.1 AS increased_salary", "upper(country)").show()

# Select all columns except some
employees.drop("id", "dept_id").show()
```

You can alias columns during selection:

```python
employees.select(col("name").alias("employee_name"), col("salary")).show()
```

## 6.4 Filtering Rows

Filtering (also called selection) reduces rows based on conditions.

```python
# Basic filter
employees.filter(col("age") > 35).show()

# Multiple conditions
employees.filter((col("salary") >= 70000) & (col("country") == "USA")).show()

# OR condition
employees.filter((col("country") == "Canada") | (col("country") == "UK")).show()

# Using SQL-style strings
employees.filter("age IS NOT NULL AND salary BETWEEN 60000 AND 90000").show()

# Negation
employees.filter(~(col("dept_id").isNull())).show()  # Non-null dept_id
```

**Performance Note**: Filters are push-down optimized when reading from sources like Parquet.

## 6.5 Adding, Modifying, and Renaming Columns

Use `withColumn()` for new or overwritten columns.

```python
# Add constant column
df = employees.withColumn("bonus", lit(5000))

# Calculated column
df = df.withColumn("total_comp", col("salary") + col("bonus"))

# Conditional logic
df = df.withColumn("experience_level",
    when(col("age") >= 40, "Senior")
    .when((col("age") >= 30) & (col("age") < 40), "Mid")
    .otherwise("Junior")
)

# String operations
from pyspark.sql.functions import upper, concat, substring
df = df.withColumn("name_upper", upper(col("name")))
df = df.withColumn("greeting", concat(lit("Hello, "), col("name")))

# Using expr for complex SQL expressions
df = df.withColumn("salary_bucket", expr("CASE WHEN salary < 60000 THEN 'Low' WHEN salary < 90000 THEN 'Medium' ELSE 'High' END"))

# Rename existing column
df = df.withColumnRenamed("total_comp", "total_compensation")

df.select("name", "experience_level", "salary_bucket", "greeting").show(truncate=False)
```

**Important**: `withColumn()` returns a **new** DataFrame—DataFrames are immutable.

## 6.6 Sorting and Ordering

```python
# Single column sort
employees.orderBy("salary").show()  # Ascending by default
employees.orderBy(col("salary").desc()).show()

# Multiple columns
employees.orderBy(col("country"), col("salary").desc()).show()

# Using sort() alias
employees.sort(col("age").asc_nulls_last(), col("salary").desc_nulls_first()).show()

# Global vs. cluster sort
employees.orderBy("salary").show()  # Full sort (shuffles data)
employees.sortWithinPartitions("salary").show()  # Sorts per partition only
```

## 6.7 Handling Missing (Null) Values

Real-world data is messy—nulls are common.








*Visual examples of detecting and handling null values in PySpark DataFrames.*

```python
# Detect nulls
employees.select([col(c).isNull().cast("int").alias(c + "_is_null") for c in employees.columns]).show()

# Drop rows with any/all nulls
employees.na.drop("any").show()   # Default: drops if any column null
employees.na.drop("all").show()   # Drops only if all columns null
employees.na.drop(subset=["age", "dept_id"]).show()  # Specific columns

# Fill nulls
employees.na.fill(0, subset=["salary"]).show()  # Numeric
employees.na.fill("Unknown", subset=["country"]).show()

# Fill with different values per column
fill_map = {"age": 30, "dept_id": 999, "country": "Unknown"}
employees.na.fill(fill_map).show()

# Advanced: forward/backward fill (Spark 3.4+)
employees.sort("id").fillna(method="ffill", subset=["age"]).show()
```

## 6.8 Removing Duplicates and Sampling

```python
# Remove exact duplicates
employees.dropDuplicates().show()

# Duplicates on subset of columns
employees.dropDuplicates(subset=["name", "age", "salary"]).show()

# Get distinct values
employees.select("country").distinct().show()

# Sampling
sample_df = employees.sample(fraction=0.5, seed=42)  # 50% without replacement
sample_df = employees.sample(withReplacement=True, fraction=1.0, seed=42)  # With replacement

# Limit results (no shuffle)
employees.limit(5).show()
```

## 6.9 Caching and Persistence

If you reuse a DataFrame multiple times, cache it to avoid recomputation.








*Difference between `cache()` (default MEMORY_AND_DISK) and custom `persist()` levels.*

```python
employees.cache()  # Same as persist(MEMORY_AND_DISK)
# Or
from pyspark.storagelevel import StorageLevel
employees.persist(StorageLevel.MEMORY_ONLY)  # Faster but risk of OOM

# Unpersist when done
employees.unpersist()
```

**Tip**: Monitor storage in Spark UI (http://localhost:4040/storage).

## 6.10 Spark SQL – The Declarative Alternative








*Examples of running SQL queries directly on registered DataFrames.*

```python
employees.createOrReplaceTempView("employees")

spark.sql("""
    SELECT 
        name,
        salary * 1.1 AS increased_salary,
        UPPER(country) AS country_upper,
        CASE WHEN age >= 40 THEN 'Senior' ELSE 'Junior' END AS level
    FROM employees
    WHERE salary > 60000
    ORDER BY salary DESC
    LIMIT 5
""").show(truncate=False)

# Mix SQL and DataFrame API
sql_df = spark.sql("SELECT name, salary FROM employees WHERE country = 'USA'")
sql_df.filter(col("salary") > 80000).show()
```

## 6.11 Practical Example: Cleaning and Enriching Employee Data

```python
cleaned = (employees
    .na.fill({"age": 30, "dept_id": 999, "country": "Unknown"})
    .withColumn("experience_level", 
                when(col("age") >= 40, "Senior")
                .when(col("age") >= 30, "Mid")
                .otherwise("Junior"))
    .withColumn("salary_bucket", expr("percentile_approx(salary, 0.5)"))  # Placeholder logic
    .dropDuplicates(subset=["name", "age", "salary"])
    .orderBy(col("salary").desc())
)

cleaned.show(truncate=False)
cleaned.write.mode("overwrite").parquet("output/cleaned_employees")
```

## 6.12 Best Practices Summary

| Practice                              | Reason                                                                 |
|---------------------------------------|------------------------------------------------------------------------|
| Chain operations fluently             | Improves readability and leverages lazy evaluation                     |
| Use `col()` over string references    | Type safety and avoids runtime errors                                  |
| Prefer built-in functions (`expr`, `when`) | Optimized by Catalyst                                                  |
| Cache intermediate results wisely     | Speeds up iterative development                                        |
| Use `limit()` early in exploration    | Avoids processing full dataset                                         |
| Inspect plans with `.explain()`       | Understand physical execution and spot inefficiencies                  |
| Avoid `collect()` on large DataFrames | Can cause driver OOM                                                   |

## 6.13 Summary

This chapter equipped you with essential tools for exploring, cleaning, and transforming DataFrames using both the DataFrame API and Spark SQL. These operations are narrow, efficient, and form the foundation for more advanced topics.

**Next Chapters**:
- Chapter 7: Aggregations and Grouped Operations
- Chapter 8: Joins and Set Operations

**Exercises**
1. Add columns for `tax = salary * 0.2` and `net_salary = salary - tax`.
2. Filter employees from non-USA countries, fill missing ages with the overall average age.
3. Write equivalent Spark SQL queries for all `withColumn` examples above.
4. Sample 30% of the data and cache it—then run multiple `show()` calls to observe speedup.

Keep practicing—these basics will become second nature!

Happy transforming!
