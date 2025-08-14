import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Configuração da página ---
st.set_page_config(page_title = 'Dashboard de Vendas',
                   layout = 'wide',
                   )

# --- Constantes ---
url = 'https://labdados.com/produtos'
regioes = ['Todas', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']

# --- Filtros ---
#   Criação da sidebar com filtros para os dados
#   se a região for Brasil, não é necessário filtrar
st.sidebar.title('Filtros')
with st.sidebar.expander('Região'):
    regiao = st.selectbox(label = 'Selecione a região para filtrar', 
                                options = regioes)
    if regiao == 'Todas':
        regiao = ''

#   se o checkbox de todos os anos for desmarcado, o usuário pode selecionar um ano específico pelo segmented control
#   caso contrário, todos os anos serão considerados na requisição dos dados
#   o ano selecionado será adicionado à query_string para filtrar os dados retornados pela API
#   a query_string é um dicionário que contém os filtros selecionados pelo usuário
#   esses filtros serão usados na requisição dos dados
with st.sidebar.expander('Ano'):
    todos_anos = st.checkbox(label = 'Dados de todo o periodo', 
                                    value = True)
    if todos_anos:
        ano = ''
    else:
        options = [2020, 2021, 2022, 2023]
        ano = st.segmented_control('Ano', 
                                        options = options, 
                                        default = [2023])
query_string = {'regiao': regiao.lower(), 
                'ano':ano}

# --- Requisição/importação dos dados ---
#   Dados de vendas de produtos, incluindo informações como:
#   produto, categoria, preço, frete, data da compra, vendedor, local da compra, avaliação e tipo de pagamento.
#   A API retorna dados em formato JSON, que são convertidos para um DataFrame do Pandas.
response = requests.get(url, params = query_string)
dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')

# --- Filtros adicionais da sidebar ---
with st.sidebar.expander('Vendedores'):
    filtro_vendedores = st.multiselect(label = 'Selecione os vendedores para filtrar os dados', 
                                            options =dados['Vendedor'].unique(),
                                            placeholder = 'Selecione os vendedores'
                                            )
if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]

# --- Função para formatar números ---
#   Função para formatar números em milhares ou milhões, com um prefixo opcional.
#   Exemplo: 1500 -> '1.50 mil', 2500000 -> '2.50 milhões'
def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor <1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

# --- tabelas ----
#   As tabelas estão separadas por receita, vendas e vendedores.

# --- Tabelas de receita ----
#   Tabelas de receita por estados, meses e categorias.
#   As tabelas são agrupadas por local da compra, data da compra e categoria do produto.
#   A receita é calculada pela soma dos preços dos produtos.
receita_estados = dados.groupby('Local da compra')[['Preço']].sum()
receita_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receita_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'ME'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month
receita_categoria = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending = False)
# Criação do dataframe para o gráfico de cascata
df_cascata = receita_categoria.copy().sort_values(by='Preço', ascending=False)
total_receita = df_cascata['Preço'].sum()
df_cascata.loc['Total'] = total_receita
df_cascata['Preço texto'] = (df_cascata['Preço']/1e6).map('R$ {:,.2f} MI'.format)
measure = ['relative'] * (len(df_cascata) - 1) + ['total']

# --- Tabelas de vendas ---
#   Tabelas de vendas por estados, meses e categorias.
#   As tabelas são agrupadas por local da compra, data da compra e categoria do produto.
#   A quantidade de vendas é calculada pela contagem dos preços dos produtos.
vendas_estados = pd.DataFrame(dados.groupby('Local da compra')['Preço'].count())
vendas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(vendas_estados, left_on = 'Local da compra', right_index = True).sort_values('Preço', ascending = False)

vendas_mensal = pd.DataFrame(dados.set_index('Data da Compra').groupby(pd.Grouper(freq = 'ME'))['Preço'].count()).reset_index()
vendas_mensal['Ano'] = vendas_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = vendas_mensal['Data da Compra'].dt.month

vendas_categoria = pd.DataFrame(dados.groupby('Categoria do Produto')['Preço'].count()).sort_values('Preço', ascending = False)

# --- Tabelas de vendedores ---
#   Tabela de vendedores, agrupada por vendedor.
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

# --- Gráficos ---
#   Gráficos de vendas e receita, incluindo gráficos de mapa, linha e barra.
#   Os gráficos são criados usando a biblioteca Plotly Express.

# --- Gráficos de receita ---
#   Gráfico de mapa da receita
fig_mapa_receita = px.scatter_geo(receita_estados, 
                                  lat = 'lat', 
                                  lon = 'lon', 
                                  scope = 'south america', 
                                  size = 'Preço',
                                  template = 'seaborn',
                                  hover_name = 'Local da compra',
                                  hover_data = {'lat': False, 'lon': False},
                                  title = 'Receita por estado')
#   Gráfico receita por mes
fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes',
                             y = 'Preço',
                             markers = False,
                             range_y = (0, receita_mensal.max()),
                             color = 'Ano',
                             line_dash = 'Ano',
                             title = 'Receita mensal',
                             labels={'Mes': '', 'Preço':''})
#   Criação de uma lista para alterar os xticks para abreviação dos meses
nome_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
fig_receita_mensal.update_xaxes(tickvals = receita_mensal['Mes'].unique(),
                                ticktext = nome_meses)
#   Gráfico receita por estado
fig_receita_estados = px.bar(receita_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             title = 'Top estados (receita)',
                             labels = {'Local da compra': '', 'Preço': ''})
