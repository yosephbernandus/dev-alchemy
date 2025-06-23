package main

import (
	"fmt"
	"sync"
)

type Data struct {
	counter uint64
}

func main() {
	d := Data{}
	wg := &sync.WaitGroup{}
	mu := &sync.Mutex{}
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			mu.Lock()
			d.counter++
			mu.Unlock()
		}()
	}
	wg.Wait()
	fmt.Println(d.counter)
}
