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

## Stramlit Cloud

- 🌐 Wersja online: [audio-notes-ai-app.streamlit.app](https://audio-notes-ai-app.streamlit.app/)

  ## Konfiguracja klucza OpenAI API

Aplikacja korzysta z modelu językowego OpenAI, dlatego do jej działania potrzebny jest **własny klucz API** użytkownika.

### Skąd wziąć klucz?

1. Wejdź na stronę [platform.openai.com](https://platform.openai.com/) i zaloguj się na swoje konto.
2. Przejdź do zakładki **API keys**.
3. Utwórz nowy klucz (np. przyciskiem **Create new secret key**).
4. Skopiuj wygenerowany klucz – po zamknięciu okienka nie będzie już widoczny w całości.

### Jak używać klucza w aplikacji?

W aktualnej wersji aplikacji klucz **nie jest przechowywany na serwerze** – użytkownik podaje go samodzielnie:

- po uruchomieniu aplikacji pojawia się pole tekstowe, w którym należy wkleić swój klucz OpenAI API,
- klucz jest używany tylko w trakcie działania aplikacji na Twoim urządzeniu / sesji.

> **Uwaga dotycząca bezpieczeństwa:**  
> - Nie udostępniaj swojego klucza innym osobom.  
> - Nie wstawiaj klucza do kodu źródłowego ani do repozytoriów publicznych (np. GitHub).  
> - W razie podejrzenia wycieku klucza możesz go w każdej chwili usunąć i wygenerować nowy w panelu OpenAI.

Bez poprawnie wklejonego klucza API aplikacja nie będzie w stanie wysyłać zapytań do modelu i część funkcji (np. czat z AI) nie zadziała.

