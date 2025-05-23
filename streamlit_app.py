import streamlit as st
import json
import re
import requests # Importa a biblioteca requests para fazer chamadas HTTP
import os # Importa a biblioteca os para acessar variáveis de ambiente
import streamlit.components.v1 as components # Importa para injetar JavaScript

# Importa o Firebase Admin SDK
import firebase_admin
from firebase_admin import credentials, firestore # Removido 'auth' pois não será usado diretamente para signIn

# --- Configuração e Inicialização do Firebase ---
# A chave da API e a configuração do Firebase são injetadas pelo ambiente Canvas.
# Para rodar localmente, você precisaria de um arquivo de credenciais de serviço.
# No ambiente Canvas, __firebase_config e __initial_auth_token são globais.

# Verifica se o Firebase já foi inicializado para evitar erros
if not firebase_admin._apps:
    try:
        # Tenta carregar a configuração do Firebase do ambiente Canvas
        firebase_config = json.loads(os.environ.get('__firebase_config', '{}'))
        if not firebase_config:
            st.error("Configuração do Firebase não encontrada. Certifique-se de que '__firebase_config' está definida no ambiente.")
            # Para testes locais, você pode carregar de um arquivo de credenciais
            # cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
            # firebase_admin.initialize_app(cred)
            st.stop() # Para a execução do app se a configuração não for encontrada
        else:
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
        
        # A autenticação do Admin SDK é feita automaticamente com as credenciais.
        # Não é necessário chamar sign_in_anonymously ou sign_in_with_custom_token aqui.
        # Essas funções são para SDKs cliente.
            
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase: {e}. Verifique suas credenciais e configuração.")
        st.stop() # Para a execução do app se o Firebase não puder ser inicializado

db = firestore.client()
app_id = os.environ.get('__app_id', 'default-app-id') # Obtém o ID do app do ambiente Canvas

# Caminho para o documento no Firestore onde a lista de doações será armazenada
# Usamos o app_id para isolar os dados deste aplicativo específico
DONATIONS_DOC_REF = db.collection('artifacts').document(app_id).collection('public').document('data').collection('donations_list').document('current_list')


# Estrutura inicial da lista de doações
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

# --- Funções de persistência do Firestore ---
def load_donations_from_firestore():
    """Carrega a lista de doações do Firestore."""
    try:
        doc = DONATIONS_DOC_REF.get()
        if doc.exists:
            st.success("Lista de doações carregada do Firestore!")
            return doc.to_dict()
        else:
            st.info("Nenhuma lista de doações encontrada no Firestore. Usando a lista inicial.")
            return initial_donations_data
    except Exception as e:
        st.error(f"Erro ao carregar doações do Firestore: {e}. Verifique suas regras de segurança ou conexão.")
        return initial_donations_data

def save_donations_to_firestore(data):
    """Salva a lista de doações no Firestore."""
    try:
        DONATIONS_DOC_REF.set(data)
        st.success("Lista de doações salva no Firestore!")
    except Exception as e:
        st.error(f"Erro ao salvar doações no Firestore: {e}. Verifique suas regras de segurança ou conexão.")

# Inicializa a lista de doações no session_state do Streamlit
# Carrega do Firestore na primeira execução
if 'donations' not in st.session_state:
    st.session_state.donations = load_donations_from_firestore()


def get_gemini_prompt(user_input):
    """
    Gera o prompt para a API Gemini para extrair informações de doação.
    Este prompt agora solicita uma ARRAY de doações.
    """
    return f"""
    Extraia todas as doações do seguinte texto. Para cada doação, identifique o nome do doador, o item doado, e a quantidade (número e unidade).
    Se uma unidade não for explicitamente mencionada, mas for implícita pelo item (por exemplo, 'litros' para 'leite', 'quilos' para 'arroz'), infira-a.
    Para itens como "Café", "Ervilha pct 500g", "Batata Palha pct 500g", considere a unidade como "pct".
    Para itens como "Refrigerante", considere a unidade como "garrafas".
    Responda no formato JSON como uma ARRAY de objetos, onde cada objeto tem as chaves 'donor_name' (string), 'item' (string), 'quantity' (integer), 'unit' (string).
    Se alguma informação estiver faltando ou não estiver clara para uma doação específica, defina o valor como null para aquela propriedade.
    Exemplo de entrada: "Fátima Ramos 2 garrafa de vinagre e 2 óleo de soja\\nRei: 10 kg Arroz e 01 pacote de 500 g de café"
    Exemplo de saída JSON:
    [
      {{
        "donor_name": "Fátima Ramos",
        "item": "vinagre",
        "quantity": 2,
        "unit": "garrafas"
      }},
      {{
        "donor_name": "Fátima Ramos",
        "item": "óleo de soja",
        "quantity": 2,
        "unit": "garrafas"
      }},
      {{
        "donor_name": "Rei",
        "item": "Arroz",
        "quantity": 10,
        "unit": "quilos"
      }},
      {{
        "donor_name": "Rei",
        "item": "café",
        "quantity": 1,
        "unit": "pct"
      }}
    ]
    Texto a ser processado: '{user_input}'
    """

