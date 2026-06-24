# -------------------------------- Ajusted Path ---------------------------------------
from pathlib import Path
from pprint import pprint
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
# print(str(Path(__file__).parent.parent))
# -------------------------------- Ajusted Path ---------------------------------------
# modulo para funcões de inserção de dados da tabela dimensões
from datetime import datetime, date, time
from decimal import Decimal, InvalidOperation
import re
from sqlite3 import IntegrityError
from models import(
    db, CadastroUF, CadastroMunicipio, CadastroTributacaoNacional, CadastroNBS, ServicoCadastro,
    ParticipanteTipo, Participante, ServicoAliquota, CadastroVersaoAplicacao, NfseChave,
    NfseNfse, NfseValorTotal, NfseDpsDps
)
from apps.pwNFSe.utils import xml_para_dit_caminhos


def _extrair_valor(dicionario_caminhos, caminho, tipo=str, default=None):
    """
    Extrai e converte um valor do dicionário de caminhos XML.
    """
    valor = dicionario_caminhos.get(caminho, None)
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


def criar_ufs():
    ufs = {
        "AC": {"estado": "Acre", "regiao": "Norte"},
        "AL": {"estado": "Alagoas", "regiao": "Nordeste"},
        "AM": {"estado": "Amazonas", "regiao": "Norte"},
        "AP": {"estado": "Amapá", "regiao": "Norte"},
        "BA": {"estado": "Bahia", "regiao": "Nordeste"},
        "CE": {"estado": "Ceará", "regiao": "Nordeste"},
        "DF": {"estado": "Distrito Federal", "regiao": "Centro-Oeste"},
        "ES": {"estado": "Espírito Santo", "regiao": "Sudeste"},
        "GO": {"estado": "Goiás", "regiao": "Centro-Oeste"},
        "MA": {"estado": "Maranhão", "regiao": "Nordeste"},
        "MG": {"estado": "Minas Gerais", "regiao": "Sudeste"},
        "MS": {"estado": "Mato Grosso do Sul", "regiao": "Centro-Oeste"},
        "MT": {"estado": "Mato Grosso", "regiao": "Centro-Oeste"},
        "PA": {"estado": "Pará", "regiao": "Norte"},
        "PB": {"estado": "Paraíba", "regiao": "Nordeste"},
        "PE": {"estado": "Pernambuco", "regiao": "Nordeste"},
        "PI": {"estado": "Piauí", "regiao": "Nordeste"},
        "PR": {"estado": "Paraná", "regiao": "Sul"},
        "RJ": {"estado": "Rio de Janeiro", "regiao": "Sudeste"},
        "RN": {"estado": "Rio Grande do Norte", "regiao": "Nordeste"},
        "RO": {"estado": "Rondônia", "regiao": "Norte"},
        "RR": {"estado": "Roraima", "regiao": "Norte"},
        "RS": {"estado": "Rio Grande do Sul", "regiao": "Sul"},
        "SC": {"estado": "Santa Catarina", "regiao": "Sul"},
        "SE": {"estado": "Sergipe", "regiao": "Nordeste"},
        "SP": {"estado": "São Paulo", "regiao": "Sudeste"},
        "TO": {"estado": "Tocantins", "regiao": "Norte"}
    }

    try:
        # Conecta ao banco
        db.connect()

        for idx, val in ufs.items():
            sg_uf = idx
            ds_uf = val['estado']
            ds_rg = val['regiao']

            uf = CadastroUF.get_or_none(CadastroUF.uf == sg_uf)
            if uf is None:
                CadastroUF.create(
                    uf = sg_uf,
                    ds_uf = ds_uf,
                    regiao = ds_rg,
                )
            else:
                # UPDATE
                uf.ds_uf = ds_uf
                uf.regiao = ds_rg
                uf.save()
        db.close()
    except IntegrityError as e:
                print(str(e))
    finally:
        db.close()


