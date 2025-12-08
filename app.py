from io import BytesIO
import streamlit as st
from audiorecorder import audiorecorder  # type: ignore
from dotenv import dotenv_values
from hashlib import md5
from openai import OpenAI
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
import time
from pydub import AudioSegment
from pydub.utils import which

def get_secret(key: str):
    """Bezpieczne pobieranie sekretów – nie sypie błędem lokalnie, gdy nie ma secrets.toml."""
    try:
        return st.secrets[key]
    except Exception:
        return None


env = dotenv_values(".env")

# Nadpisz wartości z secrets jeśli są dostępne (tylko na Streamlit Cloud)
try:
    if 'QDRANT_URL' in st.secrets:
        env['QDRANT_URL'] = st.secrets['QDRANT_URL']
    if 'QDRANT_API_KEY' in st.secrets:
        env['QDRANT_API_KEY'] = st.secrets['QDRANT_API_KEY']
except Exception as e:
    st.info("💻 Tryb lokalny – `st.secrets` niedostępne")


# 🔍 DEBUG – sprawdzenie, czy dane się wczytały
st.write(f"🌐 URL: {env.get('QDRANT_URL')}")
st.write(f"🔑 API KEY: {'✔️' if env.get('QDRANT_API_KEY') else '❌'}")



EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIM = 3072
AUDIO_TRANSCRIBE_MODEL = "whisper-1"
QDRANT_COLLECTION_NAME = "notes"

def get_openai_client():
    api_key = get_secret("OPENAI_API_KEY") or st.session_state.get("openai_api_key")
    if not api_key:
        st.warning("Dodaj klucz OpenAI (w secrets na Cloud lub w polu poniżej).")
        st.stop()
    return OpenAI(api_key=api_key)

def transcribe_audio(audio_bytes):
    openai_client = get_openai_client()
    audio_file = BytesIO(audio_bytes)
    audio_file.name = "audio.mp3"
    transcript = openai_client.audio.transcriptions.create(
        file=audio_file,
        model=AUDIO_TRANSCRIBE_MODEL,
        response_format="verbose_json",
    )
    return transcript.text

#
# DB - WERSJA Z HARDKODOWANYMI WARTOŚCIAMI + TIMEOUT + OBSŁUGA BŁĘDÓW
#
@st.cache_resource
def get_qdrant_client():
    """Tworzy połączenie z Qdrant z obsługą błędów"""
    try:
        # Użyj env.get() ale z fallback do hardkodowanych wartości
        url = env.get("QDRANT_URL") 
        api_key = env.get("QDRANT_API_KEY") 
        
        st.info(f"🔗 Łączę z Qdrant...")
        
        client = QdrantClient(
            url=url,
            api_key=api_key,
            timeout=15.0  # 15 sekund timeout
        )
        
        # Test połączenia
        collections = client.get_collections()
        st.success("✅ Połączono z Qdrant!")
        return client
        
    except Exception as e:
        st.error(f"❌ Błąd połączenia z Qdrant: {str(e)}")
        st.info("💡 Spróbuj odświeżyć stronę lub wyczyścić cache")
        return None

def assure_db_collection_exists():
    """Sprawdza i tworzy kolekcję z obsługą błędów"""
    qdrant_client = get_qdrant_client()
    
    if qdrant_client is None:
        st.error("❌ Nie można połączyć z bazą danych!")
        st.stop()
    
    try:
        if not qdrant_client.collection_exists(QDRANT_COLLECTION_NAME):
            st.info("🔨 Tworzę kolekcję...")
            qdrant_client.create_collection(
                collection_name=QDRANT_COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIM,
                    distance=Distance.COSINE,
                ),
            )
            st.success("✅ Kolekcja utworzona!")
        else:
            st.success("✅ Kolekcja już istnieje")
            
    except Exception as e:
        st.error(f"❌ Błąd przy sprawdzaniu kolekcji: {str(e)}")
        st.stop()

def get_embedding(text):
    openai_client = get_openai_client()
    result = openai_client.embeddings.create(
        input=[text],
        model=EMBEDDING_MODEL,
        dimensions=EMBEDDING_DIM,
    )
    return result.data[0].embedding

def add_note_to_db(note_text):
    """Dodaje notatkę z obsługą błędów"""
    try:
        qdrant_client = get_qdrant_client()
        if qdrant_client is None:
            st.error("❌ Brak połączenia z bazą danych!")
            return False
            
        points_count = qdrant_client.count(
            collection_name=QDRANT_COLLECTION_NAME,
            exact=True,
        )
        
        qdrant_client.upsert(
            collection_name=QDRANT_COLLECTION_NAME,
            points=[
                PointStruct(
                    id=points_count.count + 1,
                    vector=get_embedding(text=note_text),
                    payload={"text": note_text},
                )
            ]
        )
        return True
        
    except Exception as e:
        st.error(f"❌ Błąd przy zapisywaniu notatki: {str(e)}")
        return False

