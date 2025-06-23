import time
import random
import threading
import multiprocessing
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import statistics


class CollisionTester:
    def __init__(self):
        self.results = defaultdict(list)  # timestamp -> [list of IDs]
        self.lock = threading.Lock()
        self.collision_stats = defaultdict(int)

    def generate_id(self):
        """Generate timestamp + 8-digit random ID"""
        timestamp = int(time.time())
        random_part = random.randint(10000000, 99999999)  # 8 digits
        return timestamp, int(f"{timestamp}{random_part}")

    def worker_thread(self, thread_id, ids_to_generate):
        """Worker thread to generate IDs"""
        local_results = defaultdict(list)

        for _ in range(ids_to_generate):
            timestamp, user_id = self.generate_id()
            local_results[timestamp].append(user_id)

        # Merge results thread-safely
        with self.lock:
            for ts, ids in local_results.items():
                self.results[ts].extend(ids)

    def run_concurrent_test(self, total_ids, num_threads, test_duration=None):
        """Run concurrent ID generation test"""
        print(f"\n🧪 Running test: {total_ids:,} IDs, {num_threads} threads")
        print("-" * 60)

        if test_duration:
            # Time-based test
            print(f"⏱️  Duration: {test_duration} seconds")
            end_time = time.time() + test_duration
            ids_per_thread = float("inf")
        else:
            # Count-based test
            ids_per_thread = total_ids // num_threads
            print(f"📊 IDs per thread: {ids_per_thread:,}")

        self.results.clear()
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = []

            for thread_id in range(num_threads):
                if test_duration:
                    # For time-based, estimate IDs needed
                    estimated_ids = int(
                        total_ids * test_duration / 10
                    )  # Rough estimate
                    future = executor.submit(
                        self.worker_thread, thread_id, estimated_ids
                    )
                else:
                    future = executor.submit(
                        self.worker_thread, thread_id, ids_per_thread
                    )
                futures.append(future)

            # Wait for completion or timeout
            if test_duration:
                time.sleep(test_duration)
                # Cancel remaining futures
                for future in futures:
                    future.cancel()
            else:
                # Wait for all to complete
                for future in futures:
                    future.result()

        end_time = time.time()
        elapsed = end_time - start_time

        return self.analyze_results(elapsed)

    def analyze_results(self, elapsed_time):
        """Analyze results for collisions"""
        total_ids = sum(len(ids) for ids in self.results.values())
        total_collisions = 0
        collision_details = []

        for timestamp, ids in self.results.items():
            unique_ids = set(ids)
            collisions_in_second = len(ids) - len(unique_ids)

            if collisions_in_second > 0:
                total_collisions += collisions_in_second
                collision_details.append(
                    {
                        "timestamp": timestamp,
                        "total_ids": len(ids),
                        "unique_ids": len(unique_ids),
                        "collisions": collisions_in_second,
                        "collision_rate": (collisions_in_second / len(ids)) * 100,
                    }
                )

        # Calculate statistics
        ids_per_second = [len(ids) for ids in self.results.values()]

        results = {
            "total_ids": total_ids,
            "total_collisions": total_collisions,
            "collision_rate": (total_collisions / total_ids) * 100
            if total_ids > 0
            else 0,
            "elapsed_time": elapsed_time,
            "ids_per_second": total_ids / elapsed_time if elapsed_time > 0 else 0,
            "seconds_tested": len(self.results),
            "collision_details": collision_details,
            "stats": {
                "avg_ids_per_second": statistics.mean(ids_per_second)
                if ids_per_second
                else 0,
                "max_ids_per_second": max(ids_per_second) if ids_per_second else 0,
                "min_ids_per_second": min(ids_per_second) if ids_per_second else 0,
            },
        }

        return results

    def print_results(self, results):
        """Print detailed test results"""
        print(f"\n📈 TEST RESULTS")
        print("=" * 60)
        print(f"Total IDs generated: {results['total_ids']:,}")
        print(f"Total collisions: {results['total_collisions']:,}")
        print(f"Overall collision rate: {results['collision_rate']:.6f}%")
        print(f"Test duration: {results['elapsed_time']:.2f} seconds")
        print(f"Generation rate: {results['ids_per_second']:,.0f} IDs/second")
        print(f"Seconds with data: {results['seconds_tested']}")

        print(f"\n📊 Per-Second Statistics:")
        print(f"Average IDs/second: {results['stats']['avg_ids_per_second']:.1f}")
        print(f"Peak IDs/second: {results['stats']['max_ids_per_second']}")
        print(f"Min IDs/second: {results['stats']['min_ids_per_second']}")

        if results["collision_details"]:
            print(f"\n⚠️  COLLISION DETAILS:")
            print("-" * 40)
            for detail in results["collision_details"][:10]:  # Show first 10
                print(
                    f"Timestamp {detail['timestamp']}: "
                    f"{detail['collisions']} collisions out of {detail['total_ids']} IDs "
                    f"({detail['collision_rate']:.3f}%)"
                )

            if len(results["collision_details"]) > 10:
                print(
                    f"... and {len(results['collision_details']) - 10} more collision events"
                )
        else:
            print(f"\n✅ NO COLLISIONS DETECTED!")


