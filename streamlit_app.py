
import streamlit as st
import json
import re

# Simulação da chamada à API Gemini
# Em um ambiente real, você faria uma requisição HTTP para a API Gemini
# com o seu prompt e receberia a resposta.
def call_gemini_api(prompt_text):
    """
    Simula uma chamada à API Gemini para extrair informações de doação.
    Em um aplicativo real, esta função faria uma requisição HTTP para a API Gemini.
    """
    # Exemplo de como a API Gemini poderia responder para "Cristiane 6 litros de leite"
    if "Cristiane 6 litros de leite" in prompt_text:
        return {
            "donor_name": "Cristiane",
            "item": "Leite",
            "quantity": 6,
            "unit": "litros"
        }
    elif "Marraschi 2kg de Bacon" in prompt_text:
        return {
            "donor_name": "Marraschi",
            "item": "Bacon",
            "quantity": 2,
            "unit": "quilos"
        }
    elif "Marraschi 2kg de Calabresa" in prompt_text:
        return {
            "donor_name": "Marraschi",
            "item": "Calabresa",
            "quantity": 2,
            "unit": "quilos"
        }
    # Adicione mais exemplos ou use uma lógica mais robusta para simular
    # a extração de informações para outros itens e formatos.
    # Para fins de demonstração, vamos tentar extrair com regex se não for um dos exemplos fixos.
    
    # Tentativa de extração genérica usando regex para simulação
    match = re.search(r"([A-Za-zÀ-ú\s]+)\s+(\d+)\s*([A-Za-zÀ-ú]+)\s+de\s+([A-Za-zÀ-ú\s]+)", prompt_text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        quantity = int(match.group(2))
        unit = match.group(3).strip()
        item = match.group(4).strip()
        return {
            "donor_name": name,
            "item": item,
            "quantity": quantity,
            "unit": unit
        }
    
    match = re.search(r"([A-Za-zÀ-ú\s]+)\s+(\d+)\s*([A-Za-zÀ-ú]+)", prompt_text, re.IGNORECASE)
    if match:
        name = match.group(1).strip()
        quantity = int(match.group(2))
        item_or_unit = match.group(3).strip()
        
        # Simple heuristic to guess if the last part is an item or unit
        if item_or_unit.lower() in ["quilos", "litros", "pct", "vidro", "garrafas", "cartelas", "caixinhas"]:
            # Assume the unit is given, and the item is implied by context (needs real LLM for this)
            # For simulation, we'll need a way to map unit to item, or assume item is part of the prompt.
            # This is where a real LLM shines. For now, let's return null for item if it's just unit.
            return {
                "donor_name": name,
                "item": None, # Cannot infer item reliably without more context or a real LLM
                "quantity": quantity,
                "unit": item_or_unit
            }
        else:
            # Assume the last part is the item, and unit needs to be inferred or is missing
            return {
                "donor_name": name,
                "item": item_or_unit,
                "quantity": quantity,
                "unit": None # Unit needs to be inferred by real LLM
            }
    
    return None # Fallback if no match

def get_gemini_prompt(user_input):
    """
    Gera o prompt para a API Gemini para extrair informações de doação.
    """
    return f"""
    Extraia o nome do doador, o item doado, e a quantidade (número e unidade) do seguinte texto.
    Se uma unidade não for explicitamente mencionada, mas for implícita pelo item (por exemplo, 'litros' para 'leite', 'quilos' para 'arroz'), infira-a.
    Se a unidade for "pct x 500g", a quantidade deve ser o número de pacotes e a unidade "pct".
    Se a unidade for "garrafas x 2l", a quantidade deve ser o número de garrafas e a unidade "garrafas".
    Responda no formato JSON com as chaves 'donor_name', 'item', 'quantity', 'unit'.
    Se alguma informação estiver faltando ou não estiver clara, defina o valor como null.
    Texto: '{user_input}'
    """

# Estrutura inicial da lista de doações
# Usamos um dicionário para facilitar a atualização e o rastreamento
initial_donations_data = {
    "Arroz": {"total_needed": 10, "unit": "quilos", "donated_by": []},
    "Farinha de Mandioca": {"total_needed": 4, "unit": "quilos", "donated_by": []},
    "Feijão": {"total_needed": 10, "unit": "quilos", "donated_by": []},
    "Café": {"total_needed": 8, "unit": "pct", "donated_by": []}, # 8 pct x 500g
    "Macarrão Espaguete nº 8": {"total_needed": 6, "unit": "quilos", "donated_by": []},
    "Presunto Fatia": {"total_needed": 2, "unit": "quilos", "donated_by": []},
    "Queijo Fatia": {"total_needed": 2, "unit": "quilos", "donated_by": []},
    "Bacon": {"total_needed": 5, "unit": "quilos", "donated_by": [{"name": "Marraschi", "quantity": 2}]},
    "Calabresa": {"total_needed": 5, "unit": "quilos", "donated_by": [{"name": "Marraschi", "quantity": 2}]},
    "Sal": {"total_needed": None, "unit": "INTEGRAL", "donated_by": []}, # Quantidade não especificada
    "Molho de Tomate": {"total_needed": 3, "unit": "quilos", "donated_by": []},
    "Farinha de Trigo": {"total_needed": 2, "unit": "quilos", "donated_by": []},
    "Achocolatado": {"total_needed": 1, "unit": "quilo", "donated_by": []},
    "Adoçante": {"total_needed": 1, "unit": "vidro", "donated_by": []},
    "Açúcar Refinado": {"total_needed": 8, "unit": "quilos", "donated_by": []},
    "Óleo de soja": {"total_needed": 5, "unit": "garrafas", "donated_by": []},
    "Vinagre": {"total_needed": 2, "unit": "garrafas", "donated_by": []},
    "Azeite": {"total_needed": 1, "unit": "garrafa", "donated_by": []},
    "Manteiga/Margarina": {"total_needed": 3, "unit": "quilos", "donated_by": []},
    "Ovos": {"total_needed": 8, "unit": "cartelas", "donated_by": []},
    "Leite": {"total_needed": 12, "unit": "litros", "donated_by": [{"name": "Raphael", "quantity": 6}]},
    "Azeitona s/caroço": {"total_needed": 2, "unit": "pct", "donated_by": []},
    "Refrigerante": {"total_needed": 12, "unit": "garrafas", "donated_by": []}, # 12 garrafas x 2l
    "Suco Concentrado": {"total_needed": 5, "unit": "litros", "donated_by": []},
    "Biscoito Salgado": {"total_needed": 20, "unit": "pct", "donated_by": []},
    "Biscoito Doce (Maisena, Rosca)": {"total_needed": 15, "unit": "pct", "donated_by": []},
    "Biscoito Doce Recheado": {"total_needed": 12, "unit": "pct", "donated_by": []},
    "Alho": {"total_needed": 3, "unit": "quilos", "donated_by": []},
    "Ervilha pct 500g": {"total_needed": 8, "unit": "pct", "donated_by": []},
    "Batata Palha pct 500g": {"total_needed": 4, "unit": "pct", "donated_by": []},
    "Creme de Leite": {"total_needed": 15, "unit": "caixinhas", "donated_by": []}
}

# Inicializa a lista de doações no session_state do Streamlit
if 'donations' not in st.session_state:
    st.session_state.donations = initial_donations_data

def update_donation_list(donor_name, item, quantity, unit):
    """
    Atualiza a lista de doações com a nova doação.
    """
    item_found = False
    for key, data in st.session_state.donations.items():
        # Normaliza o nome do item para comparação (ignora maiúsculas/minúsculas e acentos)
        normalized_key = key.lower().replace(" ", "").replace("nº8", "n8").replace("s/caroço", "semcaroco").replace("500g", "")
        normalized_item = item.lower().replace(" ", "").replace("nº8", "n8").replace("s/caroço", "semcaroco").replace("500g", "")

        if normalized_item in normalized_key: # Verifica se o item doado é parte do nome do item na lista
            # Adiciona a nova doação à lista de doadores para este item
            st.session_state.donations[key]["donated_by"].append({"name": donor_name, "quantity": quantity})
            item_found = True
            break
    return item_found

def generate_display_text():
    """
    Gera o texto formatado da lista de doações.
    """
    header = """
🚨🚨🚨 MUITA ATENÇÃO 🚨🚨🚨
" ... até aqui o SENHOR nos ajudou... "   -     1 Samuel 7:12

Amados irmãos,  sobre  o CUR Masculino que acontecerá nos dias 06, 07 e 08 de junho peço o comprometimento de todos (mulheres,  homens e jovens) na conquista desses itens que abaixo compartilho com vocês:

Favor colocar o nome e as quantidades ao lado de cada item. A lista será atualizada diariamente.

Alimentos 	Quantidade
"""
    footer = """
VOCÊ TAMBÉM PODE FAZER SUA DOAÇÃO ATRAVÉS DA CHAVE PIX CELULAR: 21971889700
BANCO BRADESCO  - MARCIO FRANCISCO MARRASCHI PINTO E ENCAMINHAR O COMPROVANTE PARA 21974292446 E DISPONIBILIZÁ-LO NO GRUPO TAMBÉM. 

Muito obrigado! 
"""
    
    items_text = []
    for item, data in st.session_state.donations.items():
        total_needed = data["total_needed"]
        unit = data["unit"]
        donated_by_list = data["donated_by"]

        current_donated = sum(d["quantity"] for d in donated_by_list)

        donors_str = ", ".join([f"{d['name']} {d['quantity']} {unit}" for d in donated_by_list])

        line = f"▪{item}\t- "
        if total_needed is not None:
            line += f"{total_needed} {unit}"
            if donors_str:
                line += f" - {donors_str}"

            remaining = total_needed - current_donated
            if remaining <= 0:
                line = f"✅{item}\t- {total_needed} {unit} - {donors_str} - COMPLETO"
            elif remaining > 0 and donors_str:
                line += f" - faltam {remaining} {unit}"
        else: # Para itens sem quantidade total_needed (ex: Sal INTEGRAL)
            if donors_str:
                line += f" - {donors_str}"
            else:
                line += f"{unit}" # Apenas a unidade se não houver doação e não houver total_needed

        items_text.append(line)

    return header + "\n".join(items_text) + "\n" + footer

# Título da aplicação Streamlit
st.title("Sistema de Doações")

st.write("Digite o nome do doador e o que foi doado (ex: 'Cristiane 6 litros de leite'):")
user_input = st.text_input("Sua Doação:")

if st.button("Registrar Doação"):
    if user_input:
        # Simula a chamada à API Gemini
        # Em um aplicativo real, você faria:
        # gemini_prompt = get_gemini_prompt(user_input)
        # response = call_gemini_api(gemini_prompt)
        
        # Usando a função de simulação
        gemini_response = call_gemini_api(user_input)

        if gemini_response and gemini_response.get("donor_name") and gemini_response.get("item") and gemini_response.get("quantity") is not None:
            donor_name = gemini_response["donor_name"]
            item = gemini_response["item"]
            quantity = gemini_response["quantity"]
            unit = gemini_response.get("unit", "") # Pode ser null se a Gemini não inferir

            if update_donation_list(donor_name, item, quantity, unit):
                st.success(f"Doação de {donor_name} para {quantity} {unit} de {item} registrada com sucesso!")
            else:
                st.warning(f"Item '{item}' não encontrado na lista de doações. Por favor, verifique o nome do item.")
        else:
            st.error("Não foi possível extrair as informações da doação. Por favor, tente novamente com um formato mais claro.")
            st.json(gemini_response) # Para depuração, mostre a resposta simulada
    else:
        st.warning("Por favor, digite sua doação.")

st.markdown("---")
st.subheader("Lista de Doações Atualizada")
st.text_area("Lista de Doações", value=generate_display_text(), height=600, disabled=True)

# Botão para resetar a lista (opcional, para testes)
if st.button("Resetar Lista de Doações"):
    st.session_state.donations = initial_donations_data
    st.success("Lista de doações resetada para o estado inicial.")
