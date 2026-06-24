from peewee import *
from datetime import datetime
from decimal import Decimal

# Conexão com banco de dados
db = SqliteDatabase(
    'nfse.db',
    pragmas={
        'foreign_keys': 1,          # 👈 OBRIGATÓRIO: SQLite desativa FKs por padrão
        'journal_mode': 'wal',      # Melhora performance em escritas concorrentes
        'cache_size': -64000,       # Cache de ~64MB em memória
        'synchronous': 'normal'     # Equilíbrio entre segurança e velocidade
    }
)

class BaseModel(Model):
    """Classe base para todos os models"""
    class Meta:
        database = db
        # schema = 'nfse_adn'
# ============================================================================
# TABELAS DE DOMÍNIO E PARÂMETROS (Reciclagem de dados)
# ============================================================================

class Municipio(BaseModel):
    """Tabela de municípios do IBGE - reutilizável"""
    codigo = CharField(max_length=7, unique=True, index=True)
    nome = TextField()
    uf = CharField(max_length=2, default='ZZ')
    ativo = BooleanField(default=True)
    data_atualizacao = DateField()
    
    class Meta:
        table_name = 'municipio'


class Pais(BaseModel):
    """Tabela de países ISO - reutilizável"""
    codigo = CharField(max_length=2, unique=True, primary_key=True)
    nome = TextField()
    
    class Meta:
        table_name = 'pais'


class TipoTributacaoISSQN(BaseModel):
    """Códigos de tributação nacional do ISSQN"""
    codigo = CharField(max_length=12, unique=True, index=True)
    descricao = TextField()
    ativo = BooleanField(default=True, null=True)
    # data_inicio = DateField()
    # data_fim = DateField(null=True)
    
    class Meta:
        table_name = 'tipo_tributacao_issqn'


class NBS(BaseModel):
    """Nomenclatura Brasileira de Serviços"""
    codigo = CharField(max_length=9, unique=True, index=True)
    descricao = TextField()
    
    class Meta:
        table_name = 'nbs'


class TipoEvento(BaseModel):
    """Tipos de eventos da NFS-e"""
    codigo = CharField(max_length=7, unique=True)
    descricao = TextField()
    
    class Meta:
        table_name = 'tipo_evento'


class TipoRetencao(BaseModel):
    """Tipos de retenção tributária"""
    codigo = SmallIntegerField(primary_key=True)
    descricao = TextField()
    
    class Meta:
        table_name = 'tipo_retencao'


# ============================================================================
# TABELAS DE ENDEREÇO E CONTATO (Normalização)
# ============================================================================

class EnderecoNacional(BaseModel):
    """Endereços nacionais - tabela reutilizável"""
    logradouro = TextField()
    numero = CharField(max_length=60)
    complemento = TextField(null=True)
    bairro = TextField()
    municipio = ForeignKeyField(Municipio, backref='enderecos', on_delete='CASCADE')
    cep = CharField(max_length=8)
    
    class Meta:
        table_name = 'endereco_nacional'
        indexes = (
            (('cep', 'numero'), False),
        )


class EnderecoExterior(BaseModel):
    """Endereços no exterior - tabela reutilizável"""
    pais = ForeignKeyField(Pais, backref='enderecos', on_delete='CASCADE')
    codigo_postal = CharField(max_length=11, null=True)
    cidade = TextField()
    estado_provincia_regiao = TextField()
    
    class Meta:
        table_name = 'endereco_exterior'


class Contato(BaseModel):
    """Informações de contato - tabela reutilizável"""
    telefone = CharField(max_length=20, null=True)
    email = TextField(null=True)
    
    class Meta:
        table_name = 'contato'


# ============================================================================
# TABELAS DE PARTICIPANTES (Prestador, Tomador, Intermediário, Fornecedor)
# ============================================================================

class Participante(BaseModel):
    """Tabela unificada para participantes (normalização)"""
    tipo = CharField(max_length=20)  # 'PRESTADOR', 'TOMADOR', 'INTERMEDIARIO', 'FORNECEDOR'
    cnpj = CharField(max_length=14, null=True, index=True)
    cpf = CharField(max_length=11, null=True, index=True)
    nif = CharField(max_length=40, null=True)  # Para exterior
    motivo_nao_nif = SmallIntegerField(null=True)  # 0-Não informado, 1-Dispensado, 2-Não exigência
    inscricao_municipal = CharField(max_length=15, null=True)
    razao_social = TextField()
    nome_fantasia = TextField(null=True)
    endereco_nacional = ForeignKeyField(EnderecoNacional, null=True, on_delete='CASCADE')
    endereco_exterior = ForeignKeyField(EnderecoExterior, null=True, on_delete='CASCADE')
    contato = ForeignKeyField(Contato, null=True, on_delete='CASCADE')
    
    class Meta:
        table_name = 'participante'
        indexes = (
            (('tipo', 'cnpj'), False),
            (('tipo', 'cpf'), False),
        )


