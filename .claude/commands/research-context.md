# Research Context - Intelligent Information Gathering

**Command**: `/research-context` or `/rc`
**Purpose**: Conduct comprehensive research across multiple sources for informed development decisions
**Executor**: @orchestrator or direct execution

## Usage

```
/research-context <topic>
```

Examples:
- `/rc OAuth 2.0 best practices 2024`
- `/rc Next.js 14 performance optimization`
- `/rc PostgreSQL vs MongoDB for financial data`
- `/rc WebSocket implementation patterns`

## Research Strategy

### Source Priority Matrix

| Priority | Source | Best For |
|----------|--------|----------|
| 1 | Perplexity | Latest trends, best practices, comparisons |
| 2 | Ref Documentation | Official technical specs, API docs |
| 3 | Context7 | Library-specific documentation |
| 4 | GitHub Search | Real implementations, common issues |
| 5 | Web Search | Additional context, tutorials |

### Research Depth Levels

#### Quick Research (5 min)
```python
sources = ["Perplexity"]
queries = 1-2
depth = "summary"
```

#### Standard Research (15 min)
```python
sources = ["Perplexity", "Ref", "GitHub"]
queries = 3-5
depth = "detailed"
```

#### Deep Research (30+ min)
```python
sources = ["All available"]
queries = 5-10
depth = "comprehensive"
follow_up = True
```

## Research Process

### Phase 1: Query Formulation
Transform user request into optimized search queries:

```python
def formulate_queries(topic):
    base_query = topic
    queries = [
        f"{base_query} best practices 2024",
        f"{base_query} common mistakes",
        f"{base_query} performance optimization",
        f"{base_query} security considerations",
        f"{base_query} vs alternatives"
    ]
    return queries
```

### Phase 2: Parallel Research
Execute searches across multiple sources simultaneously:

```javascript
const researchTasks = [
  perplexity.ask("OAuth 2.0 PKCE flow implementation"),
  ref.search("NextAuth documentation"),
  github.searchCode("oauth implementation nextjs"),
  context7.getLibraryDocs("next-auth")
];

const results = await Promise.all(researchTasks);
```

### Phase 3: Synthesis & Analysis
Consolidate findings into actionable insights:

```markdown
## Research Synthesis

### Key Findings
1. **Best Practice**: [Description]
   - Source: [Link]
   - Confidence: High/Medium/Low

2. **Security Alert**: [Warning]
   - Impact: Critical/High/Medium/Low
   - Mitigation: [Solution]

### Recommended Approach
Based on research, recommend:
- Technology: [Specific library/framework]
- Pattern: [Architecture pattern]
- Implementation: [Step-by-step approach]
```

## Research Templates

### Technology Comparison
```markdown
# Technology Comparison: [A] vs [B]

## Overview
| Aspect | Technology A | Technology B |
|--------|--------------|--------------|
| Performance | [Rating] | [Rating] |
| Learning Curve | [Rating] | [Rating] |
| Community | [Size] | [Size] |
| Maintenance | [Active/Stable] | [Active/Stable] |

## Use Cases
- Choose A when: [Scenarios]
- Choose B when: [Scenarios]

## Recommendation
[Final recommendation with rationale]
```

### Security Research
```markdown
# Security Analysis: [Feature/Technology]

## Threat Model
- Attack Vectors: [List]
- Risk Level: [Critical/High/Medium/Low]
- Impact: [Description]

## Mitigation Strategies
1. [Strategy 1]
2. [Strategy 2]

## Implementation Checklist
- [ ] [Security measure 1]
- [ ] [Security measure 2]
```

### Performance Research
```markdown
# Performance Analysis: [Component/Feature]

## Benchmarks
| Metric | Current | Optimized | Improvement |
|--------|---------|-----------|-------------|
| Load Time | Xms | Yms | Z% |
| Memory | XMB | YMB | Z% |

## Optimization Techniques
1. [Technique 1]: [Impact]
2. [Technique 2]: [Impact]

## Implementation Priority
1. Quick wins (< 1 hour)
2. Medium effort (1-4 hours)
3. Major refactor (> 4 hours)
```

## Output Formats

### Standard Output
Save to: `/workflow-state/research-results.md`

