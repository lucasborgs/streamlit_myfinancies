import streamlit as st
import pandas as pd
import datetime as dt

st.set_page_config(page_title="My Financies", page_icon='💎')

st.markdown(
"""# About My Financies"""
)

file_uploader = st.file_uploader("Upload your financial data file", type=['csv', 'xlsx'])
if file_uploader:

    #Leitura dos dados
    df = pd.read_csv(file_uploader) if file_uploader.name.endswith('csv') else pd.read_excel(file_uploader)
    df["Data"] = pd.to_datetime(df["Data"], format="%d/%m/%Y").dt.date
    
    #Exibição dos dados
    exp1 = st.expander("View Data")
    columns_fmt = {"Valor":st.column_config.NumberColumn(format="$ %.2f")}
    exp1.dataframe(df, hide_index=True, column_config=columns_fmt)

    #Tabela resumo por instituição
    exp2 = st.expander("Summary by Institution")
    df_instituicao = df.pivot_table(index="Data", columns="Instituição", values="Valor")

    #Abas para visualização
    tab_data, tab_history, tab_share = exp2.tabs(["Data", "History", "Share"])

    #Exibição dos dataframe
    with tab_data:
        st.dataframe(df_instituicao)

    #Eexibe histrórico
    with tab_history:
        st.line_chart(df_instituicao)

    #Exibe distribuição por instituição
    with tab_share:
        date = st.date_input(
            "Select Date",
            value=df_instituicao.index.max(),
            min_value=df_instituicao.index.min(),
            max_value=df_instituicao.index.max()
        )
        last_date = df_instituicao.sort_index().iloc[-1]
        st.bar_chart(last_date)