def criar_municipios(dados_xml:dict):
    """Funcao para Criar ou Atualizar Municipio"""
    loc_emis = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/cLocEmi", int)
    loc_prest = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao", int)
    loc_incid = _extrair_valor(dados_xml, "NFSe/infNFSe/cLocIncid", int)
    locs = [loc_emis, loc_prest, loc_incid]
    try:
        # Conecta ao banco
        db.connect()
        for loc in locs:
            if loc is None: continue
            municipio = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == loc)
            if municipio is None:
                CadastroMunicipio.create(codigo = loc)
        db.close()
    except IntegrityError as e:
                print(str(e))
    finally:
        db.close()


def criar_tributacao_nacional(dados_xml:dict):
    """Funcao para Criar ou Atualizar tributacao nacional"""
    model = CadastroTributacaoNacional
    cd = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribNac", int)
    ds = _extrair_valor(dados_xml, "NFSe/infNFSe/xTribNac", str)
    cd_mun = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribMun", int)
    ds_mun = _extrair_valor(dados_xml, "NFSe/infNFSe/xTribMun", str)
        
    try:
        # Conecta ao banco
        db.connect()
        model_n = model.get_or_none(model.codigo == cd)
        if model_n is None:
                model.create(codigo = cd, descricao = ds, codigo_mun = cd_mun, descricao_mun = ds_mun)
        else:
             model_n.descricao = ds
             model_n.save()
        db.close()
    except IntegrityError as e:
                print(str(e))
    finally:
        db.close()


def criar_nbs(dados_xml:dict):
    """Funcao para Criar ou Atualizar nbs"""
    model = CadastroNBS
    cd = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS", int)
    ds = _extrair_valor(dados_xml, "NFSe/infNFSe/xNBS", str)
        
    try:
        # Conecta ao banco
        db.connect()
        model_n = model.get_or_none(model.codigo == cd)
        if model_n is None:
                model.create(codigo = cd, descricao = ds)
        else:
             model_n.descricao = ds
             model_n.save()
        db.close()
    except IntegrityError as e:
                print(str(e))
    finally:
        db.close()


def criar_cadastro_servico(dados_xml:dict):
    """Funcao para Criar ou Atualizar nbs"""
    model = ServicoCadastro       
    try:
        # Conecta ao banco
        db.connect()
        cd_trib_nac = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribNac", int)
        trib_id = CadastroTributacaoNacional.get_or_none(CadastroTributacaoNacional.codigo == cd_trib_nac).id
        # ----------------------------------------------------------------------------------------------------
        cd_nbs = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS", int)
        nbs_id = CadastroNBS.get_or_none(CadastroNBS.codigo == cd_nbs).id
        # ----------------------------------------------------------------------------------------------------
        ds = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/xDescServ", str)
        # ----------------------------------------------------------------------------------------------------
        model_n = model.get_or_none(
             (model.trib_nac_id == trib_id) &
             (model.nbs_id == nbs_id)
        )
        if model_n is None:
                model.create(trib_nac_id = trib_id, nbs_id = nbs_id, des_serv = ds)
        # else:
        #      model_n.descricao = ds
        #      model_n.save()
    except IntegrityError as e:
                print(str(e))
    finally:
        db.close()


def criar_tipo_participante():
    tipos = ['PRESTADOR', 'TOMADOR', 'INTERMEDIARIO', 'FORNECEDOR']
    try:
        # Conecta ao banco
        db.connect()

        for tipo in tipos:
            tipo_participante = ParticipanteTipo.get_or_none(ParticipanteTipo.tipo == tipo)
            if tipo_participante is None:
                ParticipanteTipo.create(tipo = tipo,)

        db.close()
    except IntegrityError as e:
                print(str(e))
    finally:
        db.close()


