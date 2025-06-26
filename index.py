import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from unidecode import unidecode

# --- Funções Auxiliares (sem alterações) ---

def buscar_alimento(nome_alimento):
    """
    Busca informações nutricionais de um alimento na API USDA FoodData Central.
    Retorna dados por 100g.
    """
    api_key = 'dL4GmUlT2nUwKdUo46D8r7U7ItI3JLI9gxLecS1Y'
    url = f"https://api.nal.usda.gov/fdc/v1/foods/search?query={unidecode(nome_alimento)}&api_key={api_key}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get('foods'):
                return data['foods'][0]
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao conectar com a API: {e}")
    return None

def calcular_calorias_diarias(peso, altura, idade, sexo):
    """
    Calcula a Taxa Metabólica Basal (TMB) usando a fórmula de Mifflin-St Jeor.
    """
    if sexo == 'M':
        return (10 * peso) + (6.25 * altura) - (5 * idade) + 5
    else:
        return (10 * peso) + (6.25 * altura) - (5 * idade) - 161

def plotar_nutrientes(dados, meta_calorias):
    """
    Cria e exibe um gráfico de barras com os nutrientes totais consumidos.
    """
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    ax.bar(dados['nutriente'], dados['valor'], color='crimson', label='Total Consumido')
    
    if meta_calorias > 0:
        ax.axhline(y=meta_calorias, color='black', linestyle='--', label=f'Meta Calórica ({meta_calorias:.0f} kcal)')
    
    ax.set_title('Resumo Nutricional do Dia', fontsize=16)
    ax.set_ylabel('Quantidade (g / kcal / mg)', fontsize=12)
    plt.xticks(rotation=45, ha="right")
    ax.legend()
    fig.tight_layout()
    st.pyplot(fig)

# --- Interface do Usuário (Streamlit) ---

# Layout alterado para 'centered' para adicionar espaçamento lateral
st.set_page_config(layout="centered")
st.title("Calculadora de Impacto Calórico")
st.write("Preencha seus dados, registre suas refeições com a quantidade em gramas e veja o resumo do seu consumo diário.")

# Inicializa o estado da sessão com a estrutura completa
if 'calorias_diarias' not in st.session_state:
    st.session_state.calorias_diarias = 0
if 'refeicoes' not in st.session_state:
    st.session_state.refeicoes = {"Café da manhã": [], "Almoço": [], "Café da tarde": [], "Janta": []}

