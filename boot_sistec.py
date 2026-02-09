from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ServicoChrome
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import time
import unicodedata
import re
import pandas as pd
from pathlib import Path


URL_SISTEC = "https://sistec.mec.gov.br/consultapublicaunidadeensino#"

UF_ALVO = "CE"
MAXIMO_CIDADES = 118
PAUSA_ENTRE_CIDADES = 2.3

XPATH_CONTAINER_ESTADOS = "/html/body/div[1]/div[3]/div/div[3]/div/table/tbody/tr[2]/td[1]"
XPATH_BASE_MUNICIPIOS = "/html/body/div[1]/div[3]/div/div[3]/div/table/tbody/tr[2]/td[1]/div/div/div/div[6]/div[2]/div"

INDICE_UF_FALLBACK = {"AC": 1, "CE": 6}

NOME_UF = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas", "BA": "Bahia", "CE": "Ceará",
    "DF": "Distrito Federal", "ES": "Espírito Santo", "GO": "Goiás", "MA": "Maranhão",
    "MT": "Mato Grosso", "MS": "Mato Grosso do Sul", "MG": "Minas Gerais", "PA": "Pará",
    "PB": "Paraíba", "PR": "Paraná", "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte", "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima",
    "SC": "Santa Catarina", "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
}


def normalizar_texto(texto: str) -> str:
    
    texto = unicodedata.normalize("NFKD", texto or "")
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.strip().lower()


def limpar_espacos(texto: str) -> str:

    return re.sub(r"\s+", " ", (texto or "").strip())

def clicar_com_js(driver, elemento):

    driver.execute_script("arguments[0].scrollIntoView({block:'center'});", elemento)
    time.sleep(0.3)

    try:
        elemento.click()

    except Exception:

        driver.execute_script("arguments[0].click();", elemento)


def separar_nome_e_codigo(texto: str):

    texto = limpar_espacos(texto)
    match = re.search(r"\[\s*([0-9]+)\s*\]\s*$", texto)

    if match:

        codigo = match.group(1)
        nome = limpar_espacos(re.sub(r"\[\s*[0-9]+\s*\]\s*$", "", texto))
        return nome, codigo

    return texto, ""


def remover_sufixos_parenteticos(nome: str) -> str:

    texto = limpar_espacos(nome)
    letras = r"[A-Za-zÀ-ÖØ-öø-ÿ]*"
    padrao_sufixo = re.compile(rf"(?:\s*[-–—]\s*)?{letras}\(\s*\d+\s*\){letras}\s*$")

    while True:

        novo = re.sub(padrao_sufixo, "", texto)

        if novo == texto:

            break

        texto = limpar_espacos(novo)

    texto = re.sub(r"[-–—/]+\s*$", "", texto).strip()
    return texto


