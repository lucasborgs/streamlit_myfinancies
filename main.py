import streamlit as st
import pandas as pd
import datetime as dt
import requests
import datetime

@st.cache_data(ttl="1day")
def get_selic():
    url = "https://www.bcb.gov.br/api/servico/sitebcb/historicotaxasjuros"
    resp = requests.get(url)
    df = pd.DataFrame(resp.json()["conteudo"])

    df["DataInicioVigencia"] = pd.to_datetime(df["DataInicioVigencia"]).dt.date
    df["DataFimVigencia"] = pd.to_datetime(df["DataFimVigencia"]).dt.date
    df["DataFimVigencia"] = df["DataFimVigencia"].fillna(datetime.datetime.today().date())

    return df

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



def main_metas():
    col1, col2 = st.columns(2)

    data_inicio_meta = col1.date_input('Início da Meta', max_value=df_stats.index.max())
    data_filtrada = df_stats.index[df_stats.index <= data_inicio_meta][-1]
    
    custos_fixos = col1.number_input('Custos Fixos', min_value=0., format="%.2f")

    salario_bruto = col2.number_input('Salário Bruto', min_value=0., format="%.2f")
    salario_liquido = col2.number_input('Salário Líquido', min_value=0., format="%.2f")

    valor_inicio_meta = df_stats.loc[data_filtrada]['Valor']
    col1.markdown("Patrimônio no início da meta: R$ %.2f" % valor_inicio_meta)

    selic_gov = get_selic()
    filter_selic_date = (selic_gov["DataInicioVigencia"] < data_inicio_meta) & (selic_gov["DataFimVigencia"] > data_inicio_meta)
    selic_default = selic_gov[filter_selic_date]["MetaSelic"].iloc[0]

    selic = st.number_input("Selic", min_value=0., value=selic_default, format="%.2f")
    selic_ano = selic / 100

    selic_mes = (selic_ano + 1) ** (1/12) - 1

    rendimento_ano = valor_inicio_meta * selic_ano
    rendimento_mes = valor_inicio_meta * selic_mes

    col1_pot, col2_pot = st.columns(2)
    arrecadacao_mensal = salario_liquido - custos_fixos + valor_inicio_meta * selic_mes
    arrecadacao_anual = 12 * (salario_liquido - custos_fixos) + (valor_inicio_meta * selic_ano)

    with col1_pot.container(border=True): 
        st.markdown(f"Arrecadação potencial mensal:\n\n R$ {arrecadacao_mensal: .2f}",
                    help= f"{salario_liquido:.2f} - {custos_fixos:.2f} + {rendimento_mes:.2f}"
                    )

        
    with col2_pot.container(border=True): 
        st.markdown(f"Arrecadação potencial anual:\n\n R$ {arrecadacao_anual: .2f}",
                    help= f"12 * ({salario_liquido:.2f} - {custos_fixos:.2f}) + {rendimento_ano:.2f}"
                    )

    with st.container(border=True):
        col1_meta, col2_meta = st.columns(2)
        with col1_meta:
            meta_estipulada = st.number_input("Meta Estipulada", min_value=-999999999., format="%.2f", value=arrecadacao_anual)

        with col2_meta:
            patrimonio_final = meta_estipulada + valor_inicio_meta
            st.markdown(f"Patrimônio Estimado Final: \n\n R$ {patrimonio_final: .2f}")

    return data_inicio_meta, valor_inicio_meta, meta_estipulada, patrimonio_final

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
        "Evolução Anual Rel.":st.column_config.NumberColumn(format="%.2f %%", step=0.01)
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

        tab_main_meta, tab_data_meta, tab_graph_meta = st.tabs(tabs=["Configuração", "Dados", "Gráficos"])

        with tab_main_meta:
            data_inicio_meta, valor_inicio_meta, meta_estipulada, patrimonio_final = main_metas()
        
        with tab_data_meta:
            meses = pd.DataFrame({
                "Data Referência":[data_inicio_meta + pd.DateOffset(months=i) for i in range(1,13)],
                "Meta Mensal": [valor_inicio_meta + round(meta_estipulada/12,2) * i for i in range(1,13)]
                })
            
            meses["Data Referência"] = meses["Data Referência"].dt.strftime("%Y-%m")
            df_patrimonio = df_stats.reset_index()[["Data", "Valor"]]
            df_patrimonio["Data Referência"] = pd.to_datetime(df_patrimonio["Data"]).dt.strftime("%Y-%m")
            meses = meses.merge(df_patrimonio, how="left", on="Data Referência")

            meses = meses[["Data Referência", "Meta Mensal", "Valor"]]
            meses["Atingimento Mensal"] = meses["Valor"] / meses["Meta Mensal"]
            meses["Atingimento Anual"] = meses["Valor"] /  patrimonio_final
            meses["Atingimento Esperado"] = meses["Meta Mensal"] / patrimonio_final
            meses = meses.set_index("Data Referência")

        columns_config_meses = {
            "Meta Mensal":st.column_config.NumberColumn("Meta Mensal", format="R$ %.2f"),
            "Valor":st.column_config.NumberColumn("Valor Atingido", format="R$ %.2f"),
            "Atingimento Mensal":st.column_config.NumberColumn("Atingimento Mensal", format="percent"),
            "Atingimento Anual":st.column_config.NumberColumn("Atingimento Anual", format="percent"),
            "Atingimento Esperado":st.column_config.NumberColumn("Atingimento Esperado", format="percent")
    }

        st.dataframe(meses, column_config=columns_config_meses)
        
        with tab_graph_meta:
            st.line_chart(meses[["Atingimento Anual", "Atingimento Esperado"]])


            
 
 
 