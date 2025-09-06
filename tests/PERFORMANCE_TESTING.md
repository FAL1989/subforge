# SubForge Performance Testing Suite
Created: 2025-09-05 17:45 UTC-3 São Paulo

## Overview

Comprehensive performance and load testing suite for SubForge, measuring execution time, memory usage, throughput, and system limits across all major components.

## Test Categories

### 1. Benchmark Tests (`@pytest.mark.benchmark`)

Performance benchmarks measuring execution time and throughput.

#### PRP Generation
- **Single PRP Generation**: Target < 100ms
- **Batch Generation**: Target > 10 PRPs/second
- **Template Rendering**: Target < 10ms
- **Complexity Scaling**: Sub-linear scaling with complexity

#### Context Engineering
- **Context Creation**: Target < 200ms
- **Cache Performance**: Cache hits 100x faster than misses
- **Repository Search**: Target < 50ms for 1000+ examples
- **Context Merging**: Target < 20ms

#### Plugin System
- **Single Plugin Loading**: Target < 500ms
- **Parallel Loading**: Target < 2s for 10 plugins
- **DI Resolution**: Target < 1ms per resolution
- **Plugin Execution**: Target < 10ms

#### Monitoring System
- **Workflow Lookup**: Target < 1ms for 1000 workflows (O(1))
- **Metrics Calculation**: Target < 100ms for 1000 workflows
- **Async Writes**: Target > 1000 writes/second
- **Aggregation**: Target < 500ms for 10k metrics

### 2. Memory Tests (`@pytest.mark.memory`)

Memory profiling and leak detection tests.

- **PRP Generation Memory**: Target < 100MB for 100 PRPs
- **Context Memory**: Target < 50MB per context
- **Memory Leak Detection**: < 10% growth after 1000 operations
- **Large Object Handling**: Efficient management of MB-sized objects

### 3. Load Tests (`@pytest.mark.load`)

System behavior under high load and stress conditions.

- **Concurrent Workflows**: 1000 workflows in < 30 seconds
- **Multi-User Load**: 100 users × 10 operations, < 5% failure rate
- **Stress Testing**: Graceful degradation under extreme load
- **Resource Exhaustion**: Proper handling when resources depleted

### 4. Scalability Tests

Testing linear and parallel scalability.

- **Linear Scalability**: Performance scales linearly with load
- **Parallel Processing**: Near-linear speedup with parallelism
- **Endurance Testing**: Stability over 60+ second runs

## Running Tests

### Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run quick performance tests
python tests/run_performance_tests.py --mode quick

# Run all performance tests
python tests/run_performance_tests.py --mode all
```

### Using pytest directly

```bash
# Run all benchmark tests
pytest tests/test_performance_suite.py --benchmark-only -v

# Run specific benchmark group
pytest tests/test_performance_suite.py --benchmark-only --benchmark-group-by=prp_generation

# Run memory tests
pytest tests/test_performance_suite.py -m memory -v

# Run load tests
pytest tests/test_performance_suite.py -m load -v

# Run specific test
pytest tests/test_performance_suite.py -k test_prp_generation_performance -v
```

### Test Runner Options

```bash
# Run all test suites
python tests/run_performance_tests.py --mode all

# Run quick subset
python tests/run_performance_tests.py --mode quick

# Run only benchmarks
python tests/run_performance_tests.py --mode benchmark

# Run specific groups
python tests/run_performance_tests.py --mode benchmark --groups prp_generation context_engineering

# Run specific tests
python tests/run_performance_tests.py --tests test_prp_generation_performance test_context_cache_performance

# Custom output directory
python tests/run_performance_tests.py --mode all --output-dir results/2025-09-05
```

## Performance Targets

| Component | Operation | Target | Actual |
|-----------|-----------|--------|--------|
| PRP Generator | Single generation | < 100ms | TBD |
| PRP Generator | Batch (100) | > 10/sec | TBD |
| Context Engineer | Creation | < 200ms | TBD |
| Context Engineer | Cache hit | 100x faster | TBD |
| Plugin System | Load single | < 500ms | TBD |
| Plugin System | Load parallel (10) | < 2s | TBD |
| Monitoring | Lookup (1000) | < 1ms | TBD |
| Monitoring | Async writes | > 1000/sec | TBD |
| Memory | 100 PRPs | < 100MB | TBD |
| Memory | Per context | < 50MB | TBD |
| Load | 1000 workflows | < 30s | TBD |
| Load | 100 users | < 5% fail | TBD |

## Test Output

### Benchmark Results

Tests generate detailed benchmark results including:
- Minimum, maximum, mean execution times
- Standard deviation
- Number of rounds and iterations
- JSON output for analysis

### Memory Profiling

Memory tests provide:
- Peak memory usage
- Memory growth over time
- Leak detection results
- Large object handling metrics

### Load Test Metrics

Load tests measure:
- Throughput (operations/second)
- Latency (average, percentiles)
- Error rates under load
- Graceful degradation behavior

## Analyzing Results

### JSON Output

Benchmark results are saved as JSON for analysis:

```python
import json

with open('performance_results/benchmark_20250905_174500.json') as f:
    results = json.load(f)
    
for benchmark in results['benchmarks']:
    print(f"{benchmark['name']}: {benchmark['stats']['mean']:.4f}s")
```

### Performance Trends

Track performance over time:

```bash
# Compare results from different runs
python tests/analyze_performance.py --compare results/run1.json results/run2.json
```

### Bottleneck Analysis

Identify performance bottlenecks:

1. Run full benchmark suite
2. Sort by execution time
3. Focus optimization on slowest operations
4. Re-run to verify improvements

## Best Practices

### When to Run

- **Before commits**: Quick tests
- **Before PRs**: Full benchmark suite
- **After optimization**: Targeted benchmarks
- **Regular CI**: Automated performance regression detection

### Interpreting Results

- **Look for trends**: Consistent slowdowns indicate issues
- **Consider variance**: High stddev suggests unstable performance
- **Check scaling**: Non-linear scaling reveals algorithmic issues
- **Monitor memory**: Growing memory indicates leaks

### Performance Optimization Workflow

1. **Baseline**: Establish current performance metrics
2. **Profile**: Identify bottlenecks with detailed profiling
3. **Optimize**: Apply targeted optimizations
4. **Verify**: Re-run tests to confirm improvements
5. **Document**: Record changes and performance gains

## Continuous Integration

### GitHub Actions Setup

```yaml
name: Performance Tests

on:
  pull_request:
    paths:
      - 'subforge/**'
      - 'tests/**'

jobs:
  performance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run performance tests
        run: python tests/run_performance_tests.py --mode quick
      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: performance-results
          path: performance_results/
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies installed
2. **Timeout Errors**: Increase timeout in pytest.ini
3. **Memory Errors**: Reduce test scale or increase system memory
4. **Async Errors**: Check asyncio compatibility

### Debug Mode

```bash
# Run with debug output
pytest tests/test_performance_suite.py -vvv --tb=long

# Run with profiling
python -m cProfile -o profile.stats tests/test_performance_suite.py
```

## Contributing

When adding new performance tests:

1. Choose appropriate marker (`@pytest.mark.benchmark`, `.memory`, `.load`)
2. Set realistic performance targets
3. Include both typical and edge cases
4. Document expected behavior
5. Add to appropriate test group

## Summary

This performance testing suite provides comprehensive coverage of SubForge's performance characteristics, enabling:

- Early detection of performance regressions
- Validation of optimization efforts
- Capacity planning and scaling decisions
- System behavior under stress conditions
- Memory efficiency verification

Regular performance testing ensures SubForge maintains high performance standards as it evolves.