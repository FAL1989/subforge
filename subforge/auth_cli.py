#!/usr/bin/env python3
"""
Authentication Management CLI for SubForge
Provides command-line interface for managing agent tokens and permissions
"""

import asyncio
import click
import json
import yaml
from pathlib import Path
from datetime import timedelta
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax

from subforge.core.authentication import (
    AuthenticationManager,
    Role,
    Permission
)
from subforge.core.communication import CommunicationManager

console = Console()


class AuthCLI:
    """Authentication management CLI"""
    
    def __init__(self, workspace: Path, config_file: Optional[Path] = None):
        self.workspace = Path(workspace)
        self.config = self._load_config(config_file) if config_file else {}
        self.comm_manager = None
        self.auth_manager = None
    
    def _load_config(self, config_file: Path) -> dict:
        """Load configuration from YAML file"""
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return {}
    
    async def initialize(self):
        """Initialize managers"""
        auth_config = self.config.get('authentication', {})
        self.comm_manager = CommunicationManager(
            workspace_dir=self.workspace,
            enable_auth=True,
            auth_config=auth_config
        )
        # Wait for system token
        await asyncio.sleep(0.1)
        self.auth_manager = self.comm_manager.auth_manager
    
    async def create_token(
        self,
        agent_id: str,
        role: str,
        lifetime_hours: Optional[int] = None,
        custom_permissions: Optional[list] = None
    ):
        """Create a new token for an agent"""
        try:
            role_enum = Role[role.upper()]
            permissions = None
            
            if custom_permissions:
                permissions = [Permission[p.upper()] for p in custom_permissions]
            
            token = await self.comm_manager.create_agent_token(
                agent_id=agent_id,
                role=role_enum,
                custom_permissions=permissions,
                lifetime_hours=lifetime_hours
            )
            
            # Display token info
            console.print(Panel.fit(
                f"[green]✓ Token created successfully[/green]\n\n"
                f"[bold]Agent ID:[/bold] {token.agent_id}\n"
                f"[bold]Role:[/bold] {token.role.value}\n"
                f"[bold]Token:[/bold] {token.token}\n"
                f"[bold]Expires:[/bold] {token.expires_at or 'Never'}\n"
                f"[bold]Permissions:[/bold] {', '.join([p.value for p in token.permissions])}"
                + (f"\n[bold]Refresh Token:[/bold] {token.refresh_token}" if token.refresh_token else ""),
                title="New Token Created",
                border_style="green"
            ))
            
            # Save to file if requested
            output_file = self.workspace / "auth" / f"token_{agent_id}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w') as f:
                json.dump({
                    "agent_id": token.agent_id,
                    "token": token.token,
                    "role": token.role.value,
                    "refresh_token": token.refresh_token,
                    "expires_at": token.expires_at.isoformat() if token.expires_at else None
                }, f, indent=2)
            
            console.print(f"\n[dim]Token saved to: {output_file}[/dim]")
            
        except Exception as e:
            console.print(f"[red]✗ Failed to create token: {e}[/red]")
    
    async def list_tokens(self):
        """List all active tokens"""
        if not self.auth_manager:
            console.print("[red]Authentication manager not initialized[/red]")
            return
        
        table = Table(title="Active Tokens", show_header=True, header_style="bold magenta")
        table.add_column("Agent ID", style="cyan", no_wrap=True)
        table.add_column("Role", style="green")
        table.add_column("Permissions", style="yellow")
        table.add_column("Created", style="blue")
        table.add_column("Expires", style="red")
        table.add_column("Usage", style="magenta")
        
        for token in self.auth_manager.token_store.active_tokens.values():
            permissions = ", ".join([p.value for p in token.permissions[:3]])
            if len(token.permissions) > 3:
                permissions += f" (+{len(token.permissions)-3})"
            
            table.add_row(
                token.agent_id,
                token.role.value,
                permissions,
                token.created_at.strftime("%Y-%m-%d %H:%M"),
                token.expires_at.strftime("%Y-%m-%d %H:%M") if token.expires_at else "Never",
                str(token.usage_count)
            )
        
        console.print(table)
    
    async def validate_token(self, token_str: str):
        """Validate a token and show its information"""
        info = await self.comm_manager.validate_token(token_str)
        
        if info:
            console.print(Panel.fit(
                f"[green]✓ Token is valid[/green]\n\n"
                f"[bold]Agent ID:[/bold] {info['agent_id']}\n"
                f"[bold]Role:[/bold] {info['role']}\n"
                f"[bold]Permissions:[/bold] {', '.join(info['permissions'])}\n"
                f"[bold]Usage Count:[/bold] {info['usage_count']}\n"
                f"[bold]Last Used:[/bold] {info['last_used'] or 'Never'}\n"
                f"[bold]Expires:[/bold] {info['expires_at'] or 'Never'}",
                title="Token Validation",
                border_style="green"
            ))
        else:
            console.print(Panel.fit(
                "[red]✗ Token is invalid or expired[/red]",
                title="Token Validation",
                border_style="red"
            ))
    
    async def revoke_token(self, token_str: str):
        """Revoke a token"""
        try:
            await self.comm_manager.revoke_agent_token(token_str)
            console.print("[green]✓ Token revoked successfully[/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to revoke token: {e}[/red]")
    
    async def update_permissions(self, agent_id: str, new_role: str):
        """Update agent permissions"""
        try:
            # Need admin token - use system token
            if not self.comm_manager.system_token:
                console.print("[red]System token not available[/red]")
                return
            
            role_enum = Role[new_role.upper()]
            updated = await self.comm_manager.update_agent_permissions(
                agent_id=agent_id,
                new_role=role_enum,
                admin_token=self.comm_manager.system_token.token
            )
            
            if updated:
                console.print(f"[green]✓ Permissions updated for {agent_id} to {new_role}[/green]")
            else:
                console.print(f"[yellow]⚠ No tokens found for agent {agent_id}[/yellow]")
        except Exception as e:
            console.print(f"[red]✗ Failed to update permissions: {e}[/red]")
    
    async def show_audit_log(self, lines: int = 20):
        """Show recent audit log entries"""
        audit_file = self.workspace / "auth" / "audit" / "security_audit.log"
        if not audit_file.exists():
            console.print("[yellow]No audit log found[/yellow]")
            return
        
        with open(audit_file, 'r') as f:
            log_lines = f.readlines()[-lines:]
        
        console.print(Panel.fit(
            "".join(log_lines),
            title=f"Audit Log (last {lines} entries)",
            border_style="blue"
        ))
    
    async def cleanup_expired(self):
        """Clean up expired tokens"""
        if self.auth_manager:
            await self.auth_manager.token_store.cleanup_expired()
            console.print("[green]✓ Expired tokens cleaned up[/green]")


