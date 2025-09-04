#!/usr/bin/env python3
"""
Git Parallel Processor - Processa mudanças Git em paralelo
Revolucionário: Análise, categorização e commit inteligente
"""

import subprocess
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Tuple
import json
from collections import defaultdict

class GitParallelProcessor:
    """Processa mudanças Git com execução paralela"""
    
    def __init__(self):
        self.changes = self.get_all_changes()
        self.categories = defaultdict(list)
        self.analysis_results = {}
        
    def get_all_changes(self) -> List[str]:
        """Obtém todas as mudanças do git"""
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True
        )
        return [line.strip() for line in result.stdout.splitlines()]
    
    def categorize_changes(self):
        """Categoriza mudanças por tipo e área"""
        for change in self.changes:
            status = change[:2].strip()
            file_path = change[3:]
            
            # Categorizar por tipo
            if status == 'M':
                change_type = 'modified'
            elif status == '??':
                change_type = 'untracked'
            elif status == 'D':
                change_type = 'deleted'
            elif status == 'A':
                change_type = 'added'
            else:
                change_type = 'other'
            
            # Categorizar por área
            if '.claude/' in file_path:
                area = 'agents'
            elif 'test' in file_path.lower():
                area = 'tests'
            elif 'subforge-dashboard/' in file_path:
                area = 'dashboard'
            elif 'subforge/' in file_path:
                area = 'core'
            elif '.md' in file_path:
                area = 'documentation'
            elif '.py' in file_path:
                area = 'python'
            else:
                area = 'misc'
            
            self.categories[area].append({
                'status': status,
                'type': change_type,
                'path': file_path
            })
    
    async def analyze_file_parallel(self, file_info: Dict) -> Dict:
        """Analisa um arquivo em paralelo"""
        file_path = file_info['path']
        
        # Análise assíncrona do arquivo
        analysis = {
            'path': file_path,
            'type': file_info['type'],
            'changes': None
        }
        
        if file_info['type'] == 'modified' and file_path.endswith('.py'):
            # Para arquivos Python modificados, contar mudanças
            try:
                result = subprocess.run(
                    ["git", "diff", "--stat", file_path],
                    capture_output=True,
                    text=True,
                    timeout=1
                )
                if result.stdout:
                    parts = result.stdout.strip().split(',')
                    if len(parts) >= 2:
                        insertions = '0'
                        deletions = '0'
                        for part in parts:
                            if '+' in part:
                                insertions = part.split()[0]
                            elif '-' in part:
                                deletions = part.split()[0]
                        analysis['changes'] = {
                            'insertions': insertions,
                            'deletions': deletions
                        }
            except:
                pass
        
        return analysis
    
    async def process_category_parallel(self, category: str, files: List[Dict]) -> Dict:
        """Processa uma categoria inteira em paralelo"""
        print(f"\n📦 Processando categoria: {category} ({len(files)} arquivos)")
        
        start_time = time.time()
        
        # Processar todos os arquivos da categoria em paralelo
        tasks = [self.analyze_file_parallel(f) for f in files]
        results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Estatísticas da categoria
        stats = {
            'category': category,
            'total_files': len(files),
            'processing_time': elapsed,
            'files_per_second': len(files) / elapsed if elapsed > 0 else 0,
            'modified': sum(1 for f in files if f['type'] == 'modified'),
            'untracked': sum(1 for f in files if f['type'] == 'untracked'),
            'analysis': results
        }
        
        print(f"  ✅ {category}: {len(files)} arquivos em {elapsed:.2f}s ({stats['files_per_second']:.1f} arquivos/s)")
        
        return stats
    
    async def run_parallel_analysis(self):
        """Executa análise paralela de todas as mudanças"""
        print("\n🚀 ANÁLISE PARALELA GIT")
        print("=" * 50)
        print(f"Total de mudanças: {len(self.changes)}")
        
        self.categorize_changes()
        
        print(f"\nCategorias encontradas: {len(self.categories)}")
        for cat, files in self.categories.items():
            print(f"  • {cat}: {len(files)} arquivos")
        
        # Processar TODAS as categorias em PARALELO
        start_time = time.time()
        
        tasks = [
            self.process_category_parallel(cat, files) 
            for cat, files in self.categories.items()
        ]
        
        print("\n⚡ Processando todas as categorias simultaneamente...")
        results = await asyncio.gather(*tasks)
        
        total_time = time.time() - start_time
        
        return {
            'total_files': len(self.changes),
            'categories': len(self.categories),
            'total_time': total_time,
            'results': results,
            'files_per_second': len(self.changes) / total_time if total_time > 0 else 0
        }
    
    def run_serial_analysis(self):
        """Executa análise serial para comparação"""
        print("\n🐌 ANÁLISE SERIAL GIT (para comparação)")
        print("=" * 50)
        
        self.categorize_changes()
        start_time = time.time()
        
        results = []
        for cat, files in self.categories.items():
            print(f"\n📦 Processando categoria: {cat} ({len(files)} arquivos)")
            cat_start = time.time()
            
            for file_info in files:
                # Simular processamento
                if file_info['type'] == 'modified':
                    subprocess.run(
                        ["git", "diff", "--stat", file_info['path']],
                        capture_output=True,
                        timeout=1
                    )
            
            cat_time = time.time() - cat_start
            results.append({
                'category': cat,
                'files': len(files),
                'time': cat_time
            })
            print(f"  ✅ {cat}: {cat_time:.2f}s")
        
        total_time = time.time() - start_time
        return {
            'total_files': len(self.changes),
            'total_time': total_time,
            'files_per_second': len(self.changes) / total_time if total_time > 0 else 0
        }
    
    def generate_smart_commits(self, results: Dict) -> List[Dict]:
        """Gera sugestões de commits inteligentes por categoria"""
        commits = []
        
        commit_messages = {
            'agents': 'feat(agents): Update agent configurations and prompts',
            'tests': 'test: Add comprehensive test coverage',
            'dashboard': 'feat(dashboard): Enhance dashboard functionality',
            'core': 'refactor(core): Improve core SubForge functionality',
            'documentation': 'docs: Update documentation and examples',
            'python': 'refactor: Improve Python code quality',
            'misc': 'chore: Update miscellaneous files'
        }
        
        for cat_result in results['results']:
            category = cat_result['category']
            if category in self.categories:
                files = [f['path'] for f in self.categories[category]]
                commits.append({
                    'category': category,
                    'message': commit_messages.get(category, f'chore({category}): Update {category} files'),
                    'files': files[:10],  # Primeiros 10 para exemplo
                    'total_files': len(files)
                })
        
        return commits

