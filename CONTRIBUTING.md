# Contributing to SubForge

Thank you for your interest in contributing to SubForge! 🎉 We're excited to have you join our community of developers building the future of AI-powered development.

## 🤝 **Ways to Contribute**

### 1. 🐛 **Bug Reports**
- Found a bug? [Open an issue](https://github.com/subforge/subforge/issues/new?template=bug_report.md)
- Include detailed steps to reproduce
- Provide system information (OS, Python version, etc.)
- Share relevant error messages and logs

### 2. 💡 **Feature Requests**
- Have an idea? [Start a discussion](https://github.com/subforge/subforge/discussions/new)
- Describe the problem you're trying to solve
- Explain why this feature would be valuable
- Consider implementation approaches

### 3. 🎨 **Template Contributions**
Templates are the heart of SubForge! We welcome new subagent templates for:
- Specific frameworks (Svelte, Flutter, etc.)
- Industry domains (fintech, healthcare, gaming)
- Specialized roles (data-scientist, ml-engineer, etc.)
- Enterprise patterns (architect, tech-lead, etc.)

### 4. 💻 **Code Contributions**
- Core engine improvements
- CLI enhancements  
- Validation system extensions
- Performance optimizations
- Test coverage improvements

### 5. 📖 **Documentation**
- Improve existing documentation
- Add tutorials and examples
- Create video walkthroughs
- Translate to other languages

## 🚀 **Getting Started**

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/YOUR_USERNAME/subforge.git
   cd subforge
   ```

2. **Test the installation**
   ```bash
   # Run the demo
   python3 demo.py
   
   # Test CLI commands
   python3 subforge/simple_cli.py --help
   python3 subforge/simple_cli.py analyze --json
   ```

3. **Explore the codebase**
   ```
   subforge/
   ├── core/                    # Core engine components
   │   ├── project_analyzer.py  # Project analysis engine
   │   ├── workflow_orchestrator.py # Workflow coordination
   │   ├── communication.py     # Inter-agent communication
   │   └── validation_engine.py # Quality validation
   ├── templates/              # Subagent templates
   ├── simple_cli.py          # Command-line interface
   └── __init__.py
   ```

### Running Tests
```bash
# Core functionality tests
python3 subforge/core/project_analyzer.py .
python3 subforge/core/validation_engine.py test_validation.json

# CLI tests
python3 subforge/simple_cli.py templates
python3 subforge/simple_cli.py analyze --dry-run
```

## 🎨 **Creating Templates**

Templates are markdown files that define subagent behavior. Here's how to create one:

### 1. **Template Structure**
```markdown
# Your Agent Name

## Description
Brief description of what this agent does.
**AUTO-TRIGGERS**: When this agent activates automatically
**USE EXPLICITLY FOR**: When to manually invoke this agent

## System Prompt
Detailed instructions for the agent's behavior, expertise, and approach.

### Core Expertise:
- Bullet points of key skills
- Technologies and frameworks
- Best practices and patterns

### Approach:
- How the agent works
- Methodology and processes
- Quality standards

## Tools
- read
- write
- edit
- bash

## Activation Patterns
**Automatic activation for:**
- Files: `*.ext`, directories, keywords
- Conditions when agent should auto-activate

**Manual activation with:**
- `@agent-name` - Direct consultation
- `/custom-command` - Specific workflows
```

### 2. **Template Guidelines**

**Do:**
- ✅ Focus on a specific domain or role
- ✅ Include detailed system prompts with examples
- ✅ Specify appropriate tool permissions
- ✅ Define clear activation patterns
- ✅ Follow existing template structure
- ✅ Test with real projects

**Don't:**
- ❌ Create overly broad or generic agents
- ❌ Give excessive tool permissions
- ✅ Duplicate existing templates
- ❌ Include sensitive information
- ❌ Use copyrighted content

### 3. **Template Testing**
```bash
# Test your template
python3 subforge/simple_cli.py templates

# Test with a project
python3 subforge/simple_cli.py analyze some-project --dry-run
```

## 💻 **Code Contribution Guidelines**

### Code Style
- Follow existing code patterns and naming conventions
- Use type hints where possible
- Add docstrings for public functions
- Keep functions focused and single-purpose

### Testing
- Test your changes with multiple project types
- Ensure CLI commands work correctly
- Run the demo to verify end-to-end functionality
- Add unit tests for new functionality

### Performance
- SubForge should remain fast (<10 minutes total execution)
- Optimize for large codebases (100k+ lines)
- Consider memory usage and parallel execution
- Profile performance-critical code paths

## 📝 **Pull Request Process**

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Keep commits focused and atomic
   - Write clear commit messages
   - Test thoroughly

3. **Submit the PR**
   - Fill out the PR template
   - Link related issues
   - Describe changes and motivation
   - Include testing steps

4. **Code Review**
   - Address reviewer feedback
   - Keep discussions constructive
   - Be patient and responsive

5. **Merge**
   - Maintainers will merge approved PRs
   - Your contribution will be credited

## 🏷️ **Commit Message Guidelines**

Use conventional commit format:
```
type(scope): description

feat: add mobile-developer template
fix: resolve project analyzer crash on empty directories  
docs: improve template creation guide
perf: optimize project analysis for large codebases
test: add validation engine unit tests
```

## 🐛 **Reporting Issues**

When reporting bugs, include:

1. **Environment Information**
   - OS and version
   - Python version
   - SubForge version/commit

2. **Steps to Reproduce**
   - Exact commands run
   - Project characteristics
   - Expected vs actual behavior

3. **Logs and Output**
   - Error messages
   - Relevant log files
   - Screenshots if applicable

## 💬 **Community Guidelines**

- Be respectful and inclusive
- Help newcomers get started
- Share knowledge and learnings
- Give constructive feedback
- Celebrate contributions

## 🎯 **Priority Areas**

We especially welcome contributions in:

1. **Templates** for popular frameworks and domains
2. **Performance optimizations** for large codebases
3. **Integration** with other developer tools
4. **Documentation** and tutorials
5. **Test coverage** improvements

## 🙋 **Getting Help**

- 💬 [GitHub Discussions](https://github.com/subforge/subforge/discussions) - Ask questions
- 🐛 [Issues](https://github.com/subforge/subforge/issues) - Report bugs  
- 📖 [Documentation](README.md) - Read the docs
- 🎬 [Demo](demo.py) - See SubForge in action

## 📜 **Code of Conduct**

By participating in this project, you agree to:
- Treat all community members with respect
- Focus on constructive collaboration
- Welcome newcomers and different perspectives  
- Help create a positive environment for everyone

---

**Thank you for contributing to SubForge!** 🚀⚒️

Your contributions help make AI-powered development accessible to developers worldwide. Every bug fix, feature addition, and template contribution makes a difference.

**Happy coding!** ✨