# ============================================================================
# TABELA PRINCIPAL - NFS-e
# ============================================================================

class NFSe(BaseModel):
    """Tabela principal - NFS-e"""
    # Identificação
    versao = CharField(max_length=4)
    id = CharField(max_length=53, unique=True, index=True)
    numero_nfse = BigIntegerField(index=True)
    
    # Localidades
    localidade_emissora = ForeignKeyField(Municipio, null=True, related_name='nfse_emissoras', on_delete='CASCADE')
    localidade_prestacao = ForeignKeyField(Municipio, null=True, related_name='nfse_prestacoes', on_delete='CASCADE')
    localidade_incidencia = ForeignKeyField(Municipio, null=True, related_name='nfse_incidencias', on_delete='CASCADE')
    
    # Descrições das localidades
    xLocEmi = TextField(null=True)
    xLocPrestacao = TextField(null=True)
    xLocIncid = TextField(null=True)
    
    # Tributação
    tributacao_nacional = ForeignKeyField(TipoTributacaoISSQN, null=True, on_delete='CASCADE')
    tributacao_municipal = CharField(max_length=3, null=True)
    nbs = ForeignKeyField(NBS, null=True, on_delete='CASCADE')
    
    # Descrições
    xTribNac = TextField()
    xTribMun = TextField(null=True)
    xNBS = TextField(null=True)
    
    # Controle
    versao_aplicativo = CharField(max_length=20)
    ambiente_gerador = SmallIntegerField()  # 1-Município, 2-Sefin Nacional
    tipo_emissao = SmallIntegerField()  # 1-Normal, 2-Transcrição
    processo_emissao = SmallIntegerField(null=True)  # 1-App contribuinte, 2-App fisco web, 3-App fisco mobile
    
    # Status
    codigo_status = SmallIntegerField()  # 100-Gerada, 101-Substituição, 102-Judicial, 103-Avulsa
    data_processamento = DateTimeField()
    numero_dfe = BigIntegerField()
    
    # Relacionamentos
    emitente = ForeignKeyField(Participante, backref='nfse_emitidas', on_delete='CASCADE')
    
    # Controle de tempo
    criado_em = DateTimeField(default=datetime.now)
    atualizado_em = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'nfse'
        indexes = (
            (('numero_nfse', 'ambiente_gerador'), True),
            (('data_processamento',), False),
        )


# ============================================================================
# DPS - Declaração de Prestação de Serviço
# ============================================================================

class DPS(BaseModel):
    """DPS vinculada à NFS-e"""
    nfse = ForeignKeyField(NFSe, backref='dps', unique=True, on_delete='CASCADE')
    versao = CharField(max_length=4)
    id = CharField(max_length=45, unique=True)
    
    # Ambiente e Data
    tipo_ambiente = SmallIntegerField()  # 1-Produção, 2-Homologação
    data_emissao = DateTimeField()
    versao_aplicativo = CharField(max_length=20)
    
    # Numeração
    serie = CharField(max_length=5)
    numero_dps = BigIntegerField()
    data_competencia = DateField()
    
    # Tipo de emitente
    tipo_emitente = SmallIntegerField()  # 1-Prestador, 2-Tomador, 3-Intermediário
    
    # Localidade emissora
    localidade_emissora = ForeignKeyField(Municipio, null=True, on_delete='CASCADE') # null=True evita bloqueio durante testes
    
    class Meta:
        table_name = 'dps'


class DPSSubstituicao(BaseModel):
    """Informações de substituição de DPS"""
    dps = ForeignKeyField(DPS, backref='substituicao', unique=True, on_delete='CASCADE')
    chave_substituida = CharField(max_length=50)
    codigo_motivo = SmallIntegerField()
    descricao_motivo = TextField(null=True)
    
    class Meta:
        table_name = 'dps_substituicao'


# ============================================================================
# SERVIÇO
# ============================================================================

