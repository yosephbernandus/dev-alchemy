import threading
import time


def print_numbers(start, end):
    for i in range(start, end + 1):
        print(f"Number: {i}")
        time.sleep(0.1)  # Small delay to simulate work


# Create threads
t1 = threading.Thread(target=print_numbers, args=(1, 5))
t2 = threading.Thread(target=print_numbers, args=(6, 10))

# Start threads
t1.start()
t2.start()

# Wait for threads to complete
t1.join()
t2.join()

print("Python threading completed")
