# -------------------------------- Ajusted Path ---------------------------------------
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent))
# -------------------------------- Code -----------------------------------------------
from playwright.sync_api import sync_playwright
from datetime import datetime, date
import calendar
from setup.settings import DIRS
import asyncio
import sys
import xml.etree.ElementTree as ET
import os
from pathlib import Path


DIR_NFSE = DIRS['DIR_NFSE']['NFSE_DOWNLOAD']

def login_nfse_certificado(dta_inicial, dta_final):   
    r = create_defults_folders()
    tipos = lista_tipo_arquivo()  # Ex: [("Download XML", "xml"), ("Download DANFS-e", "pdf")]
    
    strDtaIni = dta_inicial
    strDtaFim = dta_final

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, channel="chrome")
        context = browser.new_context(accept_downloads=True)  # Habilita downloads
        page = context.new_page()

        print("🌐 Acessando o portal...")
        page.goto("https://www.nfse.gov.br/EmissorNacional/Login", wait_until="networkidle")

        try:
            # === LOGIN COM CERTIFICADO ===
            botao = page.locator('a:has-text("Certificado Digital"), .login-certificado-digital').first
            if not botao.is_visible():
                botao = page.locator('.login-certificado-digital')
            botao.wait_for(state="visible", timeout=10000)
            # botao.click()
            print("✅ Clique realizado. Selecione o certificado no sistema operacional...")
            botao.click()

            page.wait_for_timeout(3000)  # Aguarda janela do SO

            # === ACESSAR NFS-e RECEBIDAS ===
            page.get_by_role("link").filter(has_text="NFS-e Recebidas").click()
            # page.get_by_role("link", name="NFS-e Recebidas").click()
            page.wait_for_load_state("networkidle")

            # === PROCESSAR INTERVALOS DE DATA ===
            intervalos = intervalos_mensais_str(strDtaIni, strDtaFim)

            for inicio, fim in intervalos:
                page.locator("#datainicio").fill(inicio)
                page.locator("#datafim").fill(fim)
                page.get_by_role("button", name="Filtrar").click()
                
                # Aguarda tabela carregar
                page.locator("tbody tr").first.wait_for(state="visible", timeout=20000)

                strReg = page.get_by_text('Total de ').inner_text().split(' ')[2]
                x = int(strReg)
                y = 0
                # === PAGINAÇÃO: Loop até não haver próximo ===
                while True:
                    # Pega TODAS as linhas visíveis da tabela (escopo seguro)
                    linhas = page.locator("tbody tr").all()
                    
                    if not linhas:
                        print("⚠️ Nenhuma nota encontrada neste intervalo.")
                        break

                    print(f"📦 Processando {len(linhas)} notas na página atual...")

                    for linha in linhas:
                        # ... [código de captura do strStatus mantido] ...
                        dta_hora = linha.locator(".td-datahora").inner_text()
                        ds_cnpj = linha.locator(".td-texto-grande span").inner_text()
                        ds_comp = linha.locator(".td-competencia").inner_text()
                        ds_valor = linha.locator(".td-valor").inner_text()
                        img_status = linha.locator(".td-situacao img")
                        
                        if img_status.count() > 0:
                            strStatus = (img_status.first.get_attribute("data-original-title") or 
                                        img_status.first.get_attribute("title") or 
                                        "Status_Desconhecido").strip().replace("/", "-")
                        else:
                            strStatus = "Sem_Imagem"

                        print(dta_hora, ds_cnpj, ds_comp, ds_valor, strStatus)

                        # linha.locator(".icone-trigger").click()
                        # loop para Baixar arquivos em xml e pdf
                        for tipo in tipos:
                            tipo_busca = tipo[0]
                            tipo_arquivo = tipo[1]
                            # -----
                            toggle = linha.locator(".icone-trigger")
                            if toggle.count() > 0:
                                toggle.first.click()
                                toggle.first.wait_for(state="visible", timeout=5000)
                                # page.wait_for_timeout(300)
                            # -----
                                with page.expect_download() as download_info:
                                    # linha.locator("a:has-text('Download DANFS-e')").first.click(force=True)
                                    linha.locator(f"a:has-text('{tipo_busca}')").first.click(force=True)

                                    download = download_info.value
                                    create_folder_if_not_exists(str(Path(DIR_NFSE) / strStatus))
                                    create_folder_if_not_exists(str(Path(DIR_NFSE)  / strStatus / tipo_arquivo))
                                    file_full_name = str(Path(DIR_NFSE) / strStatus / tipo_arquivo / download.suggested_filename)
                                    download.save_as(file_full_name)
                                    print(f"Arquivo baixado: {download.suggested_filename}")

                        y = y + 1
                        
                    # === VERIFICA PRÓXIMA PÁGINA ===
                    btn_proxima = page.get_by_role("link", name="")  # Ícone "próximo"
                    # if btn_proxima.count() > 0 and btn_proxima.first.is_enabled():
                    if y < x:
                        print("🔁 Indo para próxima página...")
                        btn_proxima.first.click()
                        page.wait_for_load_state("networkidle")
                        page.wait_for_timeout(1000)  # Aguarda renderização
                    else:
                        print("✅ Última página alcançada.")
                        break

        except Exception as e:
            print(f"❌ Erro crítico: {type(e).__name__} - {e}")
            page.screenshot(path="erro_nfse_debug.png", full_page=True)
            print("📸 Screenshot salvo como 'erro_nfse_debug.png'")
            import traceback
            traceback.print_exc()

        finally:
            print("🔒 Fechando navegador...")
            browser.close()  # Corrigido: era 'navegador.close'