@click.group()
@click.option('--workspace', '-w', default='.', help='Workspace directory')
@click.option('--config', '-c', type=click.Path(), help='Configuration file')
@click.pass_context
def cli(ctx, workspace, config):
    """SubForge Authentication Management CLI"""
    ctx.ensure_object(dict)
    ctx.obj['workspace'] = Path(workspace)
    ctx.obj['config'] = Path(config) if config else None


@cli.command()
@click.argument('agent_id')
@click.argument('role', type=click.Choice(['admin', 'orchestrator', 'specialist', 'reviewer', 'observer', 'guest'], case_sensitive=False))
@click.option('--lifetime', '-l', type=int, help='Token lifetime in hours')
@click.option('--permissions', '-p', multiple=True, help='Custom permissions')
@click.pass_context
def create(ctx, agent_id, role, lifetime, permissions):
    """Create a new authentication token"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.create_token(agent_id, role, lifetime, list(permissions) if permissions else None)
    
    asyncio.run(run())


@cli.command()
@click.pass_context
def list(ctx):
    """List all active tokens"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.list_tokens()
    
    asyncio.run(run())


@cli.command()
@click.argument('token')
@click.pass_context
def validate(ctx, token):
    """Validate a token"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.validate_token(token)
    
    asyncio.run(run())


@cli.command()
@click.argument('token')
@click.pass_context
def revoke(ctx, token):
    """Revoke a token"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.revoke_token(token)
    
    asyncio.run(run())