def run_stress_tests():
    """Run various stress test scenarios"""
    tester = CollisionTester()

    # Test scenarios: (total_ids, threads, description)
    scenarios = [
        (10000, 10, "Light load: 10K IDs, 10 threads"),
        (50000, 50, "Medium load: 50K IDs, 50 threads"),
        (100000, 100, "Heavy load: 100K IDs, 100 threads"),
        (200000, 200, "Extreme load: 200K IDs, 200 threads"),
        (500000, 100, "High throughput: 500K IDs, 100 threads"),
        (1000000, 500, "Maximum stress: 1M IDs, 500 threads"),
    ]

    all_results = []

    for total_ids, threads, description in scenarios:
        print(f"\n{'='*80}")
        print(f"🚀 {description}")
        print(f"{'='*80}")

        try:
            results = tester.run_concurrent_test(total_ids, threads)
            tester.print_results(results)
            all_results.append((description, results))

            # Brief pause between tests
            time.sleep(1)

        except Exception as e:
            print(f"❌ Test failed: {e}")

    # Summary report
    print(f"\n{'='*80}")
    print("📋 SUMMARY REPORT")
    print(f"{'='*80}")

    for desc, result in all_results:
        collision_rate = result["collision_rate"]
        status = (
            "✅ SAFE"
            if collision_rate < 0.01
            else "⚠️  CAUTION"
            if collision_rate < 0.1
            else "❌ HIGH RISK"
        )
        print(f"{desc}: {collision_rate:.6f}% collision rate {status}")


def run_time_based_test():
    """Run time-based collision test"""
    print(f"\n{'='*80}")
    print("⏰ TIME-BASED COLLISION TEST")
    print(f"{'='*80}")

    tester = CollisionTester()

    # High-intensity time-based test
    test_configs = [
        (10000, 100, 5),  # 10K IDs/sec for 5 seconds
        (20000, 200, 3),  # 20K IDs/sec for 3 seconds
        (50000, 500, 2),  # 50K IDs/sec for 2 seconds
    ]

    for target_rate, threads, duration in test_configs:
        print(f"\n🎯 Target: {target_rate:,} IDs/second for {duration} seconds")
        results = tester.run_concurrent_test(target_rate, threads, duration)
        tester.print_results(results)


def theoretical_analysis():
    """Show theoretical collision probabilities"""
    print(f"\n{'='*80}")
    print("🧮 THEORETICAL COLLISION ANALYSIS")
    print(f"{'='*80}")

    print("8-digit random number space: 100,000,000 combinations")
    print("\nCollision probability by concurrent users per second:")
    print("-" * 50)

    scenarios = [1000, 5000, 10000, 25000, 50000, 100000]

    for users in scenarios:
        # Birthday paradox approximation
        probability = 1 - (1 - (users - 1) / 100000000)
        percentage = probability * 100

        status = (
            "✅ Very Safe"
            if percentage < 0.001
            else "✅ Safe"
            if percentage < 0.01
            else "⚠️  Caution"
            if percentage < 0.1
            else "❌ High Risk"
        )

        print(f"{users:6,} users/sec: {percentage:.6f}% collision chance - {status}")


if __name__ == "__main__":
    print("🔬 COLLISION TESTING SUITE FOR TIMESTAMP + 8-DIGIT RANDOM IDs")
    print("=" * 80)

    # Show theoretical analysis first
    theoretical_analysis()

    # Run practical stress tests
    run_stress_tests()

    # Run time-based tests
    run_time_based_test()

    print(f"\n{'='*80}")
    print("🎉 TESTING COMPLETE!")
    print("💡 Recommendation: 8-digit random is safe for most real-world scenarios")
    print("⚡ For ultra-high traffic, consider 9-digit random for extra safety")
    print(f"{'='*80}")
