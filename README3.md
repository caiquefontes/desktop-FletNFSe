# NFSeFlet - Sistema de Gestão de Notas Fiscais

## Tecnologias:
	Linguagem = Python
	ORM (Banco de Dados) = peewee
	FrontEnd (Tela) = PythonFlet
	Links Uteis:
		https://docs.peewee-orm.com/en/latest/index.html
		https://github.com/flet-dev/examples/blob/main/python/apps/controls-gallery/gallerydata.py
		https://flet.dev/docs/

## Estrutura do Projeto

O projeto está organizado em miniapps conforme especificado no README inicial:

1. **pwNFSe** - Automação e download de NFSe via certificado digital e Parser de XML e armazenamento no banco de dados
2. **ordens** - Vínculo entre notas fiscais e pedidos de compra
3. **sapNFSe** - Validação e lançamento no SAP

## Componentes Implementados

### 1. Banco de Dados (`models.py`)
- Modelo centralizado usando Peewee ORM
- Tabelas: NFSe, PedidoCompra, SapLancamento
- Função de inicialização automática do banco

### 2. Miniapps
Cada miniapp contém:
- Interface Flet completa com barra de navegação
- Funcionalidades básicas conforme especificação
- Integração com o banco de dados
- Tratamento de erros básico

### 3. Aplicação Principal (`main.py`)
- Shell da aplicação com NavigationRail para navegação entre miniapps
- Barra de aplicação com título e configurações
- Layout responsivo

## Próximos Passos Sugeridos

1. Implementar autenticação real com certificado digital no pwNFSe
2. Melhorar o parser XML para suportar diferentes estruturas de NFSe
3. Implementar integração real com SAP (API ou RFC)
4. Adicionar testes unitários e de integração
5. Melhorar a interface com mais componentes Flet avançados
6. Implementar persistência de estado entre sessões

## Tecnologias Utilizadas

- Python 3.14+
- Flet 0.85.0 (framework UI)
- Peewee 4.0.5 (ORM)
- Selenium 4.43.0 (para automação web futura)
- SQLite (banco de dados padrão)

## Como Executar

```bash
# Criar e ativar ambiente virtual (já feito)
# Instalar dependências (já feito)
venv\Scripts\pip install -r requirements.txt

# Executar a aplicação
venv\Scripts\python main\main.py
```