class Servico(BaseModel):
    """Serviço prestado"""
    nfse = ForeignKeyField(NFSe, backref='servicos_nfse', null=True, on_delete='CASCADE')
    dps = ForeignKeyField(DPS, backref='servicos_dps', null=True, on_delete='CASCADE')
    
    # Código do serviço
    codigo_tributacao_nacional = ForeignKeyField(TipoTributacaoISSQN, on_delete='CASCADE')
    codigo_tributacao_municipal = CharField(max_length=3, null=True)
    codigo_nbs = ForeignKeyField(NBS, null=True, on_delete='CASCADE')
    codigo_interno_contribuinte = CharField(max_length=20, null=True)
    descricao_servico = TextField()
    
    class Meta:
        table_name = 'servico'


class LocalPrestacaoServico(BaseModel):
    """Local da prestação do serviço"""
    servico = ForeignKeyField(Servico, backref='local_prestacao', unique=True, on_delete='CASCADE')
    codigo_localidade = ForeignKeyField(Municipio, on_delete='CASCADE')
    codigo_pais = ForeignKeyField(Pais, on_delete='CASCADE')
    codigo_pais_consumo = SmallIntegerField(null=True)
    
    class Meta:
        table_name = 'local_prestacao_servico'


# ============================================================================
# COMÉRCIO EXTERIOR
# ============================================================================

class ComercioExterior(BaseModel):
    """Informações de comércio exterior"""
    servico = ForeignKeyField(Servico, backref='comercio_exterior', unique=True , on_delete='CASCADE')
    modo_prestacao = SmallIntegerField()
    vinculo_prestador = SmallIntegerField()
    tipo_moeda = CharField(max_length=3)
    valor_servico_moeda = DecimalField(max_digits=15, decimal_places=2)
    mecanismo_apoio_prestador = SmallIntegerField()
    mecanismo_apoio_tomador = SmallIntegerField()
    movimentacao_temporaria_bens = SmallIntegerField()
    numero_di = CharField(max_length=12, null=True)
    numero_re = CharField(max_length=12, null=True)
    indicador_mdic = SmallIntegerField()
    
    class Meta:
        table_name = 'comercio_exterior'


# ============================================================================
# GRUPOS ESPECÍFICOS DE SERVIÇO
# ============================================================================

class LocacaoSublocacao(BaseModel):
    """Locação, sublocação, arrendamento, etc."""
    servico = ForeignKeyField(Servico, backref='locacao_sublocacao', unique=True, on_delete='CASCADE')
    categoria = SmallIntegerField()
    objeto = SmallIntegerField()
    extensao = IntegerField(null=True)
    numero_postes = IntegerField(null=True)
    
    class Meta:
        table_name = 'locacao_sublocacao'


class ObraConstrucao(BaseModel):
    """Obra de construção civil"""
    servico = ForeignKeyField(Servico, backref='obra_construcao', unique=True, on_delete='CASCADE')
    inscricao_imobiliaria_fiscal = CharField(max_length=30, null=True)
    codigo_obra = CharField(max_length=30)
    endereco = ForeignKeyField(EnderecoNacional, null=True, on_delete='CASCADE')
    
    class Meta:
        table_name = 'obra_construcao'


class AtividadeEvento(BaseModel):
    """Atividade de evento"""
    servico = ForeignKeyField(Servico, backref='atividade_evento', unique=True, on_delete='CASCADE')
    nome_evento = TextField()
    data_inicio = DateField()
    data_fim = DateField()
    identificacao_atividade = CharField(max_length=30)
    endereco = ForeignKeyField(EnderecoNacional, null=True, on_delete='CASCADE')
    
    class Meta:
        table_name = 'atividade_evento'


class ExploracaoRodovia(BaseModel):
    """Exploração de rodovia"""
    servico = ForeignKeyField(Servico, backref='exploracao_rodovia', unique=True, on_delete='CASCADE')
    categoria_veiculo = SmallIntegerField()
    numero_eixos = SmallIntegerField()
    tipo_rodagem = SmallIntegerField()
    sentido = CharField(max_length=3)
    placa_veiculo = CharField(max_length=7)
    codigo_acesso_pedagio = CharField(max_length=10)
    codigo_contrato = CharField(max_length=4)
    
    class Meta:
        table_name = 'exploracao_rodovia'


