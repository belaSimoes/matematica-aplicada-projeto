import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import unidecode

# Carregar base TACO
@st.cache_data
def carregar_taco():
    df = pd.read_csv("taco.csv", encoding="ISO-8859-1", sep=";")
    df.columns = df.columns.str.strip()
    df["Alimento"] = df["Descrição"].apply(lambda x: unidecode(str(x)).lower())
    return df

def buscar_alimento(nome, df):
    nome_proc = unidecode(nome.strip().lower())
    resultados = df[df["Alimento"].str.contains(nome_proc)]
    return resultados

def calcular_valores(nutrientes_por_100g, quantidade):
    fator = quantidade / 100
    return round(nutrientes_por_100g * fator, 2)

def plotar_grafico(nutrientes):
    labels = ['Proteína', 'Lipídeos', 'Carboidrato']
    valores = [nutrientes[k] for k in labels]

    fig, ax = plt.subplots()
    ax.pie(valores, labels=labels, autopct='%1.1f%%', startangle=140)
    ax.axis('equal')
    st.pyplot(fig)

# Interface com Streamlit
def main():
    st.title("Impacto Calórico de Comidas com TACO")

    df_taco = carregar_taco()

    nome_alimento = st.text_input("Digite o nome do alimento:")
    quantidade = st.number_input("Quantidade em gramas:", min_value=1, max_value=1000, value=100)

    if nome_alimento:
        resultados = buscar_alimento(nome_alimento, df_taco)

        if resultados.empty:
            st.warning("Nenhum alimento encontrado.")
        else:
            alimento = resultados.iloc[0]  # pega o primeiro resultado
            st.subheader(f"Alimento encontrado: {alimento['Descrição']}")
            nutrientes = {
                "Energia (kcal)": calcular_valores(alimento["Energia (kcal)"], quantidade),
                "Proteína": calcular_valores(alimento["Proteína (g)"], quantidade),
                "Lipídeos": calcular_valores(alimento["Lipídeos (g)"], quantidade),
                "Carboidrato": calcular_valores(alimento["Carboidrato (g)"], quantidade)
            }

            st.write(f"**Valores para {quantidade}g:**")
            st.dataframe(pd.DataFrame(nutrientes.items(), columns=["Nutriente", "Quantidade"]))

            st.subheader("Proporção de Macronutrientes")
            plotar_grafico(nutrientes)

if __name__ == '__main__':
    main()
