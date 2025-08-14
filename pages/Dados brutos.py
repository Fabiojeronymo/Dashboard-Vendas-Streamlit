import streamlit as st
import requests
import pandas as pd
import time

#   Configuração da página
st.set_page_config(page_title='Dados brutos',
                   layout='wide',
                   )

#   Configuração do cache, ele permite que os dados sejam armazenados em cache para melhorar a performance
@st.cache_data
def converte_csv(df):
    return df.to_csv(index=False).encode('utf-8')

#   Função para exibir uma mensagem de sucesso após o download do arquivo
def mensagem_sucesso():
    sucesso = st.success('Arquivo baixado com sucesso!', icon="✅")
    time.sleep(15)
    sucesso.empty()

#   Título da página
st.title('DADOS BRUTOS 📋')

#  Carregamento dos dados
url = 'https://labdados.com/produtos'
response = requests.get(url)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format='%d/%m/%Y')

#   Sidebar para seleção de colunas e filtros
with st.expander('Colunas'):
    colunas = st.multiselect('Seleciona as colunas', list(dados.columns), list(dados.columns))

#   Sidebar para filtros
#   Cada expander contém um filtro específico para os dados
#   Dados numericos são filtrados com sliders, enquanto dados categóricos são filtrados com multiselects
st.sidebar.title('Filtros')
with st.sidebar.expander('Nome do produto'):
    produtos = st.multiselect('Selecione os produtos', dados['Produto'].unique(), dados['Produto'].unique())
with st.sidebar.expander('Categoria do produto'):
    categoria = st.multiselect('Selecione a Categoria', dados['Categoria do Produto'].unique(), dados['Categoria do Produto'].unique())
with st.sidebar.expander('Preço do produto'):
    preco = st.slider('Selecione o preço', 0, 5000, (0, 5000))
with st.sidebar.expander('Frete do produto'):
    frete = st.slider('Selecione o Frete', 0, 200, (0, 200))
with st.sidebar.expander('Data da compra'):
    data_compra = st.date_input('Selecione a data', (dados['Data da Compra'].min(), dados['Data da Compra'].max()))
with st.sidebar.expander('Nome do vendedor'):
    vendedores = st.multiselect('Selecione o vendedor', dados['Vendedor'].unique(), dados['Vendedor'].unique())
with st.sidebar.expander('Local da compra'):
    local_compra = st.multiselect('Selecione o local da compra', dados['Local da compra'].unique(), dados['Local da compra'].unique())
with st.sidebar.expander('Avaliação da compra'):
    avaliacao = st.slider('Selecione por avaliação', 0, 5, (0, 5))
with st.sidebar.expander('Tipo de pagamento'):
    tipo_pagamento = st.multiselect('Selecioneo tipo de pagamento', dados['Tipo de pagamento'].unique(), dados['Tipo de pagamento'].unique())
with st.sidebar.expander('Quantidade de parcelas'):
    parcelas = st.slider('Selecione a quantidade de parcelas', 0, 24, (0, 24))
st.sidebar.button('Limpar filtros', on_click=lambda: st.session_state.clear())

#   Exibição dos dados filtrados
#   A consulta é feita utilizando a função query do pandas, que permite filtrar os dados de acordo com os critérios selecionados
query = '''
Produto in @produtos and \
`Categoria do Produto` in @categoria and \
@preco[0] <= Preço <= @preco[1] and \
@frete[0] <= Frete <= @frete[1] and \
`Data da Compra` >= @data_compra[0] and \
Vendedor in @vendedores and \
`Local da compra` in @local_compra and \
@avaliacao[0] <= `Avaliação da compra` <= @avaliacao[1] and \
`Tipo de pagamento` in @tipo_pagamento and \
@parcelas[0] <= `Quantidade de parcelas` <= @parcelas[1]
'''

#   Filtragem dos dados com base na consulta
dados_filtrados = dados.query(query)
dados_filtrados = dados_filtrados[colunas]

#   Exibição dos dados filtrados em um dataframe
st.dataframe(dados_filtrados)

st.markdown(f'A tabela possui :blue[{dados_filtrados.shape[0]}] linhas e :blue[{dados_filtrados.shape[1]}] colunas.')

#   Botão para download dos dados filtrados
#   O botão permite que o usuário baixe os dados filtrados em formato CSV
#   O nome do arquivo é definido pelo usuário através de um input de texto
with st.popover('Download'):
    st.markdown('Escreva um nome para o arquivo')
    nome_arquivo = st.text_input('dados', label_visibility = 'collapsed', value = 'dados')
    nome_arquivo += '.csv'
    if st.download_button('Download', data = converte_csv(dados_filtrados), file_name= nome_arquivo, mime='text/csv'):
        mensagem_sucesso()