def criar_participante(dados_xml: dict):
    """ Função para Cadastrar CNPJ ou Campo CPF a partir dos dados do xml """
    model = Participante

    cam_emi = "NFSe/infNFSe/emit/"
    dct_emi = {
        "cnpj": _extrair_valor(dados_xml, cam_emi+"CNPJ", str),     
        "cpf" : _extrair_valor(dados_xml, cam_emi+"CPF", str),
        "nif": None,
        "ds_motv_nif": None,
        "nome" : _extrair_valor(dados_xml, cam_emi+"xNome", str),
        "fant" : _extrair_valor(dados_xml, cam_emi+"xFant", str),
        "im" : _extrair_valor(dados_xml, cam_emi+"IM", str),
        "op_simp_nac" : None,
        "rg_apu_trib_simp_nac" : None,
        "rg_esp_trib" : None,
    }
    
    cam_prest = "NFSe/infNFSe/DPS/infDPS/prest/"
    dct_prest = {
        "cnpj": _extrair_valor(dados_xml, cam_prest+"CNPJ", str),     
        "cpf" : _extrair_valor(dados_xml, cam_prest+"CPF", str),
        "nif": _extrair_valor(dados_xml, cam_prest+"NIF", int),
        "ds_motv_nif": None,
        "nome" : _extrair_valor(dados_xml, cam_prest+"xNome", str),
        "fant" : None,
        "im" : _extrair_valor(dados_xml, cam_prest+"IM", str),
        "op_simp_nac" : _extrair_valor(dados_xml, cam_prest+"regTrib/opSimpNac", int),
        "rg_apu_trib_simp_nac" : _extrair_valor(dados_xml, cam_prest+"regTrib/regApTribSN", int),
        "rg_esp_trib" : _extrair_valor(dados_xml, cam_prest+"regTrib/regEspTrib", int),
    }

    cam_toma = "NFSe/infNFSe/DPS/infDPS/toma/"
    dct_toma = {
        "cnpj": _extrair_valor(dados_xml, cam_toma+"CNPJ", str),     
        "cpf" : _extrair_valor(dados_xml, cam_toma+"CPF", str),
        "nif": _extrair_valor(dados_xml, cam_toma+"NIF", int),
        "ds_motv_nif": _extrair_valor(dados_xml, cam_toma+"cNaoNIF", int),
        "nome" : _extrair_valor(dados_xml, cam_toma+"xNome", str),
        "fant" : None,
        "im" : _extrair_valor(dados_xml, cam_toma+"IM", str),
        "op_simp_nac" : None,
        "rg_apu_trib_simp_nac" : None,
        "rg_esp_trib" : None,
    }

    cam_inter = "NFSe/infNFSe/DPS/infDPS/interm/"
    dct_inter = {
        "cnpj": _extrair_valor(dados_xml, cam_inter+"CNPJ", str),     
        "cpf" : _extrair_valor(dados_xml, cam_inter+"CPF", str),
        "nif": _extrair_valor(dados_xml, cam_inter+"NIF", int),
        "ds_motv_nif": _extrair_valor(dados_xml, cam_inter+"cNaoNIF", int),
        "nome" : _extrair_valor(dados_xml, cam_inter+"xNome", str),
        "fant" : None,
        "im" : _extrair_valor(dados_xml, cam_inter+"IM", str),
        "op_simp_nac" : None,
        "rg_apu_trib_simp_nac" : None,
        "rg_esp_trib" : None,
    }

    tipos = ['FORNECEDOR', 'PRESTADOR', 'TOMADOR', 'INTERMEDIARIO']
    dicts = [dct_emi, dct_prest, dct_toma, dct_inter]
    # Avaliar Lançamento cnpj ou cpf
    for idx, dct in enumerate(dicts,  start=0):
        if not dct['cnpj'] and not dct['cpf']:
            continue

        # buscar modelo
        tipo_id = ParticipanteTipo.get_or_none(ParticipanteTipo.tipo == tipos[idx])  
        model_n = model.get_or_none(
            (model.tipo == tipo_id.id) &
            (model.cnpj == dct['cnpj']) &
            (model.cpf == dct['cpf'])
        )     

        if model_n is None:
            model.create(
                tipo = tipo_id.id,
                cnpj = dct['cnpj'],
                cpf = dct['cpf'],
                nif = dct['nif'],
                ds_motv_nif = dct['ds_motv_nif'],
                des_nome = dct['nome'],
                des_fant = dct['fant'],
                ins_mun = dct['im'],
                op_simples_nac = dct['op_simp_nac'],
                reg_apu_trib_simp_nac = dct['rg_apu_trib_simp_nac'],
                reg_esp_trib = dct['rg_esp_trib'],
            )
        else:
             # update
            model_n.nif = dct['nif']
            model_n.ds_motv_nif = dct['ds_motv_nif']
            model_n.des_nome = dct['nome']
            model_n.des_fant = dct['fant']
            model_n.ins_mun = dct['im']
            model_n.op_simples_nac = dct['op_simp_nac']
            model_n.reg_apu_trib_simp_nac = dct['rg_apu_trib_simp_nac']
            model_n.reg_esp_trib = dct['rg_esp_trib'] 
            model_n.save()


