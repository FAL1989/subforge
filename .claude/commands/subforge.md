# SubForge - Intelligent Agent Generation

**Command**: `/subforge`  
**Purpose**: Execute SubForge workflow to generate intelligent Claude Code agents

## Usage

Simply run:
```
/subforge <user_request>
```

Examples:
- `/subforge Create web dashboard with FastAPI and Next.js`
- `/subforge Set up microservices architecture`  
- `/subforge Add testing and deployment pipeline`

## Implementation

When this command is invoked, execute:

```python
import asyncio
from subforge.core.workflow_orchestrator import WorkflowOrchestrator

async def run_subforge(user_request):
    orchestrator = WorkflowOrchestrator()
    result = await orchestrator.execute_workflow(user_request, ".")
    
    agents_deployed = result.deployment_plan.get("agents_deployed", [])
    print(f"🎉 SubForge complete! Generated {len(agents_deployed)} agents:")
    for agent in agents_deployed:
        print(f"   • @{agent}")
    
    return result

# Execute
result = asyncio.run(run_subforge(user_request))
```

## What It Does

1. **Analyzes** your project structure and technology stack
2. **Creates** specialized agents dynamically based on project needs  
3. **Deploys** agents to `.claude/agents/` with Context Engineering
4. **Generates** project-specific `CLAUDE.md` configuration
5. **Applies** intelligent tool assignments and model selection

---
*SubForge: AI-Powered Development Team Orchestration*