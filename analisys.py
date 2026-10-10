import pandas as pd 
import streamlit as st 
import altair as alt
import datetime as dt 

df = pd.read_excel(
    io="system_extraction.xlsx",
    engine="openpyxl",
    sheet_name='salesreport',
    usecols='A:J',
    nrows=4400
)


st.set_page_config(
    page_title='DASHBOARD DE VENDAS',
    page_icon='💲',
    layout='wide',
    initial_sidebar_state='expanded'
)



df['Data'] = pd.to_datetime(df['Data'])
max_data = df['Data'].max().to_pydatetime()
min_data = df['Data'].min().to_pydatetime()



vendas_totais = round(df['Valor Pedido'].sum(),2)
lucro_total = round(df['Margem Lucro'].sum(),2)
porcentagem_media = int(100 * lucro_total / vendas_totais)

with st.sidebar:
    st.subheader("Dashboard de vendas")
    Fvendedor = st.selectbox(
        'Selecione o vendedor',
        options=df['Vendedor'].unique(),
        index=2
    )

    Fcliente = st.selectbox(
        'Selecione o cliente',
        options=df['Cliente'].unique()
    )

    Fprdouto = st.selectbox(
        'Selecione o prdouto',
        options=df['Produto vendido'].unique()

    )

    slider_temp = st.slider (
        label="Intervalo de tempo",
        min_value=min_data,
        max_value=max_data
    )



#Produtos vendidos
tab1_qte_produto_vendido = df.loc[
    (df['Vendedor'] == Fvendedor) &
    (df['Cliente'] == Fcliente) & 
    (df['Data'] <= slider_temp ) &
     (df['Data'] <= slider_temp ) 

]

tab1_qte_produto_vendido = tab1_qte_produto_vendido.groupby("Produto vendido").sum(numeric_only=True).reset_index()

graf_qte_produto_vendido = alt.Chart(tab1_qte_produto_vendido).mark_bar(
    color="#9DD1F1"
).encode (
    x='Produto vendido',
    y='Quantidade',
    tooltip=["Produto vendido","Quantidade"]
).properties (
    title="Quantidade vendida dos produtos"
).configure_axis(
    grid=True
).configure_view( 
    strokeWidth=1
 )



# Valor arrecadado por produto

graf_valor_de_venda_produto = alt.Chart(tab1_qte_produto_vendido).mark_bar(
    color="#9DD1F1"
).encode(
    x="Produto vendido",
    y="Valor Pedido"
).properties (
    title="Valor total por produto"
)

# Valor de venda por vendedor

tab2_valor_de_venda_por_vendedor = df.loc[
    (df['Produto vendido'] == Fprdouto) &
    (df['Cliente'] == Fcliente) & 
    (df['Data'] <= slider_temp ) 
]

tab2_valor_de_venda_por_vendedor = tab2_valor_de_venda_por_vendedor.groupby('Vendedor').sum(numeric_only = True).reset_index().drop(columns=["Nº pedido","Preço"])


graf_valor_de_venda_por_vendedor = alt.Chart(tab2_valor_de_venda_por_vendedor).mark_arc(
    innerRadius=100,
    outerRadius=150
).encode (
    theta=alt.Theta(field='Valor Pedido',type='quantitative',stack=True),
    color=alt.Color(field="Vendedor",type='nominal'),
    tooltip=['Vendedor','Valor Pedido']
).properties ( 
    height= 500,
    width = 560,
    title="Valor de venda por vendedor"
 )



#Vendas mensais

tab3_vendas_mensais = df.loc[
    (df['Produto vendido'] == Fprdouto) &
    (df['Cliente'] == Fcliente) & 
    (df['Data'] <= slider_temp ) &
    (df['Vendedor'] == Fvendedor)
].copy()

tab3_vendas_mensais['mm'] = tab3_vendas_mensais['Data'].dt.strftime('%m/%Y')



graf_vendas_mensais = alt.Chart(tab3_vendas_mensais).mark_line (
    color="#666"
).encode (
    alt.X('monthdate(Data):T'),
    y = 'Valor Pedido:Q',
    tooltip=['Valor Pedido']
).properties(
    title="Vendas Mensais"
)

#Valor vendido por cliente

tab_vendas_cliente =  df.loc[
    (df['Produto vendido'] == Fprdouto) &
    (df['Data'] <= slider_temp ) &
    (df['Vendedor'] == Fvendedor)
].groupby('Cliente').sum(numeric_only=True).reset_index()



graf5_vendas_cliente = alt.Chart(tab_vendas_cliente).mark_bar(
    color="#666",
    cornerRadiusTopLeft=9,
    cornerRadiusBottomRight=9  
).encode (
    x='Cliente',
    y='Valor Pedido',
    tooltip=['Quantidade','Valor Pedido']
).properties (
    title="Valor vendido por cliente"
)

st.header(":bar_chart: Dashboard de Vendas")
if vendas_totais <= 0:
    st.write("Intervalo zerado")
    porcentagem_media = 0

dst1,dst2,dst3,dst4 = st.columns([1,1,1,2.5])
with dst1:
    st.write("Vendas totais")
    st.info(f'R${vendas_totais}')
with dst2:
    st.write("Total de lucro")
    st.info(f'R$ {lucro_total}')
with dst3:
    st.write("Margem média")
    st.info(f' {porcentagem_media} %')


cols1,cols2,cols3 = st.columns([1,1,1])
with cols1:
    st.altair_chart(graf_qte_produto_vendido)
    st.altair_chart(graf_valor_de_venda_produto)
with cols2:
    st.altair_chart(graf5_vendas_cliente)
    st.altair_chart(graf_vendas_mensais)
with cols3:
    rotVe = graf_valor_de_venda_por_vendedor.mark_text(radius=210,size=14).encode(text='Vendedor')
    rotVp = graf_valor_de_venda_por_vendedor.mark_text(radius=180,size=14).encode(text='Valor Pedido')
    st.altair_chart(graf_valor_de_venda_por_vendedor + rotVp + rotVe )
