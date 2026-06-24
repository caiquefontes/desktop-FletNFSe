# import peewee as pee
import datetime
from decimal import Decimal
from peewee import (
    SqliteDatabase,
    Model,
    CharField,
    IntegerField,
    BooleanField,
    TextField,
    ForeignKeyField,
    BigIntegerField,
    DateField,
    DecimalField,
    TimeField,
)

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

# ============================================================================
# TABELAS DE DIMENSÕES
# ============================================================================

class CadastroUF(BaseModel):
    """Tabela de UFs"""
    uf = CharField(max_length=2, default='ZZ')
    ds_uf = CharField(max_length=20)
    regiao = CharField(max_length=52)

    class Meta:
        table_name = 'cadastro_uf' 


class CadastroMunicipio(BaseModel):
    """Tabela de municípios do IBGE - reutilizável"""
    codigo = BigIntegerField(unique=True, index=True)
    nome = CharField(max_length=100, null=True, default=None) 
    uf = ForeignKeyField(CadastroUF, null=True, on_delete='CASCADE', backref='mun_ufs')
    ativo = BooleanField(default=True)
    data_atualizacao = DateField(default=datetime.date.today)
    
    class Meta:
        table_name = 'cadastro_municipio'    


class CadastroTributacaoNacional(BaseModel):
    """Códigos de tributação nacional do ISSQN"""
    codigo = IntegerField(unique=True, index=True)
    descricao = CharField(max_length=100, null=True, default=None)
    codigo_mun = IntegerField(null=True, default=None)
    descricao_mun = CharField(max_length=100, null=True, default=None)
    ativo = BooleanField(default=True, null=True)
    
    class Meta:
        table_name = 'cadastro_tributacao_nacional'


class CadastroNBS(BaseModel):
    """Nomenclatura Brasileira de Serviços"""
    codigo = BigIntegerField(unique=True, index=True)
    descricao = CharField(max_length=100, null=True, default=None) 
    ativo = BooleanField(default=True, null=True)
    
    class Meta:
        table_name = 'cadastro_nbs'


class ServicoCadastro(BaseModel):
    """Cadastro de Servico"""
    trib_nac_id = ForeignKeyField(CadastroTributacaoNacional, null=True, on_delete='CASCADE', backref='tributacao_nac')
    nbs_id = ForeignKeyField(CadastroNBS, null=True, on_delete='CASCADE', backref='nbss')
    des_serv = CharField(max_length=100, null=True, default=None)

    class Meta:
        table_name = 'servico_cadastro'


class ParticipanteTipo(BaseModel):
    # 'PRESTADOR', 'TOMADOR', 'INTERMEDIARIO', 'FORNECEDOR'
    tipo = CharField(max_length=20)
    
    class Meta:
        table_name = 'participante_tipo'


class Participante(BaseModel):
    """Cadastro de CNPJ"""
    tipo = ForeignKeyField(ParticipanteTipo, null=True, on_delete='CASCADE', backref='participantes') 
    cnpj = CharField(max_length=25, null=True, index=True)
    cpf = CharField(max_length=25, null=True)
    nif = IntegerField(null=True)
    ds_motv_nif = IntegerField(null=True)
    des_nome = CharField(max_length=100, null=True)
    des_fant = CharField(max_length=100, null=True)
    ins_mun = CharField(max_length=25, null=True)
    op_simples_nac = IntegerField(null=True)
    reg_apu_trib_simp_nac = IntegerField(null=True)
    reg_esp_trib = IntegerField(null=True)

    class Meta:
        table_name = 'participante'   


class ServicoAliquota(BaseModel):
    """Table de DePara de Servico Prestado Levando em Conta a Localidade Emissao e Localidade Prestado"""
    local_emi = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='local_emis')
    local_prest = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='local_prests')
    local_incid = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='local_incids')
    servico_id = ForeignKeyField(ServicoCadastro, null=True, on_delete='CASCADE', backref='cad_servicos')
    trib_iss_qn = IntegerField(null=True)
    trib_ret_iss_qn = IntegerField(null=True)
    vl_aliq = DecimalField(max_digits=15, decimal_places=2)
    data_criacao = DateField(default=datetime.date.today)

    class Meta:
        table_name = 'servico_aliquota' 

class CadastroVersaoAplicacao(BaseModel):
    """Versão da aplicação que gerou a NFS-e."""
    versao_aplicacao = CharField(max_length=55, null=True)

    class Meta:
        table_name = 'cadastro_versao_aplicacao'
    
