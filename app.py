import streamlit as st
import openai
import requests
import os
import urllib3
from dotenv import load_dotenv
from openai import AzureOpenAI

# Charger les variables d'environnement depuis le fichier .env
load_dotenv()

# Désactiver les avertissements SSL (temporaire si verify=False)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configuration de l'API OpenAI
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version="2023-07-01-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

# Variables Azure Search
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_index = os.getenv("AZURE_SEARCH_INDEX")
search_key = os.getenv("AZURE_SEARCH_KEY")

# Interface utilisateur
st.set_page_config(page_title="Assistant Conformité RAG", layout="centered")
st.title("📚 Assistant Conformité - RAG")
st.success("Bienvenue dans l'assistant conformité IA 💼 Pose une question ci-dessous 👇")

question = st.text_input("📝 Pose ta question sur la conformité ou les règles internes :")

if question:
    st.markdown("🔍 Recherche des documents pertinents...")

    headers = {
        "Content-Type": "application/json",
        "api-key": search_key
    }

    search_url = f"{search_endpoint}/indexes/{search_index}/docs/search?api-version=2021-04-30-Preview"

    search_payload = {
        "search": question,
        "top": 3
    }

    response = requests.post(search_url, headers=headers, json=search_payload, verify=False)
    response.raise_for_status()

    docs = response.json().get("value", [])

    if not docs:
        st.warning("⚠️ Aucun document trouvé. L'IA va répondre avec ses connaissances internes.")
        context = "Aucun document trouvé."
    else:
        context = "\n\n".join([
            f"[Document {i+1} - {doc.get('metadata_storage_name') or doc.get('source') or doc.get('title') or 'Document inconnu'}]\n{doc.get('content', '')}"
            for i, doc in enumerate(docs)
        ])

    st.markdown("🤖 Génération de la réponse via GPT...")

    response = client.chat.completions.create(
        model="gpt-35-turbo-16k",  # Nom exact du déploiement
        messages=[
            {"role": "system", "content": "Tu es un assistant expert en conformité réglementaire."},
            {"role": "user", "content": f"Voici les documents :\n{context}\n\nRéponds à la question suivante : {question}"}
        ],
        temperature=0.3,
        max_tokens=500
    )

    answer = response.choices[0].message.content

    st.markdown("### ✅ Réponse de l'IA")
    st.write(answer)

    if docs:
        st.markdown("### 📎 Sources utilisées")
        for i, doc in enumerate(docs):
            nom = doc.get('metadata_storage_name') or doc.get('source') or doc.get('title') or 'Document inconnu'
            st.write(f"**Document {i+1}** : {nom}")
