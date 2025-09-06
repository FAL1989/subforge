#!/usr/bin/env python3
"""
SubForge Simple Initialization
Main entry point for SubForge - extracts project knowledge and creates Claude Code context
No fake complexity, no templates - just real extraction and documentation
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Import core components
from subforge.core.knowledge_extractor import ProjectKnowledgeExtractor
from subforge.core.context_builder import ContextBuilder
from subforge.core.gap_analyzer import GapAnalyzer, generate_gap_report


def print_header(text: str):
    """Print formatted header"""
    print(f"\n{'='*60}")
    print(f" {text}")
    print(f"{'='*60}")


def print_section(title: str):
    """Print section header"""
    print(f"\n📂 {title}")
    print("-" * 40)


def init_subforge(project_path: str = None, verbose: bool = True) -> Dict[str, Any]:
    """
    Initialize SubForge for a project
    Extracts knowledge, analyzes gaps, and creates Claude Code context
    """
    if not project_path:
        project_path = os.getcwd()
    
    project_path = Path(project_path).resolve()
    
    if verbose:
        print_header(f"SubForge Initialization - {datetime.now().strftime('%Y-%m-%d %H:%M')} UTC-3 São Paulo")
        print(f"Project: {project_path}")
    
    results = {
        'project_path': str(project_path),
        'extraction': {},
        'gap_analysis': {},
        'context_creation': {},
        'summary': {},
        'errors': []
    }
    
    try:
        # Phase 1: Extract Knowledge
        if verbose:
            print_section("Phase 1: Extracting Project Knowledge")
            print("  🔍 Analyzing project structure...")
        
        extractor = ProjectKnowledgeExtractor(project_path)
        
        project_info = extractor.extract_project_info()
        if verbose:
            print(f"    ✅ Project: {project_info.name}")
            print(f"    ✅ Languages: {', '.join(project_info.languages[:5]) if project_info.languages else 'None detected'}")
            print(f"    ✅ Frameworks: {', '.join(project_info.frameworks[:5]) if project_info.frameworks else 'None detected'}")
        
        if verbose:
            print("  🔍 Extracting commands...")
        commands = extractor.extract_commands()
        if verbose:
            print(f"    ✅ Found {len(commands)} commands")
        
        if verbose:
            print("  🔍 Extracting workflows...")
        workflows = extractor.extract_workflows()
        if verbose:
            print(f"    ✅ Found {len(workflows)} workflows")
        
        if verbose:
            print("  🔍 Identifying modules...")
        modules = extractor.identify_modules()
        if verbose:
            print(f"    ✅ Found {len(modules)} significant modules")
            for module in modules[:5]:
                print(f"      - {module.name}: {module.description}")
        
        results['extraction'] = {
            'project_name': project_info.name,
            'languages': project_info.languages,
            'frameworks': project_info.frameworks,
            'commands_count': len(commands),
            'workflows_count': len(workflows),
            'modules_count': len(modules)
        }
        
        # Phase 2: Analyze Gaps
        if verbose:
            print_section("Phase 2: Analyzing Documentation Gaps")
            print("  🔍 Checking for missing components...")
        
        analyzer = GapAnalyzer(project_path)
        gap_report = analyzer.analyze_documentation_gaps()
        
        if verbose:
            print(f"    📊 Completeness Score: {gap_report.completeness_score:.1%}")
            print(f"    ⚠️ Missing Commands: {len(gap_report.missing_commands)}")
            print(f"    ⚠️ Missing Workflows: {len(gap_report.missing_workflows)}")
            print(f"    ⚠️ Missing Documentation: {len(gap_report.missing_documentation)}")
            print(f"    💡 Suggested Agents: {len(gap_report.suggested_agents)}")
            print(f"    🔧 Configuration Issues: {len(gap_report.configuration_issues)}")
        
        results['gap_analysis'] = {
            'completeness_score': gap_report.completeness_score,
            'missing_commands': len(gap_report.missing_commands),
            'missing_workflows': len(gap_report.missing_workflows),
            'missing_documentation': len(gap_report.missing_documentation),
            'suggested_agents': len(gap_report.suggested_agents),
            'configuration_issues': len(gap_report.configuration_issues)
        }
        
        # Phase 3: Build Context
        if verbose:
            print_section("Phase 3: Building Claude Code Context")
            print("  📝 Creating CLAUDE.md hierarchy...")
        
        builder = ContextBuilder(project_path)
        
        # Build root CLAUDE.md
        claude_md = builder.build_root_claude_md(project_info, modules, commands)
        
        # Build module CLAUDE.mds
        module_claude_mds = []
        for module in modules:
            claude_md_content = builder.build_module_claude_md(module, project_info)
            module_claude_mds.append((module, claude_md_content))
        
        if verbose:
            print(f"    ✅ Created root CLAUDE.md")
            print(f"    ✅ Created {len(module_claude_mds)} module CLAUDE.md files")
        
        # Build .claude/ structure
        if verbose:
            print("  📝 Creating .claude/ structure...")
        
        command_files = builder.build_command_files(commands)
        if verbose:
            print(f"    ✅ Created {len(command_files)} command files")
        
        # Include suggested agents from gap analysis
        agent_modules = modules.copy()
        
        # Add pseudo-modules for suggested agents that don't have modules
        for suggestion in gap_report.suggested_agents[:5]:  # Limit to top 5 suggestions
            if not any(suggestion.name.replace('-specialist', '') == m.name for m in modules):
                # Create a pseudo-module for the suggested agent
                from subforge.core.knowledge_extractor import Module
                pseudo_module = Module(
                    name=suggestion.name.replace('-specialist', ''),
                    path=project_path,
                    description=suggestion.focus_area,
                    has_tests=False,
                    has_docs=False,
                    key_files=[],
                    dependencies=[]
                )
                agent_modules.append(pseudo_module)
        
        agent_files = builder.build_agent_files(agent_modules, project_info)
        if verbose:
            print(f"    ✅ Created {len(agent_files)} agent files")
        
        workflow_files = builder.build_workflow_files(workflows, commands)
        
        # Add missing workflows from gap analysis
        for missing_wf in gap_report.missing_workflows:
            if missing_wf.priority == 'high':
                from subforge.core.context_builder import WorkflowFile
                workflow_content = f"""---