```markdown
# Research Results
**Topic**: [User's topic]
**Date**: [Timestamp]
**Depth**: Quick/Standard/Deep

## Executive Summary
[2-3 sentence summary]

## Key Findings
### Best Practices
- [Practice 1]
- [Practice 2]

### Common Pitfalls
- [Pitfall 1]: [How to avoid]
- [Pitfall 2]: [How to avoid]

### Recommended Libraries
1. [Library]: [Why recommended]
2. [Library]: [Why recommended]

## Implementation Strategy
[Step-by-step approach]

## Code Examples
```language
// Example implementation
```

## References
1. [Source](URL) - [What it covers]
2. [Source](URL) - [What it covers]
```

### Quick Reference Card
Save to: `/workflow-state/quick-reference.md`

```markdown
# Quick Reference: [Topic]

## ⚡ Quick Start
```bash
npm install [package]
```

## 🔧 Basic Setup
```javascript
// Minimal configuration
```

## ⚠️ Important Notes
- [Critical point 1]
- [Critical point 2]

## 📚 Learn More
- [Official Docs](URL)
- [Tutorial](URL)
```

## Research Automation

### Pattern Recognition
Identify and save successful patterns:

```json
{
  "pattern": "authentication_implementation",
  "successful_approach": {
    "technology": "NextAuth.js",
    "database": "PostgreSQL with Prisma",
    "security": "PKCE + CSRF tokens"
  },
  "research_time_saved": "20 minutes",
  "reuse_count": 5
}
```

### Cache Management
Cache research results for efficiency:

```python
cache_key = hash(topic + date)
if cache_exists(cache_key) and age < 7_days:
    return cached_results
else:
    new_results = conduct_research(topic)
    cache_save(cache_key, new_results)
    return new_results
```

## Integration Points

### With Dev Workflow
```python
if complexity == "HIGH":
    research_results = execute("/research-context", topic)
    context["research"] = research_results
    proceed_with_implementation()
```

### With Orchestrator
```python
@orchestrator.before_task_distribution
def enhance_with_research(task):
    if task.requires_research:
        research = get_research_results(task.topic)
        task.context.add(research)
```

## Advanced Features

### Follow-up Research
Automatically identify gaps and research them:

```python
def identify_gaps(initial_research):
    gaps = []
    if "performance" not in initial_research:
        gaps.append("performance implications")
    if "security" not in initial_research:
        gaps.append("security considerations")
    return gaps

gaps = identify_gaps(results)
for gap in gaps:
    additional_research = research(gap)
    results.merge(additional_research)
```

### Cross-Reference Validation
Verify information across multiple sources:

```python
def validate_information(claim, sources):
    confirmations = 0
    for source in sources:
        if source.confirms(claim):
            confirmations += 1
    
    confidence = confirmations / len(sources)
    return {
        "claim": claim,
        "confidence": confidence,
        "sources": confirmations
    }
```

### Trend Analysis
Track technology trends over time:

```python
def analyze_trends(technology):
    historical_data = get_historical_research(technology)
    current_data = research(technology)
    
    trend = {
        "popularity": calculate_trend(historical_data.mentions, current_data.mentions),
        "sentiment": calculate_trend(historical_data.sentiment, current_data.sentiment),
        "adoption": calculate_trend(historical_data.usage, current_data.usage)
    }
    
    return trend
```

## Quality Assurance

### Research Validation Checklist
- [ ] Multiple sources consulted
- [ ] Information is recent (< 6 months)
- [ ] Conflicting information noted
- [ ] Security implications considered
- [ ] Performance impact analyzed
- [ ] Code examples tested
- [ ] References properly cited

### Confidence Scoring
```python
confidence_factors = {
    "official_docs": 1.0,
    "multiple_sources_agree": 0.9,
    "recent_information": 0.8,
    "working_examples": 0.9,
    "community_validated": 0.7
}

final_confidence = calculate_weighted_score(confidence_factors)
```

## Troubleshooting

### Common Issues
1. **Rate limiting**: Implement exponential backoff
2. **Stale information**: Check publication dates
3. **Conflicting advice**: Note all perspectives
4. **Missing information**: Use follow-up queries

### Debug Mode
```bash
/research-context --debug <topic>
```
Shows all queries, sources, and intermediate results

## Success Metrics

- **Coverage**: % of aspects researched
- **Depth**: Average sources per aspect
- **Recency**: Average age of information
- **Confidence**: Average confidence score
- **Speed**: Time to complete research
- **Reuse**: % of cached results used

---

*Intelligent Research Context System v1.0*
*Part of Development Workflow Suite*