def call_gemini_api(prompt_text):
    """
    Chama a API Gemini para extrair informações de doação.
    Espera uma ARRAY de objetos JSON como resposta.
    """
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt_text}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": {
                "type": "ARRAY", # Agora esperando uma ARRAY
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "donor_name": {"type": "STRING"},
                        "item": {"type": "STRING"},
                        "quantity": {"type": "INTEGER"},
                        "unit": {"type": "STRING"}
                    },
                    "required": ["donor_name", "item", "quantity", "unit"]
                }
            }
        }
    }
    
    try:
        apiKey = st.secrets["GEMINI_API_KEY"]
    except KeyError:
        st.error("Chave de API Gemini não encontrada. Por favor, configure 'GEMINI_API_KEY' em seus segredos do Streamlit.")
        return None

    apiUrl = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={apiKey}"

    try:
        response = requests.post(apiUrl, headers={'Content-Type': 'application/json'}, data=json.dumps(payload))
        response.raise_for_status()
        result = response.json()

        if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
            json_string = result["candidates"][0]["content"]["parts"][0]["text"]
            parsed_json = json.loads(json_string)
            
            # Garante que a resposta seja sempre uma lista, mesmo que Gemini retorne um único objeto
            if not isinstance(parsed_json, list):
                parsed_json = [parsed_json]
            return parsed_json
        else:
            st.error(f"Estrutura de resposta inesperada da Gemini. Resposta completa: {result}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao chamar a API Gemini: {e}")
        return None
    except json.JSONDecodeError as e:
        st.error(f"Erro ao decodificar a resposta JSON da Gemini: {e}. Resposta bruta: {response.text}")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
        return None

def update_donation_list(donor_name, item, quantity, unit):
    """
    Atualiza a lista de doações com a nova doação.
    """
    item_found = False
    for key, data in st.session_state.donations.items():
        # Normaliza o nome do item para comparação (ignora maiúsculas/minúsculas e acentos)
        normalized_key = key.lower().replace(" ", "").replace("nº8", "n8").replace("s/caroço", "semcaroco").replace("500g", "")
        normalized_item = item.lower().replace(" ", "").replace("nº8", "n8").replace("s/caroço", "semcaroco").replace("500g", "")

        # Verifica se o item doado é parte do nome do item na lista
        if normalized_item in normalized_key: 
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

st.write("Digite o nome do doador e o que foi doado (ex: 'Fulano 6 litros de leite ou Sicrano 2kg de açúcar'):")
user_input = st.text_area("Sua Doação:", height=150) # Aumentei a altura para melhor visualização

if st.button("Registrar Doação"):
    if user_input:
        with st.spinner('Processando doação(ões) com Gemini...'):
            gemini_prompt = get_gemini_prompt(user_input)
            list_of_gemini_responses = call_gemini_api(gemini_prompt) # Agora espera uma lista

        if list_of_gemini_responses:
            donations_processed_count = 0
            for donation_info in list_of_gemini_responses:
                donor_name = donation_info.get("donor_name")
                item = donation_info.get("item")
                quantity = donation_info.get("quantity")
                unit = donation_info.get("unit", "")

                if donor_name and item and quantity is not None:
                    if update_donation_list(donor_name, item, quantity, unit):
                        st.success(f"Doação de {donor_name} para {quantity} {unit} de {item} registrada com sucesso!")
                        donations_processed_count += 1
                    else:
                        st.warning(f"Item '{item}' não encontrado na lista de doações. Por favor, verifique o nome do item.")
                else:
                    st.warning(f"Não foi possível extrair todas as informações de uma doação. Detalhes: {donation_info}")
            
            if donations_processed_count == 0:
                st.error("Nenhuma doação válida foi extraída do texto. Por favor, tente novamente com um formato mais claro.")
            
            # Salva a lista atualizada no Firestore após processar todas as doações
            save_donations_to_firestore(st.session_state.donations)
        else:
            st.error("Não foi possível processar as doações. A resposta da Gemini estava vazia ou inválida.")
            
    else:
        st.warning("Por favor, digite sua doação.")

st.markdown("---")
st.subheader("Lista de Doações Atualizada")
output_text_area_content = generate_display_text()
st.text_area("Lista de Doações", value=output_text_area_content, height=600, disabled=True)

# Botão para copiar o texto da área de saída
if st.button("Copiar Lista"):
    # Código JavaScript para copiar o texto para a área de transferência
    # Usamos json.dumps para escapar corretamente a string para JavaScript
    js_code = f"""
    <script>
        function copyText() {{
            var text = {json.dumps(output_text_area_content)};
            var textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.style.position = "fixed"; // Evita rolagem para o final
            textArea.style.left = "-9999px"; // Esconde o elemento
            document.body.appendChild(textArea);
            textArea.select();
            try {{
                var successful = document.execCommand('copy');
            }} catch (err) {{
                console.error('Erro ao copiar: ', err);
            }}
            document.body.removeChild(textArea);
        }}
        copyText(); // Chama a função imediatamente quando o componente é renderizado
    </script>
    """
    components.html(js_code, height=0, width=0) # height e width 0 para esconder o componente HTML
    st.success("Texto copiado para a área de transferência!")

# Botão para resetar a lista (opcional, para testes)
if st.button("Resetar Lista de Doações"):
    st.session_state.donations = initial_donations_data
    save_donations_to_firestore(st.session_state.donations) # Salva o estado inicial no Firestore
    st.success("Lista de doações resetada para o estado inicial.")