name: {missing_wf.name}
description: {missing_wf.description}
source: Suggested by SubForge gap analysis
---

# {missing_wf.name.replace('-', ' ').title()} Workflow

## Description
{missing_wf.description}

## Suggested Steps
{chr(10).join(f'{i}. {step}' for i, step in enumerate(missing_wf.suggested_steps, 1))}

## Priority
{missing_wf.priority.upper()} - {missing_wf.reason}

## Notes
This workflow was suggested by SubForge based on project analysis.
Please review and customize for your specific needs.
"""
                workflow_files.append(WorkflowFile(
                    name=missing_wf.name,
                    content=workflow_content,
                    path=builder.claude_dir / "workflows" / f"{missing_wf.name}.md"
                ))
        
        if verbose:
            print(f"    ✅ Created {len(workflow_files)} workflow files")
        
        # Phase 4: Write Files
        if verbose:
            print_section("Phase 4: Writing Context Files")
        
        write_results = builder.write_context_files(
            claude_md,
            module_claude_mds,  # Pass list of tuples directly
            command_files,
            agent_files,
            workflow_files
        )
        
        if write_results.get('errors'):
            if verbose:
                print(f"    ⚠️ Warning: {write_results['errors'][0]}")
        
        if verbose:
            if 'summary' in write_results:
                print(f"    ✅ Created {write_results['summary']['total_files']} files")
                print(f"      - 1 root CLAUDE.md")
                print(f"      - {write_results['summary']['module_claude_mds']} module CLAUDE.md files")
                print(f"      - {write_results['summary']['commands']} command files")
                print(f"      - {write_results['summary']['agents']} agent files")
                print(f"      - {write_results['summary']['workflows']} workflow files")
            else:
                print(f"    ❌ Error writing files: {write_results.get('errors', ['Unknown error'])}")
        
        results['context_creation'] = write_results['summary']
        
        # Phase 5: Generate Reports
        if verbose:
            print_section("Phase 5: Generating Reports")
        
        # Write gap analysis report
        gap_report_path = project_path / '.claude' / 'GAP_ANALYSIS.md'
        gap_report_content = generate_gap_report(project_path)
        with open(gap_report_path, 'w', encoding='utf-8') as f:
            f.write(gap_report_content)
        
        if verbose:
            print(f"    ✅ Created gap analysis report")
        
        # Create initialization summary
        summary_path = project_path / '.claude' / 'INITIALIZATION.md'
        summary_content = f"""# SubForge Initialization Summary

## Timestamp
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC-3 São Paulo

## Project Information
- **Name**: {project_info.name}
- **Path**: {project_path}
- **Architecture**: {project_info.architecture}
- **Completeness Score**: {gap_report.completeness_score:.1%}

