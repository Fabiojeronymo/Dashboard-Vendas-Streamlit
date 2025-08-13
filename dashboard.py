import streamlit as st
import requests
import pandas as pd
import plotly.express as px

## Configuração da página
st.set_page_config(page_title='Dashboard de Vendas',
                   layout='wide',
                   )

## Importação dos dados
url = 'https://labdados.com/produtos'
regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Região', regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)

query_string = {'regiao': regiao.lower(), 'ano':ano}
response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

filtro_vendedores = st.sidebar.multiselect('Vendedores', dados['Vendedor'].unique())
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

## Funções
def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

### Tabelas de receita
# Receita por estados
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
# Receita por mes
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'ME'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month
# Receita por categorias
receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)

### Tabelas de vendedores
# Tabelas vendedores
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

### Tabelas de vendas
# Vendas por estados
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
# vendas por mes
vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'ME'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month
# Vendas por categoria
vendas_categoria = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count()).sort_values('Preço', ascending = False)

## Gráficos vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                                  lat = 'lat', 
                                  lon = 'lon', 
                                  scope = 'south america', 
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Vendas por estado')
# Gráfico vendas por mes
fig_vendas_mensal = px.line(vendas_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = False,
                             range_y = (0, vendas_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Vendas mensal',
                             labels={'Mes': '', 'Preço':'Valor'},
                             )
nome_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
fig_vendas_mensal.update_xaxes(tickvals = vendas_mensal['Mes'].unique(),
                                ticktext = nome_meses, 
                                )
# Gráfico vendas por estado
fig_vendas_estados = px.bar(vendas_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top estados (vendas)')
# Gráfico receita por categoria
fig_vendas_categoria = px.bar(vendas_categoria,
                               text_auto = True,
                               title = 'Vendas por categoria')

## Gráficos Receita
# Gráfico receita por estado
fig_mapa_receita = px.scatter_geo(receita_estados, 
                                  lat = 'lat', 
                                  lon = 'lon', 
                                  scope = 'south america', 
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Receita por estado')
# Gráfico receita por mes
fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = False,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita mensal',
                             labels={'Mes': '', 'Preço':'Valor'},
                             )
# Criação de uma lista para alterar os xticks para abreviação dos meses
nome_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
fig_receita_mensal.update_xaxes(tickvals = receita_mensal['Mes'].unique(),
                                ticktext = nome_meses, 
                                )
# Gráfico receita por estado
fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top estados (receita)')
# Gráfico receita por categoria
fig_receita_categoria = px.bar(receita_categoria,
                               text_auto = True,
                               title = 'Receita por categoria')

## Visualização do streamlit
st.title('DASHBOARD DE VENDAS :bar_chart:')

aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

with aba1: 
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_categoria, use_container_width = True)
    with coluna2:
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)

with aba2:
    st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_categoria, use_container_width = True)

    with coluna2:
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)

with aba3: 
    qtd_vendedores = st.number_input('Quantidade de vendedores', min_value = 2, max_value = 10, value = 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores),
                                    x = 'sum',
                                    y = vendedores[['sum']].sort_values('sum', ascending = False).head(qtd_vendedores).index,
                                    text_auto = True,
                                    title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)        
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores),
                                    x = 'count',
                                    y = vendedores[['count']].sort_values('count', ascending = False).head(qtd_vendedores).index,
                                    text_auto = True,
                                    title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)')
        st.plotly_chart(fig_vendas_vendedores, use_container_width = True)    


st.dataframe(dados, use_container_width = True)