# ============================================================================
# TABELAS FATOS
# ============================================================================
class NfseChave(BaseModel):
    chave_acesso = CharField(max_length=55, null=False, unique=True)

    class Meta:
        table_name = 'nfse_chave'


class NfseNfse(BaseModel):
    chave_id = ForeignKeyField(NfseChave, null=True, on_delete='CASCADE', backref='nfsechaves')
    loc_emi_id = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='nfse_local_emis')
    loc_pre_id = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='nfse_local_prests')
    nr_nfse = BigIntegerField(null=False)
    loc_inc_id = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='nfse_local_incids') 
    trib_nac_id = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='nfse_local_incids') 
    nbs_id = ForeignKeyField(CadastroNBS, null=True, on_delete='CASCADE', backref='nfse_nbs') 
    ver_aplic_id = ForeignKeyField(CadastroVersaoAplicacao, null=True, on_delete='CASCADE', backref='nfse_ver_aplic') 
    nr_amb_ger = IntegerField(null=True)
    tp_emis = IntegerField(null=True)
    nr_proc_emis = IntegerField(null=True)
    nr_sit_poss = IntegerField(null=True)
    nr_dfe = BigIntegerField(null=True)
    dt_emis = DateField(null=False)
    hr_emis = TimeField()

    class Meta:
        table_name = 'nfse_nfse'


class NfseValorTotal(BaseModel):
    nfse_id = ForeignKeyField(NfseNfse, null=False, on_delete='CASCADE', backref='nfse_nfs')
    vl_cal_ded_red = DecimalField(max_digits=15, decimal_places=2)	   # vCalcDR - Valor monetário (R$) de dedução/redução da base de cálculo (BC) do ISSQN.
    tp_benef = IntegerField(null=True)	                               # tpBM - Tipo Benefício Municipal (BM):1)Isenção; 2)Redução da BC em 'ppBM' %; 3) Redução da BC em R$ 'vInfoBM'; 4) Alíquota Diferenciada de 'aliqDifBM' %; 
    vl_cal_benef = DecimalField(max_digits=15, decimal_places=2)	   # vCalcBM - Valor monetário (R$) do percentual de redução da base de cálculo (BC) do ISSQN devido a um benefício municipal (BM).
    vl_base_cal = DecimalField(max_digits=15, decimal_places=2)        # vBC	"Valor da Base de Cálculo do ISSQN (R$) = Valor do Serviço - Desconto Incondicionado - Deduções/Reduções - Benefício Municipal | vBC = vServ - descIncond - (vDR ou vCalcDR) - (vRedBCBM ou VCalcBM)"
    vl_aliq_aplic = DecimalField(max_digits=15, decimal_places=2)      # pAliqAplic	"Alíquota aplicada sobre a base de cálculo para apuração do ISSQN.
    vl_iss_qn = DecimalField(max_digits=15, decimal_places=2)          # vISSQN	"Valor do ISSQN (R$) = Valor da Base de Cálculo x Alíquota vISSQN = vBC x pAliqAplic
    vl_total_ret = DecimalField(max_digits=15, decimal_places=2)       # vTotalRet "Valor total de retenções (R$) = Σ(CP + IRRF + CSLL  + ISSQN* +  (PIS + CONFINS)**) vTotalRet = (vRetCP + vRetIRRF + vRetCSLL) + vISSQN* + (vPIS + vCOFINS)**"
    vl_total_liq = DecimalField(max_digits=15, decimal_places=2)       # vLiq "Valor líquido (R$) = Valor do serviço - Desconto condicionado - Desconto incondicionado - Valores retidos (CP, IRRF, CSLL)* - Valores, se retidos (ISSQN, PIS, COFINS)** # VLiq = vServ – vDescIncond – vDescCond – (vRetCP + vRetIRRF + vRetCSLL)* – ( vISSQN - vPIS + vCOFINS)**"

    class Meta:
        table_name = 'nfse_valortotal'


