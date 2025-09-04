# Shared Context System - Development Workflow State

**Purpose**: Centralized context sharing between orchestrator and specialized agents
**Location**: `/workflow-state/` and `.claude/context/`

## Architecture

```
workflow-state/                  # Runtime state (git-ignored)
├── current-task.json           # Active workflow state
├── research-results.md         # Latest research findings
├── agent-assignments.json      # Task distribution
├── execution-log.json          # Real-time execution tracking
└── artifacts/                  # Generated artifacts
    ├── schemas/
    ├── specs/
    └── docs/

.claude/context/                 # Persistent patterns (git-tracked)
├── shared-state.md            # This file - documentation
├── patterns.json              # Successful patterns for reuse
├── decisions-log.md           # Historical decisions
└── performance-metrics.json   # Workflow performance data
```

## Shared State Structure

### 1. Current Task State (`current-task.json`)

Real-time workflow state that all agents can read/write:

```json
{
  "workflow_id": "unique-id",
  "request_id": "request-id",
  "timestamp": "ISO-8601",
  "original_request": "user's original request",
  "enhanced_request": "clarified and improved version",
  
  "complexity_analysis": {
    "level": "low|medium|high",
    "score": 0-10,
    "factors": {
      "files_affected": number,
      "external_integrations": number,
      "security_sensitive": boolean,
      "performance_critical": boolean
    }
  },
  
  "research_results": {
    "conducted": boolean,
    "sources_consulted": [],
    "best_practices": [],
    "security_notes": [],
    "performance_tips": [],
    "common_mistakes": []
  },
  
  "task_breakdown": [
    {
      "task_id": "unique-task-id",
      "description": "what to do",
      "assigned_to": "@agent-name",
      "status": "pending|in_progress|completed|blocked",
      "dependencies": ["task-ids"],
      "can_parallel": boolean,
      "started_at": "timestamp",
      "completed_at": "timestamp",
      "output": "path/to/output",
      "notes": "any relevant notes"
    }
  ],
  
  "execution_plan": {
    "parallel_groups": [["task-ids"]],
    "sequential_chain": ["task-ids"]
  },
  
  "current_status": "planning|researching|executing|reviewing|completed",
  
  "shared_decisions": [
    {
      "decision": "what was decided",
      "rationale": "why it was decided",
      "made_by": "@agent-name",
      "timestamp": "when",
      "affects": ["components"]
    }
  ],
  
  "blockers": [
    {
      "task_id": "blocked-task",
      "reason": "why blocked",
      "needs": "what would unblock",
      "reported_by": "@agent-name"
    }
  ],
  
  "artifacts": {
    "type": "path/to/artifact"
  }
}
```

### 2. Research Results (`research-results.md`)

Consolidated research findings in markdown format:

```markdown
# Research Results - [Request Title]
Generated: [Timestamp]
Orchestrator: @orchestrator

## Executive Summary
[Brief overview of findings]

## Best Practices
- Practice 1: [Description]
  - Source: [URL]
  - Relevance: [Why it matters]
  
## Security Considerations
- [Security point 1]
- [Security point 2]

## Performance Optimizations
- [Optimization 1]
- [Optimization 2]

## Common Pitfalls to Avoid
- [Pitfall 1]: [How to avoid]
- [Pitfall 2]: [How to avoid]

## Recommended Approach
[Detailed recommended implementation strategy]

## Code Examples
```language
// Example code
```

## References
1. [Source 1](URL)
2. [Source 2](URL)
```

### 3. Agent Assignments (`agent-assignments.json`)

Dynamic task distribution tracking:

```json
{
  "assignments": {
    "@frontend-developer": {
      "current_task": "task-003",
      "queued_tasks": ["task-005", "task-008"],
      "completed_tasks": ["task-001"],
      "total_time": "45 minutes",
      "status": "active"
    },
    "@backend-developer": {
      "current_task": null,
      "queued_tasks": ["task-004"],
      "completed_tasks": ["task-002"],
      "total_time": "30 minutes",
      "status": "waiting"
    }
  },
  "workload_balance": {
    "method": "round-robin|least-loaded|expertise-based",
    "last_rebalance": "timestamp"
  }
}
```

### 4. Execution Log (`execution-log.json`)

Real-time execution tracking:

