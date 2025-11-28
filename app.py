import os
import pandas as pd
import requests
import streamlit as st

# --- Configuração inicial ---
st.set_page_config(page_title="Gerador de Matérias - ALMG", layout="wide")
st.title("📄 Gerador de Matérias Jornalísticas - ALMG")

# --- Função para carregar a chave de API ---
def get_api_key():
    api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("Erro: A chave de API do Google (GOOGLE_API_KEY) não foi configurada.")
        return None
    return api_key

# --- Função para carregar exemplos de matérias do CSV ---
def carregar_exemplos_materias(caminho_arquivo="exemplos.csv"):
    if not os.path.exists(caminho_arquivo):
        st.warning(f"Aviso: Arquivo de exemplos '{caminho_arquivo}' não encontrado. O modelo não terá referência de estilo.")
        return ""

    try:
        df = pd.read_csv(caminho_arquivo, encoding='utf-8')
        exemplos_formatados = []
        for i, row in df.iterrows():
            titulo = row.get('titulo', '').strip()
            corpo = row.get('corpo', '').strip()
            if titulo and corpo:
                exemplo = f"""Título: {titulo}

{corpo}
"""
                exemplos_formatados.append(exemplo)
        return "\n".join(exemplos_formatados)
    except Exception as e:
        st.error(f"Erro ao carregar exemplos de matérias: {e}")
        return ""

# --- Função para gerar matéria a partir de texto livre (estilo ALMG REAL) ---
def gerar_materia_a_partir_texto_livre(texto_livre, api_key, caminho_exemplos="exemplos.csv"):
    exemplos_texto = carregar_exemplos_materias(caminho_exemplos)
    
    prompt = f"""
Você é um redator oficial da Assembleia Legislativa de Minas Gerais (ALMG).  
Sua tarefa é transformar um texto não estruturado em uma **matéria jornalística institucional no estilo real das notícias publicadas no site da ALMG**.

# CARACTERÍSTICAS DO ESTILO DA ALMG (obrigatórias):
- A matéria começa com um **título informativo**, sem formatação adicional.
- **Imediatamente após o título**, vem o corpo do texto, **sem linhas separadas para "Data", "Local" ou "Por..."**.
- A **data e o local devem ser incorporados organicamente na narrativa** (ex: "Nesta terça-feira (25/11/24), no Plenário da ALMG, ...").
- Use linguagem **formal, neutra e objetiva**.
- Inclua **números de proposições** (PL, PEC, etc.) quando mencionados.
- Citações devem estar entre aspas e atribuídas claramente (ex: “...”, afirmou o deputado X).
- Não use assinatura, nem expressões como "a reportagem", "segundo informações", etc.
- Mantenha entre 150 e 250 palavras.

# EXEMPLOS REAIS DE MATÉRIAS DA ALMG
{exemplos_texto}

# TEXTO NÃO ESTRUTURADO FORNECIDO PELO USUÁRIO
{texto_livre}

# INSTRUÇÃO FINAL
Gere **apenas o texto da matéria**, começando pelo título e seguido diretamente pelo corpo.  
**Não inclua** rótulos como "Título:", "Corpo:", "Matéria:", nem comentários adicionais.
"""
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    params = {"key": api_key}
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    try:
        response = requests.post(url, params=params, json=payload, timeout=30)
        response.raise_for_status()
        resultado = response.json()
        texto = resultado.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "").strip()
        return texto if texto else "A API retornou uma resposta vazia."
    except requests.exceptions.RequestException as e:
        st.error(f"Erro na comunicação com a API: {e}")
        return None
    except Exception as e:
        st.error(f"Erro inesperado: {e}")
        return None

# --- Interface do usuário ---
st.subheader("Cole ou digite informações soltas sobre o fato")
texto_livre = st.text_area(
    "Texto livre",
    height=200,
    placeholder="Ex: Na terça-feira (25/11/24), no Plenário da ALMG, os deputados encerraram a discussão em 1º turno da PEC 010479/23 sobre a Copasa. O deputado X disse: 'Essa proposta ameaça o saneamento público'. A votação ocorrerá amanhã."
)

if st.button("Gerar Matéria no Estilo ALMG"):
    if not texto_livre.strip():
        st.error("Por favor, insira algum texto.")
    else:
        api_key = get_api_key()
        if not api_key:
            st.stop()
        with st.spinner("Gerando matéria no estilo oficial da ALMG..."):
            materia = gerar_materia_a_partir_texto_livre(texto_livre, api_key, caminho_exemplos="exemplos.csv")
        if materia:
            st.subheader("📝 Matéria Gerada")
            st.markdown(materia)
            st.download_button(
                label="📥 Baixar matéria (TXT)",
                data=materia,
                file_name="materia_almg.txt",
                mime="text/plain"
            )
