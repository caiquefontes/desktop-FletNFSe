# To Do Project
## Desenvolvimento: NFSeDigital

🏗️ 0. Base do Projeto & Infraestrutura
    [X] Configurar ambiente virtual (venv) e instalar dependências (flet, peewee, selenium/playwright).
    [X] Criar estrutura de pastas por miniapps (pacotes Python).
    [X] Desenvolver a Main Shell em Flet (Sidebar/Tabs para navegação entre apps).
    [ ] Configurar arquivo models.py centralizado para o Banco de Dados (Peewee).
        [] Tabelas de Dimesoes e suas funções
        [] Tabela Fato e suas Funções 

🌐 1. App: pwNFSe (Automação & Download)
    [X] Implementar lógica de autenticação com Certificado Digital.
    [X] Criar script de navegação para o portal da prefeitura/receita.
    [X] Desenvolver rotina de download e armazenamento temporário dos arquivos .xml.
    [X] Interface Flet: Botão "Iniciar Captura" e log de progresso em tempo real.
    [ ] Gerenciamento de Arquivos - Visualização Lista com CheckBox
        [ ] Visualizar, Baixar, Arquivar
        [ ] Processar Dados Para Banco de Dados
        [ ] Criar parser para extrair tags XML (CNPJ, Valor, Data, Itens, Chave de Acesso).
        [ ] Mapear campos do XML para as classes de Model do Peewee.
        [ ] Implementar lógica de "Upsert" (evitar duplicidade de notas no banco).
        [ ] Interface Flet: Tabela de visualização das notas importadas com filtros de data/status.

🛒 2. App: ordens (Vínculo de Compras)
    [ ] Criar funcionalidade de importação de Pedidos de Compra (CSV/Excel ou manual).
    [ ] Desenvolver algoritmo de sugestão de vínculo (Match por valor ou fornecedor).
    [ ] Implementar função para salvar o ID_Pedido na tabela da dataNFSe.
    [ ] Interface Flet: Tela de "Conciliação" (Lado A: Nota / Lado B: Pedido).

🚀 3. App: sapNFSe (Validação & Lançamento)
    [ ] Criar lógica de validação de dados antes do envio ao SAP.
    [ ] Implementar rotina de integração (via API, RFC ou automação de interface).
    [ ] Gerar logs de sucesso/erro para cada ID lançado.
    [ ] Interface Flet: Dashboard com "Pendentes de Lançamento" e botão "Lançar no SAP".

🧪 4. Testes & Refinamento
    [ ] Validar conexões do banco de dados com peewee.
    [ ] Testar responsividade da UI Flet com base nos exemplos do gallerydata.py.
    [ ] Criar tratamento de erros para certificados expirados ou portais fora do ar.