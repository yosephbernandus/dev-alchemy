import redis
import threading
import time

# Connect to Redis
redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


def get_counter():
    """Helper function to get current counter value"""
    value = redis_client.get("counter") or 0
    print(f"Current counter value: {value}")
    return int(value)


def increment_without_lock():
    """Without lock - Race condition happens"""
    # Read current value
    current = int(redis_client.get("counter") or 0)
    print(f"Thread {threading.current_thread().name}: Read value = {current}")

    # Simulate processing time (this is where race condition happens)
    time.sleep(0.1)

    # Write new value
    new_value = current + 1
    redis_client.set("counter", new_value)

    # Print counter after write
    counter_now = redis_client.get("counter")
    print(
        f"Thread {threading.current_thread().name}: Wrote value = {new_value}, Counter now = {counter_now}"
    )


def increment_with_lock():
    """With lock - No race condition"""
    lock_key = "counter_lock"

    # Try to get lock
    if redis_client.set(lock_key, "locked", nx=True, ex=5):  # Lock for 5 seconds
        try:
            # Read current value
            current = int(redis_client.get("counter") or 0)
            print(
                f"Thread {threading.current_thread().name}: Read value = {current} (LOCKED)"
            )

            # Simulate processing time
            time.sleep(0.1)

            # Write new value
            new_value = current + 1
            redis_client.set("counter", new_value)

            # Print counter after write
            counter_now = redis_client.get("counter")
            print(
                f"Thread {threading.current_thread().name}: Wrote value = {new_value}, Counter now = {counter_now} (LOCKED)"
            )

        finally:
            # Release lock
            redis_client.delete(lock_key)
    else:
        print(
            f"Thread {threading.current_thread().name}: Could not get lock, waiting..."
        )
        time.sleep(0.2)
        increment_with_lock()  # Retry


def test_without_lock():
    print("=== TEST WITHOUT LOCK ===")
    redis_client.set("counter", 0)  # Reset counter
    print(f"Initial counter: {redis_client.get('counter')}")

    # Create 5 threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=increment_without_lock, name=f"T{i+1}")
        threads.append(t)

    # Start all threads at once
    for t in threads:
        t.start()

    # Wait for all to finish
    for t in threads:
        t.join()

    final_value = redis_client.get("counter")
    print(f"Final counter value: {final_value} (Expected: 5)")
    print(f"Race condition: {'YES' if int(final_value) != 5 else 'NO'}\n")


def test_with_lock():
    print("=== TEST WITH LOCK ===")
    redis_client.set("counter", 0)  # Reset counter
    print(f"Initial counter: {redis_client.get('counter')}")

    # Create 5 threads
    threads = []
    for i in range(5):
        t = threading.Thread(target=increment_with_lock, name=f"T{i+1}")
        threads.append(t)

    # Start all threads at once
    for t in threads:
        t.start()

    # Wait for all to finish
    for t in threads:
        t.join()

    final_value = redis_client.get("counter")
    print(f"Final counter value: {final_value} (Expected: 5)")
    print(f"Race condition: {'YES' if int(final_value) != 5 else 'NO'}\n")


if __name__ == "__main__":
    print("Simple Race Condition Test\n")

    # Show initial counter
    get_counter()

    # Test without lock (will show race condition)
    # test_without_lock()

    # # Test with lock (will be consistent)
    test_with_lock()

    # Show final counter
    print("Final check:")
    get_counter()

    print("Done!")