#   Gráfico receita por categoria em cascata
fig_receita_categoria = go.Figure(go.Waterfall(
                        name="Receita",
                        orientation="v",
                        x=df_cascata.index,
                        y=df_cascata['Preço'],
                        measure=measure,
                        text=df_cascata['Preço texto'],
                        textposition="outside",
                        connector={'line': {'color': 'white'}},
                        increasing_marker = dict(color = '#1E90FF'),
                        totals={"marker": {"color": '#00FA9A'}}))
fig_receita_categoria.update_yaxes(showgrid=False)
fig_receita_categoria.update_yaxes(showticklabels=False)
#   Gráficos de vendas
#   Gráficos vendas
fig_mapa_vendas = px.scatter_geo(vendas_estados, 
                                lat = 'lat', 
                                lon = 'lon', 
                                scope = 'south america', 
                                size = 'Preço',
                                template = 'seaborn',
                                hover_name = 'Local da compra',
                                hover_data = {'lat': False, 'lon': False},
                                title = 'Vendas por estado',
                                labels={'Mes': '', 'Preço':''}) 
#   Gráfico vendas por mes
fig_vendas_mensal = px.line(vendas_mensal,
                            x = 'Mes',
                            y = 'Preço',
                            markers = False,
                            range_y = (0, vendas_mensal.max()),
                            color = 'Ano',
                            line_dash = 'Ano',
                            title = 'Vendas mensal',
                            labels={'Mes': '', 'Preço':''})
nome_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
fig_vendas_mensal.update_xaxes(tickvals = vendas_mensal['Mes'].unique(),
                                ticktext = nome_meses)
#   Gráfico vendas por estado
fig_vendas_estados = px.bar(vendas_estados.head(),
                             x = 'Local da compra',
                             y = 'Preço',
                             text_auto = True,
                             title = 'Top estados (vendas)',
                             labels = {'Local da compra': '', 'Preço': ''})
#   Gráfico receita por categoria
fig_vendas_categoria = px.bar(vendas_categoria,
                               text_auto = True,
                               title = 'Vendas por categoria',
                               labels={'Categoria do Produto': '', 'value':''})

# ---- Visualização do streamlit ----


#   Exibilçao em abas, onde cada aba contém gráficos e métricas relacionadas a receita, quantidade de vendas e vendedores.
#   As abas são criadas usando a função st.tabs, que permite organizar o conteúdo em seções separadas.
#   As métricas são exibidas usando a função st.metric, que mostra o valor atual e a variação em relação ao período anterior.
aba1, aba2, aba3 = st.tabs(['Receita', 'Vendas', 'Vendedores'])
#   Aba 1
with aba1: 
    st.title('DASHBOARD DE RECEITAS 💰')
    st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.plotly_chart(fig_mapa_receita, use_container_width = True)
        st.plotly_chart(fig_receita_categoria, use_container_width = True)
    with coluna2:
        st.plotly_chart(fig_receita_mensal, use_container_width = True)
        st.plotly_chart(fig_receita_estados, use_container_width = True)
#   Aba 2
with aba2:
    st.title('DASHBOARD DE VENDAS 🛒')
    st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        st.plotly_chart(fig_mapa_vendas, use_container_width = True)
        st.plotly_chart(fig_vendas_categoria, use_container_width = True)

    with coluna2:
        st.plotly_chart(fig_vendas_mensal, use_container_width = True)
        st.plotly_chart(fig_vendas_estados, use_container_width = True)
#   Aba 3
with aba3: 
    st.title('DASHBOARD DE VENDEDORES 🤝')
    qtd_vendedores = st.number_input('Quantidade de vendedores', min_value = 1, max_value = 10, value = 5)
    vendedor_selecionado = vendedores.index[:qtd_vendedores].str.cat(sep = ', ')
    coluna1, coluna2 = st.columns(2)
    with coluna1:
        if qtd_vendedores == 1:
            st.metric(f'Receita gerada por {vendedor_selecionado}', formata_numero(vendedores["sum"].head(qtd_vendedores).sum(), 'R$'))
        else:
            st.metric('Receita gerada por esses vendedores', formata_numero(vendedores["sum"].head(qtd_vendedores).sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending = True).head(qtd_vendedores),
                                    x = 'sum',
                                    y = vendedores[['sum']].sort_values('sum', ascending = True).head(qtd_vendedores).index,
                                    text_auto = True,
                                    title = f'Top {qtd_vendedores} vendedores (receita)',
                                    labels = {'sum': '', 'y': ''})
        st.plotly_chart(fig_receita_vendedores, use_container_width = True)       
    with coluna2:
        if qtd_vendedores == 1:
            st.metric(f'Vendas feitas por {vendedor_selecionado}', formata_numero(vendedores["count"].head(qtd_vendedores).sum()))
        else: 
            st.metric('Vendas geradas por esses vendedores', vendedores["count"].head(qtd_vendedores).sum())
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending = True).head(qtd_vendedores),
                                    x = 'count',
                                    y = vendedores[['count']].sort_values('count', ascending = True).head(qtd_vendedores).index,
                                    text_auto = True,
                                    title = f'Top {qtd_vendedores} vendedores (quantidade de vendas)',
                                    labels = {'count': '', 'y': ''})
        st.plotly_chart(fig_vendas_vendedores, use_container_width = True)    