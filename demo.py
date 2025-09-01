#!/usr/bin/env python3
"""
SubForge Demo - Complete End-to-End Demonstration
Shows all SubForge capabilities in action
"""

import asyncio
from pathlib import Path

from subforge.core.project_analyzer import ProjectAnalyzer
from subforge.core.workflow_orchestrator import WorkflowOrchestrator
from subforge.core.validation_engine import ValidationEngine
from subforge.core.communication import CommunicationChannel, send_analysis_report


def print_section(title: str, emoji: str = "🔥"):
    """Print a demo section header"""
    print(f"\n{emoji} " + "=" * 50)
    print(f" {title}")
    print("=" * 52)


async def main():
    """Complete SubForge demonstration"""

    print(r"""
 ____        _     _____
/ ___| _   _| |__ |  ___|__  _ __ __ _  ___
\___ \| | | | '_ \| |_ / _ \| '__/ _` |/ _ \
 ___) | |_| | |_) |  _| (_) | | | (_| |  __/
|____/ \__,_|_.__/|_|  \___/|_|  \__, |\___|
                                 |___/

🚀 SubForge v1.0-Alpha - Complete Demonstration
""")

    # Demo project path
    demo_path = Path.cwd()

    print_section("1. PROJECT ANALYSIS", "🔍")
    print(f"Analyzing project: {demo_path.name}")

    # Initialize components
    analyzer = ProjectAnalyzer()
    orchestrator = WorkflowOrchestrator()
    validator = ValidationEngine()

    # Run project analysis
    profile = await analyzer.analyze_project(str(demo_path))

    print("\n📊 Analysis Results:")
    print(f"  • Project: {profile.name}")
    print(f"  • Architecture: {profile.architecture_pattern.value}")
    print(f"  • Complexity: {profile.complexity.value}")
    print(f"  • Languages: {', '.join(profile.technology_stack.languages)}")
    print(f"  • Recommended Team: {len(profile.recommended_subagents)} subagents")

    for agent in profile.recommended_subagents:
        print(f"    - {agent}")

    print_section("2. WORKFLOW ORCHESTRATION", "⚡")
    print("Executing complete SubForge workflow...")

    # Run full workflow
    user_request = "Create a comprehensive development environment with modern tooling and best practices"
    context = await orchestrator.execute_workflow(user_request, str(demo_path))

    print("\n🎯 Workflow Results:")
    print(f"  • Workflow ID: {context.project_id}")
    print(f"  • Phases Completed: {len(context.phase_results)}")
    print(f"  • Generated Subagents: {len(context.template_selections.get('selected_templates', []))}")
    print(f"  • Configuration Files: {len(list(context.communication_dir.glob('**/*.md')))}")

    print_section("3. COMMUNICATION SYSTEM", "💬")
    print("Testing markdown-based communication...")

    # Create communication channel
    channel = CommunicationChannel(context.communication_dir / "communication_test")

    # Send analysis report
    message_id = send_analysis_report(
        channel,
        "project-analyzer",
        profile.to_dict()
    )

    # Get messages
    summary = channel.get_channel_summary()

    print("\n📨 Communication Results:")
    print(f"  • Message ID: {message_id}")
    print(f"  • Total Messages: {summary['total_messages']}")
    print(f"  • Message Types: {list(summary['message_types'].keys())}")

    print_section("4. VALIDATION ENGINE", "✅")
    print("Running comprehensive validation...")

    # Prepare validation context
    validation_config = {
        "project_name": profile.name,
        "subagents": context.template_selections.get("selected_templates", [])
    }

    validation_context = {
        "project_id": context.project_id,
        "project_profile": profile.to_dict(),
        "template_selections": context.template_selections,
        "generated_configurations": context.generated_configurations
    }

    # Run validation
    report = validator.validate_configuration(validation_config, validation_context)

    print("\n🎯 Validation Results:")
    print(f"  • Overall Score: {report.overall_score:.1f}%")
    print(f"  • Deployment Ready: {'✅ Yes' if report.deployment_ready else '❌ No'}")
    print(f"  • Total Checks: {report.total_checks}")
    print(f"  • Passed: {report.passed_checks}")
    print(f"  • Warnings: {report.warning_checks}")
    print(f"  • Critical Issues: {report.critical_issues}")

    if report.recommendations:
        print("\n💡 Top Recommendations:")
        for rec in report.recommendations[:3]:
            print(f"  • {rec}")

    # Test deployment
    success, message = validator.create_test_deployment(validation_config, validation_context)
    print(f"\n🧪 Test Deployment: {'✅ Success' if success else '❌ Failed'}")
    print(f"  • {message}")

    print_section("5. GENERATED ARTIFACTS", "📁")
    print("Exploring generated configuration files...")

    # List generated files
    total_files = 0
    for file_type in ["*.md", "*.json", "*.yaml"]:
        files = list(context.communication_dir.glob(f"**/{file_type}"))
        if files:
            print(f"\n📄 {file_type.replace('*', '').upper()} Files ({len(files)}):")
            for file_path in files[:5]:  # Show first 5
                relative_path = file_path.relative_to(context.communication_dir)
                size = file_path.stat().st_size
                print(f"  • {relative_path} ({size:,} bytes)")
            if len(files) > 5:
                print(f"  • ... and {len(files) - 5} more")
            total_files += len(files)

    print(f"\n📊 Total Generated Files: {total_files}")

    print_section("6. PERFORMANCE METRICS", "⚡")

    # Calculate performance metrics
    total_duration = sum(result.duration for result in context.phase_results.values())

    print("Performance Summary:")
    print(f"  • Total Execution Time: {total_duration:.2f} seconds")
    print(f"  • Files Analyzed: {profile.file_count:,}")
    print(f"  • Lines Processed: {profile.lines_of_code:,}")
    print(f"  • Configuration Files Generated: {total_files}")
    print(f"  • Validation Checks: {report.total_checks}")

    if total_duration > 0:
        files_per_sec = profile.file_count / total_duration
        lines_per_sec = profile.lines_of_code / total_duration
        print(f"  • Processing Speed: {files_per_sec:.1f} files/sec, {lines_per_sec:,.0f} lines/sec")

    print_section("7. DEMO COMPLETE! 🎉", "🚀")

    print(f"""
✨ SubForge v1.0-Alpha Demonstration Complete!

🎯 What We Just Did:
  • Analyzed a real codebase ({profile.file_count:,} files, {profile.lines_of_code:,} lines)
  • Orchestrated a 7-phase workflow with parallel processing
  • Generated {len(context.template_selections.get('selected_templates', []))} specialized subagent configurations
  • Created {total_files} configuration files with markdown communication
  • Ran {report.total_checks} comprehensive validation checks
  • Achieved {report.overall_score:.1f}% quality score with deployment readiness
  • Completed everything in {total_duration:.2f} seconds

🚀 SubForge is now ready for:
  • Beta testing with real projects
  • Community template contributions
  • GitHub repository publication
  • Claude Code marketplace integration

Configuration saved in: {context.communication_dir}
    """)


if __name__ == "__main__":
    asyncio.run(main())
