package main

import (
	"fmt"
	"sync"
)

func main() {
	var mutex sync.Mutex
	var counter int = 0
	var wg sync.WaitGroup

	orderedTask := func(taskID int) {
		defer wg.Done()

		mutex.Lock() // Acquire mutex to ensure exclusive access
		defer mutex.Unlock()

		counter++
		fmt.Printf("Task %d executing as number %d\n", taskID, counter)
		// Database operation would go here
		// db.Exec("UPDATE table SET value = ? WHERE id = ?", counter, someID)
	}

	// Launch goroutines
	wg.Add(10)
	for i := 0; i < 10; i++ {
		go orderedTask(i)
	}

	wg.Wait()
}
