import redis
import threading
import time
import json
from concurrent.futures import ThreadPoolExecutor

redis_client = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)

# ==========================================
# OPTIMISTIC LOCKING EXAMPLES
# ==========================================


class OptimisticLockingDemo:
    def __init__(self):
        # Initialize account with balance and version
        account_data = {"balance": 1000, "version": 1}
        redis_client.set("account:123", json.dumps(account_data))

    def transfer_with_version_optimistic(self, thread_id, amount):
        """Optimistic locking using version numbers"""
        max_retries = 5

        for attempt in range(max_retries):
            try:
                # 1. READ without locking
                account_data = json.loads(redis_client.get("account:123"))
                current_balance = account_data["balance"]
                current_version = account_data["version"]

                print(
                    f"Thread {thread_id}: Read balance={current_balance}, version={current_version}"
                )

                # 2. BUSINESS LOGIC (no locks held)
                if current_balance < amount:
                    print(f"Thread {thread_id}: Insufficient funds")
                    return False

                # Simulate processing time
                time.sleep(0.1)

                new_balance = current_balance - amount
                new_version = current_version + 1

                # 3. OPTIMISTIC UPDATE - only if version hasn't changed
                lua_script = """
                local current_data = redis.call('GET', KEYS[1])
                if current_data then
                    local data = cjson.decode(current_data)
                    if data.version == tonumber(ARGV[1]) then
                        local new_data = {
                            balance = tonumber(ARGV[2]),
                            version = tonumber(ARGV[3])
                        }
                        redis.call('SET', KEYS[1], cjson.encode(new_data))
                        return 1
                    else
                        return 0
                    end
                else
                    return -1
                end
                """

                result = redis_client.eval(
                    lua_script,
                    1,
                    "account:123",
                    current_version,
                    new_balance,
                    new_version,
                )

                if result == 1:
                    print(
                        f"Thread {thread_id}: ✅ Transfer successful! New balance: {new_balance}"
                    )
                    return True
                elif result == 0:
                    print(
                        f"Thread {thread_id}: ⚠️ Version conflict detected! Retry {attempt + 1}"
                    )
                    time.sleep(0.05)  # Small delay before retry
                    continue
                else:
                    print(f"Thread {thread_id}: ❌ Account not found")
                    return False

            except Exception as e:
                print(f"Thread {thread_id}: Error: {e}")
                time.sleep(0.05)

        print(f"Thread {thread_id}: ❌ Max retries exceeded")
        return False

    def transfer_with_cas_optimistic(self, thread_id, amount):
        """Optimistic locking using Compare-And-Swap"""
        max_retries = 5

        for attempt in range(max_retries):
            # 1. READ current value
            current_data = redis_client.get("account:123")
            account = json.loads(current_data)

            print(
                f"Thread {thread_id}: CAS attempt {attempt + 1}, balance={account['balance']}"
            )

            # 2. CALCULATE new value
            if account["balance"] < amount:
                print(f"Thread {thread_id}: Insufficient funds")
                return False

            new_balance = account["balance"] - amount
            new_version = account["version"] + 1
            new_data = json.dumps({"balance": new_balance, "version": new_version})

            # Simulate processing
            time.sleep(0.1)

            # 3. COMPARE-AND-SWAP: update only if value unchanged
            lua_script = """
            if redis.call('GET', KEYS[1]) == ARGV[1] then
                redis.call('SET', KEYS[1], ARGV[2])
                return 1
            else
                return 0
            end
            """

            result = redis_client.eval(
                lua_script, 1, "account:123", current_data, new_data
            )

            if result == 1:
                print(
                    f"Thread {thread_id}: ✅ CAS successful! New balance: {new_balance}"
                )
                return True
            else:
                print(
                    f"Thread {thread_id}: ⚠️ CAS failed, data changed! Retry {attempt + 1}"
                )
                time.sleep(0.05)

        print(f"Thread {thread_id}: ❌ CAS max retries exceeded")
        return False


# ==========================================
# PESSIMISTIC LOCKING FOR COMPARISON
# ==========================================


