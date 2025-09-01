# Generate PRP - SubForge Context Engineering Command

**Command**: `/generate-prp`  
**Purpose**: Generate comprehensive Product Requirements Prompts for complex development tasks  
**Methodology**: Context Engineering for superior AI execution

## Command Description

This command creates comprehensive Product Requirements Prompts (PRPs) that provide rich context, examples, and validation criteria for complex development tasks. It implements the "Context Engineering > Prompt Engineering" philosophy for optimal AI execution results.

## PRP Generation Framework

### Context Research Process
1. **Codebase Analysis**
   - Search for similar features and implementations
   - Identify reference files and patterns
   - Note existing conventions and architectural decisions
   - Check test patterns and quality standards

2. **External Research**
   - Search for relevant patterns and best practices
   - Review library documentation and examples  
   - Find implementation references and case studies
   - Identify industry standards and conventions

3. **Context Package Creation**
   - Compile relevant examples and code patterns
   - Create architecture-specific guidance
   - Build validation gates and quality criteria
   - Generate success metrics and checkpoints

### PRP Structure

#### Executive Summary
```markdown
**Task**: [Clear, specific task description]
**Context**: [Project and technical context]
**Approach**: [Recommended implementation approach]
**Success Criteria**: [Measurable success indicators]
```

#### Rich Context Section
```markdown
**Project Context:**
- Architecture Pattern: [Specific to your project]
- Technology Stack: [Actual technologies in use]
- Team Structure: [Current team composition]
- Quality Standards: [Project-specific standards]

**Technical Context:**
- Existing Patterns: [How similar features are implemented]
- Architecture Constraints: [What must be maintained]
- Integration Points: [How this connects to existing code]
- Performance Requirements: [Specific performance needs]
```

#### Examples & Patterns
```markdown
**Relevant Examples:**
[2-3 concrete examples from similar implementations]

**Code Patterns:**
[Specific patterns used in this codebase]

**Integration Examples:**
[How to integrate with existing systems]

**Testing Patterns:**
[How similar features are tested]
```

#### Implementation Blueprint
```markdown
**Implementation Steps:**
1. [Specific, actionable step]
2. [With concrete details]
3. [And clear dependencies]

**Key Components:**
- [Component 1]: [Purpose and implementation notes]
- [Component 2]: [Integration requirements]
- [Component 3]: [Testing and validation approach]
```

#### Validation Gates
```markdown
**Executable Validation:**
- [ ] **Syntax Check**: `[specific command to run]`
- [ ] **Integration Test**: `[test command with expected output]`
- [ ] **Performance Validation**: `[performance criteria and measurement]`
- [ ] **Security Review**: `[security validation steps]`

**Quality Gates:**
- [ ] Code follows established patterns
- [ ] Tests cover new functionality  
- [ ] Documentation is updated
- [ ] Integration points are verified
```

## PRP Types & Templates

### Feature Development PRP
For implementing new features with comprehensive context:
```bash
/generate-prp --type=feature --name="user-authentication" 
```

### Bug Fix PRP
For complex bug fixes requiring deep investigation:
```bash
/generate-prp --type=bugfix --issue="performance-degradation-api"
```

### Refactoring PRP  
For architectural changes and code improvements:
```bash
/generate-prp --type=refactor --scope="payment-service-modernization"
```

### Integration PRP
For integrating external services or systems:
```bash
/generate-prp --type=integration --service="stripe-payment-processing"
```

## Context Engineering Process

### Phase 1: Discovery & Research
```markdown
**Codebase Research:**
1. Search for existing similar implementations
2. Identify architectural patterns and conventions
3. Find test patterns and quality standards
4. Document integration points and dependencies

**External Research:**
1. Review official documentation and best practices
2. Find relevant implementation examples and tutorials
3. Research industry standards and security considerations
4. Identify potential challenges and solutions
```

### Phase 2: Context Compilation
```markdown
**Context Assembly:**
1. Create comprehensive project context summary
2. Compile relevant code examples and patterns
3. Build validation gates with executable tests
4. Generate success criteria and quality metrics

**Documentation Integration:**
1. Include relevant documentation URLs and references
2. Add code examples from actual project files
3. Create validation checklist with specific commands
4. Build troubleshooting guide for common issues
```

### Phase 3: PRP Generation & Validation
```markdown  
**PRP Creation:**
1. Generate comprehensive PRP document
2. Include all context, examples, and validation gates
3. Create implementation blueprint with specific steps
4. Add troubleshooting and error handling guidance

**Quality Validation:**
1. Verify all examples are relevant and accurate
2. Test all validation gates and commands
3. Ensure success criteria are measurable
4. Validate implementation steps are actionable
```

## Advanced PRP Features

### Dynamic Context Loading
```markdown
**Smart Context Detection:**
- Automatically detect relevant files and patterns
- Include recent changes and evolution patterns
- Add team-specific conventions and preferences
- Integrate with existing development workflows
```

### Validation Automation
```markdown  
**Executable Validation Gates:**
- Generate testable validation criteria
- Create automated quality checks
- Build performance and security validations
- Include rollback and recovery procedures
```

### Continuous Improvement
```markdown
**Learning from Results:**
- Track PRP effectiveness and success rates
- Identify common issues and improvement opportunities
- Update templates based on real-world outcomes
- Build knowledge base of proven patterns
```

## Usage Examples

### Basic PRP Generation
```bash
# Generate PRP for a new feature
/generate-prp "Implement user notification system with email and SMS support"

# Generate PRP for bug fix
/generate-prp "Fix memory leak in data processing pipeline" --type=bugfix

# Generate PRP for integration
/generate-prp "Integrate Stripe payment processing" --type=integration
```

### Advanced Options
```bash
# Specify context level
/generate-prp "Add caching layer" --context=deep --validation=comprehensive

# Focus on specific aspects  
/generate-prp "Refactor auth service" --focus=security,performance,scalability

# Include specific validation requirements
/generate-prp "API rate limiting" --validate=security,performance,integration
```

## Output & Integration

### Generated Files
```markdown
**PRP Document**: `PRPs/[task-name].md`
- Comprehensive context and implementation guidance
- Executable validation gates and quality criteria
- Success metrics and troubleshooting guide

**Context Package**: `context_library/[task-name]_context.md`  
- Rich context with examples and patterns
- Project-specific guidance and references
- Integration instructions and best practices
```

### Integration with Workflow
```markdown
**Development Process:**
1. Generate PRP for complex tasks
2. Review and refine context and requirements
3. Execute implementation following PRP guidance
4. Run validation gates and quality checks
5. Update PRP based on learnings and outcomes
```

## Success Metrics

- **First-Pass Implementation Success**: > 85% of PRP-guided implementations work correctly on first attempt
- **Context Relevance**: > 90% of generated context is directly applicable to the task
- **Validation Effectiveness**: > 95% of validation gates accurately detect quality issues
- **Time Efficiency**: 60-70% reduction in implementation iteration cycles

---

*Save PRP as: `PRPs/[task-name].md` for optimal organization and reusability*