#!/usr/bin/env python3
"""
SubForge CLI - Simple Command Line Interface (No external dependencies)
"""

import asyncio
import sys
import json
import argparse
from pathlib import Path

# Import SubForge core modules
try:
    from .core.project_analyzer import ProjectAnalyzer
    from .core.workflow_orchestrator import WorkflowOrchestrator
except ImportError:
    # Handle running from different directories
    sys.path.append(str(Path(__file__).parent))
    from core.project_analyzer import ProjectAnalyzer
    from core.workflow_orchestrator import WorkflowOrchestrator

# ASCII Art Banner
SUBFORGE_BANNER = r"""
 ____        _     _____
/ ___| _   _| |__ |  ___|__  _ __ __ _  ___
\___ \| | | | '_ \| |_ / _ \| '__/ _` |/ _ \
 ___) | |_| | |_) |  _| (_) | | | (_| |  __/
|____/ \__,_|_.__/|_|  \___/|_|  \__, |\___|
                                 |___/

🚀 Forge your perfect Claude Code development team
"""


def print_banner():
    """Print the SubForge banner"""
    print(SUBFORGE_BANNER)


def print_section(title: str, style: str = "="):
    """Print a section header"""
    print(f"\n{style * 60}")
    print(f" {title}")
    print(f"{style * 60}")


async def cmd_init(args):
    """Initialize SubForge for a project"""
    project_path = Path(args.project_path) if args.project_path else Path.cwd()

    if not project_path.exists():
        print(f"❌ Error: Project path does not exist: {project_path}")
        return 1

    print_banner()
    print(f"🚀 Initializing SubForge for: {project_path.name}")
    print(f"   Path: {project_path}")

    user_request = args.request or "Set up development environment with best practices"

    if args.dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made")

        # Just run analysis
        print("\n🔍 Analyzing project...")
        analyzer = ProjectAnalyzer()
        profile = await analyzer.analyze_project(str(project_path))

        display_analysis_results(profile)
        display_recommended_setup(profile)
        return 0

    # Run full workflow
    print(f"\n📝 Request: {user_request}")
    print("\n🔄 Executing SubForge workflow...")

    try:
        orchestrator = WorkflowOrchestrator()
        context = await orchestrator.execute_workflow(user_request, str(project_path))

        display_workflow_results(context)
        return 0

    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


async def cmd_analyze(args):
    """Analyze project structure"""
    project_path = Path(args.project_path) if args.project_path else Path.cwd()

    print("🔍 Analyzing project...")

    try:
        analyzer = ProjectAnalyzer()
        profile = await analyzer.analyze_project(str(project_path))

        if args.json:
            result = json.dumps(profile.to_dict(), indent=2)
            if args.output:
                Path(args.output).write_text(result)
                print(f"✅ Analysis saved to: {args.output}")
            else:
                print(result)
        else:
            display_analysis_results(profile)
            display_recommended_setup(profile)

            if args.output:
                await analyzer.save_analysis(profile, args.output)
                print(f"✅ Analysis saved to: {args.output}")

        return 0

    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


def cmd_status(args):
    """Show SubForge status"""
    project_path = Path(args.project_path) if args.project_path else Path.cwd()

    print(f"📊 SubForge Status for: {project_path.name}")

    subforge_dir = project_path / ".subforge"
    claude_dir = project_path / ".claude"

    if not subforge_dir.exists():
        print("⚠️  No SubForge configuration found. Run 'subforge init' to get started.")
        return 0

    # Find latest workflow
    workflow_dirs = sorted(subforge_dir.glob("subforge_*"), key=lambda x: x.stat().st_mtime, reverse=True)

    if not workflow_dirs:
        print("⚠️  No workflow executions found.")
        return 0

    latest_workflow = workflow_dirs[0]
    context_file = latest_workflow / "workflow_context.json"

    if context_file.exists():
        try:
            with open(context_file) as f:
                context_data = json.load(f)

            print_section("Current Configuration", "-")
            print(f"Workflow ID: {context_data['project_id']}")

            if context_data.get("template_selections", {}).get("selected_templates"):
                templates = context_data["template_selections"]["selected_templates"]
                print(f"Active Subagents: {len(templates)}")
                for template in templates:
                    print(f"  • {template}")

        except Exception as e:
            print(f"❌ Error loading workflow context: {e}")

    # Check Claude Code integration
    if claude_dir.exists():
        print("\n✅ Claude Code integration detected")

        if (claude_dir / "agents").exists():
            agents = list((claude_dir / "agents").glob("*.md"))
            print(f"   📁 agents/ ({len(agents)} files)")
            for agent in agents[:5]:  # Show first 5
                print(f"     🤖 {agent.stem}")
            if len(agents) > 5:
                print(f"     ... and {len(agents) - 5} more")
    else:
        print("\n⚠️  No Claude Code integration found")
        print("   Run 'subforge deploy' to set up Claude Code configuration")

    return 0


