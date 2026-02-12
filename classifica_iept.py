import pandas as pd
import re
import unicodedata

arquivo_entrada = "versao_1_ceara.xlsx"
arquivo_saida = "versao_1_ceara_iept_class.xlsx"

padroes_iept = [
    re.compile(r"\beeep\b"),
    re.compile(r"\binstituto\s+federal\b"),
    re.compile(r"\bcentec\b"),
    re.compile(r"\btecnica\b"),
    re.compile(r"\btecnico\b"),
    re.compile(r"\btecnologico\b"),
    re.compile(r"\bescola\s+estadual\s+de\s+educacao\b"),
]

padroes_nao_iept = [
    re.compile(r"\buniversidade(s)?\b"),
    re.compile(r"\bcentro(s)?\s+universitario(s)?\b"),
]

def normalizar(texto):

    texto = unicodedata.normalize("NFD", str(texto))
    texto = "".join(ch for ch in texto if unicodedata.category(ch) != "Mn")

    return texto.lower()

df = pd.read_excel(arquivo_entrada)

def classificar_iept(nome_instituicao):

    if pd.isna(nome_instituicao):

        return "Verificar"

    nome = normalizar(nome_instituicao)

    for padrao in padroes_nao_iept:

        if padrao.search(nome):

            return "Não"

    for padrao in padroes_iept:

        if padrao.search(nome):
            
            return "Sim"

    return "Verificar"

df["IEPT"] = df["INSTITUICAO"].apply(classificar_iept)

df.to_excel(arquivo_saida, index=False)

print("Arquivo salvo como:", arquivo_saida)