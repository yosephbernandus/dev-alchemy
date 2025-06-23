package main

import (
	"fmt"
	"sync/atomic"
)

type Data struct {
	counter atomic.Uint64
}

func main() {
	d := Data{}
	// wg := &sync.WaitGroup{}
	for i := 0; i < 1000; i++ {
		// wg.Add(1)
		go func() {
			// defer wg.Done()
			d.counter.Add(1)
		}()
	}
	// wg.Wait()
	fmt.Println(d.counter)
}
