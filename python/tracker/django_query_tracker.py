from prometheus_client import (
    Counter,
    Summary,
    push_to_gateway,
    CollectorRegistry,
)
from django.db import connection
import functools
import logging

logger = logging.getLogger("sql_profiler")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("sql_queries.log")
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


def track_db_query(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        function_name = func.__name__

        registry = CollectorRegistry()
        db_query_count = Counter(
            "settlement_db_query_count_total",
            "Total number of database queries",
            ["query_type", "function"],
            registry=registry,
        )
        db_query_duration = Summary(
            "settlement_db_query_duration_seconds",
            "Database query execution time",
            ["query_type", "function"],
            registry=registry,
        )
        slow_queries = Counter(
            "settlement_slow_queries_total",
            "Number of slow database queries (>100ms)",
            ["query_type", "function"],
            registry=registry,
        )

        from django.conf import settings

        settings.DEBUG = True

        if hasattr(connection, "queries_log"):
            connection.queries_log.clear()

        try:
            result = func(*args, **kwargs)
            return result
        finally:
            slow_query_threshold = 0.1  # 100ms

            query_stats = {
                "SELECT": {"count": 0, "time": 0, "slow": 0, "queries": []},
                "INSERT": {"count": 0, "time": 0, "slow": 0, "queries": []},
                "UPDATE": {"count": 0, "time": 0, "slow": 0, "queries": []},
                "DELETE": {"count": 0, "time": 0, "slow": 0, "queries": []},
                "OTHER": {"count": 0, "time": 0, "slow": 0, "queries": []},
            }

            # Add TOTAL for overall metrics
            db_query_count.labels(query_type="TOTAL", function=function_name).inc(0)

            if hasattr(connection, "queries"):
                total_queries = len(connection.queries)
                db_query_count.labels(query_type="TOTAL", function=function_name).inc(
                    total_queries
                )

                for i, query in enumerate(connection.queries):
                    # Get the SQL and execution time
                    sql = query.get("sql", "")
                    query_time = float(query.get("time", 0))

                    # Determine query type
                    sql_upper = sql.upper().strip()
                    query_type = "OTHER"
                    if sql_upper.startswith("SELECT"):
                        query_type = "SELECT"
                    elif sql_upper.startswith("INSERT"):
                        query_type = "INSERT"
                    elif sql_upper.startswith("UPDATE"):
                        query_type = "UPDATE"
                    elif sql_upper.startswith("DELETE"):
                        query_type = "DELETE"

                    # Update stats
                    query_stats[query_type]["count"] += 1
                    query_stats[query_type]["time"] += query_time

                    # Record metrics
                    db_query_count.labels(
                        query_type=query_type, function=function_name
                    ).inc()
                    db_query_duration.labels(
                        query_type=query_type, function=function_name
                    ).observe(query_time)

                    # Log SQL with execution time
                    log_entry = f"Query #{i+1} ({query_time:.4f}s) - {sql}"
                    query_stats[query_type]["queries"].append(log_entry)

                    # Track slow queries
                    if query_time > slow_query_threshold:
                        slow_queries.labels(
                            query_type=query_type, function=function_name
                        ).inc()
                        query_stats[query_type]["slow"] += 1
                        logger.warning(f"SLOW QUERY: {log_entry}")

            logger.info(f"=== SQL Query Summary for {function_name} ===")
            for query_type, stats in query_stats.items():
                if stats["count"] > 0:
                    avg_time = (
                        stats["time"] / stats["count"] if stats["count"] > 0 else 0
                    )
                    logger.info(
                        f"{query_type} Queries: {stats['count']} (avg: {avg_time:.4f}s, slow: {stats['slow']})"
                    )

                    for query_log in stats["queries"]:
                        logger.info(query_log)

            try:
                push_to_gateway(
                    "localhost:9091",
                    job=f"settlement_processing_{function_name}",
                    registry=registry,
                )
                print("Pushed metrics to Pushgateway")
            except Exception as e:
                print(f"Failed to push metrics: {str(e)}")

    return wrapper