def cmd_validate(args):
    """Validate SubForge configuration"""
    project_path = Path(args.project_path) if args.project_path else Path.cwd()

    print("✅ Validating SubForge configuration...")

    issues = []

    # Check SubForge directory
    subforge_dir = project_path / ".subforge"
    if not subforge_dir.exists():
        issues.append("❌ SubForge directory missing")
        print("❌ SubForge directory missing")
        return 1
    else:
        print("✅ SubForge directory found")

    # Check for workflows
    workflow_dirs = list(subforge_dir.glob("subforge_*"))
    if workflow_dirs:
        print(f"✅ {len(workflow_dirs)} workflow executions found")
    else:
        issues.append("❌ No workflow executions found")
        print("❌ No workflow executions found")

    # Check Claude Code integration
    claude_dir = project_path / ".claude"
    if claude_dir.exists():
        print("✅ Claude Code directory found")

        claude_md = claude_dir / "CLAUDE.md"
        if claude_md.exists():
            print("✅ CLAUDE.md configured")
        else:
            issues.append("❌ CLAUDE.md missing")
            print("❌ CLAUDE.md missing")

        agents_dir = claude_dir / "agents"
        if agents_dir.exists():
            agent_count = len(list(agents_dir.glob("*.md")))
            print(f"✅ {agent_count} subagent files found")
        else:
            issues.append("❌ No agents directory")
            print("❌ No agents directory")
    else:
        issues.append("❌ Claude Code directory missing")
        print("❌ Claude Code directory missing")

    # Summary
    if not issues:
        print("\n🎉 All checks passed!")
        return 0
    else:
        print(f"\n⚠️  {len(issues)} issues found:")
        for issue in issues:
            print(f"   {issue}")
        return 1


def cmd_templates(args):
    """List available templates"""
    templates_dir = Path(__file__).parent / "templates"

    print("🎨 Available Subagent Templates")

    if not templates_dir.exists():
        print("❌ Templates directory not found")
        return 1

    template_files = list(templates_dir.glob("*.md"))

    if not template_files:
        print("⚠️  No templates found")
        return 0

    print_section("Templates", "-")

    for template_file in sorted(template_files):
        name = template_file.stem
        description = extract_template_description(template_file)
        print(f"• {name:<20} - {description}")

    print(f"\nFound {len(template_files)} templates")
    return 0


def cmd_version(args):
    """Show version information"""
    print("SubForge v1.0.0-alpha")
    print("🚀 Forge your perfect Claude Code development team")
    print("\nDeveloped with ❤️  for the Claude Code community")
    return 0


def display_analysis_results(profile):
    """Display project analysis results"""
    print_section("📊 Project Analysis")

    print(f"Project Name:     {profile.name}")
    print(f"Architecture:     {profile.architecture_pattern.value.title()}")
    print(f"Complexity:       {profile.complexity.value.title()}")
    print(f"Languages:        {', '.join(profile.technology_stack.languages)}")
    print(f"Frameworks:       {', '.join(profile.technology_stack.frameworks) or 'None detected'}")
    print(f"Databases:        {', '.join(profile.technology_stack.databases) or 'None detected'}")
    print(f"Files:            {profile.file_count:,}")
    print(f"Lines of Code:    {profile.lines_of_code:,}")
    print(f"Team Size Est.:   {profile.team_size_estimate}")


def display_recommended_setup(profile):
    """Display recommended setup"""
    print_section("🎯 Recommended Setup")

    if profile.recommended_subagents:
        print("Recommended Subagents:")
        for template in profile.recommended_subagents:
            print(f"  • {template}")

    if profile.integration_requirements:
        print("\nIntegration Requirements:")
        for req in profile.integration_requirements:
            print(f"  • {req}")


def display_workflow_results(context):
    """Display workflow execution results"""
    print_section("🎉 SubForge Setup Complete!")

    print(f"Project:             {Path(context.project_path).name}")
    print(f"Workflow ID:         {context.project_id}")
    print(f"Generated Subagents: {len(context.template_selections.get('selected_templates', []))}")
    print(f"Configuration:       {context.communication_dir}")

    if context.template_selections.get("selected_templates"):
        print("\n🤖 Generated Subagents:")
        for template in context.template_selections["selected_templates"]:
            print(f"  • {template}")

    print("\n🚀 Next Steps:")
    print("1. Run 'subforge validate' to test your configuration")
    print("2. Use '@<subagent-name>' in Claude Code to invoke subagents")
    print("3. Check 'subforge status' for team overview")
    print("4. Visit your project's '.claude/' directory for generated files")


def extract_template_description(template_file: Path) -> str:
    """Extract description from template file"""
    try:
        content = template_file.read_text()
        lines = content.split('\n')

        # Look for description section
        for i, line in enumerate(lines):
            if line.startswith('## Description'):
                if i + 1 < len(lines):
                    desc = lines[i + 1].strip()
                    # Truncate if too long
                    if len(desc) > 60:
                        desc = desc[:57] + "..."
                    return desc

        return "No description available"

    except Exception:
        return "Error reading template"


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        prog='subforge',
        description='🚀 SubForge - Forge your perfect Claude Code development team'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize SubForge for your project')
    init_parser.add_argument('project_path', nargs='?', help='Path to your project (default: current directory)')
    init_parser.add_argument('--request', '-r', help='What you want to accomplish')
    init_parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    init_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze your project structure')
    analyze_parser.add_argument('project_path', nargs='?', help='Path to your project')
    analyze_parser.add_argument('--output', '-o', help='Save analysis to file')
    analyze_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    analyze_parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show current SubForge status')
    status_parser.add_argument('project_path', nargs='?', help='Path to your project')

    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate your SubForge configuration')
    validate_parser.add_argument('project_path', nargs='?', help='Path to your project')
    validate_parser.add_argument('--fix', action='store_true', help='Automatically fix issues')

    # Templates command
    subparsers.add_parser('templates', help='List available subagent templates')

    # Version command
    subparsers.add_parser('version', help='Show version information')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 0

    # Route to appropriate command
    try:
        if args.command == 'init':
            return asyncio.run(cmd_init(args))
        elif args.command == 'analyze':
            return asyncio.run(cmd_analyze(args))
        elif args.command == 'status':
            return cmd_status(args)
        elif args.command == 'validate':
            return cmd_validate(args)
        elif args.command == 'templates':
            return cmd_templates(args)
        elif args.command == 'version':
            return cmd_version(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1

    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
