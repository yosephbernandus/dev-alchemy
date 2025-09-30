# ULID Libraries Quick Benchmark Results
==================================================

## System Specifications
- CPU Cores: 8 cores
- Memory: 16GB total (15GB usable)
- Python: 3.12.3 [Clang 17.0.6 ]
- Platform: Ubuntu 20.04.6 LTS

## Performance Rankings

| Rank | Library | Generation (M ops/sec) | Parsing (M ops/sec) | Overall Score |
|------|---------|------------------------|---------------------|---------------|
| 1 | ulid-python | 7.85 | 7.07 | 100.0% |
| 2 | py-ulid | 2.52 | 0.00 | 16.0% |
| 3 | ulid-py | 0.72 | 0.27 | 6.5% |
| 4 | python-ulid | 0.27 | 0.22 | 3.3% |

## Detailed Library Analysis

### ulid-python
Performance:
- Generation: 7.85M ops/sec (100.0%)
- Parsing: 7.07M ops/sec (100.0%)
Memory Usage:
- Generation: 4.0MB overhead
- Parsing: 1.3MB overhead

### py-ulid
Performance:
- Generation: 2.52M ops/sec (32.0%)
- Parsing: Doesn't support with same feature
Memory Usage:
- Generation: 5.2MB overhead
- Parsing: Doesn't support with same feature

### ulid-py
Performance:
- Generation: 0.72M ops/sec (9.2%)
- Parsing: 0.27M ops/sec (3.8%)
Memory Usage:
- Generation: 3.6MB overhead
- Parsing: 0.8MB overhead

### python-ulid
Performance:
- Generation: 0.27M ops/sec (3.4%)
- Parsing: 0.22M ops/sec (3.2%)
Memory Usage:
- Generation: 3.7MB overhead
- Parsing: 1.3MB overhead

## Test Configuration
- Iterations: 100,000 per test
- Environment: Laptop Machine