def criar_servico_aliquota(dados_xml:dict):
    try:
        #db.connect()
        model = ServicoAliquota
        cd_loc_emis = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/cLocEmi", int)
        id_loc_emis = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == cd_loc_emis).id

        cd_loc_prest = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao", int)
        id_loc_prest = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == cd_loc_prest).id
        
        cd_loc_incid = _extrair_valor(dados_xml, "NFSe/infNFSe/cLocIncid", int)
        id_loc_incid = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == cd_loc_incid).id
        
        cd_trib_nac = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribNac", int)
        id_trib_nac = CadastroTributacaoNacional.get_or_none(CadastroTributacaoNacional.codigo == cd_trib_nac).id
        cd_nbs = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS", int)
        id_nbs = CadastroNBS.get_or_none(CadastroNBS.codigo == cd_nbs).id
        
        ds = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/xDescServ", str)
        md_servico = ServicoCadastro.get_or_none(
            (ServicoCadastro.trib_nac_id == id_trib_nac) &
            (ServicoCadastro.nbs_id == id_nbs)
        )
        id_servico = md_servico.id

        st_trib_iss_qn = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/trib/tribMun/tribISSQN", int)
        st_trib_iss_ret = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/trib/tribMun/tpRetISSQN", int)
        vl_trib_iss_aliq = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/valores/trib/tribMun/pAliq", float)

        # criar o modelo de aliquota servico
        model_n = model.get_or_none(
            (model.local_emi == id_loc_emis) &
            (model.local_prest == id_loc_prest) &
            (model.local_incid == id_loc_incid) &
            (model.servico_id == id_servico) &
            (model.vl_aliq == vl_trib_iss_aliq)
        )

        if model_n is None:
            model.create(
                local_emi = id_loc_emis,
                local_prest = id_loc_prest,
                local_incid = id_loc_incid,
                servico_id = id_servico,
                trib_iss_qn = st_trib_iss_qn,
                trib_ret_iss_qn = st_trib_iss_ret,
                vl_aliq = vl_trib_iss_aliq,
            )
        else:
            model_n.trib_iss_qn = st_trib_iss_qn
            model_n.trib_ret_iss_qn = st_trib_iss_ret
            model_n.save()

        db.close()
    
    except IntegrityError as e:
        print(str(e))
    finally:
        db.close()


def criar_versao_aplicacao(dados_xml:dict):
    model = CadastroVersaoAplicacao
    ds_ver_aplic = _extrair_valor(dados_xml, "NFSe/infNFSe/verAplic", str)
    md_ver_aplic = model.get_or_none(model.versao_aplicacao == ds_ver_aplic)

    if md_ver_aplic is None:
         model.create(
              versao_aplicacao = ds_ver_aplic
         )
    else:
         md_ver_aplic.versao_aplicacao = ds_ver_aplic
         md_ver_aplic.save()


def criar_nfse_chave(dados_xml:dict):
    model = NfseChave
    ds = _extrair_valor(dados_xml, "NFSe/infNFSe@Id", str)
    md_chv = model.get_or_none(model.chave_acesso == ds)

    if md_chv is None:
         model.create(
              chave_acesso = ds
         )


def _nfse_extrair_data_hora(dh_proc:str):
    dh_proc = dh_proc.split('T')

    dt_list = dh_proc[0].split('-')
    ano = int(dt_list[0])
    mes = int(dt_list[1])
    dia = int(dt_list[2])
    dta_emissao = date(ano, mes, dia)

    hr_list = dh_proc[1].split('-')[0].split(':')
    hora = int(hr_list[0])
    minuto = int(hr_list[1])
    segundo = int(hr_list[2])
    hr_emissao = time(hour=hora, minute=minuto, second=segundo)

    return dta_emissao, hr_emissao


