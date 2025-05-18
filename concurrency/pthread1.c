#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>

// Correct prototype for thread function
void *print_message_function(void *ptr);

int main() // `main` should explicitly return int
{
  pthread_t thread1, thread2;
  char *message1 = "Thread 1";
  char *message2 = "Thread 2";
  int iret1, iret2;

  // Create independent threads
  iret1 =
      pthread_create(&thread1, NULL, print_message_function, (void *)message1);
  iret2 =
      pthread_create(&thread2, NULL, print_message_function, (void *)message2);

  // Wait till threads are complete before continuing in main
  pthread_join(thread1, NULL);
  pthread_join(thread2, NULL);

  printf("Thread 1 returns: %d\n", iret1);
  printf("Thread 2 returns: %d\n", iret2);

  return 0;
}

void *print_message_function(void *ptr) {
  char *message = (char *)ptr;
  printf("%s \n", message);
  return NULL; // Must return a value from a `void *` function
}

/*gcc -o pthread1 pthread1.c -pthread*/
