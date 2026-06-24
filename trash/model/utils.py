# -------------------------------- Ajusted Path ---------------------------------------
from pathlib import Path
import sys
# sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
print(str(Path(__file__).parent.parent))
# -------------------------------- Code -----------------------------------------------
from playwright.sync_api import sync_playwright
from peewee import *
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from apps.pwNFSe.utils import xml_para_dit_caminhos
from trash.model.models import db
from trash.model.models import (
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
)

def extrair_valor(dicionario_caminhos, caminho, tipo=str, default=None):
    """
    Extrai e converte um valor do dicionário de caminhos XML.
    """
    valor = dicionario_caminhos.get(caminho)
    if valor is None or valor == '':
        return default
    
    try:
        if tipo == Decimal:
            # Remove formatação monetária e converte
            valor_limpo = re.sub(r'[^\d.,-]', '', str(valor)).replace('.', '').replace(',', '.')
            return Decimal(valor_limpo) if valor_limpo else default
        elif tipo == int:
            r = int(re.sub(r'[^\d-]', '', str(valor)))
            if r is None: return 0
            return r
        elif tipo == float:
            return float(valor)
        elif tipo == datetime:
            # Tenta diferentes formatos de data/hora
            for fmt in ['%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d']:
                try:
                    return datetime.strptime(valor[:26], fmt)
                except ValueError:
                    continue
            return default
        else:
            return str(valor).strip()
    except (ValueError, InvalidOperation):
        return default


def obter_ou_criar_municipio(dicionario_caminhos, caminho_codigo, caminho_descricao=None):
    """
    Obtém ou cria um registro de município.
    """
    codigo = extrair_valor(dicionario_caminhos, caminho_codigo, default='0')
    if not codigo or codigo == '0':
        return None
    
    descricao = extrair_valor(dicionario_caminhos, caminho_descricao, default='') if caminho_descricao else ''
    
    # Tenta extrair UF da descrição ou assume SP como default
    uf = descricao[-2:] if len(descricao) >= 2 else 'SP'
    
    municipio, _ = Municipio.get_or_create(
        codigo=codigo,
        defaults={
            'nome': descricao,
            'uf': uf,
            'data_atualizacao': datetime.now().date()
        }
    )
    return municipio


def obter_ou_criar_pais(codigo_pais, nome_pais=None):
    """
    Obtém ou cria um registro de país.
    """
    if not codigo_pais:
        return None
    
    pais, _ = Pais.get_or_create(
        codigo=codigo_pais,
        defaults={'nome': nome_pais or f'País {codigo_pais}'}
    )
    return pais


def criar_endereco_nacional(dicionario_caminhos, caminho_base):
    """
    Cria um registro de endereço nacional.
    """
    logradouro = extrair_valor(dicionario_caminhos, f"{caminho_base}/xLgr", default='')
    if not logradouro:
        return None
    
    municipio = obter_ou_criar_municipio(
        dicionario_caminhos,
        f"{caminho_base}/cMun",
        f"{caminho_base}/xMun" if f"{caminho_base}/xMun" in dicionario_caminhos else None
    )
    
    if not municipio:
        return None
    
    endereco, _ = EnderecoNacional.get_or_create(
        logradouro=logradouro,
        numero=extrair_valor(dicionario_caminhos, f"{caminho_base}/nro", default='S/N'),
        complemento=extrair_valor(dicionario_caminhos, f"{caminho_base}/xCpl"),
        bairro=extrair_valor(dicionario_caminhos, f"{caminho_base}/xBairro", default=''),
        municipio=municipio,
        cep=extrair_valor(dicionario_caminhos, f"{caminho_base}/CEP", default=''),
    )
    return endereco


def criar_endereco_exterior(dicionario_caminhos, caminho_base):
    """
    Cria um registro de endereço no exterior.
    """
    pais_codigo = extrair_valor(dicionario_caminhos, f"{caminho_base}/cPais")
    if not pais_codigo:
        return None
    
    pais = obter_ou_criar_pais(pais_codigo)
    
    endereco, _ = EnderecoExterior.get_or_create(
        pais=pais,
        codigo_postal=extrair_valor(dicionario_caminhos, f"{caminho_base}/cEndPost"),
        cidade=extrair_valor(dicionario_caminhos, f"{caminho_base}/xCidade", default=''),
        estado_provincia_regiao=extrair_valor(dicionario_caminhos, f"{caminho_base}/xEstProvReg"),
    )
    return endereco


