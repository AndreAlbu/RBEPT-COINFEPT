# Coletor Automatizado de Instituições do SISTEC

Este repositório contém um **bot de automação desenvolvido em Python com Selenium**, utilizado para coletar informações públicas do **SISTEC – Sistema Nacional de Informações da Educação Profissional e Tecnológica**, mantido pelo Ministério da Educação (MEC).

O script automatiza a navegação no portal, seleciona uma **Unidade da Federação**, percorre os **municípios listados** e extrai as **instituições de ensino credenciadas**, bem como seus respectivos **códigos SISTEC**, exportando os dados para uma planilha Excel.


## Contexto e Motivação

O SISTEC disponibiliza informações relevantes de forma pública, porém sem uma API aberta para consumo estruturado.  
Este projeto foi desenvolvido com fins **acadêmicos e de pesquisa**, visando:

- Automatizar a coleta de dados públicos educacionais  
- Reduzir esforço manual em levantamentos estatísticos  
- Facilitar análises posteriores em planilhas ou ferramentas de ciência de dados  

**Importante:** o script respeita apenas dados **publicamente acessíveis**, sem autenticação ou bypass de segurança.


## Interface do SISTEC

### Seleção da Unidade da Federação

![Seleção da UF](tela_inicial.png)

### Listagem de Municípios e Instituições
![Lista de Municípios](tela_ceara.png)

As imagens acima representam as telas automatizadas pelo bot durante a execução.

## Funcionalidades

- Acesso automático ao portal do SISTEC
- Seleção dinâmica do estado (UF)
- Percurso sequencial pelos municípios
- Extração de:
  - Estado
  - Município
  - Nome da instituição
  - Código SISTEC
- Normalização e limpeza textual
- Exportação dos dados para **Excel (.xlsx)**

## Tecnologias Utilizadas

- **Python 3**
- **Selenium WebDriver**
- **Chrome + ChromeDriver**
- **Pandas**
- **Webdriver Manager**
  
## Estrutura do Projeto