class InformacoesComplementares(BaseModel):
    """Informações complementares do serviço"""
    servico = ForeignKeyField(Servico, backref='info_complementares', unique=True, on_delete='CASCADE')
    id_documento_tecnico = CharField(max_length=40, null=True)
    documento_referencia = TextField(null=True)
    informacoes_adicionais = TextField(null=True)
    
    class Meta:
        table_name = 'informacoes_complementares'


# ============================================================================
# VALORES E TRIBUTOS
# ============================================================================

class ValoresNFSe(BaseModel):
    """Valores da NFS-e"""
    nfse = ForeignKeyField(NFSe, backref='valores', unique=True, on_delete='CASCADE')
    
    # Valores calculados
    valor_calculo_deducao_reducao = DecimalField(max_digits=15, decimal_places=2, null=True)
    tipo_beneficio_municipal = CharField(max_length=40, null=True)
    valor_calculo_beneficio_municipal = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_base_calculo = DecimalField(max_digits=15, decimal_places=2, null=True)
    aliquota_aplicada = DecimalField(max_digits=5, decimal_places=4, null=True)
    valor_issqn = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_total_retencoes = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_liquido = DecimalField(max_digits=15, decimal_places=2)
    
    # Uso da administração
    outras_informacoes = TextField(null=True)
    
    class Meta:
        table_name = 'valores_nfse'


class ValoresDPS(BaseModel):
    """Valores da DPS"""
    dps = ForeignKeyField(DPS, backref='valores', unique=True, on_delete='CASCADE')
    
    # Valores do serviço
    valor_recebido_intermediario = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_servico = DecimalField(max_digits=15, decimal_places=2)
    
    # Descontos
    valor_desconto_incondicionado = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_desconto_condicionado = DecimalField(max_digits=15, decimal_places=2, null=True)
    
    class Meta:
        table_name = 'valores_dps'


class DeducaoReducao(BaseModel):
    """Deduções/Reduções da base de cálculo"""
    valores_dps = ForeignKeyField(ValoresDPS, backref='deducoes_reducoes', on_delete='CASCADE')
    percentual_deducao_reducao = DecimalField(max_digits=5, decimal_places=4, null=True)
    valor_deducao_reducao = DecimalField(max_digits=15, decimal_places=2, null=True)
    
    class Meta:
        table_name = 'deducao_reducao'


class DocumentoDeducao(BaseModel):
    """Documentos para dedução/redução"""
    deducao_reducao = ForeignKeyField(DeducaoReducao, backref='documentos', on_delete='CASCADE')
    tipo_documento = SmallIntegerField()
    chave_nfse = CharField(max_length=50, null=True)
    chave_nfe = CharField(max_length=44, null=True)
    numero_documento_fiscal = CharField(max_length=255, null=True)
    numero_documento_nao_fiscal = CharField(max_length=255, null=True)
    data_emissao = DateField()
    valor_dedutivel_redutivel = DecimalField(max_digits=15, decimal_places=2)
    valor_utilizado_deducao = DecimalField(max_digits=15, decimal_places=2)
    descricao_outra_deducao = TextField(null=True)
    
    class Meta:
        table_name = 'documento_deducao'


class NFSeMunicipalDeducao(BaseModel):
    """NFS-e municipal para dedução"""
    documento_deducao = ForeignKeyField(DocumentoDeducao, backref='nfse_municipal', unique=True, on_delete='CASCADE')
    codigo_municipio = ForeignKeyField(Municipio)
    numero_nfse = BigIntegerField()
    codigo_verificacao = CharField(max_length=9)
    
    class Meta:
        table_name = 'nfse_municipal_deducao'


class NFNFSNaoEletronica(BaseModel):
    """NF/NFS não eletrônica para dedução"""
    documento_deducao = ForeignKeyField(DocumentoDeducao, backref='nfnfs_nao_eletronica', unique=True)
    numero_nfs = BigIntegerField()
    modelo = CharField(max_length=15)
    serie = CharField(max_length=9)
    
    class Meta:
        table_name = 'nfnfs_nao_eletronica'


# ============================================================================
# TRIBUTAÇÃO
# ============================================================================

class TributacaoMunicipal(BaseModel):
    """Tributação municipal (ISSQN)"""
    valores_dps = ForeignKeyField(ValoresDPS, backref='tributacao_municipal', unique=True)
    tipo_tributacao_issqn = SmallIntegerField()
    codigo_pais_resultado = CharField(max_length=2, null=True)
    aliquota = DecimalField(max_digits=5, decimal_places=4, null=True)
    tipo_retencao_issqn = SmallIntegerField(null=True)
    
    class Meta:
        table_name = 'tributacao_municipal'


