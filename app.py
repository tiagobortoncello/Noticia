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
    return api_key  # Não mostra erro aqui — vamos validar antes de usar

# --- Função para carregar exemplos de matérias do CSV ---
def carregar_exemplos_materias(caminho_arquivo="exemplos.csv"):
    if not os.path.exists(caminho_arquivo):
        return ""

    try:
        df = pd.read_csv(caminho_arquivo, encoding='utf-8')
        exemplos = []
        for _, row in df.iterrows():
            titulo = str(row.get('titulo', '')).strip()
            corpo = str(row.get('corpo', '')).strip()
            if titulo and corpo:
                exemplos.append(f"Título: {titulo}\n\n{corpo}")
        return "\n\n".join(exemplos)
    except Exception as e:
        st.warning(f"⚠️ Erro ao carregar exemplos: {e}")
        return ""

# --- Função para gerar matéria no estilo real da ALMG ---
def gerar_materia(texto_livre, api_key):
    exemplos = carregar_exemplos_materias("exemplos.csv")
    
    prompt = f"""
Você é um redator oficial da Assembleia Legislativa de Minas Gerais (ALMG).
Transforme o texto abaixo em uma matéria jornalística institucional no estilo real das notícias publicadas no site da ALMG.

# ESTILO EXIGIDO:
- Comece com um título informativo, sem aspas ou formatação.
- Em seguida, escreva o corpo em linguagem formal, neutra e objetiva.
- Incorpore data, local e agentes diretamente no texto (ex: "Nesta terça-feira (26/11/25), no Plenário da ALMG...").
- Inclua citações entre aspas com autoria clara.
- Não use assinatura, nem frases como "segundo informações".
- Mantenha entre 150 e 250 palavras.

# EXEMPLOS REAIS:
{exemplos}

# TEXTO DO USUÁRIO:
{texto_livre}

# SAÍDA:
[Escreva APENAS a matéria final, nada mais.]
"""
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    try:
        response = requests.post(
            url,
            params={"key": api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except requests.exceptions.Timeout:
        return "❌ Erro: A requisição à API excedeu o tempo limite (30s)."
    except requests.exceptions.HTTPError as e:
        if response.status_code == 400:
            return "❌ Erro: Prompt inválido ou muito longo."
        elif response.status_code == 403 or response.status_code == 401:
            return "❌ Erro: Chave da API inválida ou ausente."
        else:
            return f"❌ Erro HTTP na API: {e}"
    except Exception as e:
        return f"❌ Erro inesperado: {str(e)}"

# --- Interface do usuário ---
st.subheader("Cole ou digite informações soltas sobre o fato")
texto_livre = st.text_area(
    "Texto livre",
    height=200,
    placeholder="Ex: Na terça-feira (25/11/25), na Comissão de Saúde da ALMG, o deputado João Silva apresentou o PL 999/2025 sobre saúde mental nas escolas. Ele disse: 'Precisamos agir antes que a crise se aprofunde'."
)

if st.button("Gerar Matéria no Estilo ALMG"):
    if not texto_livre.strip():
        st.error("Por favor, insira algum texto.")
    else:
        api_key = get_api_key()
        if not api_key:
            st.error("❌ Chave da API 'GOOGLE_API_KEY' não configurada. Defina-a nas secrets do Streamlit Cloud ou como variável de ambiente.")
            st.stop()

        with st.spinner("Gerando matéria no estilo oficial da ALMG..."):
            materia = gerar_materia(texto_livre, api_key)
        
        st.subheader("📝 Matéria Gerada")
        st.markdown(materia)
        
        if not materia.startswith("❌"):
            st.download_button(
                label="📥 Baixar matéria (TXT)",
                data=materia,
                file_name="materia_almg.txt",
                mime="text/plain"
            )