with st.expander("1. Calcule sua Meta Calórica", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        peso = st.number_input("Seu peso (kg):", min_value=1.0, step=0.5, format="%.1f")
        altura = st.number_input("Sua altura (cm):", min_value=1.0, step=1.0, format="%.0f")
    with col2:
        idade = st.number_input("Sua idade (anos):", min_value=1, step=1)
        sexo = st.selectbox("Seu sexo:", options=["M", "F"], format_func=lambda x: 'Masculino' if x == 'M' else 'Feminino')
    
    if st.button("Calcular Minha Meta Diária"):
        if peso > 0 and altura > 0 and idade > 0:
            calorias_diarias = calcular_calorias_diarias(peso, altura, idade, sexo)
            st.session_state.calorias_diarias = calorias_diarias
            # A linha que resetava as refeições foi removida daqui
            st.success(f"Meta calórica atualizada para **{st.session_state.calorias_diarias:.2f} kcal**")
        else:
            st.error("Por favor, preencha todos os campos corretamente.")

# Exibição permanente da meta calórica após o cálculo
if st.session_state.calorias_diarias > 0:
    st.metric(label="Sua Meta Diária", value=f"{st.session_state.calorias_diarias:.0f} kcal")
    st.divider()

# A lógica de registro de refeições só aparece se a meta foi calculada
if st.session_state.calorias_diarias > 0:
    st.header("2. Registre suas Refeições")
    
    refeicoes_definidas = ["Café da manhã", "Almoço", "Café da tarde", "Janta"]
    
    for refeicao in refeicoes_definidas:
        st.subheader(refeicao)
        
        # Formulário para adicionar alimento, permite usar a tecla ENTER
        with st.form(key=f"form_{refeicao}", clear_on_submit=True):
            col_alimento, col_qtd = st.columns([3, 1])
            novo_alimento = col_alimento.text_input("Nome do alimento", key=f"input_{refeicao}")
            quantidade = col_qtd.number_input("Quantidade (g)", min_value=1, value=100, step=1, key=f"qtd_{refeicao}")
            
            submitted = st.form_submit_button("Adicionar")
            if submitted and novo_alimento:
                # Verifica se o alimento já foi adicionado
                nomes_ja_adicionados = [item['nome'] for item in st.session_state.refeicoes[refeicao]]
                if novo_alimento.upper() in nomes_ja_adicionados:
                    st.warning(f"'{novo_alimento}' já foi adicionado a esta refeição.")
                else:
                    with st.spinner(f"Buscando dados de '{novo_alimento}'..."):
                        alimento_info = buscar_alimento(novo_alimento)
                    
                    if alimento_info:
                        nome_alimento_api = alimento_info.get('description', novo_alimento).upper()
                        # Checa novamente com o nome retornado pela API
                        if nome_alimento_api in nomes_ja_adicionados:
                             st.warning(f"'{nome_alimento_api}' já foi adicionado a esta refeição.")
                        else:
                            nutrientes_100g = {'calorias': 0, 'proteina': 0, 'carboidratos': 0, 'ferro': 0}
                            for nutrient in alimento_info.get('foodNutrients', []):
                                nome_nutriente = nutrient.get('nutrientName', '')
                                valor_nutriente = nutrient.get('value', 0)
                                if 'Energy' in nome_nutriente: nutrientes_100g['calorias'] = valor_nutriente
                                elif 'Protein' in nome_nutriente: nutrientes_100g['proteina'] = valor_nutriente
                                elif 'Carbohydrate' in nome_nutriente: nutrientes_100g['carboidratos'] = valor_nutriente
                                elif 'Iron' in nome_nutriente: nutrientes_100g['ferro'] = valor_nutriente
                            
                            # Calcula os nutrientes para a quantidade informada
                            fator = quantidade / 100.0
                            nutrientes_scaled = {k: v * fator for k, v in nutrientes_100g.items()}

                            st.session_state.refeicoes[refeicao].append({
                                'nome': nome_alimento_api,
                                'quantidade': quantidade,
                                'nutrientes_calculados': nutrientes_scaled
                            })
                            st.success(f"'{nome_alimento_api}' ({quantidade}g) adicionado ao {refeicao.lower()}.")
                    else:
                        st.error(f"Alimento '{novo_alimento}' não encontrado. Tente um nome mais simples ou em inglês.")

        # Exibe os alimentos já adicionados com detalhes
        for i, alimento in enumerate(st.session_state.refeicoes.get(refeicao, [])):
            with st.expander(f"{alimento['quantidade']}g de {alimento['nome']}"):
                nutrientes = alimento['nutrientes_calculados']
                st.write(f"- Calorias: {nutrientes['calorias']:.2f} kcal")
                st.write(f"- Proteínas: {nutrientes['proteina']:.2f} g")
                st.write(f"- Carboidratos: {nutrientes['carboidratos']:.2f} g")
                st.write(f"- Ferro: {nutrientes['ferro']:.2f} mg")
                if st.button("Remover", key=f"remove_{refeicao}_{i}", use_container_width=True):
                    st.session_state.refeicoes[refeicao].pop(i)
                    st.rerun()

    st.divider()
    
    if st.button("Calcular Total do Dia e Gerar Resumo", type="primary"):
        if any(st.session_state.refeicoes.values()):
            st.header("3. Resumo do Dia")
            
            total_nutrientes = {'calorias': 0, 'proteina': 0, 'carboidratos': 0, 'ferro': 0}
            for lista_alimentos in st.session_state.refeicoes.values():
                for alimento in lista_alimentos:
                    for nutriente, valor in alimento['nutrientes_calculados'].items():
                        total_nutrientes[nutriente] += valor
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total de Calorias", f"{total_nutrientes['calorias']:.0f} kcal")
            c2.metric("Total de Proteínas", f"{total_nutrientes['proteina']:.1f} g")
            c3.metric("Total de Carboidratos", f"{total_nutrientes['carboidratos']:.1f} g")
            c4.metric("Total de Ferro", f"{total_nutrientes['ferro']:.2f} mg")

            df_grafico = pd.DataFrame(total_nutrientes.items(), columns=['nutriente', 'valor'])
            plotar_nutrientes(df_grafico, st.session_state.calorias_diarias)

            calorias_consumidas = total_nutrientes['calorias']
            meta_calorica = st.session_state.calorias_diarias
            if calorias_consumidas > meta_calorica:
                st.warning(f"Atenção! Você consumiu {calorias_consumidas - meta_calorica:.0f} kcal a mais que sua meta diária.")
            else:
                st.success("Parabéns! Você está dentro da sua meta calórica diária.")
        else:
            st.info("Nenhum alimento foi registrado. Adicione itens às suas refeições para ver o resumo.")