async def main():
    """Demonstração principal"""
    processor = GitParallelProcessor()
    
    print("🎯 GIT PARALLEL PROCESSOR")
    print("=" * 50)
    print(f"Arquivos com mudanças detectados: {len(processor.changes)}")
    
    # 1. Análise Serial (baseline)
    print("\n" + "=" * 50)
    serial_results = processor.run_serial_analysis()
    
    # 2. Análise Paralela
    print("\n" + "=" * 50)
    parallel_results = await processor.run_parallel_analysis()
    
    # 3. Comparação de Performance
    print("\n📊 COMPARAÇÃO DE PERFORMANCE")
    print("=" * 50)
    print(f"⏱️ Serial: {serial_results['total_time']:.2f}s")
    print(f"⚡ Paralelo: {parallel_results['total_time']:.2f}s")
    
    if parallel_results['total_time'] > 0:
        speedup = serial_results['total_time'] / parallel_results['total_time']
        print(f"🚀 Speedup: {speedup:.2f}x mais rápido!")
        print(f"📈 Taxa Serial: {serial_results['files_per_second']:.1f} arquivos/s")
        print(f"📈 Taxa Paralela: {parallel_results['files_per_second']:.1f} arquivos/s")
    
    # 4. Sugestões de Commits Inteligentes
    print("\n💡 SUGESTÕES DE COMMITS INTELIGENTES")
    print("=" * 50)
    commits = processor.generate_smart_commits(parallel_results)
    
    for i, commit in enumerate(commits, 1):
        print(f"\n{i}. {commit['message']}")
        print(f"   📁 {commit['total_files']} arquivos na categoria '{commit['category']}'")
        if commit['files']:
            print(f"   Exemplos: {', '.join(commit['files'][:3])}")
    
    # 5. Salvar resultados
    with open('git_parallel_results.json', 'w') as f:
        json.dump({
            'serial': serial_results,
            'parallel': parallel_results,
            'speedup': speedup if 'speedup' in locals() else None,
            'commits': commits
        }, f, indent=2)
    
    print("\n📄 Resultados salvos em: git_parallel_results.json")
    print("\n✨ ANÁLISE COMPLETA!")
    
    return parallel_results

if __name__ == "__main__":
    asyncio.run(main())