class NfseDpsDps(BaseModel):
    # -----  Dados DPS  -----
    nfse_id = ForeignKeyField(NfseNfse, null=False, on_delete='CASCADE', backref='nfse_nfs')
    dps_id = CharField(max_length=45, null=False)
    tp_amb = IntegerField(null=True)
    dt_emi = DateField(null=True)
    hr_emi  = TimeField()
    vr_apli = CharField(max_length=10, null=True)
    cd_serie = IntegerField(null=True)
    nr_dps = IntegerField(null=True)
    dt_comp = DateField(null=True)
    tp_emit = IntegerField(null=True) # Emitente da DPS: 1 - Prestador; 2 - Tomador; 3 - Intermediário;
    loc_emi_id = ForeignKeyField(CadastroMunicipio, null=True, on_delete='CASCADE', backref='dps_local_emis')
    prestador_id = ForeignKeyField(Participante, null=False, on_delete='CASCADE', backref='prestadores')
    tomador_id = ForeignKeyField(Participante, null=False, on_delete='CASCADE', backref='tomadores')
    intermediario_id = ForeignKeyField(Participante, null=False, on_delete='CASCADE', backref='intermediarios')
    serv_aliq = ForeignKeyField(ServicoAliquota, null=False, on_delete='CASCADE',backref='servicos')

    # -----  Valores  -----
    vl_recebimento = DecimalField(max_digits=15, decimal_places=2) 
    vl_servico = DecimalField(max_digits=15, decimal_places=2) 
    vl_desc_incondicional = DecimalField(max_digits=15, decimal_places=2) 
    vl_desc_condicional = DecimalField(max_digits=15, decimal_places=2) 
    vl_aliq_ded_red = DecimalField(max_digits=15, decimal_places=2) 
    vl_ded_red = DecimalField(max_digits=15, decimal_places=2) 

    class Meta:
        table_name = 'nfse_dps_dps'


class NfseDpsTrib(BaseModel):
    # model relacionado a tributação incidente ao servico prestado.
    dps_id = ForeignKeyField(NfseDpsDps, null=False, on_delete='CASCADE', backref='dps_ids')

    # Tributacao Municipal
    cd_trib_iss_qn = IntegerField() # NFSe/infNFSe/DPS/infDPS/valores/trib/tribMun/
    cd_PaisResult = IntegerField() 
    cd_nbm = IntegerField() 
    vl_red_bc_bm = DecimalField(max_digits=15, decimal_places=2) 
    vp_red_bc_bm = DecimalField(max_digits=15, decimal_places=2) 

    # Tributacao Federal (piscofins)
    cd_cst = IntegerField() 
    vl_bc_pis_cofins = DecimalField(max_digits=15, decimal_places=2) 
    vp_aliq_pis = DecimalField(max_digits=15, decimal_places=2) 
    vp_aliq_cofins = DecimalField(max_digits=15, decimal_places=2) 
    vl_pis = DecimalField(max_digits=15, decimal_places=2) 
    vl_confins = DecimalField(max_digits=15, decimal_places=2) 
    tp_ret_pis_cofins  = IntegerField() 
    vl_ret_cp = DecimalField(max_digits=15, decimal_places=2) 
    vl_ret_irrf = DecimalField(max_digits=15, decimal_places=2) 
    vl_ret_csll = DecimalField(max_digits=15, decimal_places=2) 


    class Meta:
        table_name = 'nfse_dps_trib'


class NfseDpsSubst(BaseModel):
    dps_id = ForeignKeyField(NfseDpsDps, null=False, on_delete='CASCADE', backref='dps_ids')
    ch_nfse_subs = CharField(max_length=45, null=False)
    cd_motivo = IntegerField()
    ds_motivo = CharField(null=True)

    class Meta:
        table_name = 'nfse_dps_subst'

class NfseDpsInfcompl(BaseModel):
    dps_id = ForeignKeyField(NfseDpsDps, null=False, on_delete='CASCADE', backref='dps_ids')
    id_doc_tec = CharField(max_length=45, null=False)
    doc_ref = CharField(max_length=45, null=True)
    ds_inf_comp = CharField(null=True)

    class Meta:
        table_name = 'nfse_dps_infcompl'

# ============================================================================
# Teste Main
# ============================================================================
def criar_tabelas():
    """Cria todas as tabelas no banco de dados"""
    try:
        db.connect()
        db.create_tables([
            # Domínios
            CadastroUF, CadastroMunicipio, ParticipanteTipo, Participante, CadastroTributacaoNacional,
            CadastroNBS, ServicoCadastro, ServicoAliquota, CadastroVersaoAplicacao, NfseChave,
            NfseNfse, NfseValorTotal,
            
            ],
            safe=True
        )
    finally:
        db.close()

if __name__ == '__main__':
    r = criar_tabelas()
    