class BeneficioMunicipal(BaseModel):
    """Benefício municipal"""
    tributacao_municipal = ForeignKeyField(TributacaoMunicipal, backref='beneficios', unique=True)
    numero_bm = BigIntegerField()
    valor_reducao_base_calculo = DecimalField(max_digits=15, decimal_places=2, null=True)
    percentual_reducao_base_calculo = DecimalField(max_digits=5, decimal_places=4, null=True)
    
    class Meta:
        table_name = 'beneficio_municipal'


class ExigibilidadeSuspensa(BaseModel):
    """Exigibilidade suspensa"""
    tributacao_municipal = ForeignKeyField(TributacaoMunicipal, backref='exigibilidade_suspensa', unique=True)
    tipo_suspensao = SmallIntegerField()
    numero_processo = CharField(max_length=30)
    
    class Meta:
        table_name = 'exigibilidade_suspensa'


class Imunidade(BaseModel):
    """Imunidade do ISSQN"""
    tributacao_municipal = ForeignKeyField(TributacaoMunicipal, backref='imunidade', unique=True)
    tipo_imunidade = SmallIntegerField()
    
    class Meta:
        table_name = 'imunidade'


class TributacaoFederal(BaseModel):
    """Tributação federal"""
    valores_dps = ForeignKeyField(ValoresDPS, backref='tributacao_federal', unique=True)
    valor_retencao_cp = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_retencao_irrf = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_retencao_csll = DecimalField(max_digits=15, decimal_places=2, null=True)
    
    class Meta:
        table_name = 'tributacao_federal'


class PISCOFINS(BaseModel):
    """PIS/COFINS"""
    tributacao_federal = ForeignKeyField(TributacaoFederal, backref='piscofins', unique=True)
    cst = SmallIntegerField()
    valor_base_calculo = DecimalField(max_digits=15, decimal_places=2, null=True)
    aliquota_pis = DecimalField(max_digits=5, decimal_places=4, null=True)
    aliquota_cofins = DecimalField(max_digits=5, decimal_places=4, null=True)
    valor_pis = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_cofins = DecimalField(max_digits=15, decimal_places=2, null=True)
    tipo_retencao = SmallIntegerField(null=True)
    
    class Meta:
        table_name = 'piscofins'


class TotaisTributos(BaseModel):
    """Totais de tributos (Lei 12.741/2012)"""
    valores_dps = ForeignKeyField(ValoresDPS, backref='totais_tributos', unique=True)
    valor_total_tributos = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_total_tributos_federais = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_total_tributos_estaduais = DecimalField(max_digits=15, decimal_places=2, null=True)
    valor_total_tributos_municipais = DecimalField(max_digits=15, decimal_places=2, null=True)
    percentual_total_tributos = DecimalField(max_digits=5, decimal_places=4, null=True)
    percentual_total_tributos_federais = DecimalField(max_digits=5, decimal_places=4, null=True)
    percentual_total_tributos_estaduais = DecimalField(max_digits=5, decimal_places=4, null=True)
    percentual_total_tributos_municipais = DecimalField(max_digits=5, decimal_places=4, null=True)
    indicador_total_tributos = SmallIntegerField(null=True)
    percentual_total_simples_nacional = DecimalField(max_digits=5, decimal_places=4, null=True)
    
    class Meta:
        table_name = 'totais_tributos'


# ============================================================================
# EVENTOS
# ============================================================================

