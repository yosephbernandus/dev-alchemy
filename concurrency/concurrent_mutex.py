import threading

# Using a lock to ensure ordered execution
lock = threading.Lock()
counter = 0


def ordered_task(task_id):
    global counter
    with lock:  # Acquire lock, ensuring only one thread executes this block at a time
        current = counter
        counter += 1
        print(f"Task {task_id} executing as number {counter}")
        # Database operation would go here
        # db.execute("UPDATE table SET value = %s WHERE id = %s", (counter, some_id))


# Launch threads
threads = []
for i in range(10):
    t = threading.Thread(target=ordered_task, args=(i,))
    threads.append(t)
    t.start()

for t in threads:
    t.join()
