# Tracker

I Use this for doing a profiling process and find the bottleneck / problematic process in local computer

1. django_query_tracker
Function to tracking django query + integration with the prometheus and visualize using grafana.
How to use:
```
from memory_profiler import profile
@profile(stream=open("memory_profiler.log", "w+"))  # Optional
@track_db_query
def foo()
    ....
```

2. monitor_function
Function to track function process that running and sending to prometheus and visualize in grafana
How to use:
```
from memory_profiler import profile
@profile(stream=open("memory_profiler.log", "w+"))  # Optional
@monitor_function
def foo()
    ....
```