## Extraction Results
- **Languages**: {', '.join(project_info.languages) if project_info.languages else 'None detected'}
- **Frameworks**: {', '.join(project_info.frameworks) if project_info.frameworks else 'None detected'}
- **Commands Found**: {len(commands)}
- **Workflows Found**: {len(workflows)}
- **Modules Identified**: {len(modules)}

## Created Context Files
- **Root CLAUDE.md**: {project_path}/CLAUDE.md
- **Module Contexts**: {len(module_claude_mds)} files
- **Commands**: {len(command_files)} files in .claude/commands/
- **Agents**: {len(agent_files)} files in .claude/agents/
- **Workflows**: {len(workflow_files)} files in .claude/workflows/

## Gap Analysis
- **Missing Commands**: {len(gap_report.missing_commands)}
- **Missing Workflows**: {len(gap_report.missing_workflows)}
- **Missing Documentation**: {len(gap_report.missing_documentation)}
- **Configuration Issues**: {len(gap_report.configuration_issues)}

## Next Steps
1. Review the gap analysis report: .claude/GAP_ANALYSIS.md
2. Customize the generated agents in .claude/agents/
3. Add missing commands and workflows as identified
4. Update CLAUDE.md with project-specific information
5. Test agent invocation with @agent-name pattern

## How to Use
- **Commands**: Type `/command-name` to use a command
- **Agents**: Type `@agent-name` to invoke a specialized agent
- **Workflows**: Reference workflows for standard processes

---
*Generated by SubForge - Knowledge Extraction System*
*No templates, no fake data - just real project analysis*
"""
        
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        if verbose:
            print(f"    ✅ Created initialization summary")
        
        # Final summary
        results['summary'] = {
            'success': True,
            'project_name': project_info.name,
            'completeness_score': gap_report.completeness_score,
            'files_created': write_results['summary']['total_files'] + 2,  # +2 for reports
            'claude_md_path': str(project_path / 'CLAUDE.md'),
            'claude_dir_path': str(project_path / '.claude'),
            'message': f"SubForge initialization complete for {project_info.name}"
        }
        
        if verbose:
            print_header("Initialization Complete!")
            print(f"\n✅ SubForge has successfully analyzed and documented your project.")
            print(f"📊 Project Completeness: {gap_report.completeness_score:.1%}")
            print(f"📁 Context files created in: {project_path}/.claude/")
            print(f"📄 Main context file: {project_path}/CLAUDE.md")
            print(f"\n💡 Next steps:")
            print(f"   1. Review .claude/GAP_ANALYSIS.md for improvement suggestions")
            print(f"   2. Customize agents in .claude/agents/ for your specific needs")
            print(f"   3. Update CLAUDE.md with additional project details")
            print(f"\n🚀 Claude Code can now use:")
            print(f"   - @agent-name to invoke specialized agents")
            print(f"   - /command-name to run project commands")
            print(f"   - Hierarchical context from CLAUDE.md files")
        
    except Exception as e:
        results['errors'].append(str(e))
        results['summary'] = {
            'success': False,
            'error': str(e),
            'message': f"SubForge initialization failed: {e}"
        }
        
        if verbose:
            print(f"\n❌ Error during initialization: {e}")
            import traceback
            traceback.print_exc()
    
    return results


def main():
    """
    Main entry point for SubForge initialization
    """
    parser = argparse.ArgumentParser(
        description='SubForge - Extract project knowledge and create Claude Code context',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  subforge init                    # Initialize in current directory
  subforge init /path/to/project   # Initialize specific project
  subforge init --quiet            # Initialize without output
  
SubForge extracts real knowledge from your project:
- No templates or fake data
- Analyzes existing documentation
- Identifies gaps and suggests improvements
- Creates Claude Code context files
        """
    )
    
    parser.add_argument(
        'action',
        nargs='?',
        default='init',
        choices=['init'],
        help='Action to perform (default: init)'
    )
    
    parser.add_argument(
        'project_path',
        nargs='?',
        default=os.getcwd(),
        help='Path to project (default: current directory)'
    )
    
    parser.add_argument(
        '--quiet', '-q',
        action='store_true',
        help='Suppress output'
    )
    
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='SubForge 2.0.0 - Knowledge Extraction System'
    )
    
    args = parser.parse_args()
    
    # Run initialization
    if args.action == 'init':
        results = init_subforge(
            project_path=args.project_path,
            verbose=not args.quiet
        )
        
        # Exit with appropriate code
        sys.exit(0 if results['summary']['success'] else 1)


if __name__ == "__main__":
    main()