class PessimisticLockingDemo:
    def __init__(self):
        account_data = {"balance": 1000, "version": 1}
        redis_client.set("account:456", json.dumps(account_data))

    def transfer_with_pessimistic_lock(self, thread_id, amount):
        """Pessimistic locking - lock first, then work"""
        lock_key = "lock:account:456"

        print(f"Thread {thread_id}: Trying to acquire lock...")

        # 1. ACQUIRE LOCK FIRST
        if redis_client.set(lock_key, f"thread_{thread_id}", nx=True, ex=5):
            try:
                print(f"Thread {thread_id}: 🔒 Lock acquired!")

                # 2. READ data (safe because we have lock)
                account_data = json.loads(redis_client.get("account:456"))
                current_balance = account_data["balance"]

                print(f"Thread {thread_id}: Balance: {current_balance}")

                # 3. BUSINESS LOGIC
                if current_balance < amount:
                    print(f"Thread {thread_id}: Insufficient funds")
                    return False

                # Simulate processing time (lock is held)
                time.sleep(0.1)

                # 4. UPDATE (safe because we have lock)
                new_balance = current_balance - amount
                new_version = account_data["version"] + 1
                new_data = {"balance": new_balance, "version": new_version}
                redis_client.set("account:456", json.dumps(new_data))

                print(
                    f"Thread {thread_id}: ✅ Transfer successful! New balance: {new_balance}"
                )
                return True

            finally:
                # 5. RELEASE LOCK
                redis_client.delete(lock_key)
                print(f"Thread {thread_id}: 🔓 Lock released")
        else:
            print(f"Thread {thread_id}: ❌ Could not acquire lock")
            return False


# ==========================================
# TEST FUNCTIONS
# ==========================================


def test_optimistic_locking():
    print("=" * 60)
    print("OPTIMISTIC LOCKING TEST")
    print("=" * 60)

    demo = OptimisticLockingDemo()

    print("Initial account state:")
    account = json.loads(redis_client.get("account:123"))
    print(f"Balance: {account['balance']}, Version: {account['version']}\n")

    # 5 threads trying to withdraw $100 each
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            future = executor.submit(
                demo.transfer_with_version_optimistic, f"T{i+1}", 100
            )
            futures.append(future)

        results = [f.result() for f in futures]

    print(f"\nSuccessful transfers: {sum(results)}")

    final_account = json.loads(redis_client.get("account:123"))
    print(f"Final balance: {final_account['balance']}")
    print(f"Final version: {final_account['version']}\n")


def test_pessimistic_locking():
    print("=" * 60)
    print("PESSIMISTIC LOCKING TEST")
    print("=" * 60)

    demo = PessimisticLockingDemo()

    print("Initial account state:")
    account = json.loads(redis_client.get("account:456"))
    print(f"Balance: {account['balance']}, Version: {account['version']}\n")

    # 5 threads trying to withdraw $100 each
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for i in range(5):
            future = executor.submit(
                demo.transfer_with_pessimistic_lock, f"T{i+1}", 100
            )
            futures.append(future)

        results = [f.result() for f in futures]

    print(f"\nSuccessful transfers: {sum(results)}")

    final_account = json.loads(redis_client.get("account:456"))
    print(f"Final balance: {final_account['balance']}")
    print(f"Final version: {final_account['version']}\n")


def test_cas_optimistic():
    print("=" * 60)
    print("COMPARE-AND-SWAP OPTIMISTIC TEST")
    print("=" * 60)

    # Reset account
    account_data = {"balance": 1000, "version": 1}
    redis_client.set("account:123", json.dumps(account_data))

    demo = OptimisticLockingDemo()

    print("Testing CAS approach:")
    account = json.loads(redis_client.get("account:123"))
    print(f"Initial: Balance: {account['balance']}, Version: {account['version']}\n")

    # 3 threads using CAS
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i in range(3):
            future = executor.submit(
                demo.transfer_with_cas_optimistic, f"CAS-T{i+1}", 150
            )
            futures.append(future)

        results = [f.result() for f in futures]

    print(f"\nSuccessful CAS transfers: {sum(results)}")

    final_account = json.loads(redis_client.get("account:123"))
    print(f"Final balance: {final_account['balance']}")
    print(f"Final version: {final_account['version']}\n")


if __name__ == "__main__":
    print("🔄 Optimistic vs Pessimistic Locking Demo\n")

    test_optimistic_locking()
    # test_cas_optimistic()
    # test_pessimistic_locking()
