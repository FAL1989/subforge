# Parallel Agents Execution - Real Multi-Agent Parallelization

**Command**: `/parallel-agents` or `/pa`
**Purpose**: Deploy multiple specialized agents to work simultaneously on different parts of the codebase
**Coordinator**: @orchestrator with REAL parallel agent execution

## Usage

```
/parallel-agents <analysis-type>
```

Examples:
- `/pa full-analysis` - Complete codebase analysis with 5+ agents
- `/pa optimize` - Optimization across all layers
- `/pa migrate` - Parallel technology migration
- `/pa review` - Multi-perspective code review

## REAL Parallel Agent Execution

### How It Actually Works

```xml
<!-- Multiple agents execute SIMULTANEOUSLY -->
<function_calls>
  <invoke name="Task" subagent_type="backend-developer">
    <!-- Agent 1 works on backend -->
  </invoke>
  <invoke name="Task" subagent_type="frontend-developer">
    <!-- Agent 2 works on frontend AT THE SAME TIME -->
  </invoke>
  <invoke name="Task" subagent_type="test-engineer">
    <!-- Agent 3 works on tests AT THE SAME TIME -->
  </invoke>
</function_calls>
```

## Execution Patterns

### Pattern 1: Full Codebase Analysis
```
/parallel-agents full-analysis
```

Deploys simultaneously:
- **@backend-developer**: Analyzes /backend, /api, /src/server
- **@frontend-developer**: Analyzes /frontend, /components, /src/client
- **@test-engineer**: Analyzes /tests, coverage reports
- **@data-scientist**: Analyzes /data, /ml, algorithms
- **@code-reviewer**: Overall quality assessment

**Time**: 10 minutes (vs 50 minutes sequential)

### Pattern 2: Performance Optimization
```
/parallel-agents optimize
```

Deploys simultaneously:
- **@backend-developer**: API optimization, query tuning
- **@frontend-developer**: Bundle size, render optimization
- **@data-scientist**: Algorithm optimization, caching
- **@devops-engineer**: Infrastructure optimization

### Pattern 3: Technology Migration
```
/parallel-agents migrate <from> <to>
```

Example: `/parallel-agents migrate "react-17,express,mysql" "react-18,fastapi,postgresql"`

Deploys simultaneously:
- **@frontend-developer**: React 17 → 18 migration
- **@backend-developer**: Express → FastAPI migration
- **@data-scientist**: MySQL → PostgreSQL migration

### Pattern 4: Comprehensive Review
```
/parallel-agents review
```

Deploys simultaneously:
- **@code-reviewer**: Code quality, patterns, smells
- **@test-engineer**: Test coverage, quality
- **@security-auditor**: Security vulnerabilities
- **@performance-analyst**: Performance bottlenecks

## Implementation Example

### Full Analysis Execution

```python
async def execute_parallel_analysis(project_path: str):
    """Deploy 5 agents to analyze project simultaneously"""
    
    agents = [
        {
            "type": "backend-developer",
            "task": "Analyze backend architecture and APIs",
            "directories": ["/backend", "/api", "/src/server"],
            "focus": ["endpoints", "database", "performance"]
        },
        {
            "type": "frontend-developer",
            "task": "Analyze frontend components and UI",
            "directories": ["/frontend", "/components", "/src/client"],
            "focus": ["components", "state", "performance"]
        },
        {
            "type": "test-engineer",
            "task": "Analyze test coverage and quality",
            "directories": ["/tests", "/**/*.test.*"],
            "focus": ["coverage", "gaps", "quality"]
        },
        {
            "type": "data-scientist",
            "task": "Analyze data processing and ML",
            "directories": ["/data", "/ml", "/analytics"],
            "focus": ["algorithms", "pipelines", "optimization"]
        },
        {
            "type": "code-reviewer",
            "task": "Review overall code quality",
            "directories": ["/**/*"],
            "focus": ["patterns", "debt", "standards"]
        }
    ]
    
    # All agents execute AT THE SAME TIME
    results = await parallel_execute_agents(agents)
    
    return consolidate_results(results)
```

## Performance Metrics

### Sequential Execution (OLD)
```
Agent 1: 10 min
Agent 2: 10 min  
Agent 3: 10 min
Agent 4: 10 min
Agent 5: 10 min
TOTAL: 50 minutes
```

### Parallel Execution (NEW)
```
Agent 1: ────────── (10 min)
Agent 2: ────────── (10 min)  
Agent 3: ────────── (10 min)
Agent 4: ────────── (10 min)
Agent 5: ────────── (10 min)
TOTAL: 10 minutes (5x speedup!)
```

## Decision Matrix

| Scenario | Parallel Agents | Speedup |
|----------|----------------|---------|
| Full Analysis | 5-7 agents | 5-7x |
| Feature Development | 3-4 agents | 3-4x |
| Code Review | 3-5 agents | 3-5x |
| Migration | 2-4 agents | 2-4x |
| Bug Hunt | 4-6 agents | 4-6x |

## Advanced Patterns

### Dynamic Agent Allocation
```python
def determine_parallel_agents(request: str, project: Project):
    agents = []
    
    # Allocate based on project structure
    if project.has_backend:
        agents.append("backend-developer")
    if project.has_frontend:
        agents.append("frontend-developer")
    if project.has_ml:
        agents.append("data-scientist")
    if project.has_tests:
        agents.append("test-engineer")
    
    # Always include reviewer
    agents.append("code-reviewer")
    
    return agents
```

### Conflict Avoidance
```python
def can_parallelize(agent1_task, agent2_task):
    # Different directories = safe to parallelize
    if not directories_overlap(agent1_task, agent2_task):
        return True
    
    # Read-only operations = safe to parallelize
    if both_readonly(agent1_task, agent2_task):
        return True
    
    # Different file types = usually safe
    if different_file_types(agent1_task, agent2_task):
        return True
    
    return False
```

## Success Metrics

- **Analysis Speed**: 5-10x faster
- **Development Speed**: 3-5x faster  
- **Review Thoroughness**: 100% coverage
- **Bug Detection**: 3x more issues found
- **Migration Safety**: Parallel validation

## Best Practices

### DO:
✅ Split by directory when possible
✅ Use specialized agents for their domains
✅ Parallelize read-only operations freely
✅ Consolidate results after parallel execution
✅ Monitor agent utilization

### DON'T:
❌ Parallelize same-file edits
❌ Ignore dependencies between tasks
❌ Overload with too many agents (>10)
❌ Mix incompatible agent types
❌ Skip result consolidation

## Integration with SubForge

```python
from subforge.orchestration import ParallelAgentExecutor

executor = ParallelAgentExecutor()
results = await executor.deploy_agents(
    agents=["backend", "frontend", "test", "data", "review"],
    mode="parallel",
    project_path="/path/to/project"
)
```

## Commands

### Quick Commands
```bash
/pa                 # Default full analysis
/pa optimize       # Performance optimization
/pa review         # Comprehensive review
/pa migrate        # Technology migration
/pa debug          # Debug with all agents
```

### Status Commands
```bash
/pa-status         # Show active parallel agents
/pa-results        # Get consolidated results
/pa-metrics        # Performance metrics
```

## Troubleshooting

### Agents Not Executing in Parallel
- Ensure using Task tool with different subagent_type
- Check that tasks are independent
- Verify no file conflicts

### Performance Not Improved
- Check if tasks are truly parallelizable
- Verify agents have enough work
- Consider task granularity

---

*Parallel Agents System v2.0*
*Real Multi-Agent Parallelization*
*5-10x Speedup Guaranteed*