def main():

    opcoes = webdriver.ChromeOptions()
    opcoes.add_argument("--start-maximized")

    driver = webdriver.Chrome(
        service=ServicoChrome(ChromeDriverManager().install()),
        options=opcoes
    )

    try:

        driver.get(URL_SISTEC)

        # 1) "clique aqui"
        xpath_clique_aqui = "//*[self::a or self::button][contains(translate(normalize-space(.),'CLIQUE AQUI','clique aqui'),'clique aqui')]"
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, xpath_clique_aqui))).click()
        print("Cliquei em 'clique aqui'.")

        # 2) clicar UF
        WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, XPATH_CONTAINER_ESTADOS)))
        time.sleep(0.7)

        h3_estados = driver.find_elements(By.XPATH, XPATH_CONTAINER_ESTADOS + "//h3")
        textos_estados = [h.text.strip() for h in h3_estados]

        nome_uf_alvo = NOME_UF.get(UF_ALVO, UF_ALVO)
        nome_uf_alvo_norm = normalizar_texto(nome_uf_alvo)

        elemento_uf = None

        for h3, texto in zip(h3_estados, textos_estados):

            if texto and (normalizar_texto(texto) == nome_uf_alvo_norm or nome_uf_alvo_norm in normalizar_texto(texto)):
                
                elemento_uf = h3
                break

        if not elemento_uf and UF_ALVO.upper() in INDICE_UF_FALLBACK:

            indice = INDICE_UF_FALLBACK[UF_ALVO.upper()]
            xpath_fallback = f"{XPATH_CONTAINER_ESTADOS}/div/div/div/h3[{indice}]"
            candidatos = driver.find_elements(By.XPATH, xpath_fallback)
            
            if candidatos:

                elemento_uf = candidatos[0]

        if not elemento_uf:

            raise RuntimeError(f"Não localizei o estado '{nome_uf_alvo}'.")

        clicar_com_js(driver, elemento_uf)
        print(f"Estado selecionado: {nome_uf_alvo}")
        time.sleep(1.0)

        # 3) obter municípios
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, XPATH_BASE_MUNICIPIOS + "/h3[1]"))
        )

        elementos_municipios = driver.find_elements(By.XPATH, XPATH_BASE_MUNICIPIOS + "/h3")
        
        total_listados = len(elementos_municipios)

        total_processar = total_listados if MAXIMO_CIDADES is None else min(MAXIMO_CIDADES, total_listados)
        
        print(f"Municípios listados: {total_listados} | Processando: {total_processar}")

        registros = []

        # 4) loop nas cidades
        for indice_municipio in range(1, total_processar + 1):

            xpath_municipio = f"{XPATH_BASE_MUNICIPIOS}/h3[{indice_municipio}]"
            xpath_painel = f"{xpath_municipio}/following-sibling::div[1]"
            xpath_titulo = f"{xpath_painel}/div[1]/h3"
            xpath_lista = f"{xpath_painel}/div[2]/div"

            try:

                elemento_municipio = driver.find_element(By.XPATH, xpath_municipio)

            except Exception:

                print(f"Município {indice_municipio} não encontrado. Pulando.")
                continue

            nome_municipio = limpar_espacos(elemento_municipio.text)

            if not nome_municipio:

                print(f"Município {indice_municipio} com texto vazio. Pulando.")
                continue

            clicar_com_js(driver, elemento_municipio)
            print(f"\n{indice_municipio:02d}. Município: {nome_municipio}")
            time.sleep(PAUSA_ENTRE_CIDADES)

            # esperar painel aparecer
            try:
                
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath_painel)))
            
            except Exception:

                print("Painel não visível, tentando novamente...")
                clicar_com_js(driver, elemento_municipio)
                time.sleep(PAUSA_ENTRE_CIDADES)
                WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.XPATH, xpath_painel)))

            # verificar/printar título
            texto_titulo = ""

            try:

                elemento_titulo = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, xpath_titulo))
                )

                texto_titulo = limpar_espacos(elemento_titulo.text)

            except Exception:

                try:

                    elemento_titulo = driver.find_element(By.XPATH, xpath_painel + "//h3[1]")
                    texto_titulo = limpar_espacos(elemento_titulo.text)

                except Exception:
                    pass

            if texto_titulo:

                if "unidade" in normalizar_texto(texto_titulo) and "ensino" in normalizar_texto(texto_titulo):
                    
                    print(f"Título detectado: {texto_titulo}")

                else:

                    print(f"Título diferente encontrado: {texto_titulo}")
            else:

                print("Título do painel não encontrado.")

            # coletar instituições
            instituicoes = []

            try:

                WebDriverWait(driver, 12).until(EC.presence_of_element_located((By.XPATH, xpath_lista + "/h3[1]")))
                h3_instituicoes = driver.find_elements(By.XPATH, xpath_lista + "/h3")

            except Exception:

                h3_instituicoes = []

            for h3 in h3_instituicoes:

                texto_bruto = limpar_espacos(h3.text)

                if not texto_bruto:

                    spans = h3.find_elements(By.XPATH, ".//span")

                    if spans:

                        texto_bruto = limpar_espacos(spans[0].text)

                if not texto_bruto:

                    continue

                # 1) extrai CODIGO_SISTEC
                nome_instituicao, codigo_sistec = separar_nome_e_codigo(texto_bruto)

                # 2) remove sufixos
                nome_instituicao = remover_sufixos_parenteticos(nome_instituicao)

                instituicoes.append((nome_instituicao, codigo_sistec))

            if not instituicoes:

                print("Nenhuma instituição encontrada.")
            else:

                print(f"{len(instituicoes)} instituição(ões) encontradas.")

                for nome_instituicao, codigo_sistec in instituicoes:

                    registros.append({
                        "ESTADO": nome_uf_alvo,
                        "MUNICIPIO": nome_municipio,
                        "INSTITUICAO": nome_instituicao,
                        "CODIGO_SISTEC": codigo_sistec
                    })

            # reatualiza a lista
            elementos_municipios = driver.find_elements(By.XPATH, XPATH_BASE_MUNICIPIOS + "/h3")

        # 5) salvar Excel
        if not registros:

            print("\nNenhum registro coletado.")

        else:
            
            df = pd.DataFrame(registros, columns=["ESTADO", "MUNICIPIO", "INSTITUICAO", "CODIGO_SISTEC"])
            nome_arquivo = f"sistec_{UF_ALVO}_primeiras_{total_processar}_cidades.xlsx"
            caminho_saida = Path.cwd() / nome_arquivo
            df.to_excel(caminho_saida, index=False)

            print(f"\nExcel salvo com {len(df)} linhas: {caminho_saida}")

        input("\nFim...")

    finally:

        driver.quit()


if __name__ == "__main__":

    main()
