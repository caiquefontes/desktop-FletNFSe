# Documentação da Estrutura de Arquivos - NFSeFlet

Este documento descreve a estrutura de arquivos e diretórios do projeto NFSeFlet, detalhando o propósito de cada componente.

## Estrutura de Diretórios

```
NFSeFlet/
├── apps/                          # Miniaplicações modulares
│   ├── ordens/                    # Módulo de vínculo NFSe x Pedidos
│   │   └── app.py
│   ├── pwNFSe/                    # Módulo de automação e download de NFSe
│   │   ├── app.py
│   │   └── utils.py
│   └── sapNFSe/                   # Módulo de validação e lançamento SAP
│       └── app.py
├── files/                         # Diretório de armazenamento de arquivos
│   ├── nfse_accept/               # NFSe aceitas/aprovadas
│   ├── nfse_download/             # NFSe baixadas
│   └── nfse_reject/               # NFSe rejeitadas
├── main/                          # Aplicação principal
│   ├── main.py                    # Shell da aplicação com NavigationRail
│   └── components/                # Componentes reutilizáveis da UI
├── model/                         # Camada de dados e modelos
│   ├── models.py                  # Modelos Peewee ORM (NFSe, PedidoCompra, SapLancamento)
│   └── utils/
│       └── data_blk.py            # Utilitários de processamento de dados
├── setup/                         # Configurações do sistema
│   └── settings.py                # Configurações gerais da aplicação
├── tests/                         # Testes automatizados
│   └── test_structure.py          # Testes de estrutura
├── trash/                         # Arquivos obsoletos/backup
│   ├── erro_login.png             # Screenshot de erro de login
│   ├── erro_nfse_debug.png        # Screenshot de debug NFSe
│   ├── main.py                    # Versão antiga do main
│   ├── models_old.py              # Versão antiga dos modelos
│   └── model/                     # Backup de estrutura antiga
└── [arquivos raiz]                # Arquivos na raiz do projeto
```

## Arquivos da Raiz do Projeto

| Arquivo | Descrição |
|---------|-----------|
| `anexoiv-leiautesrn_adn-snnfse_v1-00-02-producao.xlsx` | Leiaute oficial do Anexo IV - Schema de NFSe (versão produção) |
| `nfse.db` | Banco de dados SQLite com dados da aplicação |
| `README.md` | Documentação principal do projeto |
| `requirements.txt` | Dependências Python do projeto |
| `ToDo.md` | Lista de tarefas e melhorias planejadas |

## Descrição dos Módulos

### 1. apps/ - Miniaplicações

Cada subdiretório representa uma funcionalidade independente do sistema:

#### apps/ordens/
- **Propósito**: Gerenciar vínculo entre Notas Fiscais de Serviço e Pedidos de Compra
- **Arquivo principal**: `app.py` - Interface Flet com funcionalidades de busca, associação e consulta

#### apps/pwNFSe/
- **Propósito**: Automação de download de NFSe via certificado digital e parsing de XML
- **Arquivos**:
  - `app.py` - Interface para autenticação e download
  - `utils.py` - Funções auxiliares para parsing XML e extração de dados

#### apps/sapNFSe/
- **Propósito**: Validação de dados e lançamento de NFSe no sistema SAP
- **Arquivo principal**: `app.py` - Interface de validação e integração com SAP

### 2. files/ - Diretório de Dados

Diretório para armazenamento organizado de arquivos XML e PDFs de NFSe:

- **nfse_accept/**: Armazena NFSe que foram validadas e aprovadas
- **nfse_download/**: Armazena NFSe baixadas da prefeitura/webservice
- **nfse_reject/**: Armazena NFSe que apresentaram erros ou foram rejeitadas

### 3. main/ - Aplicação Principal

- **main.py**: Ponto de entrada da aplicação. Contém o shell principal com NavigationRail para navegação entre os módulos (pwNFSe, ordens, sapNFSe)
- **components/**: Componentes de interface reutilizáveis (botões, formulários, tabelas customizadas)

### 4. model/ - Camada de Dados

- **models.py**: Definição dos modelos do banco de dados usando Peewee ORM
  - `NFSe`: Dados da nota fiscal de serviço
  - `PedidoCompra`: Dados de pedidos de compra
  - `SapLancamento`: Registros de lançamento no SAP
  
- **utils/data_blk.py**: Utilitários para processamento e transformação de dados em blocos (bulk operations)

### 5. setup/ - Configurações

- **settings.py**: Arquivo centralizado de configurações (caminhos, credenciais, parâmetros de integração)

### 6. tests/ - Testes

- **test_structure.py**: Testes automatizados para validação da estrutura do projeto

### 7. trash/ - Arquivos Obsoletos

Diretório para backup de versões antigas e arquivos de debug:
- Screenshots de erros para documentação de bugs
- Versões antigas de código (main.py, models_old.py)
- Estrutura de diretórios antiga preservada para referência

## Dependências do Projeto

```
flet==0.85.0          # Framework de interface gráfica
peewee==4.0.5         # ORM para banco de dados
selenium==4.43.0      # Automação de browser (futuro)
```

## Fluxo de Dados

```
[Webservice Prefeitura] 
    ↓ (download via pwNFSe)
files/nfse_download/
    ↓ (parser XML)
model/models.py (banco de dados)
    ↓ (validação)
apps/ordens/ (vínculo com pedidos)
    ↓ (validação SAP)
apps/sapNFSe/ (lançamento)
files/nfse_accept/ ou files/nfse_reject/
```

## Convenções do Projeto

- Cada miniapp em `apps/` é independente e autocontido
- Interfaces seguem padrão Flet com NavigationRail
- Banco de dados centralizado em `model/models.py`
- Utilitários compartilhados em `model/utils/`
- Arquivos de configuração centralizados em `setup/`

## Como Navegar

1. **Para entender a UI**: Comece por `main/main.py` e depois explore `apps/*/app.py`
2. **Para entender os dados**: Consulte `model/models.py` e `setup/settings.py`
3. **Para entender integrações**: Veja `apps/pwNFSe/utils.py` e `apps/sapNFSe/app.py`
4. **Para executar**: Consulte o README.md principal

---

**Última atualização**: Junho/2026
**Versão**: 1.0