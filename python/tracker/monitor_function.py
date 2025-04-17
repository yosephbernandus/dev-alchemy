import time
import functools
from prometheus_client.registry import CollectorRegistry
import psutil
import os
from prometheus_client import Counter, Histogram, Gauge, push_to_gateway
from raven.contrib.django.raven_compat.models import logger

FUNCTION_CALLS = Counter(
    "settlement_function_calls_total",
    "Number of calls to settlement function",
    ["status"],
)

FUNCTION_DURATION = Histogram(
    "settlement_function_duration_seconds",
    "Duration of settlement function execution",
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0],
)

MEMORY_USAGE = Gauge(
    "settlement_memory_usage_mb", "Memory usage during settlement processing"
)

CPU_USAGE = Gauge("settlement_cpu_percent", "CPU usage during settlement processing")


def monitor_function(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        process = psutil.Process(os.getpid())
        start_memory = process.memory_info().rss / (1024 * 1024)
        MEMORY_USAGE.set(start_memory)

        start_time = time.time()
        registry = CollectorRegistry()

        status = "unknown"
        try:
            # Execute the function
            result = func(*args, **kwargs)
            status = "success"
            return result
        except Exception as e:
            status = "error"
            raise
        finally:
            duration = time.time() - start_time
            FUNCTION_DURATION.observe(duration)
            FUNCTION_CALLS.labels(status=status).inc()

            current_memory = process.memory_info().rss / (1024 * 1024)
            MEMORY_USAGE.set(current_memory)
            CPU_USAGE.set(process.cpu_percent())

            try:
                push_to_gateway(
                    "localhost:9091", job="settlement_processing", registry=registry
                )
            except Exception as e:
                pass

            print(
                f"Function executed in {duration:.2f}s with {current_memory-start_memory:.2f}MB memory increase"
            )
            logger.info(
                {
                    "action": "monitor_function",
                    "function_name": func.__name__,
                    "duration": duration,
                    "memory_usage": current_memory - start_memory,
                    "cpu_usage": process.cpu_percent(),
                }
            )

    return wrapper
