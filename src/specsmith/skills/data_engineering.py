# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Layer1Labs Silicon, Inc. All rights reserved.
"""Data engineering skill domain — ETL, dbt, Spark, data quality, feature stores."""

from specsmith.skills import SkillDomain, SkillEntry

SKILLS: list[SkillEntry] = [
    SkillEntry(
        slug="data-pipeline-etl",
        name="Data Pipeline — ETL/ELT design with Airflow, Prefect, or dbt",
        description=(
            "Design and implement data pipelines: source extraction, transformation, "
            "loading, orchestration, and monitoring. Use when building a new data pipeline, "
            "debugging pipeline failures, or migrating from ETL to ELT patterns."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "etl",
            "elt",
            "pipeline",
            "airflow",
            "prefect",
            "dbt",
            "orchestration",
            "incremental",
            "idempotent",
        ],
        project_types=["data-ml", "streaming-pipeline", "data-warehouse"],
        body="""\
# Data Pipeline (ETL/ELT)

ELT is now preferred over ETL: load raw data first, transform in the warehouse.

## When to use
- Building a new data pipeline from source to destination
- Migrating from ETL to ELT
- Debugging a failed or slow pipeline

## ELT vs ETL
| | ETL | ELT |
|--|-----|-----|
| Transform | Before loading | After loading |
| Best for | Legacy systems, limited warehouse compute | Cloud DWs (Snowflake, BigQuery, Redshift) |
| Tool | Informatica, SSIS | dbt, Spark SQL |

## Pipeline design principles

### 1. Idempotent — safe to re-run
```python
# Bad: inserts duplicate rows on re-run
INSERT INTO orders SELECT * FROM raw_orders

# Good: upsert or truncate-and-reload
INSERT INTO orders SELECT * FROM raw_orders
ON CONFLICT (order_id) DO UPDATE SET ...
```

### 2. Incremental where possible
```python
# Prefect flow with incremental watermark
@task
def extract_new_orders(last_run: datetime) -> list[dict]:
    return db.query(
        "SELECT * FROM orders WHERE updated_at > %s",
        (last_run,)
    )
```

### 3. Schema on read (raw layer)
Always keep a raw copy before transformation:
```
raw.orders          ← exact copy from source (never modified)
staging.orders      ← light cleaning (types, nulls)
marts.orders        ← business-logic transformations
```

## Orchestration with Prefect

```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(cache_key_fn=task_input_hash, cache_expiration=timedelta(hours=1))
def extract(source_url: str) -> pd.DataFrame:
    return pd.read_parquet(source_url)

@task
def transform(df: pd.DataFrame) -> pd.DataFrame:
    return df.dropna(subset=["id"]).assign(
        loaded_at=pd.Timestamp.utcnow()
    )

@task
def load(df: pd.DataFrame, table: str) -> None:
    df.to_sql(table, engine, if_exists="replace", index=False)

@flow(name="daily-orders-pipeline")
def orders_pipeline(date: str):
    raw = extract(f"s3://data-lake/orders/{date}.parquet")
    clean = transform(raw)
    load(clean, "staging.orders")
```

## Monitoring

```python
# Alert on row count anomalies
@task
def validate(df: pd.DataFrame, expected_min_rows: int = 1000) -> None:
    if len(df) < expected_min_rows:
        raise ValueError(f"Only {len(df)} rows — expected ≥ {expected_min_rows}")
```

## Verification checklist
- [ ] Pipeline is idempotent (safe to re-run)
- [ ] Raw data preserved before transformation
- [ ] Incremental load implemented (not full reload where possible)
- [ ] Row count / schema validation after each stage
- [ ] Failure alerts configured
- [ ] Pipeline run history tracked (Prefect/Airflow logs)
""",
    ),
    SkillEntry(
        slug="dbt-development",
        name="dbt Development — data modelling, testing, and documentation",
        description=(
            "Build dbt models: staging, intermediate, and mart layers, with tests, "
            "documentation, and incremental strategies. Use when adding new dbt models, "
            "writing dbt tests, or setting up a dbt project from scratch."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "dbt",
            "data-modelling",
            "sql",
            "snowflake",
            "bigquery",
            "redshift",
            "incremental",
            "tests",
            "documentation",
        ],
        project_types=["data-warehouse"],
        body="""\
# dbt Development

dbt = SQL + version control + tests + documentation. It is the standard
tool for ELT transformations in modern data warehouses.

## When to use
- Adding new models to a dbt project
- Writing tests for existing models
- Setting up a new dbt project

## Project structure (medallion architecture)

```
models/
  staging/            ← 1:1 with source tables; light cleaning only
    stg_orders.sql
    stg_customers.sql
  intermediate/       ← business logic joins and calculations
    int_order_items_joined.sql
  marts/              ← final tables consumed by BI/ML
    fct_orders.sql
    dim_customers.sql
```

## Staging model (thin layer)

```sql
-- models/staging/stg_orders.sql
{{ config(materialized='view') }}

WITH source AS (
    SELECT * FROM {{ source('raw', 'orders') }}
),
renamed AS (
    SELECT
        order_id::TEXT    AS order_id,
        customer_id::TEXT AS customer_id,
        total_cents::INT  AS total_amount_cents,
        created_at::TIMESTAMP AS created_at
    FROM source
)
SELECT * FROM renamed
```

## Incremental model

```sql
-- models/marts/fct_orders.sql
{{ config(
    materialized='incremental',
    unique_key='order_id',
    on_schema_change='fail'
) }}

SELECT o.order_id, c.customer_name, o.total_amount_cents
FROM {{ ref('stg_orders') }} o
JOIN {{ ref('dim_customers') }} c USING (customer_id)

{% if is_incremental() %}
WHERE o.created_at > (SELECT MAX(created_at) FROM {{ this }})
{% endif %}
```

## Testing

```yaml
# models/staging/schema.yml
models:
  - name: stg_orders
    columns:
      - name: order_id
        tests:
          - not_null
          - unique
      - name: total_amount_cents
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

```bash
# Run all tests
dbt test

# Run tests for one model
dbt test --select stg_orders
```

## Documentation

```yaml
# models/marts/schema.yml
models:
  - name: fct_orders
    description: "One row per order. Updated daily."
    columns:
      - name: order_id
        description: "Unique identifier for each order."
```

```bash
dbt docs generate && dbt docs serve
```

## Verification checklist
- [ ] `not_null` and `unique` tests on every primary key
- [ ] Staging models are views (not tables)
- [ ] Incremental models have `unique_key` defined
- [ ] All models documented in `schema.yml`
- [ ] `dbt test` passes before PR merge
- [ ] `dbt build` run in CI (compile + test + run)
""",
    ),
    SkillEntry(
        slug="data-quality",
        name="Data Quality — validation, profiling, and monitoring with Great Expectations",
        description=(
            "Data quality framework: schema validation, statistical profiling, expectation "
            "suites, and pipeline checkpoints. Use when setting up data quality checks, "
            "investigating data anomalies, or building a data contract between teams."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "data-quality",
            "great-expectations",
            "dbt-tests",
            "soda",
            "schema-validation",
            "profiling",
            "data-contract",
            "anomaly-detection",
        ],
        body="""\
# Data Quality

Bad data costs more than the infra to catch it.
Build quality checks into every pipeline.

## When to use
- Setting up data quality checks for a pipeline
- Investigating unexpected nulls, duplicates, or out-of-range values
- Establishing data contracts between producers and consumers

## Three layers of data quality

| Layer | What it checks | Tool |
|-------|---------------|------|
| Schema | Column types, nullability | dbt source tests, Pydantic |
| Statistical | Distributions, ranges, uniqueness | Great Expectations |
| Business | Domain rules, referential integrity | dbt custom tests, SQL assertions |

## Great Expectations quickstart

```python
import great_expectations as gx

context = gx.get_context()
ds = context.sources.add_pandas("my_source")
asset = ds.add_dataframe_asset("orders")

# Build expectation suite
suite = context.add_expectation_suite("orders.suite")
batch = asset.add_batch_definition_whole_dataframe("full")

# Define expectations
suite.add_expectation(gx.expectations.ExpectColumnToExist(column="order_id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToNotBeNull(column="order_id"))
suite.add_expectation(gx.expectations.ExpectColumnValuesToBeUnique(column="order_id"))
suite.add_expectation(
    gx.expectations.ExpectColumnValuesToBeBetween(
        column="total_cents", min_value=0, max_value=10_000_000
    )
)

# Validate
result = context.run_checkpoint(
    checkpoint_name="orders_checkpoint",
    batch_request=batch.build_batch_request(dataframe=df),
)
assert result.success
```

## dbt custom test (business rule)

```sql
-- tests/assert_order_total_positive.sql
SELECT order_id
FROM {{ ref('fct_orders') }}
WHERE total_amount_cents < 0
```

## Statistical anomaly detection

```python
# Z-score check for daily row counts
def check_row_count_anomaly(conn, table: str, z_threshold: float = 3.0) -> None:
    stats = conn.execute(f'''
        SELECT AVG(daily_count) AS mean, STDDEV(daily_count) AS std
        FROM (
            SELECT DATE(created_at) AS day, COUNT(*) AS daily_count
            FROM {table}
            WHERE created_at > NOW() - INTERVAL \'30 days\'
            GROUP BY 1
        ) t
    ''').fetchone()
    today_count = conn.execute(
        f"SELECT COUNT(*) FROM {table} WHERE created_at::date = CURRENT_DATE"
    ).scalar()
    z_score = abs(today_count - stats.mean) / (stats.std or 1)
    if z_score > z_threshold:
        raise ValueError(f"Row count anomaly: z={z_score:.1f} (today={today_count})")
```

## Verification checklist
- [ ] Schema validation on every pipeline input
- [ ] Not-null checks on required columns
- [ ] Uniqueness checks on primary keys
- [ ] Row count monitored vs. historical baseline
- [ ] Expectation suite committed to version control
- [ ] Failed validations block pipeline progression
""",
    ),
    SkillEntry(
        slug="stream-processing",
        name="Stream Processing — real-time data with Kafka and Flink/Spark Streaming",
        description=(
            "Build real-time stream processing pipelines: Kafka producers/consumers, "
            "windowing, stateful processing, and exactly-once semantics. Use when building "
            "real-time analytics, event-driven systems, or CDC pipelines."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "kafka",
            "flink",
            "spark-streaming",
            "stream-processing",
            "windowing",
            "exactly-once",
            "cdc",
            "event-driven",
            "consumer-group",
        ],
        project_types=["streaming-pipeline"],
        body="""\
# Stream Processing

Stream processing is batch processing at any time window.
Start with Kafka; add Flink/Spark only when you need stateful aggregations.

## When to use
- Real-time dashboards, fraud detection, recommendations
- CDC (Change Data Capture) from a database
- Event-driven microservices communication

## Kafka producer (Python)

```python
from confluent_kafka import Producer
import json

producer = Producer({"bootstrap.servers": "localhost:9092"})

def produce_order_event(order: dict) -> None:
    producer.produce(
        topic="orders",
        key=order["order_id"].encode(),
        value=json.dumps(order).encode(),
        callback=lambda err, msg: print(f"Delivered: {msg.offset()}" if not err else f"Error: {err}"),
    )
    producer.poll(0)  # trigger delivery callbacks

producer.flush()
```

## Kafka consumer (Python)

```python
from confluent_kafka import Consumer

consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-processor",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,  # manual commit for exactly-once
})
consumer.subscribe(["orders"])

while True:
    msg = consumer.poll(1.0)
    if msg and not msg.error():
        order = json.loads(msg.value())
        process_order(order)  # idempotent
        consumer.commit(asynchronous=False)  # commit after processing
```

## Flink window aggregation (PyFlink)

```python
from pyflink.datastream import StreamExecutionEnvironment
from pyflink.datastream.window import TumblingEventTimeWindows
from pyflink.common.time import Time

env = StreamExecutionEnvironment.get_execution_environment()

stream = env.from_source(kafka_source, WatermarkStrategy.no_watermarks(), "Kafka")

# Count orders per minute
result = (
    stream
    .key_by(lambda x: x["customer_id"])
    .window(TumblingEventTimeWindows.of(Time.minutes(1)))
    .aggregate(CountAggregate())
)
result.add_sink(kafka_sink)
env.execute("order-count-per-minute")
```

## Kafka topic design

```bash
# Create topic with retention and compaction
kafka-topics.sh --create \
  --topic orders \
  --partitions 12 \
  --replication-factor 3 \
  --config retention.ms=604800000 \\  # 7 days
  --config min.insync.replicas=2
```

**Partition count** = expected throughput / single-partition throughput.
More partitions = more parallelism but more overhead.

## Verification checklist
- [ ] Consumer group ID unique per application
- [ ] Manual offset commits after successful processing
- [ ] Processing logic is idempotent
- [ ] Dead-letter topic for failed messages
- [ ] Schema registry used for Avro/Protobuf (prevents schema drift)
- [ ] Consumer lag monitored (`kafka-consumer-groups.sh --describe`)
""",
    ),
    SkillEntry(
        slug="ml-experiment-tracking",
        name="ML Experiment Tracking — MLflow, W&B, and reproducible experiments",
        description=(
            "Track ML experiments with MLflow or Weights & Biases: logging params, "
            "metrics, artifacts, and model versions. Use when starting a new ML project, "
            "comparing model variants, or promoting a model to production."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "mlflow",
            "wandb",
            "experiment-tracking",
            "hyperparameters",
            "model-registry",
            "reproducibility",
            "artifacts",
            "versioning",
        ],
        project_types=["data-ml", "mlops-platform"],
        body="""\
# ML Experiment Tracking

Without tracking, you cannot reproduce results or explain why a model works.
Track everything from day one.

## When to use
- Starting a new ML project or model family
- Comparing model variants (hyperparameter search, architecture changes)
- Promoting a model from experiment to production

## MLflow quickstart

```python
import mlflow
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("churn-prediction")

with mlflow.start_run(run_name="rf-v1"):
    # Log params
    params = {"n_estimators": 200, "max_depth": 6, "random_state": 42}
    mlflow.log_params(params)

    # Train
    model = RandomForestClassifier(**params)
    model.fit(X_train, y_train)

    # Log metrics
    auc = roc_auc_score(y_test, model.predict_proba(X_test)[:, 1])
    mlflow.log_metric("auc", auc)
    mlflow.log_metric("n_train", len(X_train))

    # Log model artifact
    mlflow.sklearn.log_model(model, "model", registered_model_name="churn-rf")

    # Log feature importance plot
    mlflow.log_figure(fig_importance, "feature_importance.png")
```

## Weights & Biases

```python
import wandb

run = wandb.init(project="churn-prediction", config={
    "n_estimators": 200,
    "max_depth": 6,
})

for epoch in range(num_epochs):
    train_loss = ...
    val_loss = ...
    wandb.log({"train_loss": train_loss, "val_loss": val_loss, "epoch": epoch})

wandb.log({"auc": auc, "confusion_matrix": wandb.plot.confusion_matrix(...)})
wandb.finish()
```

## Hyperparameter sweep

```python
# MLflow: manual comparison
mlflow.search_runs(
    experiment_names=["churn-prediction"],
    filter_string="metrics.auc > 0.80",
    order_by=["metrics.auc DESC"],
)

# W&B: automated sweep
sweep_config = {
    "method": "bayes",
    "metric": {"goal": "maximize", "name": "auc"},
    "parameters": {
        "n_estimators": {"values": [100, 200, 500]},
        "max_depth": {"min": 3, "max": 10},
    },
}
sweep_id = wandb.sweep(sweep_config, project="churn-prediction")
wandb.agent(sweep_id, function=train, count=50)
```

## Model promotion workflow

```python
# 1. Compare challenger vs champion
champion = mlflow.get_registered_model("churn-rf").latest_versions[0]
champion_auc = float(mlflow.get_run(champion.run_id).data.metrics["auc"])

# 2. Promote if improvement > threshold
if challenger_auc - champion_auc > 0.005:
    client = mlflow.tracking.MlflowClient()
    client.transition_model_version_stage(
        name="churn-rf",
        version=challenger.version,
        stage="Production",
    )
```

## Verification checklist
- [ ] Every run logs: params, metrics, and model artifact
- [ ] Dataset version (hash or S3 URI) logged with each run
- [ ] Random seeds logged for reproducibility
- [ ] Model registered in Model Registry before deployment
- [ ] Experiment names follow a consistent naming convention
- [ ] Run comparison automated in CI pipeline
""",
    ),
    SkillEntry(
        slug="feature-engineering",
        name="Feature Engineering — feature stores, transformations, and versioning",
        description=(
            "Design and implement ML features: transformation pipelines, feature stores, "
            "point-in-time correct joins, and feature versioning. Use when building features "
            "for ML models, setting up a feature store, or preventing training/serving skew."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "feature-engineering",
            "feature-store",
            "feast",
            "tecton",
            "sklearn",
            "training-serving-skew",
            "point-in-time",
            "pipeline",
        ],
        body="""\
# Feature Engineering

The quality of features determines 80% of model performance.
Feature stores prevent the training/serving skew that kills production models.

## When to use
- Building features for a new ML model
- Setting up a feature store to share features between teams
- Investigating training/serving skew

## Training/serving skew prevention

The same transformation must run at training time AND serving time:

```python
# Bad: inline transformations (easy to diverge)
# Training:
X_train["age_bucket"] = pd.cut(X_train["age"], bins=[0, 18, 35, 65, 100])
# Serving: (might be written differently)
age_bucket = "young" if age < 18 else ...

# Good: shared transformation pipeline
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OrdinalEncoder

pipeline = Pipeline([
    ("age_scaler", StandardScaler()),
    ("cat_encoder", OrdinalEncoder(handle_unknown="use_encoded_value")),
])

pipeline.fit(X_train)
joblib.dump(pipeline, "feature_pipeline.pkl")  # same pkl used in serving
```

## Feature store with Feast

```python
from feast import FeatureStore, Entity, FeatureView, Field
from feast.types import Float64, Int64

customer = Entity(name="customer_id", join_keys=["customer_id"])

customer_stats = FeatureView(
    name="customer_stats",
    entities=[customer],
    schema=[
        Field(name="total_orders", dtype=Int64),
        Field(name="avg_order_value", dtype=Float64),
        Field(name="days_since_last_order", dtype=Int64),
    ],
    source=BigQuerySource(table="myproject.features.customer_stats"),
)

store = FeatureStore(repo_path=".")
store.apply([customer, customer_stats])

# Point-in-time correct training set
training_df = store.get_historical_features(
    entity_df=entity_df,  # order_id, customer_id, event_timestamp
    features=["customer_stats:total_orders", "customer_stats:avg_order_value"],
).to_df()

# Serving
features = store.get_online_features(
    features=["customer_stats:total_orders"],
    entity_rows=[{"customer_id": "123"}],
).to_dict()
```

## Common transformations

```python
from sklearn.preprocessing import (
    StandardScaler,      # continuous features
    MinMaxScaler,        # bounded ranges (e.g. percentages)
    OrdinalEncoder,      # low-cardinality categoricals
    OneHotEncoder,       # when cardinality < 20
    TargetEncoder,       # high-cardinality categoricals
)
from sklearn.impute import SimpleImputer

preprocess = ColumnTransformer([
    ("num", StandardScaler(), numerical_cols),
    ("cat", OrdinalEncoder(), categorical_cols),
    ("impute", SimpleImputer(strategy="median"), cols_with_nulls),
])
```

## Verification checklist
- [ ] Same transformation pipeline used at training and serving time
- [ ] Feature pipeline serialised and versioned alongside model
- [ ] Point-in-time correct joins used for historical training data
- [ ] Feature distributions checked for drift (train vs. production)
- [ ] High-cardinality features handled (target encoding, hashing)
- [ ] Missing value strategy defined and consistent
""",
    ),
    SkillEntry(
        slug="data-lakehouse",
        name="Data Lakehouse — Delta Lake, Iceberg, and open table formats",
        description=(
            "Build a data lakehouse with Delta Lake or Apache Iceberg: ACID transactions "
            "on object storage, time travel, schema evolution, and table maintenance. "
            "Use when building a modern data platform or migrating from a data warehouse."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "delta-lake",
            "iceberg",
            "lakehouse",
            "parquet",
            "spark",
            "acid",
            "time-travel",
            "schema-evolution",
            "compaction",
        ],
        body="""\
# Data Lakehouse

A data lakehouse = data lake (cheap object storage) + warehouse features
(ACID transactions, schema enforcement, time travel).

## When to use
- Building a new data platform from scratch
- Adding ACID transactions to an existing S3/GCS data lake
- Migrating from a traditional data warehouse

## Delta Lake with PySpark

```python
from pyspark.sql import SparkSession
from delta.tables import DeltaTable

spark = SparkSession.builder \
    .config("spark.jars.packages", "io.delta:delta-core_2.12:2.4.0") \
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension") \
    .getOrCreate()

# Write
orders_df.write.format("delta").mode("overwrite").save("s3://my-lake/orders")

# Upsert (MERGE INTO)
delta_table = DeltaTable.forPath(spark, "s3://my-lake/orders")
delta_table.alias("target").merge(
    new_orders.alias("source"),
    "target.order_id = source.order_id"
).whenMatchedUpdateAll() \
 .whenNotMatchedInsertAll() \
 .execute()
```

## Time travel

```python
# Query data as of 7 days ago
df = spark.read.format("delta") \
    .option("timestampAsOf", "2026-05-28") \
    .load("s3://my-lake/orders")

# Restore to a previous version
delta_table.restoreToTimestamp("2026-05-28T00:00:00")
```

## Schema evolution

```python
# Add new column without breaking existing readers
df_with_new_col.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("s3://my-lake/orders")
```

## Table maintenance

```python
# Compact small files (run weekly)
delta_table.optimize().executeCompaction()

# Remove files older than retention window
delta_table.vacuum(retentionHours=168)  # 7 days
```

## Apache Iceberg (alternative)

```python
# Iceberg with Spark
spark.sql('''
    CREATE TABLE catalog.db.orders (
        order_id STRING,
        total_cents BIGINT,
        created_at TIMESTAMP
    )
    USING iceberg
    PARTITIONED BY (days(created_at))
''')

# Metadata queries
spark.sql("SELECT * FROM catalog.db.orders.snapshots").show()
spark.sql("SELECT * FROM catalog.db.orders FOR SYSTEM_TIME AS OF '2026-05-28'")
```

## Verification checklist
- [ ] ACID writes verified (no partial writes on failure)
- [ ] Table optimise scheduled weekly
- [ ] Vacuum run to reclaim storage
- [ ] Schema changes tested with `mergeSchema`
- [ ] Partition strategy aligned to query patterns
- [ ] Time travel retention period configured
""",
    ),
    SkillEntry(
        slug="spark-pipeline",
        name="Apache Spark — distributed data processing with PySpark",
        description=(
            "PySpark patterns: DataFrame operations, partitioning, broadcast joins, "
            "caching, and cluster tuning. Use when processing large datasets (> 100GB), "
            "migrating from Pandas to Spark, or debugging Spark performance issues."
        ),
        domain=SkillDomain.DATA_ENGINEERING,
        tags=[
            "spark",
            "pyspark",
            "dataframe",
            "partitioning",
            "broadcast-join",
            "caching",
            "shuffle",
            "parallelism",
            "databricks",
        ],
        project_types=["streaming-pipeline", "data-ml"],
        body="""\
# Apache Spark

Spark is a distributed computing engine. Use it when data exceeds RAM,
or when you need distributed ML at scale.

## When to use
- Processing datasets > 100 GB that don't fit in RAM
- Distributed model training with Spark ML
- ETL pipelines across a Hadoop/Databricks cluster

## DataFrame operations

```python
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("orders-pipeline").getOrCreate()

orders = spark.read.parquet("s3://data-lake/raw/orders/")

result = (
    orders
    .filter(F.col("status") == "completed")
    .groupBy("customer_id")
    .agg(
        F.count("order_id").alias("total_orders"),
        F.sum("total_cents").alias("total_spent_cents"),
        F.max("created_at").alias("last_order_at"),
    )
    .withColumn("avg_order_value", F.col("total_spent_cents") / F.col("total_orders"))
)

result.write.mode("overwrite").parquet("s3://data-lake/marts/customer_stats/")
```

## Partitioning

```python
# Read: partition pruning (only scan relevant partitions)
orders = spark.read.parquet("s3://data-lake/orders/") \
    .filter(F.col("created_date") == "2026-06-04")  # prunes other partitions

# Write: partition by date for query performance
result.write.partitionBy("created_date") \
    .mode("overwrite").parquet("s3://data-lake/orders/")
```

## Broadcast join (small table optimisation)

```python
# Without broadcast: shuffle join (expensive)
orders.join(products, "product_id")

# With broadcast: send small table to all workers
from pyspark.sql.functions import broadcast
orders.join(broadcast(products), "product_id")  # products must be < 10MB
```

## Caching

```python
# Cache reused DataFrames
customer_stats.cache()  # lazy — only materialises on first action
customer_stats.count()  # trigger materialisation

# Release cache when done
customer_stats.unpersist()
```

## Performance tuning

```python
# Set parallelism
spark.conf.set("spark.sql.shuffle.partitions", "200")  # default is 200; increase for big joins

# Check execution plan
orders.join(customers, "customer_id").explain(mode="formatted")
```

## Verification checklist
- [ ] `explain()` checked — no full table scans on partitioned tables
- [ ] Small tables use broadcast joins
- [ ] Shuffle partition count tuned to data size
- [ ] Expensive DataFrames cached and unpersisted after use
- [ ] Output partitioned by query dimension (date, region)
- [ ] Cluster size sized to task (not just "biggest available")
""",
    ),
]