def criar_ou_obter_participante(caminho_arquivo_xml:str, caminho_base, tipo_participante):
    """
    Cria ou obtém um participante (Prestador, Tomador, Intermediário, Fornecedor).
    """
    dados_xml = xml_para_dit_caminhos(caminho_arquivo_xml)

    if not dados_xml:
        raise ValueError("Não foi possível extrair dados do XML")
    
    dicionario_caminhos = dados_xml

    cnpj = extrair_valor(dicionario_caminhos, f"{caminho_base}/CNPJ")
    cpf = extrair_valor(dicionario_caminhos, f"{caminho_base}/CPF")
    nif = extrair_valor(dicionario_caminhos, f"{caminho_base}/NIF")
    
    if not cnpj and not cpf and not nif:
        return None
    
    # Determina identificador único
    identificador = cnpj or cpf or nif
    
    participante, criado = Participante.get_or_create(
        tipo=tipo_participante,
        cnpj=cnpj,
        cpf=cpf,
        defaults={
            'nif': nif,
            'razao_social': extrair_valor(dicionario_caminhos, f"{caminho_base}/xNome"),
            'nome_fantasia': extrair_valor(dicionario_caminhos, f"{caminho_base}/xFant"),
            'inscricao_municipal': extrair_valor(dicionario_caminhos, f"{caminho_base}/IM"),
        }
    )
    
    # Atualiza endereço se necessário
    if criado or not participante.endereco_nacional_id:
        # Tenta criar endereço nacional
        end_nac_path = f"{caminho_base}/end/endNac"
        if f"{end_nac_path}/xLgr" in dicionario_caminhos:
            endereco = criar_endereco_nacional(dicionario_caminhos, end_nac_path)
            if endereco:
                participante.endereco_nacional = endereco
        
        # Tenta criar endereço exterior
        end_ext_path = f"{caminho_base}/end/endExt"
        if f"{end_ext_path}/cPais" in dicionario_caminhos:
            endereco_ext = criar_endereco_exterior(dicionario_caminhos, end_ext_path)
            if endereco_ext:
                participante.endereco_exterior = endereco_ext
        
        # Contato
        fone = extrair_valor(dicionario_caminhos, f"{caminho_base}/fone")
        email = extrair_valor(dicionario_caminhos, f"{caminho_base}/email")
        if fone or email:
            contato, _ = Contato.get_or_create(
                telefone=fone,
                email=email
            )
            participante.contato = contato
        
        participante.save()
    
    return participante

    
def criar_ou_obter_municipio( caminho_arquivo_xml:str, caminho_cod, caminho_nome=None, is_required=True):
    
    dados_xml = xml_para_dit_caminhos(caminho_arquivo_xml)
    
    if not dados_xml:
        raise ValueError("Não foi possível extrair dados do XML")
    
    cod = extrair_valor(dados_xml, caminho_cod, default='').strip()
    data_atual = datetime.now().date()
    
    # Trata "0" ou vazio como não informado
    if not cod or cod == '0':
        if is_required:
            # Busca ou Cria placeholder válido para não quebrar FK
            mun, criado = Municipio.get_or_create(
                codigo='0000000',
                defaults={
                    'nome': 'Município Não Informado', 
                    'uf': 'XX', 
                    'ativo': False,
                    'data_atualizacao': data_atual
                }
            )
            
            # Se já existia, garante que a data de atualização seja renovada (opcional)
            if not criado:
                mun.data_atualizacao = data_atual
                mun.save()
                
            return mun
        return None
    
    nome = extrair_valor(dados_xml, caminho_nome, default='') if caminho_nome else ''
    uf = 'ZZ'
    
    # Busca por 'codigo'. Se não existir, cria com os valores do 'defaults'
    mun, criado = Municipio.get_or_create(
        codigo=cod,
        defaults={
            'nome': nome, 
            'uf': uf, 
            'data_atualizacao': data_atual
        }
    )

    # === LÓGICA DE ATUALIZAÇÃO ===
    # Se o registro já existia (criado == False), atualizamos os dados vindos do XML atual
    if not criado:
        mun.nome = nome
        mun.uf = uf
        mun.data_atualizacao = data_atual
        mun.save() # Salva as alterações no banco de dados

    return mun