```json
{
  "events": [
    {
      "timestamp": "ISO-8601",
      "event_type": "task_started|task_completed|decision_made|blocker_found",
      "agent": "@agent-name",
      "task_id": "task-id",
      "details": {},
      "duration_ms": 1234
    }
  ],
  "performance_metrics": {
    "total_duration_ms": 45678,
    "parallel_efficiency": 0.75,
    "first_attempt_success_rate": 0.9,
    "agent_utilization": {
      "@agent-name": 0.8
    }
  }
}
```

## Access Patterns

### For Orchestrator (Read/Write All)
```python
# Read entire state
state = read_json("/workflow-state/current-task.json")

# Update specific section
state["current_status"] = "executing"
state["task_breakdown"][0]["status"] = "in_progress"
write_json("/workflow-state/current-task.json", state)

# Append to research
append_to_file("/workflow-state/research-results.md", new_findings)
```

### For Specialized Agents (Read All, Write Specific)
```python
# Read context
state = read_json("/workflow-state/current-task.json")
my_task = find_my_task(state["task_breakdown"])

# Update only my task
my_task["status"] = "completed"
my_task["output"] = "/path/to/output"
update_task_in_state(my_task)

# Add decision
add_shared_decision({
  "decision": "Used React Hook Form",
  "rationale": "Best form validation",
  "made_by": "@frontend-developer"
})
```

## Synchronization Rules

### Locking Protocol
To prevent conflicts when multiple agents update state:

1. **Read-Modify-Write** pattern:
```python
state = read_state()
state = modify_state(state)
write_state_if_unchanged(state)  # Atomic operation
```

2. **Section-based updates**:
- Agents only modify their assigned sections
- Orchestrator handles global state changes

3. **Event-driven updates**:
- Agents emit events
- Orchestrator aggregates and updates state

## State Lifecycle

### 1. Initialization
- Orchestrator creates initial state
- Sets workflow_id and request details
- Performs complexity analysis

### 2. Research Phase
- Orchestrator conducts research if needed
- Populates research_results
- Saves research artifacts

### 3. Planning Phase
- Orchestrator creates task_breakdown
- Defines execution_plan
- Assigns agents

### 4. Execution Phase
- Agents read their assignments
- Update task status in real-time
- Add decisions and blockers

### 5. Review Phase
- Orchestrator validates completion
- Runs quality gates
- Aggregates results

### 6. Completion
- Final state archived
- Patterns extracted for learning
- Metrics recorded

## Conflict Resolution

### Write Conflicts
If two agents try to update simultaneously:
1. Last-write-wins for independent fields
2. Merge for arrays (append)
3. Orchestrator resolves complex conflicts

### Task Dependencies
If dependency not met:
1. Agent reports blocker
2. Orchestrator reassigns or waits
3. Automatic retry when unblocked

## Performance Optimization

### State Size Management
- Archive completed workflows
- Compress large artifacts
- Limit history to recent events

### Access Patterns
- Cache frequently read sections
- Batch updates when possible
- Use incremental updates

## Monitoring & Debugging

### Health Checks
```json
{
  "state_health": {
    "last_update": "timestamp",
    "size_bytes": 12345,
    "active_agents": 3,
    "blocked_tasks": 0,
    "state_version": 1
  }
}
```

### Debug Mode
Enable verbose logging:
```json
{
  "debug": true,
  "log_level": "verbose",
  "trace_decisions": true,
  "record_all_events": true
}
```

## Best Practices

### DO:
- ✅ Update state immediately when status changes
- ✅ Add detailed notes for complex decisions
- ✅ Clean up completed task data
- ✅ Use artifacts for large outputs
- ✅ Record blockers immediately

### DON'T:
- ❌ Store large files in state (use artifacts/)
- ❌ Modify other agents' tasks
- ❌ Delete historical decisions
- ❌ Skip status updates
- ❌ Ignore blockers

## Integration with Commands

### `/dw-status`
Reads and displays current state

### `/dw-update`
Manual state update

### `/dw-reset`
Clear current state and start fresh

### `/dw-history`
View historical workflows

## Future Enhancements

1. **State Versioning**: Track all state changes
2. **Distributed Locking**: Prevent concurrent modifications
3. **State Analytics**: Learn from patterns
4. **Auto-Recovery**: Restore from failures
5. **State Compression**: Optimize storage

---

*Shared Context System v1.0*
*Part of Intelligent Development Workflow*