class EventoNFSe(BaseModel):
    """Eventos da NFS-e"""
    versao = CharField(max_length=4)
    id = CharField(max_length=62, unique=True, index=True)
    versao_aplicativo = CharField(max_length=20, null=True)
    ambiente_gerador = SmallIntegerField()
    numero_sequencial_evento = SmallIntegerField()
    data_processamento = DateTimeField()
    numero_dfe = BigIntegerField()
    
    # Autor do evento
    cnpj_autor = CharField(max_length=14, null=True, index=True)
    cpf_autor = CharField(max_length=11, null=True, index=True)
    data_evento = DateTimeField()
    tipo_ambiente = SmallIntegerField()
    versao_aplicativo_evento = CharField(max_length=20)
    
    # Tipo de evento
    tipo_evento = ForeignKeyField(TipoEvento)
    nfse = ForeignKeyField(NFSe, backref='eventos')
    
    # Descrição e motivo
    descricao = TextField()
    codigo_motivo = SmallIntegerField(null=True)
    descricao_motivo = TextField(null=True)
    
    # Campos específicos
    chave_substituta = CharField(max_length=50, null=True)
    cpf_agente_tributario = CharField(max_length=11, null=True)
    numero_processo_adm = CharField(max_length=30, null=True)
    descricao_processo_adm = TextField(null=True)
    id_evento_manifestacao_rejeicao = CharField(max_length=59, null=True)
    id_bloqueio_oficio = CharField(max_length=60, null=True)
    codigo_evento_bloqueio = CharField(max_length=7, null=True)
    
    # Controle
    criado_em = DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'evento_nfse'
        indexes = (
            (('nfse', 'tipo_evento'), False),
            (('data_processamento',), False),
        )


# ============================================================================
# REGIMES DE TRIBUTAÇÃO DO PRESTADOR
# ============================================================================

class RegimeTributacaoPrestador(BaseModel):
    """Regime de tributação do prestador"""
    participante = ForeignKeyField(Participante, backref='regimes_tributacao')
    data_referencia = DateField()
    
    # Simples Nacional
    opcao_simples_nacional = SmallIntegerField()
    regime_apuracao_tributaria_sn = SmallIntegerField(null=True)
    
    # Regime especial
    regime_especial_tributacao = SmallIntegerField()
    
    class Meta:
        table_name = 'regime_tributacao_prestador'
        indexes = (
            (('participante', 'data_referencia'), True),
        )


# ============================================================================
# BANCO DE DADOS PARA CONTROLAR LANÇAMENTOS NO SAP
# ============================================================================
class SapLancamento(BaseModel):
    nfse = ForeignKeyField(NFSe, backref='lancamentos_sap')  # Linked NFSe
    numero_documento_sap = CharField(max_length=50)  # SAP document number
    data_lancamento = DateField()
    valor_lancado = DecimalField(max_digits=15, decimal_places=2)
    usuario_lancamento = CharField(max_length=100)
    status = CharField(max_length=20, default='pendente')  # pendente, sucesso, erro
    observacao = TextField(null=True)
    criado_em = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])
    atualizado_em = DateTimeField(constraints=[SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        table_name = 'sap_lancamento'


# ============================================================================
# FUNÇÕES AUXILIARES
# ============================================================================

def criar_tabelas():
    """Cria todas as tabelas no banco de dados"""
    db.connect()
    db.create_tables([
        # Domínios
        Municipio,
        Pais,
        TipoTributacaoISSQN,
        NBS,
        TipoEvento,
        TipoRetencao,
        
        # Endereços e Contatos
        EnderecoNacional,
        EnderecoExterior,
        Contato,
        
        # Participantes
        Participante,
        RegimeTributacaoPrestador,
        
        # NFS-e principal
        NFSe,
        DPS,
        DPSSubstituicao,
        
        # Serviço
        Servico,
        LocalPrestacaoServico,
        ComercioExterior,
        LocacaoSublocacao,
        ObraConstrucao,
        AtividadeEvento,
        ExploracaoRodovia,
        InformacoesComplementares,
        
        # Valores
        ValoresNFSe,
        ValoresDPS,
        DeducaoReducao,
        DocumentoDeducao,
        NFSeMunicipalDeducao,
        NFNFSNaoEletronica,
        
        # Tributação
        TributacaoMunicipal,
        BeneficioMunicipal,
        ExigibilidadeSuspensa,
        Imunidade,
        TributacaoFederal,
        PISCOFINS,
        TotaisTributos,
        
        # Eventos
        EventoNFSe,
    ], safe=True)
    db.close()


# ============================================================================
# EXEMPLO DE USO
# ============================================================================

if __name__ == '__main__':
    # Criar tabelas
    criar_tabelas()
    print("Modelo de dados NFS-e - ADN criado com sucesso!")
    print("Total de tabelas: 40")
    print("\nPrincipais características:")
    print("- Normalização 3FN aplicada")
    print("- Tabelas reutilizáveis: Município, País, Participante, Endereço")
    print("- Separação entre NFS-e e DPS")
    print("- Suporte a eventos")
    print("- Tributação detalhada (municipal e federal)")
    print("- Grupos específicos de serviço (obra, evento, rodovia, etc.)")