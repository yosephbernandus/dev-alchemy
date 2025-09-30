#!/usr/bin/env python3
"""
Individual ULID library benchmark runner.
Runs in isolated Docker container with resource limits.
"""

import time
import json
import statistics
import sys
import os
import psutil
from typing import Dict, Callable, Any


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def benchmark_function(
    func: Callable, iterations: int = 10000, warmup: int = 100
) -> Dict[str, Any]:
    """Benchmark a function with detailed metrics."""
    # Warmup
    for _ in range(warmup):
        try:
            func()
        except Exception:
            pass

    # Collect baseline memory
    baseline_memory = get_memory_usage()

    # Actual timing
    times = []
    memory_samples = []

    for i in range(iterations):
        start_time = time.perf_counter()
        try:
            result = func()
            end_time = time.perf_counter()
            times.append(end_time - start_time)

            # Sample memory every 1000 iterations
            if i % 1000 == 0:
                memory_samples.append(get_memory_usage())

        except Exception as e:
            print(f"Error during iteration {i}: {e}")
            continue

    if not times:
        return {
            "success": False,
            "error": "No successful iterations",
            "ops_per_sec": 0,
            "mean_time": 0,
            "median_time": 0,
            "memory_usage": 0,
        }

    # Calculate statistics
    mean_time = statistics.mean(times)
    median_time = statistics.median(times)
    min_time = min(times)
    max_time = max(times)
    ops_per_sec = 1.0 / mean_time if mean_time > 0 else 0

    # Memory statistics
    peak_memory = max(memory_samples) if memory_samples else baseline_memory
    memory_overhead = peak_memory - baseline_memory

    return {
        "success": True,
        "ops_per_sec": ops_per_sec,
        "mean_time": mean_time,
        "median_time": median_time,
        "min_time": min_time,
        "max_time": max_time,
        "total_iterations": len(times),
        "baseline_memory_mb": baseline_memory,
        "peak_memory_mb": peak_memory,
        "memory_overhead_mb": memory_overhead,
    }


def run_ulid_python_benchmark():
    """Benchmark ulid-python library."""
    try:
        import pyulid

        # Test ULID generation
        print("Testing ULID generation...")
        gen_results = benchmark_function(pyulid.ulid, iterations=100000)

        # Test timestamp parsing
        print("Testing timestamp parsing...")
        test_ulid = pyulid.ulid()
        parse_results = benchmark_function(
            lambda: pyulid.ulid_timestamp(test_ulid), iterations=100000
        )

        return {
            "library": "ulid-python",
            "generation": gen_results,
            "parsing": parse_results,
        }

    except ImportError as e:
        return {"library": "ulid-python", "error": f"Import failed: {e}"}


def run_python_ulid_benchmark():
    """Benchmark python-ulid library."""
    try:
        import time
        from ulid import ULID  # python-ulid correct import

        # Test ULID generation
        print("Testing ULID generation...")
        gen_results = benchmark_function(lambda: str(ULID()), iterations=100000)

        # Test timestamp parsing (from existing ULID)
        print("Testing timestamp parsing...")
        test_ulid_str = str(ULID())
        parse_results = benchmark_function(
            lambda: ULID.from_str(test_ulid_str).timestamp, iterations=100000
        )

        return {
            "library": "python-ulid",
            "generation": gen_results,
            "parsing": parse_results,
        }

    except ImportError as e:
        return {"library": "python-ulid", "error": f"Import failed: {e}"}
    except Exception as e:
        return {"library": "python-ulid", "error": f"Runtime error: {e}"}


def run_py_ulid_benchmark():
    """Benchmark py-ulid library."""
    try:
        import ulid  # py-ulid imports as ulid

        # Test ULID generation
        print("Testing ULID generation...")
        gen_results = benchmark_function(lambda: str(ulid.ULID()), iterations=100000)

        # Test timestamp parsing (py-ulid does support timestamp extraction)
        print("Testing timestamp parsing...")
        test_ulid = str(ulid.ULID())
        parse_results = benchmark_function(
            lambda: ulid.ULID.from_str(test_ulid).timestamp, iterations=100000
        )

        return {
            "library": "py-ulid",
            "generation": gen_results,
            "parsing": parse_results,
        }

    except ImportError as e:
        return {"library": "py-ulid", "error": f"Import failed: {e}"}
    except Exception as e:
        return {"library": "py-ulid", "error": f"Runtime error: {e}"}


def run_ulid_py_benchmark():
    """Benchmark ulid-py library."""
    try:
        import datetime
        import ulid  # ulid-py imports as ulid

        # Test ULID generation
        print("Testing ULID generation...")
        gen_results = benchmark_function(ulid.new, iterations=100000)

        # Test timestamp parsing (ulid-py supports from_timestamp)
        print("Testing timestamp parsing...")
        timestamp = datetime.datetime(2023, 1, 1)
        parse_results = benchmark_function(
            lambda: ulid.from_timestamp(timestamp), iterations=100000
        )

        return {
            "library": "ulid-py",
            "generation": gen_results,
            "parsing": parse_results,
        }

    except ImportError as e:
        return {"library": "ulid-py", "error": f"Import failed: {e}"}
    except Exception as e:
        return {"library": "ulid-py", "error": f"Runtime error: {e}"}


def main():
    """Main benchmark runner."""
    library_name = os.environ.get("BENCHMARK_LIBRARY", "ulid-python")

    print(f"Running benchmark for: {library_name}")
    print(f"Python version: {sys.version}")
    print(f"Available memory: {psutil.virtual_memory().available / 1024 / 1024:.1f} MB")
    print(f"CPU cores: {psutil.cpu_count()}")
    print("-" * 50)

    # Run the appropriate benchmark
    if library_name == "ulid-python":
        results = run_ulid_python_benchmark()
    elif library_name == "python-ulid":
        results = run_python_ulid_benchmark()
    elif library_name == "py-ulid":
        results = run_py_ulid_benchmark()
    elif library_name == "ulid-py":
        results = run_ulid_py_benchmark()
    else:
        results = {"library": library_name, "error": "Unknown library"}

    # Add system info
    results["system_info"] = {
        "python_version": sys.version,
        "available_memory_mb": psutil.virtual_memory().available / 1024 / 1024,
        "cpu_cores": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
    }

    # Output results as JSON (to mounted volume if available, otherwise local)
    output_dir = "/results" if os.path.exists("/results") else "/benchmark"
    output_file = f"{output_dir}/results_{library_name.replace('-', '_')}.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")

    # Also print summary
    if "error" not in results:
        print("\nSUMMARY:")
        print(f"Generation: {results['generation'].get('ops_per_sec', 0):,.0f} ops/sec")
        print(f"Parsing: {results['parsing'].get('ops_per_sec', 0):,.0f} ops/sec")
    else:
        print(f"ERROR: {results['error']}")


if __name__ == "__main__":
    main()
