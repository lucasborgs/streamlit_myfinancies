import streamlit as st
import pandas as pd
import datetime as dt

def calc_stats(df: pd.DataFrame):
    df_data = df.groupby(by="Data")[['Valor']].sum()
    df_data['Lag_1'] = df_data['Valor'].shift(1)
    df_data['Diferença Mensal'] = df_data['Valor'] - df_data['Lag_1']
    df_data['MM 6'] = df_data['Valor'].rolling(window=6).mean()
    df_data['MM 12'] = df_data['Valor'].rolling(window=12).mean()
    df_data['MM 24'] = df_data['Valor'].rolling(window=24).mean()
    df_data['Diferença Mensal Relativa'] = df_data['Valor'] / df_data['Lag_1'] -1 
    df_data['Evolução semestral'] = df_data['Valor'].rolling(window=6).apply(lambda x: x[-1] - x[0])
    df_data['Evolução anual'] = df_data['Valor'].rolling(window=12).apply(lambda x: x[-1] - x[0])
    df_data['Evolução Semestral Rel.'] = df_data['Valor'].rolling(window=6).apply(lambda x:(x[-1] / x[0] -1) if x[0] != 0 else 0)
    df_data['Evolução Anual Rel.'] = df_data['Valor'].rolling(window=12).apply(lambda x: (x[-1] / x[0] -1) if x[0] != 0 else 0)

    df_data = df_data.drop(columns=['Lag_1'], axis=1)

    return df_data

st.set_page_config(page_title="My Financies", page_icon='💎')

st.markdown(
"""# My Financies"""
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

    exp3 = st.expander("Statistics")
    df_stats = calc_stats(df)

    columns_config = {
        "Valor":st.column_config.NumberColumn(format="R$ %.2f"),
        "Diferença Mensal":st.column_config.NumberColumn(format="R$ %.2f"),
        "MM 6":st.column_config.NumberColumn(format="R$ %.2f"),
        "MM 12":st.column_config.NumberColumn(format="R$ %.2f"),
        "MM 24":st.column_config.NumberColumn(format="R$ %.2f"),
        "Dif. Mensal Relativa":st.column_config.NumberColumn(format="%.2f %%", step=0.01),
        "Evolução semestral":st.column_config.NumberColumn(format="R$ %.2f"),
        "Evolução anual":st.column_config.NumberColumn(format="R$ %.2f"),
        "Evolução Semestral Rel.":st.column_config.NumberColumn(format="%.2f %%", step=0.01),
        "Evolução Anual Rel.":st.column_config.NumberColumn(format="%.2f %%", step=0.01),
    }

    tab_stats, tab_abs, tab_rel = exp3.tabs(["All", "Absolute", "Relative"])

    with tab_stats:
        st.dataframe(df_stats, column_config=columns_config)

    with tab_abs:
        abs_cols  = ["Diferença Mensal",
                     "MM 6",
                     "MM 12",
                     "MM 24"]
        st.line_chart(df_stats[abs_cols])

    with tab_rel:
        rel_cols  = ["Diferença Mensal Relativa",
                     "Evolução Semestral Rel.",
                     "Evolução Anual Rel."]
        st.line_chart(df_stats[rel_cols])

    with st.expander('Metas'):
        
        col1, col2 = st.columns(2)

        data_inicio_meta = col1.date_input('Início da Meta', max_value=df_stats.index.max())
        data_filtrada = df_stats.index[df_stats.index <= data_inicio_meta][-1]

        custos_fixos = col1.number_input('Custos Fixos', min_value=0., format="%.2f")

        salario_bruto = col2.number_input('Salário Bruto', min_value=0., format="%.2f")
        salario_liquido = col2.number_input('Salário Líquido', min_value=0., format="%.2f")

        valor_inicio_meta = df_stats.loc[data_filtrada]['Valor']
        col1.markdown("Patrimônio no início da meta: R$ %.2f" % valor_inicio_meta)

        col1_pot, col2_pot = st.columns(2)
        arrecadacao_mensal = salario_liquido - custos_fixos

        with col1_pot.container(border=True): 
            st.markdown(f"Arrecadação potencial mensal:\n\n R$ {arrecadacao_mensal: .2f}")

        
        with col2_pot.container(border=True): 
            st.markdown(f"Arrecadação potencial anual:\n\n R$ {arrecadacao_mensal * 12: .2f}")

        with st.container(border=True):
            col1_meta, col2_meta = st.columns(2)
            with col1_meta:
                meta_estipulada = st.number_input("Meta Estipulada", min_value=0., format="% .2f", value=arrecadacao_mensal*12)

            with col2_meta:
                patrimonio_final = meta_estipulada + valor_inicio_meta
                st.markdown(f"Patrimônio Estimado Final: \n\n R$ {patrimonio_final: .2f}")

        
 

 