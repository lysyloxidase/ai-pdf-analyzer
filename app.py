import streamlit as st
import anthropic
from pypdf import PdfReader
import arxiv
from datetime import datetime

# --- Konfiguracja wyglądu strony ---
st.set_page_config(page_title="AI Asystent Badacza (Claude Haiku)", page_icon="⚡", layout="wide")
st.title("⚡ AI Asystent Badacza: Szybka i tania analiza (Claude 3 Haiku)")
st.write("Wgraj pliki PDF, a ultra-szybki model Claude 3 Haiku wyciągnie z nich to, co najważniejsze i porówna z najnowszą literaturą z ostatnich 2 lat.")

# --- Pasek boczny: Konfiguracja ---
with st.sidebar:
    st.header("⚙️ Ustawienia")
    klucz_api = st.text_input("Wklej swój klucz API Anthropic (Claude):", type="password")
    st.info("Pamiętaj: Nigdy nie udostępniaj swojego klucza publicznie!")

# --- Główne okno: Wgrywanie plików ---
wgrane_pliki = st.file_uploader("Wybierz pliki PDF", type="pdf", accept_multiple_files=True)

# --- Przycisk uruchamiający analizę ---
if st.button("🚀 Rozpocznij analizę i stwórz raport", type="primary"):
    
    if not klucz_api:
        st.error("Proszę, podaj najpierw klucz API w panelu bocznym!")
        st.stop()
        
    if not wgrane_pliki:
        st.warning("Proszę wgrać przynajmniej jeden plik PDF.")
        st.stop()

    try:
        # Inicjalizacja klienta Anthropic
        client = anthropic.Anthropic(api_key=klucz_api)
        
        with st.spinner('Krok 1/4: Błyskawiczne czytanie plików PDF...'):
            tekst_z_pdfow = ""
            for plik in wgrane_pliki:
                czytnik = PdfReader(plik)
                for strona in czytnik.pages:
                    tekst_z_pdfow += strona.extract_text() + "\n"
        
        with st.spinner('Krok 2/4: Generowanie zapytań wyszukiwania (Oszczędzanie tokenów)...'):
            prompt_slowa_kluczowe = f"""
            Na podstawie poniższego krótkiego fragmentu tekstu, podaj JEDNO zapytanie po angielsku (max 3-4 słowa), 
            aby znaleźć podobne badania na platformie Arxiv. Podaj TYLKO zapytanie, żadnego innego tekstu.
            Tekst: {tekst_z_pdfow[:2500]} 
            """
            
            # Używamy niezawodnego modelu Claude 3 Haiku
            response_query = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=20,
                messages=[{"role": "user", "content": prompt_slowa_kluczowe}]
            )
            zapytanie = response_query.content[0].text.strip()
            st.info(f"🔍 Szukam nowej literatury dla hasła: **{zapytanie}**")

        with st.spinner('Krok 3/4: Pobieranie najnowszych badań z bazy Arxiv...'):
            klient_arxiv = arxiv.Client()
            wyszukiwanie = arxiv.Search(query=zapytanie, max_results=4, sort_by=arxiv.SortCriterion.SubmittedDate)
            
            nowa_literatura_tekst = ""
            aktualny_rok = datetime.now().year
            for wynik in klient_arxiv.results(wyszukiwanie):
                if wynik.published.year >= (aktualny_rok - 2):
                    nowa_literatura_tekst += f"- Tytuł: {wynik.title} ({wynik.published.year})\n  Podsumowanie: {wynik.summary}\n\n"
                    
            if not nowa_literatura_tekst:
                nowa_literatura_tekst = "Nie znaleziono odpowiednich badań z ostatnich 2 lat."

        with st.spinner('Krok 4/4: Pisanie ostatecznego raportu. Haiku analizuje dane...'):
            # ZMODYFIKOWANY PROMPT GŁÓWNY
            prompt_glowny = f"""
            Jesteś profesorem i analitykiem. Oto tekst dostarczonych mi badań:
            {tekst_z_pdfow}

            Oto abstrakty najnowszych badań z bazy Arxiv:
            {nowa_literatura_tekst}

            Napisz profesjonalny raport w języku polskim, zawierający:
            1. **Obszerny opis:** Streszczenie dostarczonych plików PDF i znalezienie tego, co je łączy.
            2. **Wkład badawczy:** Dokładne i wyraźne określenie, co nowatorskiego wnoszą wgrane prace (PDF) do obecnego stanu wiedzy w tej dziedzinie.
            3. **Kontekst najnowszych badań:** Jak wgrane PDFy mają się do najnowszej literatury.
            4. **Future Directions:** Kierunki rozwoju na przyszłość.

            Format: użyj Markdown, pogrubień i wypunktowań. Raport ma być czytelny i profesjonalny.
            """
            
            # Główne zapytanie do Claude 3 Haiku
            response_raport = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt_glowny}]
            )
            raport = response_raport.content[0].text

        # Wyświetlenie wyniku
        st.success("✅ Analiza zakończona sukcesem!")
        st.markdown("---")
        st.markdown(raport)

    except Exception as e:
        st.error(f"Wystąpił błąd podczas przetwarzania: {e}")
