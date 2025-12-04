# Audio Notatki AI

Aplikacja Streamlit do nagrywania głosówek, automatycznej transkrypcji i wyszukiwania notatek po treści. 
Idealna, gdy chcesz szybko „zrzucić z głowy” pomysły, a potem łatwo do nich wrócić.

## Funkcje

- 🎙 Nagrywanie notatek głosowych bezpośrednio w przeglądarce (komponent `audiorecorder`)
- 📁 Wgrywanie plików audio z dysku (tryb chmurowy)
- ✍️ Automatyczna transkrypcja nagrania do tekstu (OpenAI / model STT)
- 🧾 Edycja transkrypcji przed zapisem (możesz poprawić tekst)
- 🧠 Zapisywanie notatek w bazie (Qdrant – wektorowa baza danych)
- 🔍 Wyszukiwanie notatek po podobieństwie semantycznym (nie tylko „po słowie kluczowym”)
- 🖥 Dwa tryby pracy: lokalny (bez zewnętrznej bazy) i chmurowy (Qdrant w SaaS)

## Technologia

- Python + Streamlit
- OpenAI API (transkrypcja / LLM)
- Qdrant (wektorowe przechowywanie notatek)
- `audiorecorder` do nagrywania audio w przeglądarce

## Demo

- 🌐 Wersja online: [audio-notes-ai-app.streamlit.app](https://audio-notes-ai-app.streamlit.app/)