def list_notes_from_db(query=None):
    """Lista notatek z obsługą błędów"""
    try:
        qdrant_client = get_qdrant_client()
        if qdrant_client is None:
            st.error("❌ Brak połączenia z bazą danych!")
            return []
            
        if not query:
            notes = qdrant_client.scroll(collection_name=QDRANT_COLLECTION_NAME, limit=10)[0]
            result = []
            for note in notes:
                result.append({
                    "text": note.payload["text"],
                    "score": None,
                })
            return result
        else:
            notes = qdrant_client.search(
                collection_name=QDRANT_COLLECTION_NAME,
                query_vector=get_embedding(text=query),
                limit=10,
            )
            result = []
            for note in notes:
                result.append({
                    "text": note.payload["text"],
                    "score": note.score,
                })
            return result
            
    except Exception as e:
        st.error(f"❌ Błąd przy wyszukiwaniu notatek: {str(e)}")
        return []

#
# MAIN
#
st.set_page_config(page_title="Audio Notatki", layout="centered")

# Przycisk do czyszczenia cache
if st.sidebar.button("🔄 Wyczyść cache połączenia"):
    st.cache_resource.clear()
    st.rerun()

# OpenAI API key protection
if not st.session_state.get("openai_api_key"):
    if "OPENAI_API_KEY" in env:
        st.session_state["openai_api_key"] = env["OPENAI_API_KEY"]
    else:
        st.info("Dodaj swój klucz API OpenAI aby móc korzystać z tej aplikacji")
        st.session_state["openai_api_key"] = st.text_input("Klucz API", type="password")
        if st.session_state["openai_api_key"]:
            st.rerun()

if not st.session_state.get("openai_api_key"):
    st.stop()

# Session state initialization
if "note_audio_bytes_md5" not in st.session_state:
    st.session_state["note_audio_bytes_md5"] = None

if "note_audio_bytes" not in st.session_state:
    st.session_state["note_audio_bytes"] = None

if "note_text" not in st.session_state:
    st.session_state["note_text"] = ""

if "note_audio_text" not in st.session_state:
    st.session_state["note_audio_text"] = ""

st.title("Audio Notatki")

# Sprawdź połączenie z bazą danych
with st.spinner("🔄 Sprawdzam połączenie z bazą danych..."):
    assure_db_collection_exists()

add_tab, search_tab = st.tabs(["Dodaj notatkę", "Wyszukaj notatkę"])

with add_tab:
    st.write("🔄 Czekam na komponent audio...")
    time.sleep(1.5)

    note_audio = audiorecorder(
        start_prompt="Nagraj notatkę",
        stop_prompt="Zatrzymaj nagrywanie",
    )

    if note_audio:
        st.write("✅ Audio nagrane")
        st.write("📏 Długość audio:", len(note_audio.raw_data))

        audio = BytesIO()
        note_audio.export(audio, format="mp3")
        st.session_state["note_audio_bytes"] = audio.getvalue()

        current_md5 = md5(st.session_state["note_audio_bytes"]).hexdigest()
        if st.session_state.get("note_audio_bytes_md5") != current_md5:
            st.session_state["note_audio_text"] = ""
            st.session_state["note_text"] = ""
            st.session_state["note_audio_bytes_md5"] = current_md5

        st.audio(st.session_state["note_audio_bytes"], format="audio/mp3")

        # Transkrypcja
        if st.button("Transkrybuj audio"):
            with st.spinner("🎯 Transkrybuję audio..."):
                st.session_state["note_audio_text"] = transcribe_audio(st.session_state["note_audio_bytes"])

        # Edycja tekstu
        if st.session_state["note_audio_text"]:
            st.session_state["note_text"] = st.text_area(
                "Edytuj notatkę",
                value=st.session_state["note_audio_text"]
            )

        # Zapisz notatkę
        if st.session_state["note_text"] and st.button("Zapisz notatkę", disabled=not st.session_state["note_text"]):
            with st.spinner("💾 Zapisuję notatkę..."):
                if add_note_to_db(note_text=st.session_state["note_text"]):
                    st.toast("Notatka zapisana!", icon="🎉")
                    # Wyczyść formularz po zapisaniu
                    st.session_state["note_text"] = ""
                    st.session_state["note_audio_text"] = ""
                    st.session_state["note_audio_bytes_md5"] = None

    else:
        st.write("⚠️ Brak danych audio lub puste nagranie")

with search_tab:
    query = st.text_input("Wyszukaj notatkę")
    if st.button("Szukaj"):
        with st.spinner("🔍 Wyszukuję notatki..."):
            notes = list_notes_from_db(query)
            
            if notes:
                st.success(f"Znaleziono {len(notes)} notatek:")
                for note in notes:
                    with st.container(border=True):
                        st.markdown(note["text"])
                        if note["score"]:
                            st.markdown(f':violet[Podobieństwo: {note["score"]:.3f}]')
            else:
                st.info("Nie znaleziono notatek.")
