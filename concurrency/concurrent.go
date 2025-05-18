package main

import (
	"fmt"
	"sync"
	"time"
)

func printNumbers(start, end int, wg *sync.WaitGroup) {
	defer wg.Done() // Mark this goroutine as done when function returns

	for i := start; i <= end; i++ {
		fmt.Printf("Number: %d\n", i)
		time.Sleep(100 * time.Millisecond) // Small delay to simulate work
	}
}

func main() {
	var wg sync.WaitGroup
	wg.Add(2) // We will launch 2 goroutines

	// Launch goroutines
	go printNumbers(1, 5, &wg)
	go printNumbers(6, 10, &wg)

	// Wait for goroutines to complete
	wg.Wait()

	fmt.Println("Go goroutines completed")
}