def criar_ou_obter_nota_fiscal_servico(caminho_arquivo_xml: str):

    dados_xml = xml_para_dit_caminhos(caminho_arquivo_xml)

    loc_emis_nfse = criar_ou_obter_municipio(caminho_arquivo_xml, "NFSe/infNFSe/cLocEmi", "NFSe/infNFSe/xLocEmi")
    loc_prest = criar_ou_obter_municipio(caminho_arquivo_xml, "NFSe/infNFSe/cLocPrestacao", "NFSe/infNFSe/xLocPrestacao")
    loc_incid = criar_ou_obter_municipio(caminho_arquivo_xml, "NFSe/infNFSe/cLocIncid", "NFSe/infNFSe/xLocIncid", is_required=False)
    emitente = criar_ou_obter_participante(caminho_arquivo_xml, "NFSe/infNFSe/emit", "PRESTADOR")

    # 1. Extraímos o ID que identifica unicamente esta nota
    id_nfse = extrair_valor(dados_xml, "NFSe/infNFSe@Id")

    # Dicionário com todos os dados que queremos salvar ou atualizar
    dados_nota = {
        "versao": extrair_valor(dados_xml, "NFSe@versao"),
        "numero_nfse": extrair_valor(dados_xml, "NFSe/infNFSe/nNFSe", tipo=int),
        "localidade_emissora_id": loc_emis_nfse.id,
        "localidade_prestacao_id": loc_prest.id if loc_prest else None,
        "localidade_incidencia_id": loc_incid.id if loc_incid else None,
        "xLocEmi": extrair_valor(dados_xml, "NFSe/infNFSe/xLocEmi"),
        "xLocPrestacao": extrair_valor(dados_xml, "NFSe/infNFSe/xLocPrestacao"),
        "xLocIncid": extrair_valor(dados_xml, "NFSe/infNFSe/xLocIncid"),
        "xTribNac": extrair_valor(dados_xml, "NFSe/infNFSe/xTribNac"),
        "versao_aplicativo": extrair_valor(dados_xml, "NFSe/infNFSe/verAplic"),
        "ambiente_gerador": extrair_valor(dados_xml, "NFSe/infNFSe/ambGer", tipo=int, default=1),
        "tipo_emissao": extrair_valor(dados_xml, "NFSe/infNFSe/tpEmis", tipo=int, default=1),
        "codigo_status": extrair_valor(dados_xml, "NFSe/infNFSe/cStat", tipo=int),
        "data_processamento": extrair_valor(dados_xml, "NFSe/infNFSe/dhProc", tipo=datetime),
        "numero_dfe": extrair_valor(dados_xml, "NFSe/infNFSe/nDFe", tipo=int, default=0),
        "emitente_id": emitente.id,
    }

    # 2. Tentamos buscar pelo 'id'. Se não existir, 'criado' será True e o Peewee cria o registro.
    nfse, criado = NFSe.get_or_create(
        id=id_nfse,
        defaults=dados_nota  # Se for criar do zero, usa esses dados
    )

    # 3. Caso o registro já existisse (criado == False), nós atualizamos os campos com os novos dados
    if not criado:
        for chave, valor in dados_nota.items():
            setattr(nfse, chave, valor)
        nfse.save()  # Salva as alterações no banco de dados

    return nfse


def criar_ou_atualizar_cadastro_nbs(cod_nbs:int, des_nbs:str):
    # cod_nbs = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS")
    # des_nbs = extrair_valor(dados_xml, "NFSe/infNFSe/xNBS")
    
    if cod_nbs is None:
        print("Error: codigo nbs inacessivel")
        raise()

    nbs = NBS.get_or_none(NBS.codigo == cod_nbs)

    if nbs is None:
        try:
            nbs = NBS.create(
                codigo = cod_nbs,
                descricao = des_nbs
            )
            print(f"✅ DPS criada com sucesso! ID: {nbs.id}")
        except IntegrityError as e:
                print("🔴 Erro de Integridade ao criar NBS:")
                print(str(e))
                # Verifica se é FK ou Unique Constraint
                if "FOREIGN KEY" in str(e):
                    print(f"   -> Verifique se os IDs nbs_id={nbs.id} existem na tabela correta.")
                raise
    else:
        nbs.descricao = des_nbs
        nbs.save()
        print(f"✅ NBS atualizado com sucesso! ID: {nbs.id}")
    
    return nbs.id
    


