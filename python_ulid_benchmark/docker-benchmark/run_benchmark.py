#!/usr/bin/env python3
"""
Docker-based ULID benchmark orchestrator.
Runs each library in isolated containers with resource limits.
"""

import subprocess
import json
import time
from pathlib import Path
from typing import Dict

# Libraries to benchmark
LIBRARIES = ["ulid-python", "python-ulid", "py-ulid", "ulid-py"]

# Resource limits (512MB RAM, 2 CPU cores)
MEMORY_LIMIT = "512m"
CPU_LIMIT = "2"


def build_docker_image(library: str) -> bool:
    """Build Docker image for a library."""
    dockerfile = f"Dockerfile.{library}"
    image_tag = f"ulid-benchmark-{library}"

    print(f"Building Docker image for {library}...")

    try:
        cmd = [
            "docker",
            "build",
            "-f",
            dockerfile,
            "-t",
            image_tag,
            ".",  # Build context is current directory
        ]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
        )

        if result.returncode == 0:
            print(f"Successfully built {image_tag}")
            return True
        else:
            print(f"Failed to build {image_tag}")
            print(f"Error: {result.stderr}")
            return False

    except subprocess.TimeoutExpired:
        print(f"Build timeout for {library}")
        return False
    except Exception as e:
        print(f"Build error for {library}: {e}")
        return False


def run_benchmark_container(library: str) -> Dict:
    """Run benchmark for a library in Docker container."""
    image_tag = f"ulid-benchmark-{library}"
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)

    print(f"Running benchmark for {library}...")

    try:
        # Create container with resource limits
        cmd = [
            "docker",
            "run",
            "--rm",
            f"--memory={MEMORY_LIMIT}",
            f"--cpus={CPU_LIMIT}",
            "--memory-swap=-1",  # Disable swap
            "-v",
            f"{results_dir.absolute()}:/results",  # Mount to /results to avoid overwriting /benchmark
            image_tag,
        ]

        start_time = time.time()
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=180,  # 3 minute timeout
        )
        end_time = time.time()

        if result.returncode == 0:
            print(f"Benchmark completed for {library} in {end_time - start_time:.1f}s")

            # Load results
            results_file = results_dir / f"results_{library.replace('-', '_')}.json"
            if results_file.exists():
                with open(results_file, "r") as f:
                    return json.load(f)
            else:
                return {"library": library, "error": "Results file not found"}
        else:
            print(f"Benchmark failed for {library}")
            print(f"Stdout: {result.stdout}")
            print(f"Stderr: {result.stderr}")
            return {"library": library, "error": f"Container failed: {result.stderr}"}

    except subprocess.TimeoutExpired:
        print(f"Benchmark timeout for {library}")
        return {"library": library, "error": "Benchmark timeout"}
    except Exception as e:
        print(f"Benchmark error for {library}: {e}")
        return {"library": library, "error": str(e)}


def cleanup_docker_images():
    """Clean up Docker images."""
    print("Cleaning up Docker images...")
    for library in LIBRARIES:
        image_tag = f"ulid-benchmark-{library}"
        try:
            subprocess.run(
                ["docker", "rmi", image_tag], capture_output=True, check=False
            )
        except Exception:
            pass


def main():
    """Main orchestrator."""
    print("ULID Docker Benchmark Suite")
    print("=" * 50)
    print(f"Resource limits: {MEMORY_LIMIT} RAM, {CPU_LIMIT} CPU cores")
    print(f"Libraries to test: {', '.join(LIBRARIES)}")
    print()

    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Docker is not available. Please install Docker first.")
        return 1

    all_results = []
    successful_builds = []

    # Build all Docker images first
    print("Building Docker images...")
    for library in LIBRARIES:
        if build_docker_image(library):
            successful_builds.append(library)

    print(f"\n Successfully built {len(successful_builds)}/{len(LIBRARIES)} images")

    if not successful_builds:
        print(" No images built successfully. Exiting.")
        return 1

    # Run benchmarks
    print("\nRunning benchmarks...")
    for library in successful_builds:
        result = run_benchmark_container(library)
        all_results.append(result)

        # Print quick summary
        if "error" not in result:
            gen_ops = result.get("generation", {}).get("ops_per_sec", 0)
            val_ops = result.get("validation", {}).get("ops_per_sec", 0)
            parse_ops = result.get("parsing", {}).get("ops_per_sec", 0)
            print(
                f"   Gen: {gen_ops:,.0f} ops/sec, Val: {val_ops:,.0f} ops/sec, Parse: {parse_ops:,.0f} ops/sec"
            )
        else:
            print(f"   Error: {result['error']}")
        print()

    # Save consolidated results
    results_file = Path("consolidated_results.json")
    with open(results_file, "w") as f:
        json.dump(
            {
                "benchmark_info": {
                    "memory_limit": MEMORY_LIMIT,
                    "cpu_limit": CPU_LIMIT,
                    "timestamp": time.time(),
                },
                "results": all_results,
            },
            f,
            indent=2,
        )

    print(f"Results saved to: {results_file}")

    # Cleanup
    cleanup_docker_images()

    print("\n Benchmark complete!")
    print("Run 'python visualize_results.py' to generate charts.")

    return 0


if __name__ == "__main__":
    exit(main())