def lista_tipo_arquivo():
    lst = [
        ("Download DANFS-e", "pdf"),
        ("Download XML", "xml")
    ]

    return lst


def intervalos_mensais_str(data_inicial: str, data_final: str):
    # Converte strings dd/mm/yyyy para date
    dt_ini = datetime.strptime(data_inicial, "%d/%m/%Y").date()
    dt_fim = datetime.strptime(data_final, "%d/%m/%Y").date()
    intervalos = []
    ano = dt_ini.year
    mes = dt_ini.month
    while True:
        primeiro_dia = date(ano, mes, 1)
        ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])
        inicio_intervalo = max(primeiro_dia, dt_ini)
        fim_intervalo = min(ultimo_dia, dt_fim)
        # Converte datas para o formato dd/mm/yyyy
        intervalo_str = (
            inicio_intervalo.strftime("%d/%m/%Y"),
            fim_intervalo.strftime("%d/%m/%Y")
        )
        intervalos.append(intervalo_str)
        # Encerra quando chegar ao mês final
        if ano == dt_fim.year and mes == dt_fim.month:
            break
        # Avança um mês
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return intervalos


def create_defults_folders():
    folders = DIRS['DIR_NFSE']
    for folder in folders:
        _path = Path(folders[folder])
        if _path.is_dir():
            ...
        else:
            _path.mkdir()
        

def create_folder_if_not_exists(path_folder:str):
    Path(path_folder).mkdir(parents=True, exist_ok=True)


def xml_para_dit_caminhos(caminho_arquivo):
    """
    Lê um arquivo XML e retorna um dicionário mapeando 
    o caminho de cada tag ao seu respectivo valor de texto.
    """
    try:
        tree = ET.parse(caminho_arquivo)
        root = tree.getroot()
        resultado = {}
        
        def iterar_elementos(elemento, caminho_atual=""):
            # Remove possíveis namespaces da tag
            tag_limpa = elemento.tag.split('}')[-1]
            novo_caminho = f"{caminho_atual}/{tag_limpa}" if caminho_atual else tag_limpa
            
            # 1. CAPTURA OS ATRIBUTOS DA TAG (Seja ela mãe, intermediária ou filha)
            for chave_attr, valor_attr in elemento.attrib.items():
                # Define uma sintaxe clara para diferenciar atributos (ex: @id ou [id])
                caminho_atributo = f"{novo_caminho}@{chave_attr}"
                resultado[caminho_atributo] = valor_attr.strip()
            
            # 2. CAPTURA O TEXTO (Se houver e for nó folha)
            if elemento.text and elemento.text.strip() and len(elemento) == 0:
                resultado[novo_caminho] = elemento.text.strip()
                
            for filho in elemento:
                iterar_elementos(filho, novo_caminho)
                
        iterar_elementos(root)
        return resultado

    except (ET.ParseError, FileNotFoundError) as e:
        print(f"Erro: {e}")
        return {}




if __name__ == "__main__":
    d_ini = '01/05/2026'
    d_fim = '05/05/2026'
    # r = create_defults_folders()
    # login_nfse_certificado(d_ini, d_fim)
    DIRS = Path(DIR_NFSE) / 'NFS-e Gerada' / 'xml'
    files = os.listdir(DIRS)
    for file in files:
        full_name_file = DIRS / file
        dct_data = xml_para_dit_caminhos(full_name_file)
        
        # for idx, item in dct_data.items():
        #   print(idx, item, sep=': ')
        
        print(dct_data['NFSe/infNFSe/emit/CNPJ'], dct_data[f'NFSe/infNFSe@Id'], dct_data.get('NFSe/infNFSe/valores/vLiq', 0), sep='|')