def criar_ou_atualizar_cadastro_trib_nac(cod_trib_nac:int, des_trib_nac:str):
    # cod_nbs = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS")
    # des_nbs = extrair_valor(dados_xml, "NFSe/infNFSe/xNBS")
    
    if cod_trib_nac is None:
        print("Error: codigo nbs inacessivel")
        raise()

    trib_nac = TipoTributacaoISSQN.get_or_none(NBS.codigo == cod_trib_nac)

    if trib_nac is None:
        try:
            trib_nac = TipoTributacaoISSQN.create(
                codigo = cod_trib_nac,
                descricao = des_trib_nac
            )
            print(f"✅ DPS criada com sucesso! ID: {trib_nac.id}")
        except IntegrityError as e:
                print("🔴 Erro de Integridade ao criar NBS:")
                print(str(e))
                # Verifica se é FK ou Unique Constraint
                if "FOREIGN KEY" in str(e):
                    print(f"   -> Verifique se os IDs nbs_id={trib_nac.id} existem na tabela correta.")
                raise
    else:
        trib_nac.descricao = des_trib_nac
        trib_nac.save()
        print(f"✅ NBS atualizado com sucesso! ID: {trib_nac.id}")
    
    return trib_nac.id
    



def criar_dps_nota_fiscal_servico(caminho_arquivo_xml):
    """
    Função principal que extrai dados do XML e insere no banco de dados.
    """    
    dados_xml = xml_para_dit_caminhos(caminho_arquivo_xml)
    if not dados_xml:
        raise ValueError("Não foi possível extrair dados do XML")

    for chv, vlr in dados_xml.items():
        print(chv)
        ...
    
    print('*'*50)
    print('INPUT')
    print('*'*50)
    try:
        # === AUXILIAR: Busca/Cria Município com fallback seguro ===
        id_nfse = extrair_valor(dados_xml, "NFSe/infNFSe@Id")
        nfse = NFSe.get_or_none(NFSe.id == id_nfse)
        if nfse is None:
            print('Error: nota fiscal nao criada, impossivel criação DPS')
            raise()  
        # ==================== DPS ====================
        dps_versao = extrair_valor(dados_xml, "NFSe/infNFSe/DPS@versao")
        dps_id = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS@Id")
        # 3. Criação da DPS usando os IDs persistidos
        dps = DPS.get_or_none(DPS.id == dps_id)
        print('0/20')
        if dps is None:
            try:
                dps = DPS.create(
                    nfse_id=nfse.id,
                    versao=dps_versao or '1.00',
                    id=dps_id,
                    tipo_ambiente=int(extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/tpAmb", default=1)),
                    data_emissao=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/dhEmi", tipo=datetime),
                    versao_aplicativo=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/verAplic", default='1.0'),
                    serie=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serie", default='00001'),
                    numero_dps=int(extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/nDPS", default=0)),
                    data_competencia=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/dCompet", tipo=datetime),
                    tipo_emitente=int(extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/tpEmit", default=1)),
                    localidade_emissora_id=nfse.localidade_emissora
                )
                print(f"✅ DPS criada com sucesso! ID: {dps.id}")
            except IntegrityError as e:
                print("🔴 Erro de Integridade ao criar DPS:")
                print(str(e))
                # Verifica se é FK ou Unique Constraint
                if "FOREIGN KEY" in str(e):
                    print(f"   -> Verifique se os IDs nfse_id={nfse.id} e mun_id={dps.id} existem na tabela correta.")
                raise
        else:
            # ATUALIZAR OS DADOS CASO EXISTA

            dps.versao = dps_versao or '1.00'
            dps.tipo_ambiente = int(extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/tpAmb", default=1))
            dps.data_emissao = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/dhEmi", tipo=datetime)
            dps.versao_aplicativo = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/verAplic", default='1.0')
            dps.serie = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serie", default='00001')
            dps.numero_dps = int(extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/nDPS", default=0))
            dps.data_competencia = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/dCompet", tipo=datetime)
            dps.tipo_emitente = int(extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/tpEmit", default=1))
            dps.localidade_emissora = nfse.localidade_emissora

            dps.save()
            print(f"✅ DPS atualizado com sucesso! ID: {dps.id}")

        print('1/20')
        # Substituição (se houver)
        ch_substituida = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/subst/chSubstda")
        if ch_substituida:
            DPSSubstituicao.create(
                dps=dps,
                chave_substituida=ch_substituida,
                codigo_motivo=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/subst/cMotivo", tipo=int),
                descricao_motivo=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/subst/xMotivo")
            )
            print(f"✅ CHAVE substituicao atualizado com sucesso! ID: {ch_substituida}")
        print('2/20')
        # ==================== PRESTADOR ====================
        prestador = criar_ou_obter_participante(
            caminho_arquivo_xml,
            "NFSe/infNFSe/DPS/infDPS/prest",
            "PRESTADOR"
        )
        print('3/20')
        # Regime de tributação do prestador
        if prestador and "NFSe/infNFSe/DPS/infDPS/prest/regTrib/opSimpNac" in dados_xml:
            prest_reg_trib = RegimeTributacaoPrestador.get_or_none(RegimeTributacaoPrestador.participante == prestador)
            if prest_reg_trib is None:
                RegimeTributacaoPrestador.create(
                    participante=prestador,
                    data_referencia=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/dCompet", tipo=datetime),
                    opcao_simples_nacional=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/regTrib/opSimpNac", tipo=int),
                    reg_apuracao_tributaria_sn=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/regTrib/regApTribSN", tipo=int),
                    regime_especial_tributacao=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/regTrib/regEspTrib", tipo=int)
                )
            else:
                # atualziar registro
                prest_reg_trib.data_referencia=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/dCompet", tipo=datetime),
                prest_reg_trib.opcao_simples_nacional=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/regTrib/opSimpNac", tipo=int),
                prest_reg_trib.reg_apuracao_tributaria_sn=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/regTrib/regApTribSN", tipo=int),
                prest_reg_trib.regime_especial_tributacao=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/regTrib/regEspTrib", tipo=int)

        print('4/20')
        # ==================== TOMADOR ====================
        tomador = criar_ou_obter_participante(
            caminho_arquivo_xml,
            "NFSe/infNFSe/DPS/infDPS/toma",
            "TOMADOR"
        )
        print('5/20')
        # ==================== INTERMEDIÁRIO ====================
        intermediario = criar_ou_obter_participante(
            caminho_arquivo_xml,
            "NFSe/infNFSe/DPS/infDPS/interm",
            "INTERMEDIARIO"
        )
        print('6/20')
        # ==================== SERVIÇO ====================
        # Obtém ou cria código de tributação
        # Gerar Cadastro do codigo de NBS
        print('7/20')
        cod_nbs=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS")
        des_nbs = extrair_valor(dados_xml, "NFSe/infNFSe/xNBS")
        id_nbs = criar_ou_atualizar_cadastro_nbs(cod_nbs=cod_nbs, des_nbs=des_nbs)
        # ---
        cod_trib_nac = extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribNac")
        des_trib_nac = extrair_valor(dados_xml, "NFSe/infNFSe/xTribNac")
        id_trib_nac = criar_ou_atualizar_cadastro_trib_nac(cod_trib_nac, des_trib_nac)
        # ---
        codigo_interno_contribuinte=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cIntContrib")
        codigo_tributacao_municipal=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribMun")

        print('*'*50)
        print(codigo_tributacao_municipal, codigo_interno_contribuinte, codigo_trib_nac)
        print('*'*50)

        servico = Servico.create(
            nfse=nfse.id,
            dps=dps.id,
            codigo_tributacao_nacional=id_trib_nac,
            codigo_tributacao_municipal=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribMun"),
            codigo_nbs=id_nbs,
            codigo_interno_contribuinte=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cIntContrib"),
            descricao_servico=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/xDescServ")
        )
        print('8/20')
        # Local da prestação
        LocalPrestacaoServico.create(
            servico=servico,
            codigo_localidade=obter_ou_criar_municipio(
                dados_xml,
                "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao"
            ),
            codigo_pais=obter_ou_criar_pais(
                extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cPaisPrestacao")
            ),
            codigo_pais_consumo=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cPaisConsum", tipo=int)
        )
        print('9/20')
        # Comércio Exterior (se houver)
        if "NFSe/infNFSe/DPS/infDPS/serv/comExt/mdPrestacao" in dados_xml:
            ComercioExterior.create(
                servico=servico,
                modo_prestacao=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/mdPrestacao", tipo=int),
                vinculo_prestador=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/vincPrest", tipo=int),
                tipo_moeda=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/tpMoeda"),
                valor_servico_moeda=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/vServMoeda", tipo=Decimal),
                mecanismo_apoio_prestador=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/mecAFComexP", tipo=int),
                mecanismo_apoio_tomador=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/mecAFComexT", tipo=int),
                movimentacao_temporaria_bens=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/movTempBens", tipo=int),
                numero_di=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/nDI"),
                numero_re=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/nRE"),
                indicador_mdic=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/comExt/mdic", tipo=int)
            )
        print('10/20')
        # Obra (se houver)
        if "NFSe/infNFSe/DPS/infDPS/serv/obra/cObra" in dados_xml:
            ObraConstrucao.create(
                servico=servico,
                inscricao_imobiliaria_fiscal=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/obra/inscImobFisc"),
                codigo_obra=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/obra/cObra"),
                endereco=criar_endereco_nacional(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/obra/end")
            )
        print('11/20')
        # Atividade de Evento (se houver)
        if "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/xNome" in dados_xml:
            AtividadeEvento.create(
                servico=servico,
                nome_evento=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/xNome"),
                data_inicio=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/dtIni", tipo=datetime),
                data_fim=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/dtFim", tipo=datetime),
                identificacao_atividade=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/idAtvEv"),
                endereco=criar_endereco_nacional(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/atvEvento/end")
            )
        print('12/20')
        # Exploração de Rodovia (se houver)
        if "NFSe/infNFSe/DPS/infDPS/serv/explRod/categVeic" in dados_xml:
            ExploracaoRodovia.create(
                servico=servico,
                categoria_veiculo=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/categVeic", tipo=int),
                numero_eixos=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/nEixos", tipo=int),
                tipo_rodagem=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/rodagem", tipo=int),
                sentido=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/sentido"),
                placa_veiculo=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/placa"),
                codigo_acesso_pedagio=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/codAcessoPed"),
                codigo_contrato=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/explRod/codContrato")
            )
        print('13/20')
        # Informações Complementares
        if "NFSe/infNFSe/DPS/infDPS/serv/infoCompl/idDocTec" in dados_xml:
            InformacoesComplementares.create(
                servico=servico,
                id_documento_tecnico=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/infoCompl/idDocTec"),
                documento_referencia=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/infoCompl/docRef"),
                informacoes_adicionais=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/infoCompl/xInfComp")
            )
        print('14/20')
        # ==================== VALORES ====================
        # Valores DPS
        valores_dps = ValoresDPS.create(
            dps=dps,
            valor_recebido_intermediario=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/vServPrest/vReceb", tipo=Decimal),
            valor_servico=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/vServPrest/vServ", tipo=Decimal),
            valor_desconto_incondicionado=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/vDescCondIncond/vDescIncond", tipo=Decimal),
            valor_desconto_condicionado=extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/vDescCondIncond/vDescCond", tipo=Decimal)
        )
        print('15/20')
        # Deduções/Reduções
        caminho_deducoes = "NFSe/infNFSe/DPS/infDPS/valores/vDedRed"
        
        # Verifica se há deduções por percentual ou valor
        pdr = extrair_valor(dados_xml, f"{caminho_deducoes}/pDR", tipo=Decimal)
        vdr = extrair_valor(dados_xml, f"{caminho_deducoes}/vDR", tipo=Decimal)
        
        if pdr or vdr:
            deducao = DeducaoReducao.create(
                valores_dps=valores_dps,
                percentual_deducao_reducao=pdr,
                valor_deducao_reducao=vdr
            )
        print('16/20')
        # Verifica se há documentos de dedução
        # (Aqui seria necessário iterar sobre múltiplos documentos se houver)
        
        # Valores NFS-e
        ValoresNFSe.create(
            nfse=nfse,
            valor_calculo_deducao_reducao=extrair_valor(dados_xml, "NFSe/infNFSe/valores/vCalcDR", tipo=Decimal),
            tpBM=extrair_valor(dados_xml, "NFSe/infNFSe/valores/tpBM"),
            valor_calculo_beneficio_municipal=extrair_valor(dados_xml, "NFSe/infNFSe/valores/vCalcBM", tipo=Decimal),
            valor_base_calculo=extrair_valor(dados_xml, "NFSe/infNFSe/valores/vBC", tipo=Decimal),
            aliquota_aplicada=extrair_valor(dados_xml, "NFSe/infNFSe/valores/pAliqAplic", tipo=Decimal),
            valor_issqn=extrair_valor(dados_xml, "NFSe/infNFSe/valores/vISSQN", tipo=Decimal),
            valor_total_retencoes=extrair_valor(dados_xml, "NFSe/infNFSe/valores/vTotalRet", tipo=Decimal),
            valor_liquido=extrair_valor(dados_xml, "NFSe/infNFSe/valores/vLiq", tipo=Decimal),
            outras_informacoes=extrair_valor(dados_xml, "NFSe/infNFSe/xOutInf")
        )
        print('17/20')
        # ==================== TRIBUTAÇÃO ====================
        # Tributação Municipal
        caminho_trib_mun = "NFSe/infNFSe/DPS/infDPS/valores/trib/tribMun"
        
        if f"{caminho_trib_mun}/tribISSQN" in dados_xml:
            tributacao_municipal = TributacaoMunicipal.create(
                valores_dps=valores_dps,
                tipo_tributacao_issqn=extrair_valor(dados_xml, f"{caminho_trib_mun}/tribISSQN", tipo=int),
                codigo_pais_resultado=extrair_valor(dados_xml, f"{caminho_trib_mun}/cPaisResult"),
                aliquota=extrair_valor(dados_xml, f"{caminho_trib_mun}/pAliq", tipo=Decimal),
                tipo_retencao_issqn=extrair_valor(dados_xml, f"{caminho_trib_mun}/tpRetISSQN", tipo=int)
            )
            
            # Benefício Municipal
            if f"{caminho_trib_mun}/BM/nBM" in dados_xml:
                BeneficioMunicipal.create(
                    tributacao_municipal=tributacao_municipal,
                    numero_bm=extrair_valor(dados_xml, f"{caminho_trib_mun}/BM/nBM", tipo=int),
                    valor_reducao_base_calculo=extrair_valor(dados_xml, f"{caminho_trib_mun}/BM/vRedBCBM", tipo=Decimal),
                    percentual_reducao_base_calculo=extrair_valor(dados_xml, f"{caminho_trib_mun}/BM/pRedBCBM", tipo=Decimal)
                )
            
            # Exigibilidade Suspensa
            if f"{caminho_trib_mun}/exigSusp/tpSusp" in dados_xml:
                ExigibilidadeSuspensa.create(
                    tributacao_municipal=tributacao_municipal,
                    tipo_suspensao=extrair_valor(dados_xml, f"{caminho_trib_mun}/exigSusp/tpSusp", tipo=int),
                    numero_processo=extrair_valor(dados_xml, f"{caminho_trib_mun}/exigSusp/nProcesso")
                )
            
            # Imunidade
            if f"{caminho_trib_mun}/tpImunidade" in dados_xml:
                Imunidade.create(
                    tributacao_municipal=tributacao_municipal,
                    tipo_imunidade=extrair_valor(dados_xml, f"{caminho_trib_mun}/tpImunidade", tipo=int)
                )
        print('18/20')
        # Tributação Federal
        caminho_trib_fed = "NFSe/infNFSe/DPS/infDPS/valores/trib/tribFed"
        
        if f"{caminho_trib_fed}/piscofins/CST" in dados_xml:
            tributacao_federal = TributacaoFederal.create(
                valores_dps=valores_dps,
                valor_retencao_cp=extrair_valor(dados_xml, f"{caminho_trib_fed}/vRetCP", tipo=Decimal),
                valor_retencao_irrf=extrair_valor(dados_xml, f"{caminho_trib_fed}/vRetIRRF", tipo=Decimal),
                valor_retencao_csll=extrair_valor(dados_xml, f"{caminho_trib_fed}/vRetCSLL", tipo=Decimal)
            )
            
            # PIS/COFINS
            piscofins = PISCOFINS.create(
                tributacao_federal=tributacao_federal,
                cst=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/CST", tipo=int),
                valor_base_calculo=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/vBCPisCofins", tipo=Decimal),
                aliquota_pis=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/pAliqPis", tipo=Decimal),
                aliquota_cofins=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/pAliqCofins", tipo=Decimal),
                valor_pis=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/vPis", tipo=Decimal),
                valor_cofins=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/vCofins", tipo=Decimal),
                tipo_retencao=extrair_valor(dados_xml, f"{caminho_trib_fed}/piscofins/tpRetPisCofins", tipo=int)
            )
        print('19/20')
        # Totais de Tributos (Lei 12.741/2012)
        caminho_tot_trib = "NFSe/infNFSe/DPS/infDPS/valores/trib/totTrib"
        
        if f"{caminho_tot_trib}/vTotTrib/vTotTribFed" in dados_xml:
            TotaisTributos.create(
                valores_dps=valores_dps,
                valor_total_tributos=extrair_valor(dados_xml, f"{caminho_tot_trib}/vTotTrib/vTotTrib", tipo=Decimal),
                valor_total_tributos_federais=extrair_valor(dados_xml, f"{caminho_tot_trib}/vTotTrib/vTotTribFed", tipo=Decimal),
                valor_total_tributos_estaduais=extrair_valor(dados_xml, f"{caminho_tot_trib}/vTotTrib/vTotTribEst", tipo=Decimal),
                valor_total_tributos_municipais=extrair_valor(dados_xml, f"{caminho_tot_trib}/vTotTrib/vTotTribMun", tipo=Decimal),
                percentual_total_tributos=extrair_valor(dados_xml, f"{caminho_tot_trib}/pTotTrib/pTotTrib", tipo=Decimal),
                percentual_total_tributos_federais=extrair_valor(dados_xml, f"{caminho_tot_trib}/pTotTrib/pTotTribFed", tipo=Decimal),
                percentual_total_tributos_estaduais=extrair_valor(dados_xml, f"{caminho_tot_trib}/pTotTrib/pTotTribEst", tipo=Decimal),
                percentual_total_tributos_municipais=extrair_valor(dados_xml, f"{caminho_tot_trib}/pTotTrib/pTotTribMun", tipo=Decimal),
                indicador_total_tributos=extrair_valor(dados_xml, f"{caminho_tot_trib}/indTotTrib", tipo=int),
                percentual_total_simples_nacional=extrair_valor(dados_xml, f"{caminho_tot_trib}/pTotTribSN", tipo=Decimal)
            )
        print('20/20')
        return nfse
        
    except Exception as e:
        print(f"Erro ao inserir NFS-e: {e}")
        raise




# ==================== FUNÇÃO DE TESTE ====================
def testar_insercao(caminho_xml):
    """
    Função auxiliar para testar a inserção.
    """
    try:
        # Conecta ao banco
        db.connect()
        
        # Insere a NFS-e
        nfse = inserir_nfse_xml(caminho_xml)
        
        print(f"\n=== Resumo da Inserção ===")
        print(f"NFS-e ID: {nfse.id}")
        print(f"Número: {nfse.numero_nfse}")
        print(f"Emitente: {nfse.emitente.razao_social}")
        print(f"Valor Líquido: {nfse.valores.valor_liquido if hasattr(nfse, 'valores') else 'N/A'}")
        
        return nfse
        
    except Exception as e:
        print(f"Erro no teste: {e}")
        raise
    finally:
        db.close()


# ==================== EXEMPLO DE USO ====================
if __name__ == "__main__":
    # Exemplo de uso
    caminho_arquivo = r"C:\Users\cfontes\Documents\PROJETOS_PYTHON\NFSeFlet\files\nfse_download\NFS-e Gerada\xml\53001081240281347000174000000028564726051777763150.xml"
    # db.drop_tables([DPS, NFSe, Municipio, Participante, EnderecoNacional, Contato], safe=True)
    # db.create_tables([Municipio, Contato, EnderecoNacional, Participante, NFSe, DPS], safe=True)
    # print("✅ Schema recriado com sucesso.")

    try:
        # z = criar_ou_obter_municipio(caminho_arquivo)
        g = criar_ou_obter_nota_fiscal_servico(caminho_arquivo)
        r = criar_dps_nota_fiscal_servico(caminho_arquivo)
        print("Inserção concluída com sucesso!")
    except Exception as e:
        print(f"Falha na inserção: {e}")
    finally:
        db.close()