# Optimize Agents - SubForge Context Engineering Command

**Command**: `/optimize-agents`  
**Purpose**: Analyze and optimize existing Claude Code agent configurations  
**Approach**: Context Engineering + Continuous Improvement

## Command Description

This command analyzes your current Claude Code setup and applies Context Engineering principles to optimize agent performance, eliminate redundancies, and improve coordination.

## Analysis Framework

### Current State Assessment
1. **Agent Performance Analysis**
   - Review agent activation patterns and usage frequency
   - Identify overlapping responsibilities and conflicts
   - Analyze coordination effectiveness between agents
   - Assess tool usage and permission optimization

2. **Context Quality Evaluation**  
   - Review agent system prompts for project specificity
   - Evaluate context richness and example availability
   - Assess integration with current codebase patterns
   - Check alignment with project evolution

3. **Workflow Effectiveness Review**
   - Analyze development workflow efficiency
   - Identify bottlenecks and coordination issues
   - Review quality gate effectiveness
   - Assess automation and command utility

## Optimization Strategy

### Agent Specialization Enhancement
```markdown
**Current Issues Detected:**
- [ ] Agent role overlap or ambiguity
- [ ] Generic prompts without project context  
- [ ] Inefficient tool assignments
- [ ] Poor coordination protocols

**Optimization Actions:**
- Sharpen agent specializations based on actual usage patterns
- Enrich system prompts with project-specific context and examples
- Optimize tool permissions for security and efficiency
- Improve coordination protocols and handoff procedures
```

### Context Engineering Application
1. **Rich Context Integration**
   - Add project-specific examples to each agent
   - Include relevant patterns and best practices
   - Create validation gates for agent outputs
   - Build comprehensive reference documentation

2. **PRP Enhancement**  
   - Generate Product Requirements Prompts for common tasks
   - Create context-rich prompts for complex operations
   - Establish success criteria and validation checkpoints
   - Build reusable prompt templates

## Optimization Process

### Phase 1: Analysis & Discovery
```bash
# Analyze current configuration
- Review .claude/agents/ directory
- Parse CLAUDE.md configuration  
- Analyze recent Claude Code interaction logs
- Identify usage patterns and pain points
```

### Phase 2: Context Engineering
```bash
# Generate enhanced context
- Create context packages for each agent
- Build project-specific examples library
- Generate validation gates for quality assurance
- Develop coordination protocols
```

### Phase 3: Configuration Enhancement
```bash  
# Apply optimizations
- Update agent system prompts with rich context
- Optimize tool assignments and permissions
- Enhance CLAUDE.md with improved workflows
- Create custom commands and automation
```

### Phase 4: Validation & Testing
```bash
# Comprehensive testing
- Test agent functionality with real scenarios
- Validate coordination and handoff procedures  
- Run quality gates and validation checks
- Generate usage documentation and examples
```

## Specific Optimizations

### Agent Prompt Enhancement
Transform generic prompts into context-rich, project-specific prompts:

**Before (Generic)**:
```markdown
You are a backend developer. Help with server-side development tasks.
```

**After (Context-Engineered)**:
```markdown  
You are a backend developer specializing in this Python/FastAPI microservices project.

**Project Context:**
- Architecture: Microservices with API Gateway pattern
- Tech Stack: Python 3.11, FastAPI, PostgreSQL, Docker
- Team Size: 5 developers
- Complexity: Medium-to-High

**Your Specializations:**
- FastAPI application development with async/await patterns
- Database integration using SQLAlchemy with Alembic migrations
- API design following OpenAPI 3.0 specifications
- Microservice communication patterns and error handling

**Project-Specific Examples:**
[Rich examples of actual code patterns from this project]

**Quality Standards:**  
[Project-specific quality gates and validation criteria]
```

### Tool Optimization
- Remove unused tools to reduce cognitive load
- Add project-specific tools based on actual tech stack
- Optimize permissions for security and efficiency
- Group related tools for better organization

### Coordination Enhancement  
- Define clear handoff protocols between agents
- Create escalation paths for complex issues
- Establish shared context and communication patterns
- Build automated quality gates and validation

## Expected Outcomes

### Performance Improvements
- **Agent Effectiveness**: 40-60% improvement in task completion accuracy
- **Context Relevance**: 80-90% of responses include project-specific guidance
- **Coordination Efficiency**: 50% reduction in agent conflicts and overlaps
- **Development Velocity**: 25-35% faster task completion with better context

### Quality Enhancements
- More accurate and project-specific agent responses
- Reduced need for manual corrections and clarifications
- Better integration with existing codebase patterns
- Improved consistency across development tasks

### Team Benefits
- Faster onboarding for new team members
- Consistent development practices across the team
- Better knowledge retention and sharing
- Reduced cognitive load with optimized agent specializations

## Usage Examples

```bash
# Basic optimization
/optimize-agents

# Focus on specific aspects
/optimize-agents --focus=specialization
/optimize-agents --focus=context  
/optimize-agents --focus=coordination

# Conservative optimization (minimal changes)
/optimize-agents --mode=conservative

# Comprehensive optimization (major improvements)
/optimize-agents --mode=comprehensive
```

## Safety & Rollback

- **Backup Creation**: Automatically backup current configuration before optimization
- **Incremental Changes**: Apply optimizations gradually with validation at each step
- **Rollback Plan**: Easy rollback to previous configuration if needed
- **Testing Environment**: Test optimizations in isolated environment first

---

*Powered by SubForge Context Engineering - Making your agents 10x more effective*