@cli.command()
@click.argument('agent_id')
@click.argument('new_role', type=click.Choice(['admin', 'orchestrator', 'specialist', 'reviewer', 'observer', 'guest'], case_sensitive=False))
@click.pass_context
def update(ctx, agent_id, new_role):
    """Update agent permissions"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.update_permissions(agent_id, new_role)
    
    asyncio.run(run())


@cli.command()
@click.option('--lines', '-n', default=20, help='Number of log lines to show')
@click.pass_context
def audit(ctx, lines):
    """Show audit log"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.show_audit_log(lines)
    
    asyncio.run(run())


@cli.command()
@click.pass_context
def cleanup(ctx):
    """Clean up expired tokens"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        await auth_cli.cleanup_expired()
    
    asyncio.run(run())


@cli.command()
@click.pass_context
def status(ctx):
    """Show authentication system status"""
    async def run():
        auth_cli = AuthCLI(ctx.obj['workspace'], ctx.obj['config'])
        await auth_cli.initialize()
        
        status = auth_cli.comm_manager.get_auth_status()
        
        console.print(Panel.fit(
            f"[bold]Authentication System Status[/bold]\n\n"
            f"[bold]Enabled:[/bold] {'✓' if status['enabled'] else '✗'}\n"
            f"[bold]Auth Manager:[/bold] {'✓' if status['has_auth_manager'] else '✗'}\n"
            f"[bold]System Token:[/bold] {'✓' if status['has_system_token'] else '✗'}\n"
            f"[bold]Workspace:[/bold] {status['workspace']}\n"
            f"[bold]Auth Directory:[/bold] {status['auth_directory'] or 'N/A'}",
            title="System Status",
            border_style="cyan"
        ))
        
        # Show token statistics
        if auth_cli.auth_manager:
            total_tokens = len(auth_cli.auth_manager.token_store.active_tokens)
            revoked_tokens = len(auth_cli.auth_manager.token_store.revoked_tokens)
            
            console.print(f"\n[bold]Statistics:[/bold]")
            console.print(f"  Active Tokens: {total_tokens}")
            console.print(f"  Revoked Tokens: {revoked_tokens}")
    
    asyncio.run(run())


@cli.command()
@click.pass_context
def roles(ctx):
    """Show available roles and their permissions"""
    from subforge.core.authentication import ROLE_PERMISSIONS
    
    table = Table(title="Available Roles", show_header=True, header_style="bold magenta")
    table.add_column("Role", style="cyan", no_wrap=True)
    table.add_column("Permissions", style="yellow")
    
    for role, permissions in ROLE_PERMISSIONS.items():
        perm_list = ", ".join([p.value for p in permissions[:5]])
        if len(permissions) > 5:
            perm_list += f" (+{len(permissions)-5} more)"
        table.add_row(role.value, perm_list)
    
    console.print(table)


@cli.command()
@click.pass_context
def example(ctx):
    """Show example usage"""
    example_code = """
# Create a token for an orchestrator agent
python -m subforge.auth_cli create orchestrator_001 orchestrator --lifetime 48

# List all active tokens
python -m subforge.auth_cli list

# Validate a token
python -m subforge.auth_cli validate <token_string>

# Update agent permissions
python -m subforge.auth_cli update backend_dev specialist

# Revoke a token
python -m subforge.auth_cli revoke <token_string>

# Show audit log
python -m subforge.auth_cli audit --lines 50

# Check system status
python -m subforge.auth_cli status

# Clean up expired tokens
python -m subforge.auth_cli cleanup
"""
    
    syntax = Syntax(example_code, "bash", theme="monokai", line_numbers=True)
    console.print(Panel(syntax, title="Example Usage", border_style="green"))


if __name__ == "__main__":
    cli()