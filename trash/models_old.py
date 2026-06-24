"""
Centralized database models for NFSeFlet project using Peewee ORM.
"""

import peewee as pee

# Database configuration
# Using SQLite for simplicity, can be changed to other databases
db = pee.SqliteDatabase('sqlite.db')

# Base model class
class BaseModel(pee.Model):
    class Meta:
        database = db

# cadastro de empresas
class Empresa(BaseModel):
    # dados
    id_empresa = pee.IntegerField(primary_key=True)
    ds_cnpj = pee.CharField(max_length=20)
    ds_cpf = pee.CharField(max_length=20, null=True)
    ds_ins_mun = pee.IntegerField(null=True)
    ds_nome = pee.CharField(max_length=20, null=True) 
    ds_fant = pee.CharField(max_length=20, null=True) 
    # Endereço
    ds_Lgr = pee.CharField(max_length=100, null=True) 
    nr_imovel = pee.IntegerField(null=True)
    ds_cpl = pee.CharField(max_length=100, null=True) 
    ds_bairro = pee.CharField(max_length=100, null=True) 
    cd_mun = pee.IntegerField(null=True)
    ds_uf = pee.CharField(max_length=100, null=True) 
    cd_cep = pee.IntegerField(null=True)
    ds_fone = pee.CharField(max_length=100, null=True) 
    ds_email = pee.CharField(max_length=100, null=True) 
    
    class Meta:
        table_name = 'empresa'

# NFSe (Nota Fiscal de Serviços Eletrônica) model
class NFSe(BaseModel):
    # capa
    cd_chave_acesso = pee.CharField(max_length=50, unique=True)  # Access key
    nr_nfse = pee.IntegerField()
    cd_loc_incid = pee.IntegerField()
    nr_ver_aplic = pee.IntegerField()
    cd_amb_ger = pee.IntegerField()
    cd_tipo_emis = pee.IntegerField()
    cd_proc_emis = pee.IntegerField()
    cd_sit_nfse = pee.IntegerField()
    dt_hr = pee.DateTimeField()
    nr_dfe_mun = pee.IntegerField()
    created_at = pee.DateTimeField(constraints=[pee.SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = pee.DateTimeField(constraints=[pee.SQL('DEFAULT CURRENT_TIMESTAMP')])
    # emitente
    id_empresa = pee.ForeignKeyField(model=Empresa, backref='empresas')
    # valores
    vl_calc_dr = pee.FloatField(default=0)
    cd_tp_benef_mun = pee.IntegerField()
    vl_calc_benef_mun = pee.FloatField(default=0)
    vl_base_cal = pee.FloatField(default=0)
    p_aliq_aplic = pee.FloatField(default=0)
    vl_iss_qn = pee.FloatField(default=0)
    vl_total_reten = pee.FloatField(default=0)
    vl_total_liq = pee.FloatField(default=0)

    class Meta:
        table_name = 'nfse'


class NFSeDPS(BaseModel):
    ...    

# Pedido de Compra (Purchase Order) model
class PedidoCompra(BaseModel):
    numero_pedido = pee.CharField(max_length=50, unique=True)  # Purchase order number
    cnpj_fornecedor = pee.CharField(max_length=20)  # Supplier CNPJ
    valor_total = pee.DecimalField(max_digits=15, decimal_places=2)
    data_pedido = pee.DateField()
    descricao = pee.TextField(null=True)
    nfse = pee.ForeignKeyField(NFSe, backref='pedidos', null=True)  # Link to NFSe
    status = pee.CharField(max_length=20, default='pendente')  # pendente, vinculado, processo
    created_at = pee.DateTimeField(constraints=[pee.SQL('DEFAULT CURRENT_TIMESTAMP')])
    updated_at = pee.DateTimeField(constraints=[pee.SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        table_name = 'pedido_compra'

# SAP Lancamento (Launch) model
class SapLancamento(BaseModel):
    nfse = pee.ForeignKeyField(NFSe, backref='lancamentos_sap')  # Linked NFSe
    numero_documento_sap = pee.CharField(max_length=50)  # SAP document number
    data_lancamento = pee.DateField()
    valor_lancado = pee.DecimalField(max_digits=15, decimal_places=2)
    usuario_lancamento = pee.CharField(max_length=100)
    status = pee.CharField(max_length=20, default='pendente')  # pendente, sucesso, erro
    observacao = pee.TextField(null=True)
    criado_em = pee.DateTimeField(constraints=[pee.SQL('DEFAULT CURRENT_TIMESTAMP')])
    atualizado_em = pee.DateTimeField(constraints=[pee.SQL('DEFAULT CURRENT_TIMESTAMP')])

    class Meta:
        table_name = 'sap_lancamento'

# Database initialization function
def initialize_database():
    """Initialize the database and create tables if they don't exist."""
    db.connect()
    db.create_tables([NFSe, PedidoCompra, SapLancamento], safe=True)
    print("Database initialized successfully!")

if __name__ == "__main__":
    initialize_database()