def criar_nfse_nfse(dados_xml:dict):
    # ----------------------------------------------------------------------------------------------------------------
    nr_nfse = _extrair_valor(dados_xml, "NFSe/infNFSe/nNFSe", int)
    nr_amb_ger = _extrair_valor(dados_xml, "NFSe/infNFSe/ambGer", int)
    tp_emis = _extrair_valor(dados_xml, "NFSe/infNFSe/tpEmis", int)
    nr_proc_emis = _extrair_valor(dados_xml, "NFSe/infNFSe/procEmi", int)
    nr_sit_poss = _extrair_valor(dados_xml, "NFSe/infNFSe/cStat", int)
    nr_dfe = _extrair_valor(dados_xml, "NFSe/infNFSe/nDFe", int)
    # ----------------------------------------------------------------------------------------------------------------
    dh_proc = _extrair_valor(dados_xml, "NFSe/infNFSe/dhProc", str)
    dta_emissao, hr_emissao = _nfse_extrair_data_hora(dh_proc)
    # ----------------------------------------------------------------------------------------------------------------
    chave_ds = _extrair_valor(dados_xml, "NFSe/infNFSe@Id", str)
    chave_id = NfseChave.get_or_none(NfseChave.chave_acesso == chave_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    loc_emi_ds = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/cLocEmi", int)
    loc_emi_id = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == loc_emi_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    loc_pre_ds = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao", int)
    loc_pre_id = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == loc_pre_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    loc_inc_ds = _extrair_valor(dados_xml, "NFSe/infNFSe/cLocIncid", int)
    loc_inc_id = CadastroMunicipio.get_or_none(CadastroMunicipio.codigo == loc_inc_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    trib_nac_ds = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribNac", int)
    trib_nac_id = CadastroTributacaoNacional.get_or_none(CadastroTributacaoNacional.codigo == trib_nac_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    nbs_ds = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS", int)
    nbs_id = CadastroNBS.get_or_none(CadastroNBS.codigo == nbs_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    ver_aplic_ds = _extrair_valor(dados_xml, "NFSe/infNFSe/verAplic", str)
    ver_aplic_id = CadastroVersaoAplicacao.get_or_none(CadastroVersaoAplicacao.versao_aplicacao == ver_aplic_ds).id
    # ----------------------------------------------------------------------------------------------------------------
    # criar dados do cabelhaço da nota fiscal --- ID
    md_nfse = NfseNfse.get_or_none(NfseNfse.chave_id==chave_id)
    if md_nfse is None:
         NfseNfse.create(
            chave_id = chave_id,
            loc_emi_id = loc_emi_id,
            loc_pre_id = loc_pre_id,
            nr_nfse = nr_nfse,
            loc_inc_id = loc_inc_id,
            trib_nac_id = trib_nac_id,
            nbs_id = nbs_id,
            ver_aplic_id = ver_aplic_id,
            nr_amb_ger = nr_amb_ger,
            tp_emis = tp_emis,
            nr_proc_emis = nr_proc_emis,
            nr_sit_poss = nr_sit_poss,
            nr_dfe = nr_dfe,
            dt_emis = dta_emissao,
            hr_emis = hr_emissao,
        )


def criar_nfse_valortotal(dados_xml:dict):
    # ----------------------------------------------------------------------------------------------------------------
    chave_ds = _extrair_valor(dados_xml, "NFSe/infNFSe@Id", str)
    chave_id = NfseChave.get_or_none(NfseChave.chave_acesso == chave_ds).id
    nfse_id = NfseNfse.get_or_none(NfseNfse.chave_id == chave_id).id
    # ----------------------------------------------------------------------------------------------------------------
    # criar dados do cabelhaço da nota fiscal --- ID
    md_nfse = NfseValorTotal.get_or_none(NfseValorTotal.nfse_id==nfse_id)
    main_val = 'NFSe/infNFSe/valores/'
    if md_nfse is None:
        NfseValorTotal.create(
            nfse_id = nfse_id,
            vl_cal_ded_red = _extrair_valor(dados_xml, main_val+"vCalcDR", float, default=0),
            tp_benef = _extrair_valor(dados_xml,main_val+"tpBM", float, default=0),
            vl_cal_benef = _extrair_valor(dados_xml,main_val+"vCalcBM", float, default=0),
            vl_base_cal =  _extrair_valor(dados_xml,main_val+"vBC", float, default=0),
            vl_aliq_aplic = _extrair_valor(dados_xml,main_val+"pAliqAplic", float, default=0),
            vl_iss_qn = _extrair_valor(dados_xml,main_val+"vISSQN", float, default=0),
            vl_total_ret = _extrair_valor(dados_xml,main_val+"vTotalRet", float, default=0),
            vl_total_liq = _extrair_valor(dados_xml,main_val+"vLiq", float, default=0),
        )
    # ----------------------------------------------------------------------------------------------------------------


def criar_nfse_dps_dps(dados_xml:dict):

    # Configurções
    model_cnpj = Participante
    model_serv = ServicoCadastro
    model_mun = CadastroMunicipio
    model_alq = ServicoAliquota
    DPS = NfseDpsDps

    # ----------------------------------------------------------------------------------------------------------------
    chave_ds = _extrair_valor(dados_xml, "NFSe/infNFSe@Id", str)
    chave_id = NfseChave.get_or_none(NfseChave.chave_acesso == chave_ds).id
    nfse_id = NfseNfse.get_or_none(NfseNfse.chave_id == chave_id).id
    # ----------------------------------------------------------------------------------------------------------------
    # Servico
    # ------- Emissao | Prestacao | Incidencia
    municipios = {
        'emissao': _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/cLocEmi", int),
        'prestacao': _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/locPrest/cLocPrestacao", int),
        'incidencia': _extrair_valor(dados_xml, "NFSe/infNFSe/cLocIncid", int),
    }
    mun_id = {}
    for chv, mun in municipios.items():
        em = model_mun.get_or_none(model_mun.codigo == mun).id
        mun_id[chv] = em 
    # ----------------------------------------------------------------------------------------------------------------        
    # ------- Cadastro Servico
    cd_trib_nac = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cTribNac", int)
    trib_id = CadastroTributacaoNacional.get_or_none(CadastroTributacaoNacional.codigo == cd_trib_nac).id
    cd_nbs = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/serv/cServ/cNBS", int)
    nbs_id = CadastroNBS.get_or_none(CadastroNBS.codigo == cd_nbs).id
    servico_id = model_serv.get_or_none(model_serv.trib_nac_id == trib_id & model_serv.nbs_id == nbs_id).id
    serv_aliq = model_alq.get_or_none(
            (model_alq.local_emi==mun_id['emissao']) &
            (model_alq.local_prest==mun_id['prestacao']) & 
            (model_alq.local_incid==mun_id['incidencia']) &
            (model_alq.servico_id==servico_id)  
        ).id
    serv_aliq_id = serv_aliq.id 
    # ----------------------------------------------------------------------------------------------------------------
    cnpj_prest = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/prest/CNPJ", str)
    cnpj_toma = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/toma/CNPJ", str)
    cnpj_inter = _extrair_valor(dados_xml, "NFSe/infNFSe/DPS/infDPS/interm/CNPJ", str)

    tipos = ['PRESTADOR', 'TOMADOR', 'INTERMEDIARIO']
    dic_cnpj = [cnpj_prest, cnpj_toma, cnpj_inter]
    dic_id = {}

    for idx, tipo in enumerate(tipos, start=0):
        tipo_id = ParticipanteTipo.get_or_none(ParticipanteTipo.tipo == tipos[idx])  
        md_cnpj = model_cnpj.get_or_none(
            (model_cnpj.tipo == tipo_id.id) &
            (model_cnpj.cnpj == dic_cnpj['cnpj'])
        )
        dic_id[tipo]= md_cnpj.id

    prestador_id = dic_id.get('PRESTADOR', 0)
    tomador_id  = dic_id.get('TOMADOR', 0) 
    intermediario_id  = dic_id.get('INTERMEDIARIO', 0) 
    
    # ----------------------------------------------------------------------------------------------------------------
    main_path = "NFSe/infNFSe/DPS/infDPS/"

    dt_hr_emi = _extrair_valor(dados_xml, main_path+"dhEmi", str)
    dta, hr = _nfse_extrair_data_hora(dt_hr_emi)
    dt_comp_str = _extrair_valor(dados_xml, main_path+"dCompet", str).split('-')

    dps_id = _extrair_valor(dados_xml, main_path+"id", str)
    tp_amb = _extrair_valor(dados_xml, main_path+"tpAmb", str)
    dt_emi = dta
    hr_emi  = hr
    vr_apli = _extrair_valor(dados_xml, main_path+"verAplic", str)
    cd_serie = _extrair_valor(dados_xml, main_path+"serie", int)
    nr_dps = _extrair_valor(dados_xml, main_path+"nDPS", int)
    dt_comp = date(dt_comp_str[2], dt_comp_str[1], dt_comp_str[0])
    tp_emit = _extrair_valor(dados_xml, main_path+"tpEmit", int)

    md_dps = DPS.get_or_none(DPS.dps_id == dps_id)
    if md_dps is None:
         md_dps.create(
            nfse_id = nfse_id,
            dps_id = dps_id,
            tp_amb = tp_amb,
            dt_emi = dt_emi,
            hr_emi  = hr_emi,
            vr_apli = vr_apli,
            cd_serie = cd_serie,
            nr_dps = nr_dps,
            dt_comp = dt_comp,
            tp_emit = tp_emit,
            loc_emi_id = mun_id['emissao'],
            prestador_id = prestador_id,
            tomador_id = tomador_id,
            intermediario_id = intermediario_id,
            serv_aliq = serv_aliq_id,
            # Valores
            vl_recebimento = _extrair_valor(dados_xml, main_path+"valores/vServPrest/vReceb", float),
            vl_servico = _extrair_valor(dados_xml, main_path+"valores/vServPrest/vServ", float), 
            vl_desc_incondicional = _extrair_valor(dados_xml, main_path+"valores/vDescCondIncond/vDescIncond", float),
            vl_desc_condicional = _extrair_valor(dados_xml, main_path+"valores/vDescCondIncond/vDescCond", float),
            vl_aliq_ded_red = _extrair_valor(dados_xml, main_path+"valores/vDedRed/pDR", float), 
            vl_ded_red = _extrair_valor(dados_xml, main_path+"valores/vDedRed/vDR", float), 
        )


def criar_nfse_dps_trib(dados_xml:dict):
    ...


def criar_nfse_dps_subst(dados_xml:dict):
    ...


def criar_nfse_dps_infcompl(dados_xml:dict):
    ...



if __name__ == '__main__':
    caminho_arquivo = r"C:\Users\cfontes\Documents\PROJETOS_PYTHON\NFSeFlet\files\nfse_download\NFS-e Gerada\xml\53001081240281347000174000000028564726051777763150.xml"
    dados_xml = xml_para_dit_caminhos(caminho_arquivo)
    # for idx, xml in dados_xml.items():
    #      print(idx)
    print("=" * 50)
    r0 = criar_ufs()
    r1 = criar_municipios(dados_xml)
    r2 = criar_tributacao_nacional(dados_xml)
    r3 = criar_nbs(dados_xml)
    r4 = criar_cadastro_servico(dados_xml)
    r5 = criar_tipo_participante()
    r6 = criar_participante(dados_xml)
    r7 = criar_servico_aliquota(dados_xml)
    r8 = criar_versao_aplicacao(dados_xml)
    r8 = criar_nfse_chave(dados_xml)
    r9 = criar_nfse_nfse(dados_xml)
    r10 = criar_nfse_nfse(dados_xml)
    r11 = criar_nfse_valortotal(dados_xml)