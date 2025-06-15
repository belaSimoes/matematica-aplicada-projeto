import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from unidecode import unidecode

# Função para buscar dados da API USDA FoodData Central
def buscar_alimento(nome_alimento):
    api_key = 'dL4GmUlT2nUwKdUo46D8r7U7ItI3JLI9gxLecS1Y'
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={unidecode(nome_alimento)}&api_key={api_key}"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data['foods']:
            return data['foods'][0]  # Retorna o primeiro alimento encontrado
    return None

# Função para calcular necessidades calóricas diárias
def calcular_calorias_diarias(peso, altura, idade, sexo):
    if sexo == 'M':
        calorias = (10 * peso) + (6.25 * altura) - (5 * idade) + 5
    else:
        calorias = (10 * peso) + (6.25 * altura) - (5 * idade) - 161
    return calorias

# Função para exibir gráfico
def plotar_nutrientes(dados, meta_calorias):
    plt.figure(figsize=(10, 5))
    plt.bar(dados['nutriente'], dados['valor'], color='skyblue')
    plt.axhline(y=meta_calorias, color='r', linestyle='--', label='Meta Calórica')
    plt.title('Distribuição Nutricional')
    plt.xlabel('Nutrientes')
    plt.ylabel('Quantidade')
    plt.xticks(rotation=45)
    plt.legend()
    st.pyplot(plt)

# Título da aplicação
st.title("Impacto Calórico de Comidas em Geral")
st.write("Preencha as informações abaixo para calcular suas necessidades nutricionais.")

# Dados do usuário
peso = st.number_input("Digite seu peso (kg):", min_value=1.0)
altura = st.number_input("Digite sua altura (cm):", min_value=1)
idade = st.number_input("Digite sua idade (anos):", min_value=1)
sexo = st.selectbox("Selecione seu sexo:", options=["M", "F"])

# Calcular calorias diárias
if st.button("Calcular Calorias Diárias"):
    calorias_diarias = calcular_calorias_diarias(peso, altura, idade, sexo)
    st.session_state.calorias_diarias = calorias_diarias
    st.session_state.refeicoes = {}
    st.write(f"Sua meta calórica diária é: **{calorias_diarias:.2f} kcal**")

# Perguntas sobre refeições
if 'refeicoes' not in st.session_state:
    st.session_state.refeicoes = {}

for refeicao in ["Café da manhã", "Almoço", "Café da tarde", "Janta"]:
    comida = st.text_input(f"O que você comeu no {refeicao.lower()}:", key=refeicao)
    if comida:
        alimento_info = buscar_alimento(comida)
        if alimento_info:
            nutrientes = {
                'calorias': 0,
                'proteina': 0,
                'carboidratos': 0,
                'ferro': 0
            }
            for nutrient in alimento_info['foodNutrients']:
                if nutrient['nutrientName'] == 'Energy':
                    nutrientes['calorias'] += nutrient['value']
                elif nutrient['nutrientName'] == 'Protein':
                    nutrientes['proteina'] += nutrient['value']
                elif nutrient['nutrientName'] == 'Carbohydrate, by difference':
                    nutrientes['carboidratos'] += nutrient['value']
                elif nutrient['nutrientName'] == 'Iron, Fe':
                    nutrientes['ferro'] += nutrient['value']
            
            st.session_state.refeicoes[refeicao] = nutrientes
        else:
            st.error(f"Alimento '{comida}' não encontrado.")

# Calcular totais
if st.session_state.refeicoes:
    total_nutrientes = {
        'calorias': sum(refeicao['calorias'] for refeicao in st.session_state.refeicoes.values()),
        'proteina': sum(refeicao['proteina'] for refeicao in st.session_state.refeicoes.values()),
        'carboidratos': sum(refeicao['carboidratos'] for refeicao in st.session_state.refeicoes.values()),
        'ferro': sum(refeicao['ferro'] for refeicao in st.session_state.refeicoes.values())
    }

    st.write("Resumo das refeições:")
    st.write(total_nutrientes)

    # Plotar gráfico
    plotar_nutrientes(pd.DataFrame(total_nutrientes.items(), columns=['nutriente', 'valor']), st.session_state.calorias_diarias)

    # Verificar se passou da meta
    if total_nutrientes['calorias'] > st.session_state.calorias_diarias:
        st.warning("Você excedeu sua meta calórica diária!")
    else:
        st.success("Você está dentro da sua meta calórica diária!")