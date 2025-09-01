# 📚 Documentação Completa do Claude Code

## 📋 Índice

1. [Visão Geral do Claude Code](#visão-geral)
2. [Sistema de Subagents](#sistema-de-subagents)
3. [Arquivos CLAUDE.md](#arquivos-claudemd)
4. [Slash Commands e Workflows](#slash-commands-e-workflows)
5. [Patterns Avançados](#patterns-avançados)
6. [Integrações e Ferramentas](#integrações-e-ferramentas)
7. [Boas Práticas](#boas-práticas)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral do Claude Code

### O que é Claude Code
Claude Code é um assistente de codificação agnóstico da Anthropic, projetado para acelerar o desenvolvimento de software através da compreensão profunda, edição e gerenciamento de codebases inteiras diretamente do terminal ou IDE.

### Principais Capacidades

#### 🧠 Consciência Profunda da Codebase
- **Mapeamento Rápido**: Mapeia, pesquisa e explica codebases inteiras em segundos
- **Compreensão Estrutural**: Entende estrutura do projeto, dependências e relações entre arquivos
- **Análise de Projetos Desconhecidos**: Capacidade de analisar projetos grandes e desconhecidos rapidamente

#### 🤖 Edição e Planejamento Agnóstico
- **Planejamento Autônomo**: Planeja trabalho usando listas de ToDo dinâmicas
- **Execução Recursiva**: Executa subtarefas automaticamente (criar arquivos, atualizar imports, executar testes)
- **Coordenação Multi-arquivo**: Faz mudanças coordenadas em múltiplos arquivos
- **Migração Arquitetural**: Pode migrar padrões arquiteturais através de projetos

#### 🔧 Interação Direta com Ambiente
- **Terminal Nativo**: Funciona nativamente no terminal, eliminando context-switching
- **Execução de Comandos**: Executa comandos, interage com ferramentas de build/teste
- **Controle de Versão**: Gerencia git sem sair do shell
- **Aprovação Explícita**: Nunca modifica arquivos sem aprovação explícita do usuário

#### 🎨 Prototipagem Autônoma
- **Protótipos End-to-End**: Pode prototipar features ou fixes completos
- **Design para Código**: Gera código a partir de designs Figma ou requisitos abstratos
- **Loops Iterativos**: Estabelece loops iterativos para validar ideias rapidamente

#### 🐛 Debug com IA
- **Análise de Logs**: Analisa logs, stack traces e screenshots
- **Diagnóstico de Causa Raiz**: Identifica causas raiz e propõe fixes guiados
- **Sistemas Desconhecidos**: Efetivo mesmo com sistemas não familiares

---

## 🤝 Sistema de Subagents

### Arquitetura Completa

#### 🏗️ Conceitos Fundamentais
- **Isolamento**: Cada subagent opera em sua própria janela de contexto
- **Especialização**: Cada agent é especializado em um domínio específico
- **Orquestração**: Tasks podem ser atribuídos manual ou automaticamente
- **Segurança**: Cada agent recebe permissões de ferramentas explícitas
- **Versionamento**: Definições de subagents são versionadas e portáveis

#### 📁 Estrutura de Arquivos
```
.claude/agents/
├── backend-developer.md
├── frontend-developer.md
├── devops-engineer.md
├── security-auditor.md
├── code-reviewer.md
└── database-architect.md
```

#### 🎯 Definição de Subagent
```markdown
---
name: backend-developer
description: Especialista em desenvolvimento backend
model: opus
tools: 
  - shell
  - read
  - write
  - grep
---

# System Prompt
Você é um desenvolvedor backend sênior especializado em...

## Expertise Areas
- APIs REST e GraphQL
- Bancos de dados SQL e NoSQL
- Arquitetura de microserviços
- Performance e escalabilidade

## Activation Patterns
- Palavras-chave: api, backend, database, server
- Padrões de arquivo: **/*api*/**/**, **/*backend*/**
- Linguagens: python, javascript, java, go
```

### Criação e Configuração

#### 🔧 Métodos de Criação
1. **Via CLI**: Use a interface do Claude Code para criar novos agents
2. **Manual**: Crie arquivos Markdown na estrutura apropriada
3. **Templates**: Use templates pré-definidos e customize

#### ⚙️ Opções de Configuração
- **name**: Identificador único do subagent
- **description**: Descrição clara do propósito e capacidades
- **model**: Modelo Claude a usar (haiku, sonnet, opus)
- **tools**: Lista de ferramentas permitidas
- **system_prompt**: Prompt detalhado com expertise e comportamento

#### 🎭 Permissões de Ferramentas
```yaml
tools:
  - bash          # Execução de comandos
  - read          # Leitura de arquivos
  - write         # Escrita de arquivos
  - edit          # Edição de arquivos
  - grep          # Busca em arquivos
  - glob          # Pattern matching
  - database      # Acesso a banco de dados
  - api           # Chamadas de API
```

### Patterns de Orquestração Avançados

#### 🔄 Execução Sequencial
```
spec-analyst → architect → planner → developer → tester → reviewer
```

#### ⚡ Execução Paralela
```
├── frontend-developer (UI components)
├── backend-developer (API endpoints)  
├── database-architect (schema design)
└── security-auditor (security review)
```

#### 🎯 Slash Commands Multi-Agent
```bash
/full-stack-feature "Build user dashboard"
# Invoca: UI designer + API developer + database architect + tester
```

#### 🚪 Quality Gates
- Validação de saída antes de passar para o próximo agent
- Enforcement de consistência e correção
- Checkpoints de qualidade em workflows multi-stage

### Coordenação Multi-Agent

#### 📄 Troca de Artefatos
- Agents se comunicam via documentos estruturados
- Não há troca direta de mensagens
- Orquestrador central gerencia distribuição de tarefas

#### 🎛️ Orquestrador Central
- **Distribuição de Tarefas**: Atribui trabalho aos agents apropriados
- **Monitoramento de Progresso**: Acompanha status dos workflows
- **Tratamento de Erros**: Gerencia falhas e recovery
- **Síntese Final**: Integra outputs de múltiplos agents

### Casos de Uso Reais

#### 🌐 Entrega de Feature Full-Stack
```
1. Product Manager Agent → Especifica requisitos
2. UI Designer Agent → Cria mockups e componentes
3. API Developer Agent → Implementa endpoints
4. Database Architect → Projeta schema
5. Security Auditor → Revisa segurança
6. Test Engineer → Cria testes automatizados
7. DevOps Engineer → Configura deployment
8. Code Reviewer → Valida qualidade final
```

#### 🚨 Resposta a Incidentes
```
Parallel Execution:
├── Network Specialist → Diagnóstico de rede
├── Database Expert → Análise de performance DB
├── Security Analyst → Verificação de segurança
└── System Monitor → Coleta de métricas
```

#### 🤖 ML Pipeline
```
1. Data Engineer → Preparação de dados
2. ML Engineer → Treinamento de modelos
3. Model Validator → Avaliação de performance
4. MLOps Engineer → Deploy e monitoring
```

### Otimização de Performance

#### 🎯 Atribuição Inteligente de Modelos
- **Haiku**: Tasks rotineiras e rápidas
- **Sonnet**: Análises de complexidade média
- **Opus**: Análises críticas e complexas

#### 📊 Gerenciamento de Contexto
- Manter prompts focados para minimizar overhead
- Limitar janelas de contexto por agent
- Usar contexto compartilhado apenas quando necessário

#### ⚡ Concorrência
- Explorar execução paralela sempre que possível
- Identificar dependências críticas no path
- Balancear carga entre agents disponíveis

### Tratamento de Erros e Debug

#### 🚪 Quality Gates
- Estágios de validação em pontos-chave do workflow
- Captura e correção de erros precocemente
- Validação de output antes de deployment

#### 📝 Logging Explícito
- Cada subagent mantém histórico de ações
- Artifacts logs para diagnosis e auditoria
- Rastreabilidade completa de decisões

#### 🏠 Isolamento para Tolerância a Falhas
- Erros contidos dentro de contextos individuais
- Falhas não poluem sessão principal ou outros agents
- Recovery granular por agent

#### 🔍 Debug Manual
- Desenvolvedores podem editar prompts/configs de agents
- Re-execução facilitada de workflows falhados
- Inspeção interativa de logs via CLI

---

## 📄 Arquivos CLAUDE.md

### Estrutura e Sintaxe Completa

#### 📋 Formato Básico
- **Formato**: Markdown regular (.md)
- **Sintaxe**: Nenhuma sintaxe especial necessária além de organização clara
- **Parsing**: Claude analisa documentação estruturada legível por humanos

#### 🏗️ Seções Recomendadas
```markdown
# Comandos Build/CLI
- npm run build: Constrói a aplicação
- npm test: Executa testes
- npm run dev: Servidor de desenvolvimento

# Estilo de Código
- Use Prettier com indent de 2 espaços  
- Prefira async/await para operações assíncronas
- ESLint configuration em .eslintrc

# Workflow de Desenvolvimento
- Sempre criar branch a partir da main
- PRs devem ter pelo menos 1 review
- Testes obrigatórios para novas features

# Arquivos Principais
- src/index.js: Entry point da aplicação
- src/components/: Componentes React reutilizáveis  
- src/utils/: Utilitários e helpers

# Avisos Especiais
- NÃO usar jQuery - projeto usa React puro
- Evitar mutação direta de state
- Sempre validar props com PropTypes

# Setup de Desenvolvimento
- Node.js >= 18
- Usar npm (não yarn)
- Variáveis de ambiente em .env.local
```

### Organização Hierárquica

#### 📊 Hierarquia de Precedência
```
1. ~/.claude/CLAUDE.md          # Preferências globais do usuário
2. ~/projects/CLAUDE.md         # Normas da organização/time
3. ~/repo/CLAUDE.md             # Convenções específicas do projeto
4. ~/repo/frontend/CLAUDE.md    # Especificidades do frontend
5. ~/repo/backend/CLAUDE.md     # Especificidades do backend
```

**Regra de Precedência**: O arquivo mais específico (mais profundo) tem prioridade, mas contexto mais amplo é sempre mesclado.

#### 🏢 Exemplos por Tipo de Projeto

##### Monorepo
```
/CLAUDE.md                    # Regras cross-cutting
/frontend/CLAUDE.md          # Específico do frontend
/backend/CLAUDE.md           # Específico do backend
/shared/CLAUDE.md            # Bibliotecas compartilhadas
/docs/CLAUDE.md              # Diretrizes de documentação
```

##### Microserviços
```
/CLAUDE.md                   # Overview e convenções gerais
/user-service/CLAUDE.md      # Específico do serviço de usuários
/payment-service/CLAUDE.md   # Específico do serviço de pagamento
/gateway/CLAUDE.md           # Específico do API gateway
```

### Best Practices por Tipo de Projeto

#### 🌐 Aplicação Web (React/Node)
```markdown
# Comandos
- npm run build: Build frontend
- npm run start: Start servidor
- npm run test: Executa testes Jest

# Estilo de Código
- ES6+ (import/export)
- Componentes funcionais React
- Hooks ao invés de classes
- TypeScript obrigatório

# Workflow  
- Branches: feature/{short-desc}
- PRs requerem referência de issue
- CI/CD via GitHub Actions

# Testing
- Jest para unit tests
- Testing Library para componentes
- Cypress para E2E
```

#### 🐍 Biblioteca Python
```markdown
# Comandos
- pytest: Executa testes
- make lint: Executa flake8
- python -m build: Gera distribuição

# Estilo de Código
- Seguir PEP8 rigorosamente
- Type annotations obrigatórias
- Docstrings em todos os métodos públicos
- Black formatter

# Workflow
- Branch naming: username/feature_description  
- Merge com squash commits
- Pre-commit hooks configurados

# Setup
- Python 3.9+
- Poetry para dependency management
- Virtual environment obrigatório
```

#### ☕ Aplicação Java Enterprise
```markdown
# Comandos
- mvn clean compile: Compila projeto
- mvn test: Executa testes unitários
- mvn spring-boot:run: Inicia aplicação

# Estilo de Código
- Google Java Style Guide
- Lombok para reduzir boilerplate
- SonarQube quality gates

# Arquitetura
- Spring Boot + Spring Data JPA
- Hexagonal architecture
- Clean code principles

# Database
- PostgreSQL para produção
- H2 para testes
- Flyway para migrations
```

### Opções de Configuração Avançadas

#### 🎯 Override de Precedência
- Use CLAUDE.md específicos por diretório para refinar/sobrescrever defaults
- Personalização através de arquivos em nível de usuário
- Context exclusion para marcar detalhes raramente relevantes

#### 🔧 Integração com Ferramentas
```markdown
# Integração com Ferramentas
- ESLint config: .eslintrc.json
- Prettier config: .prettierrc
- TypeScript config: tsconfig.json
- Jest config: jest.config.js

# Deployment
- Docker: Dockerfile na raiz
- Kubernetes: manifests em /k8s
- CI/CD: .github/workflows/

# Monitoramento
- Logs estruturados com Winston
- Métricas com Prometheus
- Health checks em /health
```

#### 🎪 Task Specifications
- Place task-oriented MD files (e.g., `specs/add-feature-x.md`) para controle de alta precisão
- Documentar especificações de features específicas
- Instruções detalhadas para implementações complexas

### Integração com Subagents

#### 🤖 Documentando Subagents
```markdown
# Subagents Disponíveis

## Backend Developer
- **Responsabilidade**: APIs, database, server logic
- **Invocação**: Automática para arquivos em /src/api, /src/models
- **Tools**: shell, database, API testing

## Frontend Developer  
- **Responsabilidade**: UI components, styling, state management
- **Invocação**: Automática para arquivos .jsx, .tsx, /src/components
- **Tools**: browser tools, bundler, testing

## Security Auditor
- **Responsabilidade**: Análise de segurança, vulnerabilidades
- **Invocação**: Manual via /security-audit ou automática em deploys
- **Tools**: security scanners, penetration testing tools

# Orquestração
- Para mudanças full-stack: invocar backend-developer + frontend-developer
- Para releases: security-auditor → code-reviewer → devops-engineer
- Para debugging: sempre consultar logs via monitoring-agent primeiro
```

### Exemplos para Frameworks Específicos

#### ⚛️ React + Next.js
```markdown
# Next.js Setup
- next dev: Desenvolvimento
- next build: Build produção  
- next start: Servidor produção

# Estrutura de Páginas
- /pages: File-based routing
- /components: Componentes reutilizáveis
- /lib: Utilities e configurations
- /public: Assets estáticos

# Performance
- Image optimization automática
- Code splitting por página
- API routes em /pages/api

# Deploy
- Vercel preferred
- Environment variables em .env.local
- Build cache em .next/
```

#### 🚀 Express.js API
```markdown
# Express API
- npm run dev: Nodemon development
- npm start: Production server
- npm run test: Jest + Supertest

# Estrutura
- /routes: Definição de rotas
- /controllers: Business logic
- /middleware: Custom middlewares
- /models: Database models

# Database
- MongoDB com Mongoose
- Connection string em .env
- Migrations em /migrations

# Security
- Helmet para headers
- CORS configurado
- Rate limiting implementado
- JWT para authentication
```

### Troubleshooting Comum

#### 🚨 Contexto Não Carrega
- **Verificação**: Nome do arquivo deve ser exatamente `CLAUDE.md` (case-sensitive)
- **Localização**: Arquivo deve estar no diretório correto que Claude escaneia
- **Permissões**: Verificar permissões de leitura do arquivo

#### ⚡ Regras Conflitantes  
- **Precedência**: Arquivo mais específico vence - revisar CLAUDE.md de nível inferior
- **Debugging**: Usar comando de debug para ver qual arquivo está sendo aplicado
- **Logs**: Verificar logs do Claude Code para entender a ordem de aplicação

#### 🌫️ Comportamentos Ambíguos
- **Clareza**: Ser explícito - contexto unclear leva a respostas genéricas ou incorretas
- **Exemplos**: Incluir exemplos específicos de código e comandos
- **Detalhamento**: Detalhar edge cases e exceções

#### 🔄 Staleness (Desatualização)
- **Manutenção**: Atualizar CLAUDE.md junto com mudanças de código  
- **Time Sync**: Encorajar equipe a manter CLAUDE.md accurate e current
- **Versionamento**: Versionar CLAUDE.md junto com o código no git

#### 💾 Context Overflow
- **Segmentação**: Para projetos muito grandes, segmentar conhecimento em múltiplos CLAUDE.md
- **Modularização**: Um por feature/módulo para evitar issues de limite de contexto
- **Priorização**: Focar informações mais críticas nos arquivos principais

---

## ⚡ Slash Commands e Workflows

### Lista Completa de Comandos

#### 🔧 Comandos Built-in Principais
- **`/help`**: Lista todos comandos disponíveis com descrições
- **`/clear`**: Limpa contexto da conversa atual para fresh start
- **`/compact`**: Comprime histórico da sessão para otimização
- **`/init`**: Cria arquivo CLAUDE.md com metadata do projeto
- **`/add-dir`**: Adiciona diretório ao contexto da sessão
- **`/forward`**: Encaminha contexto para outro agent ou sessão
- **`/mcp`**: Gerencia servidores MCP (Meta-Code-Processors)
- **`/ide`**: Integração com IDEs populares
- **`/exit`**: Finaliza sessão atual

#### 📋 Listagem de Comandos
```bash
# Ver todos os comandos disponíveis
/help

# Ver comandos específicos de projeto vs usuário
/help project
/help user
```

### Criação de Comandos Customizados

#### 📁 Estrutura de Diretórios
```
# Comandos específicos do projeto
.claude/commands/
├── review.md           # /review
├── deploy.md           # /deploy  
├── test-all.md         # /test-all
└── security/
    ├── audit.md        # /security:audit
    └── scan.md         # /security:scan

# Comandos globais do usuário  
~/.claude/commands/
├── personal-setup.md  # /user:personal-setup
└── my-workflow.md     # /user:my-workflow
```

#### 🔨 Processo de Criação
```bash
# 1. Criar diretório de comandos
mkdir -p .claude/commands

# 2. Criar arquivo markdown (nome = comando)
echo "Execute comprehensive code review..." > .claude/commands/review.md

# 3. Usar comando
/review
# ou com namespace:
/project:review
```

#### 📝 Template de Comando Básico
```markdown
# Review Command
Execute a comprehensive code review following these steps:

1. **Code Quality Analysis**
   - Check for code smells and anti-patterns
   - Verify naming conventions
   - Assess function/class complexity

2. **Security Review**  
   - Scan for common vulnerabilities
   - Check input validation
   - Verify authentication/authorization

3. **Performance Check**
   - Identify potential bottlenecks
   - Review database queries
   - Check for memory leaks

4. **Testing Coverage**
   - Verify unit test coverage > 80%
   - Check for integration tests
   - Validate edge cases

## Arguments
Use $ARGUMENTS for specific files/directories to review.

## Output Format
Provide structured markdown report with:
- ✅ Items that passed review
- ⚠️ Warnings that should be addressed  
- ❌ Critical issues that must be fixed
```

#### 🎯 Comandos com Argumentos
```markdown
# Deploy Command with Arguments

Deploy application to specified environment.

## Usage
/deploy production
/deploy staging  
/deploy development

## Steps
1. Validate environment: $ARGUMENTS
2. Run tests for target environment
3. Build optimized bundle
4. Deploy to $ARGUMENTS environment
5. Run post-deployment health checks
6. Send notification to team

## Environment-Specific Actions
- **production**: Requires approval, full test suite, rollback plan
- **staging**: Integration tests, performance benchmarks  
- **development**: Fast deployment, basic health checks
```

### Estratégias de Automação de Workflow

#### 🔄 Workflows Encadeados
```markdown
# Release Workflow (/release)

Execute complete release process:

## Phase 1: Pre-Release
/test-all
/security:audit  
/review

## Phase 2: Build & Package
- Run production build
- Generate release notes
- Create git tag
- Package artifacts

## Phase 3: Deploy
/deploy staging
- Run staging tests
- Performance benchmarks  
/deploy production

## Phase 4: Post-Deploy
- Health checks
- Monitoring alerts
- Team notifications
- Documentation updates
```

#### ⚡ Comandos Paralelos
```markdown
# Parallel Quality Check (/quality-gate)

Run multiple quality checks in parallel:

**Concurrent Execution:**
- Static code analysis (ESLint, SonarQube)
- Security scanning (OWASP, Snyk)  
- Dependency audit (npm audit, safety)
- Performance profiling (Lighthouse, WebPageTest)
- Accessibility testing (axe, pa11y)

**Consolidation:**
- Aggregate all results
- Generate unified report
- Determine pass/fail status
- Create action items for failures
```

#### 🎭 Comandos Condicionais
```markdown
# Smart Deploy (/smart-deploy)

Intelligent deployment based on changes detected:

## Change Detection
- If package.json changed → Full dependency reinstall
- If database migrations present → Run migration checks
- If config files changed → Validate configuration  
- If security-related changes → Run security audit

## Environment Selection
```bash
# Auto-detect target based on branch:
- main branch → production deployment
- develop branch → staging deployment  
- feature/* branches → development deployment
```

## Deployment Strategy
- Breaking changes detected → Blue-green deployment
- Minor changes → Rolling update
- Hotfix → Fast-track deployment with minimal checks
```

### Integração com CI/CD

#### 🤖 GitHub Actions Integration
```yaml
# .github/workflows/claude-review.yml
name: Claude Code Review

on:
  pull_request:
    branches: [main]

jobs:
  claude-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Claude Code
        run: |
          # Install Claude Code CLI
          curl -sSL https://install.claude.ai | bash
          
      - name: Run Code Review
        run: |
          # Execute custom review command
          claude /review --output=review-report.md
          
      - name: Comment PR
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('review-report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## 🤖 Claude Code Review\n\n${report}`
            });
```

#### 🚀 Jenkins Pipeline
```groovy
// Jenkinsfile
pipeline {
    agent any
    
    stages {
        stage('Claude Quality Gate') {
            steps {
                script {
                    // Run Claude Code quality checks
                    sh 'claude /quality-gate'
                    
                    // Parse results
                    def results = readFile('quality-report.json')
                    def quality = readJSON text: results
                    
                    // Gate deployment based on quality score
                    if (quality.score < 80) {
                        error("Quality gate failed: ${quality.score}/100")
                    }
                }
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh 'claude /deploy production'
            }
        }
    }
    
    post {
        always {
            // Archive Claude reports
            archiveArtifacts artifacts: '*-report.*', fingerprint: true
        }
    }
}
```

### Patterns Avançados de Comandos

#### 🔄 Comando Recursivo
```markdown
# Recursive Refactor (/refactor-recursive)

Perform recursive refactoring across entire codebase:

## Pattern Detection
1. Scan for code patterns to refactor
2. Prioritize by impact/complexity
3. Create refactoring plan

## Execution Phases
```bash
Phase 1: Safe Refactors (no behavior change)
- Rename variables/functions for clarity
- Extract common code to utilities
- Remove dead code

Phase 2: Structural Changes  
- Move files to better locations
- Reorganize imports/exports
- Update architectural patterns

Phase 3: Optimization
- Performance improvements
- Memory usage optimization
- Bundle size reduction
```

## Validation
- Run full test suite after each phase
- Check for breaking changes
- Validate performance benchmarks
```

#### 🎯 Multi-Repository Command
```markdown
# Cross-Repo Sync (/sync-repos)

Synchronize changes across related repositories:

## Repository Detection
- Frontend repo: /path/to/frontend
- Backend repo: /path/to/backend  
- Shared libraries: /path/to/shared

## Sync Operations
```bash
1. Shared Library Updates
   - Update version in package.json
   - Push changes to npm registry
   - Update dependents

2. API Contract Sync
   - Generate OpenAPI spec from backend
   - Update frontend API clients
   - Validate contract compatibility

3. Configuration Sync  
   - Environment variables
   - Feature flags
   - Security policies
```

## Validation
- Cross-repo integration tests
- End-to-end testing
- Deployment coordination
```

### Otimização de Performance

#### 🚀 Comandos Otimizados
```markdown
# Performance Best Practices

## Prompt Optimization
- Keep prompts concise and focused
- Avoid ambiguous language
- Use structured templates

## Context Management
- Clear context regularly with /clear
- Use /compact for long sessions
- Scope commands to relevant files only

## Execution Efficiency
```bash
# Good: Specific and focused
/review src/auth/login.js

# Better: Multiple related files  
/review src/auth/ --pattern="*.js"

# Avoid: Too broad, slow execution
/review src/ --all-files
```

## Resource Management
- Cache command results when possible
- Reuse configurations across similar projects
- Parallelize independent operations
```

#### 📊 Monitoramento de Performance
```markdown
# Performance Monitoring (/monitor-performance)

Track and optimize command execution:

## Metrics Collection
- Command execution time
- Context size and complexity
- Success/failure rates
- Resource utilization

## Optimization Suggestions
```bash
Slow Commands (>30s):
- /review: Consider smaller scope
- /deploy: Check network connectivity  
- /test-all: Run tests in parallel

High Failure Rate Commands:
- /security:scan: Update tool configurations
- /deploy production: Review approval process
```

## Reporting
- Generate weekly performance reports
- Identify bottleneck commands
- Suggest optimizations
```

### Exemplos Complexos do Mundo Real

#### 🏢 Enterprise Release Pipeline
```markdown
# Enterprise Release (/enterprise-release)

Complete enterprise release workflow:

## Pre-Release (Parallel Execution)
```bash
┌─ Security Team ─────────┐    ┌─ QA Team ───────────────┐
│ /security:full-audit    │    │ /test:integration       │
│ /compliance:check       │    │ /test:performance       │  
│ /vulnerability:scan     │    │ /test:accessibility     │
└─────────────────────────┘    └─────────────────────────┘

┌─ DevOps Team ──────────┐     ┌─ Documentation Team ───┐
│ /infrastructure:check  │     │ /docs:generate          │
│ /monitoring:setup      │     │ /changelog:create       │
│ /rollback:prepare      │     │ /release-notes:draft    │
└────────────────────────┘     └─────────────────────────┘
```

## Release Execution
```bash
1. Stakeholder Approval Gate
   - Product Owner sign-off
   - Security team approval
   - Infrastructure readiness

2. Production Deployment  
   - Blue-green deployment strategy
   - Health checks every 30 seconds
   - Rollback trigger on error threshold

3. Post-Release Validation
   - Smoke tests on production
   - Performance monitoring
   - User acceptance validation
```

## Rollback Procedures
- Automated rollback triggers
- Data migration rollback
- External service notifications
```

#### 🔬 Research & Development Workflow
```markdown
# R&D Experiment (/rd-experiment)

Research and development experiment pipeline:

## Experiment Setup
```bash
1. Hypothesis Definition
   - Problem statement
   - Success criteria  
   - Risk assessment

2. Environment Preparation
   - Isolated development environment
   - Data sampling and anonymization
   - Monitoring and logging setup

3. Baseline Establishment
   - Current system metrics
   - Performance benchmarks
   - User experience baseline
```

## Experiment Execution
```bash
Phase 1: Proof of Concept (2 weeks)
├── /prototype:create
├── /metrics:baseline
└── /validation:quick

Phase 2: Full Implementation (4 weeks)  
├── /implement:full-feature
├── /testing:comprehensive
└── /performance:optimize

Phase 3: Validation (2 weeks)
├── /ab-test:setup
├── /metrics:collect
└── /analysis:statistical
```

## Results Analysis  
- Statistical significance testing
- Performance impact analysis
- User experience evaluation
- Business impact assessment

## Decision Matrix
```bash
Success: 
- Implement in production
- Plan rollout strategy
- Update documentation

Partial Success:
- Identify improvement areas  
- Plan iteration cycle
- Adjust hypothesis

Failure:
- Document learnings
- Archive experiment
- Explore alternative approaches
```
```

---

## 🎨 Patterns Avançados

### Patterns de Orquestração

#### 🌊 Event-Driven Orchestration
```markdown
# Event-Driven Pattern

## Event Triggers
```bash
Code Push → Security Scan → Code Review → Deploy
     ↓              ↓              ↓         ↓
  Notification   Vuln Alert    PR Update  Success
```

## Implementation
```yaml
events:
  - trigger: git_push
    actions:
      - /security:scan
      - /test:automated
      
  - trigger: security_scan_complete  
    condition: no_high_vulnerabilities
    actions:
      - /review:automated
      
  - trigger: review_approved
    actions:
      - /deploy:staging
```
```

#### 🔄 Circuit Breaker Pattern
```markdown
# Circuit Breaker for Commands

## States
- **CLOSED**: Normal operation
- **OPEN**: Failures detected, bypass command
- **HALF-OPEN**: Testing if service recovered

## Implementation
```python
class CommandCircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60):
        self.failure_count = 0
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def call_command(self, command):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF-OPEN"
            else:
                return "Command temporarily unavailable"
                
        try:
            result = execute_command(command)
            if self.state == "HALF-OPEN":
                self.state = "CLOSED"
                self.failure_count = 0
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
            
            raise e
```
```

#### 🎭 Saga Pattern para Long-Running Workflows
```markdown
# Saga Pattern Implementation

## Workflow Steps
```bash
1. Reserve Resources    → Compensate: Release Resources
2. Validate Input       → Compensate: Clean Invalid Data  
3. Process Business     → Compensate: Reverse Business Logic
4. Update Database      → Compensate: Rollback Database
5. Send Notifications   → Compensate: Send Cancellation Notice
```

## Saga Coordinator
```yaml
saga_definition:
  name: "feature_deployment"
  steps:
    - step: "reserve_resources"
      command: "/infra:reserve"
      compensate: "/infra:release"
      
    - step: "run_tests"  
      command: "/test:full-suite"
      compensate: "/cleanup:test-data"
      
    - step: "deploy"
      command: "/deploy:production" 
      compensate: "/rollback:production"
      
    - step: "notify"
      command: "/notify:success"
      compensate: "/notify:rollback"

compensation_strategy: "backward" # ou "forward"
```

## Error Handling
```python
class SagaOrchestrator:
    def execute_saga(self, saga_definition):
        executed_steps = []
        
        try:
            for step in saga_definition.steps:
                result = self.execute_step(step)
                executed_steps.append((step, result))
                
        except Exception as e:
            # Execute compensation in reverse order
            for step, _ in reversed(executed_steps):
                try:
                    self.execute_compensation(step)
                except Exception as comp_error:
                    # Log compensation failure
                    self.log_compensation_failure(step, comp_error)
            
            raise e
```
```

### Patterns de Resilência

#### 🔄 Retry Pattern with Backoff
```markdown
# Intelligent Retry Pattern

## Retry Strategy
```python
import time
import random

class SmartRetry:
    def __init__(self, max_attempts=3, base_delay=1, max_delay=60):
        self.max_attempts = max_attempts
        self.base_delay = base_delay  
        self.max_delay = max_delay
    
    def execute_with_retry(self, command, *args, **kwargs):
        for attempt in range(self.max_attempts):
            try:
                return execute_command(command, *args, **kwargs)
                
            except TransientError as e:
                if attempt == self.max_attempts - 1:
                    raise e
                
                # Exponential backoff with jitter
                delay = min(
                    self.base_delay * (2 ** attempt) + random.uniform(0, 1),
                    self.max_delay
                )
                
                print(f"Attempt {attempt + 1} failed, retrying in {delay:.2f}s")
                time.sleep(delay)
                
            except PermanentError as e:
                # Don't retry permanent errors
                raise e
```

## Error Classification
```python
class ErrorClassifier:
    TRANSIENT_ERRORS = [
        "Network timeout",
        "Service temporarily unavailable", 
        "Rate limit exceeded",
        "Database connection lost"
    ]
    
    PERMANENT_ERRORS = [
        "Authentication failed",
        "Permission denied",
        "Invalid syntax",
        "File not found"
    ]
    
    def classify_error(self, error_message):
        if any(transient in error_message for transient in self.TRANSIENT_ERRORS):
            return "TRANSIENT"
        elif any(permanent in error_message for permanent in self.PERMANENT_ERRORS):
            return "PERMANENT"
        else:
            return "UNKNOWN"
```
```

#### 🛡️ Bulkhead Pattern
```markdown
# Resource Isolation Pattern

## Resource Pools
```python
class ResourcePool:
    def __init__(self, pool_name, max_resources=10):
        self.pool_name = pool_name
        self.max_resources = max_resources
        self.active_resources = 0
        self.queue = []
    
    def acquire_resource(self, command_type):
        if self.active_resources < self.max_resources:
            self.active_resources += 1
            return Resource(self.pool_name, command_type)
        else:
            raise ResourceExhaustedError(f"No resources available in {self.pool_name}")
    
    def release_resource(self, resource):
        self.active_resources -= 1

# Separate pools for different command types
pools = {
    "critical": ResourcePool("critical", max_resources=5),
    "standard": ResourcePool("standard", max_resources=15), 
    "background": ResourcePool("background", max_resources=30)
}

def execute_command_with_isolation(command, priority="standard"):
    pool = pools[priority]
    resource = pool.acquire_resource(command.type)
    
    try:
        return resource.execute(command)
    finally:
        pool.release_resource(resource)
```

## Command Prioritization
```yaml
command_priorities:
  critical:
    - /security:emergency-patch
    - /rollback:production
    - /incident:response
    
  standard:
    - /deploy:staging
    - /test:integration  
    - /review:code
    
  background:
    - /docs:generate
    - /cleanup:logs
    - /metrics:collect
```
```

### Patterns de Monitoramento e Observabilidade

#### 📊 Distributed Tracing Pattern
```markdown
# Distributed Tracing for Commands

## Trace Context
```python
import uuid
from datetime import datetime

class TraceContext:
    def __init__(self, trace_id=None, parent_span_id=None):
        self.trace_id = trace_id or str(uuid.uuid4())
        self.spans = []
        self.parent_span_id = parent_span_id
    
    def start_span(self, operation_name):
        span = Span(
            span_id=str(uuid.uuid4()),
            trace_id=self.trace_id,
            parent_id=self.parent_span_id,
            operation_name=operation_name,
            start_time=datetime.utcnow()
        )
        self.spans.append(span)
        return span
    
    def finish_span(self, span, status="success", metadata=None):
        span.end_time = datetime.utcnow()
        span.duration = (span.end_time - span.start_time).total_seconds()
        span.status = status
        span.metadata = metadata or {}

# Usage in commands
def traced_command(func):
    def wrapper(*args, **kwargs):
        trace = TraceContext()
        span = trace.start_span(f"command.{func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            trace.finish_span(span, "success", {"result_size": len(str(result))})
            return result
            
        except Exception as e:
            trace.finish_span(span, "error", {"error": str(e)})
            raise e
        finally:
            # Send trace to monitoring system
            send_trace_to_jaeger(trace)
    
    return wrapper

@traced_command
def deploy_command(environment):
    # Command implementation
    pass
```

## Metrics Collection
```python
class CommandMetrics:
    def __init__(self):
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        self.gauges = defaultdict(float)
    
    def increment_counter(self, metric_name, tags=None):
        key = f"{metric_name}_{hash(str(tags))}"
        self.counters[key] += 1
    
    def record_duration(self, metric_name, duration, tags=None):
        key = f"{metric_name}_{hash(str(tags))}"
        self.histograms[key].append(duration)
    
    def set_gauge(self, metric_name, value, tags=None):
        key = f"{metric_name}_{hash(str(tags))}"
        self.gauges[key] = value

# Metrics in action
metrics = CommandMetrics()

def execute_command_with_metrics(command):
    start_time = time.time()
    tags = {"command": command.name, "environment": os.getenv("ENV", "dev")}
    
    try:
        result = execute_command(command)
        metrics.increment_counter("command.success", tags)
        return result
        
    except Exception as e:
        metrics.increment_counter("command.failure", tags | {"error": type(e).__name__})
        raise e
        
    finally:
        duration = time.time() - start_time
        metrics.record_duration("command.duration", duration, tags)
```
```

#### 🚨 Health Check Pattern
```markdown
# Comprehensive Health Monitoring

## Health Check Framework
```python
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List

class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded" 
    UNHEALTHY = "unhealthy"

@dataclass
class HealthCheck:
    name: str
    status: HealthStatus
    message: str
    details: Dict = None
    duration_ms: float = 0

class HealthChecker:
    def __init__(self):
        self.checks = {}
    
    def register_check(self, name, check_function, timeout=5):
        self.checks[name] = {
            'function': check_function,
            'timeout': timeout
        }
    
    def run_all_checks(self) -> List[HealthCheck]:
        results = []
        
        for name, config in self.checks.items():
            start_time = time.time()
            
            try:
                with timeout_context(config['timeout']):
                    result = config['function']()
                    status = HealthStatus.HEALTHY if result else HealthStatus.UNHEALTHY
                    message = "OK" if result else "Check failed"
                    
            except TimeoutError:
                status = HealthStatus.UNHEALTHY
                message = f"Timeout after {config['timeout']}s"
                
            except Exception as e:
                status = HealthStatus.UNHEALTHY
                message = f"Error: {str(e)}"
            
            duration = (time.time() - start_time) * 1000
            results.append(HealthCheck(name, status, message, duration_ms=duration))
        
        return results

# Register health checks
health = HealthChecker()
health.register_check("database", check_database_connection)
health.register_check("external_api", check_external_api) 
health.register_check("disk_space", check_disk_space)
health.register_check("memory_usage", check_memory_usage)

def check_database_connection():
    # Implementation
    return db.ping()

def check_external_api():
    # Implementation  
    response = requests.get("https://api.example.com/health", timeout=3)
    return response.status_code == 200
```

## Health Dashboard
```python
class HealthDashboard:
    def generate_health_report(self) -> Dict:
        checks = health.run_all_checks()
        
        healthy_count = sum(1 for check in checks if check.status == HealthStatus.HEALTHY)
        total_count = len(checks)
        
        overall_status = HealthStatus.HEALTHY
        if healthy_count == 0:
            overall_status = HealthStatus.UNHEALTHY
        elif healthy_count < total_count:
            overall_status = HealthStatus.DEGRADED
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.utcnow().isoformat(),
            "checks": {
                check.name: {
                    "status": check.status.value,
                    "message": check.message,
                    "duration_ms": check.duration_ms
                }
                for check in checks
            },
            "summary": {
                "total": total_count,
                "healthy": healthy_count,
                "degraded": sum(1 for check in checks if check.status == HealthStatus.DEGRADED),
                "unhealthy": sum(1 for check in checks if check.status == HealthStatus.UNHEALTHY)
            }
        }

# Health endpoint for monitoring
@app.route('/health')
def health_endpoint():
    dashboard = HealthDashboard()
    report = dashboard.generate_health_report()
    
    status_code = 200
    if report["status"] == "unhealthy":
        status_code = 503
    elif report["status"] == "degraded":
        status_code = 206
    
    return jsonify(report), status_code
```
```

---

## 🔧 Integrações e Ferramentas

### Integração com IDEs

#### 🎨 VS Code Integration
```json
// .vscode/settings.json
{
  "claude.enable": true,
  "claude.contextFiles": [
    "CLAUDE.md",
    "README.md",
    "package.json"
  ],
  "claude.autoSuggest": true,
  "claude.reviewOnSave": true,
  "claude.commands": {
    "review": ".claude/commands/review.md",
    "test": ".claude/commands/test.md",
    "deploy": ".claude/commands/deploy.md"
  }
}
```

#### 💎 JetBrains Integration
```xml
<!-- .idea/claude.xml -->
<component name="ClaudeSettings">
  <option name="enabled" value="true" />
  <option name="contextFiles">
    <list>
      <option value="CLAUDE.md" />
      <option value="build.gradle" />
      <option value="README.md" />
    </list>
  </option>
  <option name="autoComplete" value="true" />
  <option name="codeReview" value="true" />
</component>
```

### Meta-Code-Processors (MCPs)

#### 🌐 Firecrawl MCP
```yaml
# .claude/mcp/firecrawl.yml
name: firecrawl
description: Web scraping and screenshot processing
capabilities:
  - web_scraping
  - screenshot_analysis
  - content_extraction

configuration:
  api_key: ${FIRECRAWL_API_KEY}
  max_pages: 10
  respect_robots: true
  
commands:
  - name: scrape_docs
    description: Scrape documentation websites
    pattern: "scrape docs from {url}"
    
  - name: analyze_screenshot  
    description: Analyze UI screenshots
    pattern: "analyze screenshot {image_path}"
```

#### 📊 Custom Analytics MCP
```python
# mcps/analytics.py
class AnalyticsMCP:
    def __init__(self, config):
        self.config = config
        self.analytics_client = AnalyticsClient(config['api_key'])
    
    def get_performance_metrics(self, timeframe='7d'):
        """Get application performance metrics"""
        return self.analytics_client.get_metrics(
            timeframe=timeframe,
            metrics=['response_time', 'error_rate', 'throughput']
        )
    
    def analyze_user_behavior(self, feature):
        """Analyze user behavior for specific feature"""
        return self.analytics_client.analyze_feature_usage(feature)
    
    def generate_insights(self, data):
        """Generate actionable insights from analytics data"""
        insights = []
        
        if data['error_rate'] > 0.05:
            insights.append({
                'type': 'warning',
                'message': 'Error rate above 5% threshold',
                'recommendation': 'Investigate recent deployments'
            })
        
        return insights

# Registration
claude_mcp.register_processor('analytics', AnalyticsMCP)
```

### Hooks & Automation

#### 🔄 Post-Edit Hooks
```bash
#!/bin/bash
# .claude/hooks/post-edit.sh

echo "Running post-edit hooks..."

# Format code
if command -v prettier >/dev/null 2>&1; then
    echo "Formatting with Prettier..."
    prettier --write --ignore-unknown .
fi

# Lint code  
if command -v eslint >/dev/null 2>&1; then
    echo "Linting with ESLint..."
    eslint --fix --ext .js,.jsx,.ts,.tsx src/
fi

# Run type checking
if command -v tsc >/dev/null 2>&1; then
    echo "Type checking..."
    tsc --noEmit
fi

# Run tests on changed files
if command -v jest >/dev/null 2>&1; then
    echo "Running relevant tests..."
    jest --findRelatedTests --passWithNoTests
fi

echo "Post-edit hooks completed!"
```

#### 🚨 Pre-Deploy Hook
```python
#!/usr/bin/env python3
# .claude/hooks/pre-deploy.py

import sys
import subprocess
import json
from pathlib import Path

def run_security_scan():
    """Run security vulnerability scan"""
    result = subprocess.run(['npm', 'audit', '--json'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        audit_data = json.loads(result.stdout)
        high_vulns = audit_data.get('metadata', {}).get('vulnerabilities', {}).get('high', 0)
        
        if high_vulns > 0:
            print(f"❌ {high_vulns} high-severity vulnerabilities found!")
            return False
    
    print("✅ Security scan passed")
    return True

def check_test_coverage():
    """Ensure test coverage meets threshold"""
    result = subprocess.run(['npm', 'run', 'test:coverage'], 
                          capture_output=True, text=True)
    
    # Parse coverage report
    coverage_file = Path('./coverage/coverage-summary.json')
    if coverage_file.exists():
        with open(coverage_file) as f:
            coverage = json.load(f)
        
        total_coverage = coverage['total']['lines']['pct']
        if total_coverage < 80:
            print(f"❌ Test coverage {total_coverage}% below 80% threshold")
            return False
    
    print(f"✅ Test coverage sufficient: {total_coverage}%")
    return True

def validate_build():
    """Ensure production build succeeds"""
    result = subprocess.run(['npm', 'run', 'build'], 
                          capture_output=True, text=True)
    
    if result.returncode != 0:
        print("❌ Production build failed")
        print(result.stderr)
        return False
    
    print("✅ Production build successful")
    return True

def main():
    print("🔍 Running pre-deploy checks...")
    
    checks = [
        ("Security Scan", run_security_scan),
        ("Test Coverage", check_test_coverage), 
        ("Build Validation", validate_build)
    ]
    
    failed_checks = []
    
    for check_name, check_func in checks:
        print(f"\n--- {check_name} ---")
        if not check_func():
            failed_checks.append(check_name)
    
    if failed_checks:
        print(f"\n❌ Deploy blocked! Failed checks: {', '.join(failed_checks)}")
        sys.exit(1)
    else:
        print("\n✅ All pre-deploy checks passed! Deploy approved.")
        sys.exit(0)

if __name__ == "__main__":
    main()
```

### Session Management Avançado

#### 💾 Context Persistence
```python
# .claude/session-manager.py

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path

class SessionManager:
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.session_dir = self.project_root / ".claude" / "sessions"
        self.session_dir.mkdir(parents=True, exist_ok=True)
    
    def save_session(self, session_data):
        """Save current session state"""
        session_id = self.generate_session_id(session_data)
        session_file = self.session_dir / f"{session_id}.json"
        
        session_data.update({
            'timestamp': datetime.utcnow().isoformat(),
            'project_hash': self.get_project_hash(),
            'session_id': session_id
        })
        
        with open(session_file, 'w') as f:
            json.dump(session_data, f, indent=2)
        
        return session_id
    
    def load_session(self, session_id):
        """Load previous session state"""
        session_file = self.session_dir / f"{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file) as f:
            return json.load(f)
    
    def list_recent_sessions(self, limit=10):
        """List recent sessions for this project"""
        sessions = []
        project_hash = self.get_project_hash()
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    session = json.load(f)
                
                if session.get('project_hash') == project_hash:
                    sessions.append(session)
                    
            except (json.JSONDecodeError, KeyError):
                continue
        
        # Sort by timestamp, most recent first
        sessions.sort(key=lambda x: x['timestamp'], reverse=True)
        return sessions[:limit]
    
    def cleanup_old_sessions(self, days=30):
        """Remove sessions older than specified days"""
        cutoff = datetime.utcnow() - timedelta(days=days)
        removed_count = 0
        
        for session_file in self.session_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    session = json.load(f)
                
                session_time = datetime.fromisoformat(session['timestamp'])
                if session_time < cutoff:
                    session_file.unlink()
                    removed_count += 1
                    
            except (json.JSONDecodeError, KeyError, ValueError):
                # Remove corrupted session files
                session_file.unlink()
                removed_count += 1
        
        return removed_count
    
    def get_project_hash(self):
        """Generate hash of project structure for session matching"""
        project_files = [
            'package.json', 'requirements.txt', 'Cargo.toml', 
            'pom.xml', 'build.gradle', 'composer.json'
        ]
        
        hasher = hashlib.md5()
        hasher.update(str(self.project_root.absolute()).encode())
        
        for file_name in project_files:
            file_path = self.project_root / file_name
            if file_path.exists():
                hasher.update(file_path.read_bytes())
        
        return hasher.hexdigest()
    
    def generate_session_id(self, session_data):
        """Generate unique session ID"""
        content = f"{session_data.get('command', '')}{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

# Usage in Claude Code
def save_current_session():
    session_manager = SessionManager()
    
    session_data = {
        'command': current_command,
        'context_files': list_context_files(),
        'variables': get_session_variables(),
        'last_outputs': get_recent_outputs(5)
    }
    
    session_id = session_manager.save_session(session_data)
    print(f"Session saved: {session_id}")
    return session_id

def restore_session(session_id):
    session_manager = SessionManager()
    session_data = session_manager.load_session(session_id)
    
    if session_data:
        load_context_files(session_data['context_files'])
        set_session_variables(session_data['variables'])
        print(f"Session {session_id} restored successfully")
        return True
    
    return False
```

#### 🔄 Multi-Directory Context Management
```python
# .claude/context-manager.py

class ContextManager:
    def __init__(self):
        self.active_contexts = {}
        self.context_stack = []
    
    def add_directory_context(self, path, alias=None):
        """Add directory to active context"""
        path = Path(path).resolve()
        context_id = alias or path.name
        
        # Scan directory for relevant files
        context_files = self.scan_directory(path)
        
        self.active_contexts[context_id] = {
            'path': str(path),
            'files': context_files,
            'claude_md': self.find_claude_md(path),
            'added_at': datetime.utcnow().isoformat()
        }
        
        print(f"Added context '{context_id}': {len(context_files)} files")
        return context_id
    
    def remove_directory_context(self, context_id):
        """Remove directory from active context"""
        if context_id in self.active_contexts:
            del self.active_contexts[context_id]
            print(f"Removed context '{context_id}'")
            return True
        return False
    
    def list_contexts(self):
        """List all active contexts"""
        for context_id, context in self.active_contexts.items():
            file_count = len(context['files'])
            path = context['path']
            print(f"  {context_id}: {path} ({file_count} files)")
    
    def find_relevant_files(self, query):
        """Find files relevant to query across all contexts"""
        relevant_files = []
        
        for context_id, context in self.active_contexts.items():
            for file_info in context['files']:
                # Simple relevance scoring
                score = self.calculate_relevance(query, file_info)
                if score > 0.3:  # Threshold
                    relevant_files.append({
                        'context': context_id,
                        'file': file_info,
                        'score': score
                    })
        
        # Sort by relevance score
        relevant_files.sort(key=lambda x: x['score'], reverse=True)
        return relevant_files
    
    def scan_directory(self, path):
        """Scan directory for relevant files"""
        relevant_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', 
            '.rs', '.cpp', '.c', '.h', '.cs', '.php', '.rb',
            '.md', '.txt', '.json', '.yaml', '.yml', '.toml',
            '.sql', '.sh', '.bat', '.ps1'
        }
        
        ignore_patterns = {
            'node_modules', '.git', '__pycache__', '.venv', 
            'venv', 'target', 'build', 'dist', '.gradle'
        }
        
        files = []
        for file_path in path.rglob('*'):
            if file_path.is_file():
                # Skip ignored directories
                if any(ignored in file_path.parts for ignored in ignore_patterns):
                    continue
                
                # Include relevant file types
                if file_path.suffix.lower() in relevant_extensions:
                    files.append({
                        'path': str(file_path.relative_to(path)),
                        'full_path': str(file_path),
                        'size': file_path.stat().st_size,
                        'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                    })
        
        return files
    
    def find_claude_md(self, path):
        """Find CLAUDE.md file in directory"""
        claude_md_path = path / "CLAUDE.md"
        if claude_md_path.exists():
            return str(claude_md_path)
        return None
    
    def calculate_relevance(self, query, file_info):
        """Calculate relevance score for file based on query"""
        query_lower = query.lower()
        file_path_lower = file_info['path'].lower()
        
        score = 0.0
        
        # Exact filename match
        if query_lower in Path(file_path_lower).stem:
            score += 0.8
        
        # Directory match  
        if query_lower in file_path_lower:
            score += 0.5
        
        # Extension relevance
        extension_scores = {
            '.md': 0.1, '.py': 0.3, '.js': 0.3, '.ts': 0.3,
            '.jsx': 0.3, '.tsx': 0.3, '.json': 0.2, '.yml': 0.2
        }
        
        file_ext = Path(file_info['path']).suffix.lower()
        score += extension_scores.get(file_ext, 0.1)
        
        return min(score, 1.0)  # Cap at 1.0

# Integration with Claude Code
context_manager = ContextManager()

def add_directory(path, alias=None):
    """Add directory to Claude context"""
    return context_manager.add_directory_context(path, alias)

def list_contexts():
    """List active contexts"""
    context_manager.list_contexts()

def find_files(query):
    """Find relevant files for query"""
    return context_manager.find_relevant_files(query)
```

---

## ✅ Boas Práticas

### Segurança e Controle de Acesso

#### 🔐 Principle of Least Privilege
```yaml
# Security Configuration Template
subagent_permissions:
  backend-developer:
    tools:
      - bash        # Limited shell access
      - read        # File reading
      - write       # File writing  
      - edit        # File editing
    restrictions:
      - no_system_files      # Cannot modify system files
      - no_credential_files  # Cannot access .env, secrets
      - sandboxed_execution  # Runs in isolated environment
    
  security-auditor:
    tools:
      - bash        # Full shell for security tools
      - read        # Read access to all files
      - grep        # Pattern searching
      - network     # Network analysis tools
    restrictions:
      - read_only_mode      # Cannot modify files
      - audit_logging       # All actions logged
    
  code-reviewer:
    tools:
      - read        # Read source files
      - grep        # Search capabilities
    restrictions:
      - no_write_access     # Read-only access
      - no_execution       # Cannot run commands
```

#### 🛡️ Secrets Management
```python
# .claude/security/secrets-manager.py

import os
import keyring
from cryptography.fernet import Fernet

class SecretsManager:
    def __init__(self):
        self.cipher_suite = Fernet(self._get_or_create_key())
    
    def _get_or_create_key(self):
        """Get or create encryption key"""
        key = keyring.get_password("claude-code", "encryption-key")
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password("claude-code", "encryption-key", key)
        return key.encode()
    
    def store_secret(self, name, value):
        """Store encrypted secret"""
        encrypted_value = self.cipher_suite.encrypt(value.encode())
        keyring.set_password("claude-code", name, encrypted_value.decode())
    
    def get_secret(self, name):
        """Retrieve and decrypt secret"""
        encrypted_value = keyring.get_password("claude-code", name)
        if encrypted_value:
            decrypted_value = self.cipher_suite.decrypt(encrypted_value.encode())
            return decrypted_value.decode()
        return None
    
    def inject_secrets_to_env(self):
        """Inject secrets as environment variables"""
        secrets = {
            "DATABASE_URL": self.get_secret("database-url"),
            "API_KEY": self.get_secret("api-key"),
            "JWT_SECRET": self.get_secret("jwt-secret")
        }
        
        for key, value in secrets.items():
            if value:
                os.environ[key] = value

# Usage in commands
secrets = SecretsManager()

def secure_deploy_command():
    # Inject secrets before deployment
    secrets.inject_secrets_to_env()
    
    # Run deployment with secure environment
    result = subprocess.run(['docker', 'deploy'], env=os.environ)
    
    # Clean up environment
    for key in ["DATABASE_URL", "API_KEY", "JWT_SECRET"]:
        os.environ.pop(key, None)
    
    return result
```

#### 📋 Audit Logging
```python
# .claude/security/audit-logger.py

import json
import hashlib
from datetime import datetime
from pathlib import Path

class AuditLogger:
    def __init__(self, log_dir=".claude/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_file = self.log_dir / f"audit-{datetime.now().strftime('%Y-%m')}.log"
    
    def log_action(self, action_type, details, sensitive=False):
        """Log action with optional sensitive data handling"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action_type": action_type,
            "details": self._sanitize_details(details) if sensitive else details,
            "user": os.getenv("USER", "unknown"),
            "session_id": self._get_session_id(),
            "checksum": None
        }
        
        # Add integrity checksum
        log_entry["checksum"] = self._calculate_checksum(log_entry)
        
        with open(self.log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _sanitize_details(self, details):
        """Remove sensitive information from log details"""
        sensitive_keys = ["password", "token", "secret", "key", "credential"]
        
        if isinstance(details, dict):
            sanitized = {}
            for key, value in details.items():
                if any(sensitive_key in key.lower() for sensitive_key in sensitive_keys):
                    sanitized[key] = "[REDACTED]"
                else:
                    sanitized[key] = value
            return sanitized
        
        return details
    
    def _calculate_checksum(self, log_entry):
        """Calculate integrity checksum"""
        entry_without_checksum = {k: v for k, v in log_entry.items() if k != "checksum"}
        content = json.dumps(entry_without_checksum, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _get_session_id(self):
        """Get current session ID"""
        return os.getenv("CLAUDE_SESSION_ID", "unknown")

# Integration with commands
audit = AuditLogger()

def audit_command_execution(func):
    """Decorator to audit command execution"""
    def wrapper(*args, **kwargs):
        command_name = func.__name__
        
        # Log command start
        audit.log_action("command_start", {
            "command": command_name,
            "args": str(args),
            "kwargs": str(kwargs)
        })
        
        try:
            result = func(*args, **kwargs)
            
            # Log successful completion
            audit.log_action("command_success", {
                "command": command_name,
                "result_size": len(str(result)) if result else 0
            })
            
            return result
            
        except Exception as e:
            # Log failure
            audit.log_action("command_failure", {
                "command": command_name,
                "error": str(e),
                "error_type": type(e).__name__
            })
            raise e
    
    return wrapper

@audit_command_execution
def sensitive_deploy_command(credentials):
    # This will be audited with sensitive data redacted
    audit.log_action("credential_access", {"action": "deploy_credentials"}, sensitive=True)
    # ... deployment logic
```

### Performance e Otimização

#### ⚡ Context Optimization
```python
# .claude/optimization/context-optimizer.py

class ContextOptimizer:
    def __init__(self, max_context_size=100000):  # ~100KB
        self.max_context_size = max_context_size
        self.context_cache = {}
    
    def optimize_context(self, file_list, query=None):
        """Optimize context by selecting most relevant files"""
        optimized_files = []
        current_size = 0
        
        # Sort files by relevance
        scored_files = self._score_files(file_list, query)
        
        for file_info in scored_files:
            file_size = self._estimate_file_size(file_info)
            
            if current_size + file_size <= self.max_context_size:
                optimized_files.append(file_info)
                current_size += file_size
            else:
                # Try to include summary instead of full file
                summary = self._get_file_summary(file_info)
                summary_size = len(summary)
                
                if current_size + summary_size <= self.max_context_size:
                    optimized_files.append({
                        **file_info,
                        'content': summary,
                        'is_summary': True
                    })
                    current_size += summary_size
        
        return optimized_files
    
    def _score_files(self, file_list, query):
        """Score files by relevance to query"""
        if not query:
            # Default scoring without query
            return sorted(file_list, key=self._default_score, reverse=True)
        
        scored = []
        for file_info in file_list:
            score = self._calculate_relevance_score(file_info, query)
            scored.append((score, file_info))
        
        # Sort by score, descending
        return [file_info for score, file_info in sorted(scored, reverse=True)]
    
    def _calculate_relevance_score(self, file_info, query):
        """Calculate relevance score for file"""
        score = 0.0
        file_path = file_info.get('path', '')
        
        # Path relevance
        if query.lower() in file_path.lower():
            score += 0.5
        
        # File type relevance
        important_extensions = {'.py': 0.3, '.js': 0.3, '.ts': 0.3, '.md': 0.2}
        ext = Path(file_path).suffix.lower()
        score += important_extensions.get(ext, 0.1)
        
        # Recent modification bonus
        if 'modified' in file_info:
            modified_time = datetime.fromisoformat(file_info['modified'])
            days_old = (datetime.now() - modified_time).days
            if days_old < 7:
                score += 0.2
        
        # Size penalty for very large files
        size = file_info.get('size', 0)
        if size > 50000:  # 50KB
            score *= 0.8
        
        return score
    
    def _default_score(self, file_info):
        """Default scoring without query"""
        score = 0.0
        
        # Prefer certain file types
        important_extensions = {'.md': 0.9, '.py': 0.8, '.js': 0.8, '.ts': 0.8}
        ext = Path(file_info.get('path', '')).suffix.lower()
        score += important_extensions.get(ext, 0.3)
        
        # Prefer smaller files
        size = file_info.get('size', 0)
        if size < 10000:  # 10KB
            score += 0.3
        
        return score
    
    def _get_file_summary(self, file_info):
        """Generate summary of file content"""
        file_path = file_info.get('full_path')
        if not file_path or not Path(file_path).exists():
            return "File not accessible"
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract key information
            lines = content.split('\n')
            summary_lines = []
            
            # Include first few lines
            summary_lines.extend(lines[:5])
            
            # Include function/class definitions
            for line in lines:
                stripped = line.strip()
                if (stripped.startswith('def ') or 
                    stripped.startswith('class ') or
                    stripped.startswith('function ') or
                    stripped.startswith('export ')):
                    summary_lines.append(line)
            
            # Include comments with TODO/FIXME
            for line in lines:
                if 'TODO' in line or 'FIXME' in line:
                    summary_lines.append(line)
            
            return '\n'.join(summary_lines[:20])  # Limit to 20 lines
            
        except Exception:
            return "Unable to generate summary"
    
    def _estimate_file_size(self, file_info):
        """Estimate file size in context"""
        return file_info.get('size', 1000)  # Default estimate

# Usage
optimizer = ContextOptimizer()

def optimize_files_for_context(files, query=None):
    return optimizer.optimize_context(files, query)
```

#### 🚀 Command Caching
```python
# .claude/optimization/command-cache.py

import pickle
import hashlib
from pathlib import Path
from datetime import datetime, timedelta

class CommandCache:
    def __init__(self, cache_dir=".claude/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.default_ttl = timedelta(hours=24)
    
    def get(self, command, args=None, kwargs=None):
        """Get cached result if available and valid"""
        cache_key = self._generate_cache_key(command, args, kwargs)
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        if not cache_file.exists():
            return None
        
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Check if cache is still valid
            if self._is_cache_valid(cached_data):
                return cached_data['result']
            else:
                # Remove expired cache
                cache_file.unlink()
                return None
                
        except Exception:
            # Remove corrupted cache
            cache_file.unlink()
            return None
    
    def set(self, command, result, args=None, kwargs=None, ttl=None):
        """Cache command result"""
        cache_key = self._generate_cache_key(command, args, kwargs)
        cache_file = self.cache_dir / f"{cache_key}.cache"
        
        cached_data = {
            'result': result,
            'timestamp': datetime.utcnow(),
            'ttl': ttl or self.default_ttl,
            'command': command,
            'args': args,
            'kwargs': kwargs
        }
        
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception as e:
            print(f"Failed to cache result: {e}")
    
    def _generate_cache_key(self, command, args, kwargs):
        """Generate unique cache key"""
        content = f"{command}_{str(args)}_{str(kwargs)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _is_cache_valid(self, cached_data):
        """Check if cached data is still valid"""
        timestamp = cached_data.get('timestamp')
        ttl = cached_data.get('ttl', self.default_ttl)
        
        if not timestamp:
            return False
        
        expiry_time = timestamp + ttl
        return datetime.utcnow() < expiry_time
    
    def clear_expired(self):
        """Remove all expired cache entries"""
        removed_count = 0
        
        for cache_file in self.cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                if not self._is_cache_valid(cached_data):
                    cache_file.unlink()
                    removed_count += 1
                    
            except Exception:
                # Remove corrupted files
                cache_file.unlink()
                removed_count += 1
        
        return removed_count
    
    def clear_all(self):
        """Remove all cache entries"""
        removed_count = 0
        for cache_file in self.cache_dir.glob("*.cache"):
            cache_file.unlink()
            removed_count += 1
        return removed_count

# Cache decorator
cache = CommandCache()

def cached_command(ttl_hours=24):
    """Decorator to cache command results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_result = cache.get(func.__name__, args, kwargs)
            if cached_result is not None:
                print(f"Using cached result for {func.__name__}")
                return cached_result
            
            # Execute command
            result = func(*args, **kwargs)
            
            # Cache result
            ttl = timedelta(hours=ttl_hours)
            cache.set(func.__name__, result, args, kwargs, ttl)
            
            return result
        return wrapper
    return decorator

# Usage examples
@cached_command(ttl_hours=1)
def expensive_analysis_command(codebase_path):
    # This command result will be cached for 1 hour
    return analyze_codebase(codebase_path)

@cached_command(ttl_hours=24)
def dependency_scan_command():
    # This command result will be cached for 24 hours
    return scan_dependencies()
```

### Quality Assurance

#### 🔍 Code Quality Gates
```python
# .claude/quality/quality-gates.py

from dataclasses import dataclass
from typing import List, Dict, Any
from enum import Enum

class QualityLevel(Enum):
    BLOCKING = "blocking"      # Must pass to proceed
    WARNING = "warning"        # Should address but not blocking
    INFO = "info"             # Informational only

@dataclass
class QualityCheck:
    name: str
    level: QualityLevel
    threshold: float
    message: str
    fix_suggestion: str = ""

class QualityGateEngine:
    def __init__(self):
        self.checks = []
        self.results = {}
    
    def register_check(self, check: QualityCheck):
        """Register a quality check"""
        self.checks.append(check)
    
    def run_all_checks(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run all registered quality checks"""
        results = {
            "passed": [],
            "warnings": [],
            "failures": [],
            "overall_status": "PASSED"
        }
        
        for check in self.checks:
            try:
                check_result = self._run_check(check, context)
                
                if check_result["passed"]:
                    results["passed"].append(check_result)
                elif check.level == QualityLevel.BLOCKING:
                    results["failures"].append(check_result)
                    results["overall_status"] = "FAILED"
                else:
                    results["warnings"].append(check_result)
                    if results["overall_status"] == "PASSED":
                        results["overall_status"] = "WARNING"
                        
            except Exception as e:
                error_result = {
                    "check": check.name,
                    "passed": False,
                    "error": str(e),
                    "level": check.level.value
                }
                results["failures"].append(error_result)
                results["overall_status"] = "FAILED"
        
        return results
    
    def _run_check(self, check: QualityCheck, context: Dict[str, Any]) -> Dict[str, Any]:
        """Run individual quality check"""
        # This would be implemented based on check type
        if check.name == "test_coverage":
            return self._check_test_coverage(check, context)
        elif check.name == "code_complexity":
            return self._check_code_complexity(check, context)
        elif check.name == "security_scan":
            return self._check_security(check, context)
        elif check.name == "performance_budget":
            return self._check_performance_budget(check, context)
        else:
            raise NotImplementedError(f"Check {check.name} not implemented")
    
    def _check_test_coverage(self, check: QualityCheck, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check test coverage meets threshold"""
        coverage_file = Path("./coverage/coverage-summary.json")
        
        if not coverage_file.exists():
            return {
                "check": check.name,
                "passed": False,
                "message": "Coverage report not found",
                "level": check.level.value
            }
        
        with open(coverage_file) as f:
            coverage_data = json.load(f)
        
        total_coverage = coverage_data["total"]["lines"]["pct"]
        passed = total_coverage >= check.threshold
        
        return {
            "check": check.name,
            "passed": passed,
            "value": total_coverage,
            "threshold": check.threshold,
            "message": f"Coverage: {total_coverage}% (threshold: {check.threshold}%)",
            "level": check.level.value,
            "fix_suggestion": check.fix_suggestion if not passed else ""
        }
    
    def _check_code_complexity(self, check: QualityCheck, context: Dict[str, Any]) -> Dict[str, Any]:
        """Check code complexity metrics"""
        # Run complexity analysis tool
        result = subprocess.run(
            ['radon', 'cc', '.', '--json'],
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return {
                "check": check.name,
                "passed": False,
                "message": "Failed to run complexity analysis",
                "level": check.level.value
            }
        
        complexity_data = json.loads(result.stdout)
        high_complexity_count = 0
        
        for file_path, functions in complexity_data.items():
            for func in functions:
                if func.get('complexity', 0) > check.threshold:
                    high_complexity_count += 1
        
        passed = high_complexity_count == 0
        
        return {
            "check": check.name,
            "passed": passed,
            "value": high_complexity_count,
            "threshold": 0,
            "message": f"High complexity functions: {high_complexity_count}",
            "level": check.level.value,
            "fix_suggestion": check.fix_suggestion if not passed else ""
        }

# Quality gate configuration
def setup_quality_gates():
    """Setup standard quality gates"""
    gate = QualityGateEngine()
    
    # Test coverage check
    gate.register_check(QualityCheck(
        name="test_coverage",
        level=QualityLevel.BLOCKING,
        threshold=80.0,
        message="Test coverage must be >= 80%",
        fix_suggestion="Add unit tests for uncovered code paths"
    ))
    
    # Code complexity check
    gate.register_check(QualityCheck(
        name="code_complexity",
        level=QualityLevel.WARNING,
        threshold=10.0,
        message="Functions should have complexity <= 10",
        fix_suggestion="Refactor complex functions into smaller pieces"
    ))
    
    # Security scan check
    gate.register_check(QualityCheck(
        name="security_scan",
        level=QualityLevel.BLOCKING,
        threshold=0.0,
        message="No high-severity security vulnerabilities allowed",
        fix_suggestion="Update dependencies or fix security issues"
    ))
    
    return gate

# Integration with commands
def run_quality_gate():
    """Run all quality checks"""
    gate = setup_quality_gates()
    context = {
        "project_root": Path.cwd(),
        "environment": os.getenv("NODE_ENV", "development")
    }
    
    results = gate.run_all_checks(context)
    
    # Print results
    print(f"Quality Gate Status: {results['overall_status']}")
    
    if results["passed"]:
        print(f"✅ Passed checks: {len(results['passed'])}")
    
    if results["warnings"]:
        print(f"⚠️ Warning checks: {len(results['warnings'])}")
        for warning in results["warnings"]:
            print(f"  - {warning['message']}")
    
    if results["failures"]:
        print(f"❌ Failed checks: {len(results['failures'])}")
        for failure in results["failures"]:
            print(f"  - {failure['message']}")
            if failure.get("fix_suggestion"):
                print(f"    💡 {failure['fix_suggestion']}")
    
    return results["overall_status"] != "FAILED"
```

---

## 🔧 Troubleshooting

### Problemas Comuns e Soluções

#### 🚨 Contexto Não Carrega
```markdown
## Problema: CLAUDE.md não está sendo reconhecido

### Diagnóstico
```bash
# Verificar localização do arquivo
find . -name "CLAUDE.md" -type f

# Verificar permissões
ls -la CLAUDE.md

# Verificar sintaxe do arquivo
head -20 CLAUDE.md
```

### Soluções
1. **Nome do Arquivo**: Deve ser exatamente `CLAUDE.md` (case-sensitive)
2. **Localização**: Colocar no diretório raiz do projeto ou onde Claude está sendo executado
3. **Permissões**: Garantir que o arquivo tem permissões de leitura
4. **Encoding**: Usar UTF-8 encoding
5. **Sintaxe**: Verificar se é Markdown válido
```

#### ⚡ Performance Lenta
```markdown
## Problema: Claude Code executando lentamente

### Diagnóstico
```bash
# Verificar tamanho do contexto
find . -name "*.py" -o -name "*.js" -o -name "*.ts" | wc -l

# Verificar arquivos grandes
find . -size +1M -name "*.py" -o -name "*.js" -o -name "*.ts"

# Verificar diretórios desnecessários
du -sh node_modules/ .git/ __pycache__/ 2>/dev/null || true
```

### Soluções
1. **Limitar Contexto**: Usar `/clear` regularmente
2. **Otimizar Arquivos**: Excluir arquivos desnecessários do contexto
3. **Compact Session**: Usar `/compact` para comprimir histórico
4. **Gitignore**: Garantir que `.gitignore` exclui arquivos grandes
```

#### 🔄 Subagents Não Funcionam
```markdown
## Problema: Subagents não sendo invocados automaticamente

### Diagnóstico
```bash
# Verificar estrutura de diretórios
ls -la .claude/agents/

# Verificar formato dos arquivos
head -10 .claude/agents/backend-developer.md

# Verificar logs de debug
tail -f ~/.claude/logs/debug.log
```

### Soluções
1. **Estrutura Correta**: Verificar se arquivos estão em `.claude/agents/`
2. **Formato Markdown**: Garantir que arquivos são Markdown válidos
3. **Metadata**: Incluir metadata necessária (name, description, tools)
4. **Activation Patterns**: Definir patterns claros para auto-invocação
5. **Permissions**: Verificar se Claude tem permissão para ler os arquivos
```

#### 🚫 Comandos Personalizados Não Executam
```markdown
## Problema: Slash commands customizados não funcionam

### Diagnóstico
```bash
# Verificar estrutura de comandos
ls -la .claude/commands/

# Listar comandos disponíveis
claude /help

# Verificar sintaxe do comando
cat .claude/commands/my-command.md
```

### Soluções
1. **Localização**: Comandos devem estar em `.claude/commands/`
2. **Nome do Arquivo**: Nome do arquivo = nome do comando (sem .md)
3. **Sintaxe**: Arquivo deve ser Markdown válido
4. **Permissões**: Verificar permissões de leitura
5. **Namespace**: Usar namespace correto (`/project:command`)
```

### Debug e Diagnóstico

#### 🔍 Debug Mode
```python
# .claude/debug/debug-tools.py

import logging
import json
from datetime import datetime
from pathlib import Path

class DebugManager:
    def __init__(self, debug_level="INFO"):
        self.debug_dir = Path(".claude/debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, debug_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.debug_dir / "debug.log"),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger("claude-code")
    
    def log_context_loading(self, files_loaded, errors):
        """Log context loading information"""
        self.logger.info(f"Loaded {len(files_loaded)} files into context")
        
        if errors:
            self.logger.warning(f"Failed to load {len(errors)} files:")
            for error in errors:
                self.logger.warning(f"  - {error}")
    
    def log_command_execution(self, command, duration, success):
        """Log command execution details"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(f"Command '{command}' {status} in {duration:.2f}s")
    
    def log_subagent_selection(self, task, selected_agent, reason):
        """Log subagent selection process"""
        self.logger.info(f"Selected '{selected_agent}' for task '{task}' - Reason: {reason}")
    
    def generate_debug_report(self):
        """Generate comprehensive debug report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "system_info": self._get_system_info(),
            "project_info": self._get_project_info(),
            "context_info": self._get_context_info(),
            "performance_info": self._get_performance_info()
        }
        
        report_file = self.debug_dir / f"debug-report-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        self.logger.info(f"Debug report generated: {report_file}")
        return report_file
    
    def _get_system_info(self):
        """Get system information"""
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_free": psutil.disk_usage('.').free
        }
    
    def _get_project_info(self):
        """Get project information"""
        info = {
            "project_root": str(Path.cwd().absolute()),
            "claude_md_exists": Path("CLAUDE.md").exists(),
            "agents_dir_exists": Path(".claude/agents").exists(),
            "commands_dir_exists": Path(".claude/commands").exists()
        }
        
        # Count files by type
        file_counts = {}
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.json']:
            count = len(list(Path('.').rglob(f'*{ext}')))
            if count > 0:
                file_counts[ext] = count
        
        info["file_counts"] = file_counts
        return info
    
    def _get_context_info(self):
        """Get context information"""
        context_info = {
            "active_files": 0,
            "total_size": 0,
            "large_files": []
        }
        
        # Analyze context files (mock implementation)
        for file_path in Path('.').rglob('*.py'):
            if file_path.stat().st_size > 50000:  # 50KB
                context_info["large_files"].append({
                    "path": str(file_path),
                    "size": file_path.stat().st_size
                })
        
        return context_info
    
    def _get_performance_info(self):
        """Get performance information"""
        import psutil
        
        return {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_io": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else {}
        }

# Usage
debug = DebugManager(debug_level="DEBUG")

def debug_command_execution(func):
    """Decorator for debugging command execution"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        command_name = func.__name__
        
        debug.logger.debug(f"Starting command: {command_name}")
        debug.logger.debug(f"Args: {args}")
        debug.logger.debug(f"Kwargs: {kwargs}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            debug.log_command_execution(command_name, duration, True)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            debug.log_command_execution(command_name, duration, False)
            debug.logger.error(f"Command failed: {e}")
            raise e
    
    return wrapper

@debug_command_execution
def sample_command():
    # Command implementation
    pass
```

#### 📊 Health Check System
```python
# .claude/debug/health-check.py

class ClaudeHealthChecker:
    def __init__(self):
        self.checks = []
    
    def run_health_check(self):
        """Run comprehensive health check"""
        results = {
            "overall_status": "HEALTHY",
            "checks": [],
            "recommendations": []
        }
        
        # Check 1: Configuration files
        config_check = self._check_configuration()
        results["checks"].append(config_check)
        if not config_check["passed"]:
            results["overall_status"] = "WARNING"
        
        # Check 2: Directory structure
        structure_check = self._check_directory_structure()
        results["checks"].append(structure_check)
        if not structure_check["passed"]:
            results["overall_status"] = "WARNING"
        
        # Check 3: File permissions
        permissions_check = self._check_permissions()
        results["checks"].append(permissions_check)
        if not permissions_check["passed"]:
            results["overall_status"] = "ERROR"
        
        # Check 4: Context size
        context_check = self._check_context_size()
        results["checks"].append(context_check)
        if not context_check["passed"]:
            results["recommendations"].append("Consider reducing context size for better performance")
        
        # Check 5: Subagents configuration
        subagents_check = self._check_subagents()
        results["checks"].append(subagents_check)
        
        return results
    
    def _check_configuration(self):
        """Check if CLAUDE.md exists and is valid"""
        claude_md_path = Path("CLAUDE.md")
        
        if not claude_md_path.exists():
            return {
                "name": "CLAUDE.md Configuration",
                "passed": False,
                "message": "CLAUDE.md file not found",
                "recommendation": "Create CLAUDE.md file with project information"
            }
        
        try:
            content = claude_md_path.read_text(encoding='utf-8')
            if len(content.strip()) < 50:
                return {
                    "name": "CLAUDE.md Configuration", 
                    "passed": False,
                    "message": "CLAUDE.md file is too short",
                    "recommendation": "Add more detailed project information to CLAUDE.md"
                }
        except Exception as e:
            return {
                "name": "CLAUDE.md Configuration",
                "passed": False,
                "message": f"Error reading CLAUDE.md: {e}",
                "recommendation": "Fix CLAUDE.md file encoding or syntax"
            }
        
        return {
            "name": "CLAUDE.md Configuration",
            "passed": True,
            "message": "CLAUDE.md file is properly configured"
        }
    
    def _check_directory_structure(self):
        """Check if directory structure is correct"""
        required_dirs = [".claude", ".claude/agents", ".claude/commands"]
        missing_dirs = []
        
        for dir_path in required_dirs:
            if not Path(dir_path).exists():
                missing_dirs.append(dir_path)
        
        if missing_dirs:
            return {
                "name": "Directory Structure",
                "passed": False,
                "message": f"Missing directories: {', '.join(missing_dirs)}",
                "recommendation": f"Create missing directories: {', '.join(missing_dirs)}"
            }
        
        return {
            "name": "Directory Structure",
            "passed": True,
            "message": "All required directories exist"
        }
    
    def _check_permissions(self):
        """Check file permissions"""
        files_to_check = ["CLAUDE.md"]
        
        # Add agent files
        agents_dir = Path(".claude/agents")
        if agents_dir.exists():
            files_to_check.extend([str(f) for f in agents_dir.glob("*.md")])
        
        # Add command files
        commands_dir = Path(".claude/commands")
        if commands_dir.exists():
            files_to_check.extend([str(f) for f in commands_dir.glob("*.md")])
        
        permission_issues = []
        
        for file_path in files_to_check:
            path = Path(file_path)
            if path.exists() and not os.access(path, os.R_OK):
                permission_issues.append(file_path)
        
        if permission_issues:
            return {
                "name": "File Permissions",
                "passed": False,
                "message": f"Cannot read files: {', '.join(permission_issues)}",
                "recommendation": "Fix file permissions with chmod +r"
            }
        
        return {
            "name": "File Permissions",
            "passed": True,
            "message": "All files are readable"
        }
    
    def _check_context_size(self):
        """Check if context size is reasonable"""
        total_size = 0
        file_count = 0
        
        for ext in ['.py', '.js', '.ts', '.jsx', '.tsx', '.md']:
            for file_path in Path('.').rglob(f'*{ext}'):
                if not any(ignore in str(file_path) for ignore in ['node_modules', '.git', '__pycache__']):
                    total_size += file_path.stat().st_size
                    file_count += 1
        
        # Convert to MB
        size_mb = total_size / (1024 * 1024)
        
        if size_mb > 100:  # 100MB threshold
            return {
                "name": "Context Size",
                "passed": False,
                "message": f"Large context size: {size_mb:.1f}MB ({file_count} files)",
                "recommendation": "Consider using .gitignore or context optimization"
            }
        
        return {
            "name": "Context Size", 
            "passed": True,
            "message": f"Context size OK: {size_mb:.1f}MB ({file_count} files)"
        }
    
    def _check_subagents(self):
        """Check subagents configuration"""
        agents_dir = Path(".claude/agents")
        
        if not agents_dir.exists():
            return {
                "name": "Subagents Configuration",
                "passed": True,
                "message": "No subagents configured (optional)"
            }
        
        agent_files = list(agents_dir.glob("*.md"))
        
        if not agent_files:
            return {
                "name": "Subagents Configuration",
                "passed": True,
                "message": "Subagents directory exists but no agents configured"
            }
        
        valid_agents = 0
        for agent_file in agent_files:
            try:
                content = agent_file.read_text(encoding='utf-8')
                if "name:" in content or "# " in content:
                    valid_agents += 1
            except Exception:
                continue
        
        return {
            "name": "Subagents Configuration",
            "passed": True,
            "message": f"{valid_agents} subagents configured"
        }

# Usage
def run_health_check():
    """Run and display health check results"""
    checker = ClaudeHealthChecker()
    results = checker.run_health_check()
    
    print(f"🏥 Claude Code Health Check - Status: {results['overall_status']}")
    print("=" * 50)
    
    for check in results["checks"]:
        status_icon = "✅" if check["passed"] else "❌"
        print(f"{status_icon} {check['name']}: {check['message']}")
        
        if not check["passed"] and "recommendation" in check:
            print(f"   💡 {check['recommendation']}")
    
    if results["recommendations"]:
        print("\n📋 Additional Recommendations:")
        for rec in results["recommendations"]:
            print(f"   • {rec}")
    
    return results["overall_status"] == "HEALTHY"

# Add as slash command
def health_command():
    """Health check slash command"""
    return run_health_check()
```

Esta documentação fornece uma base sólida e abrangente sobre o Claude Code, cobrindo todos os aspectos essenciais para construir nossa fábrica de subagents. Agora vamos prosseguir com a documentação das demais seções e depois criar o plano final da fábrica.