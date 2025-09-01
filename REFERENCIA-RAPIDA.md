# 🚀 Claude Code - Referência Rápida

## 📋 Comandos Essenciais

### Comandos Built-in
```bash
/help                    # Lista todos os comandos
/clear                   # Limpa contexto atual
/compact                 # Comprime histórico da sessão
/init                    # Cria CLAUDE.md inicial
/add-dir <path>         # Adiciona diretório ao contexto
/exit                   # Sair do Claude Code
```

### Estrutura de Arquivos
```
projeto/
├── CLAUDE.md                    # Configuração principal
├── .claude/
│   ├── agents/                  # Subagents personalizados
│   │   ├── backend-dev.md
│   │   ├── frontend-dev.md
│   │   └── security-audit.md
│   ├── commands/               # Comandos personalizados
│   │   ├── review.md
│   │   ├── deploy.md
│   │   └── test-all.md
│   └── logs/                   # Logs e debug
```

## 🤖 Subagents - Quick Setup

### Template Básico de Subagent
```markdown
# Nome do Subagent

## Description
Breve descrição do propósito e capacidades.
**AUTO-TRIGGERS**: quando é invocado automaticamente
**USE FOR**: casos de uso específicos

## System Prompt
Você é um especialista em [domínio]...

## Tools
- bash
- read
- write
- edit
- grep

## Activation Patterns
- Palavras-chave: api, backend, frontend
- Arquivos: **/*.py, **/*.js
- Tasks: code_review, testing, deployment
```

### Subagents Essenciais
```bash
backend-developer      # APIs, databases, server logic
frontend-developer     # UI, components, client-side
devops-engineer        # Deploy, CI/CD, infrastructure  
security-auditor       # Security scans, vulnerabilities
code-reviewer          # Code quality, standards
test-engineer          # Testing, QA, automation
```

## 📄 CLAUDE.md Template

### Estrutura Básica
```markdown
# Projeto [Nome]

## Comandos Build
- npm run build: Compila projeto
- npm test: Executa testes
- npm run dev: Servidor desenvolvimento

## Estilo de Código
- Prettier + ESLint
- TypeScript obrigatório
- 2 espaços de indentação

## Workflow
- Branches: feature/nome-da-feature
- PRs requerem 1+ reviews
- CI/CD via GitHub Actions

## Estrutura de Arquivos
- src/: Código fonte
- tests/: Testes automatizados
- docs/: Documentação

## Setup Desenvolvimento
- Node.js >= 18
- npm install
- cp .env.example .env.local
```

## ⚡ Slash Commands Personalizados

### Criar Comando Personalizado
```bash
# 1. Criar diretório
mkdir -p .claude/commands

# 2. Criar arquivo comando
echo "Conteúdo do comando..." > .claude/commands/meu-comando.md

# 3. Usar comando
/meu-comando
```

### Template de Comando
```markdown
# Meu Comando Personalizado

Execute as seguintes ações:

1. **Preparação**
   - Verificar dependências
   - Validar ambiente

2. **Execução** 
   - Executar testes
   - Gerar relatório

3. **Finalização**
   - Cleanup temporários
   - Notificar conclusão

## Argumentos
Use $ARGUMENTS para parâmetros dinâmicos.

## Saída Esperada
- ✅ Successo: Relatório completo
- ❌ Erro: Mensagem de erro e sugestões
```

## 🔧 Troubleshooting Rápido

### CLAUDE.md não funciona
```bash
# Verificar arquivo existe
ls -la CLAUDE.md

# Verificar permissões  
chmod +r CLAUDE.md

# Verificar conteúdo
head -10 CLAUDE.md
```

### Subagents não ativam
```bash
# Verificar estrutura
ls -la .claude/agents/

# Verificar formato
head -5 .claude/agents/*.md

# Forçar uso manual
claude "usar subagent backend-developer para analisar API"
```

### Performance lenta
```bash
# Limpar contexto
/clear

# Comprimir sessão
/compact

# Verificar arquivos grandes
find . -size +1M -not -path "./node_modules/*" -not -path "./.git/*"
```

## 🎯 Workflows Comuns

### Code Review Completo
```bash
/review      # Se comando customizado existe
# ou manualmente:
claude "revisar código seguindo padrões do CLAUDE.md"
```

### Deploy Seguro
```bash
/security-scan    # Verificar vulnerabilidades
/test-all        # Executar todos os testes
/deploy staging  # Deploy para staging
/deploy prod     # Deploy para produção
```

### Setup Novo Projeto
```bash
/init                    # Criar CLAUDE.md inicial
mkdir -p .claude/{agents,commands}
# Copiar templates de subagents
# Configurar comandos personalizados
```

## 📊 Best Practices

### Performance
- Use `/clear` regularmente
- Mantenha CLAUDE.md conciso e atualizado
- Exclua arquivos desnecessários do contexto

### Segurança
- Não inclua secrets em CLAUDE.md
- Use variáveis de ambiente para credenciais
- Configure permissões mínimas para subagents

### Qualidade
- Mantenha subagents focados em domínios específicos
- Use quality gates antes de deploys
- Versionne configurações no git

## 🔗 Links Úteis

- **Documentação Oficial**: https://docs.anthropic.com/claude-code
- **Repositório de Examples**: https://github.com/anthropics/claude-code-examples
- **Community**: https://discord.gg/claude-code

---

## 📱 Cheat Sheet

### Atalhos Essenciais
- `Ctrl+C`: Interromper operação
- `/help`: Ver comandos
- `/clear`: Limpar contexto
- `↑/↓`: Navegar histórico

### Estados de Subagents
- **pending**: Aguardando execução
- **in_progress**: Em execução
- **completed**: Concluído
- **failed**: Falhou

### Níveis de Quality Gates
- **BLOCKING**: Deve passar para prosseguir
- **WARNING**: Deve ser endereçado
- **INFO**: Apenas informativo