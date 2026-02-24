import streamlit as st
import google.generativeai as genai
from pypdf import PdfReader
import arxiv
from datetime import datetime
import time # Dodajemy bibliotekę do odmierzania czasu

# --- Konfiguracja wyglądu strony ---
st.set_page_config(page_title="AI Asystent Badacza", page_icon="🧠", layout="wide")
st.title("🧠 AI Asystent Badacza: Analiza PDF i Future Directions")
st.write("Wgraj swoje pliki PDF, a sztuczna inteligencja przeanalizuje je, znajdzie najnowszą literaturę z ostatnich 2 lat i wygeneruje kompleksowy raport.")
st.info("💡 **Wskazówka:** Ponieważ korzystamy z darmowej wersji AI, wgrywaj na początek krótsze pliki (np. 1-2 badania do 15 stron), aby nie przekroczyć limitów.")

# --- Pasek boczny: Konfiguracja ---
with st.sidebar:
    st.header("⚙️ Ustawienia")
    klucz_api = st.text_input("Wklej swój klucz API Gemini:", type="password")
    st.markdown("[Jak zdobyć darmowy klucz API?](https://aistudio.google.com/)")

# --- Główne okno: Wgrywanie plików ---
wgrane_pliki = st.file_uploader("Wybierz pliki PDF", type="pdf", accept_multiple_files=True)

# --- Przycisk uruchamiający analizę ---
if st.button("🚀 Rozpocznij analizę i stwórz raport", type="primary"):
    
    if not klucz_api:
        st.error("Proszę, podaj najpierw klucz API Gemini w panelu bocznym!")
        st.stop()
        
    if not wgrane_pliki:
        st.warning("Proszę wgrać przynajmniej jeden plik PDF.")
        st.stop()

    try:
        # Konfiguracja API - używamy najnowszego modelu 2.0
        genai.configure(api_key=klucz_api)
        model = genai.GenerativeModel('gemini-2.0-flash')
        
        with st.spinner('Krok 1/4: Czytanie plików PDF (to może chwilę potrwać)...'):
            tekst_z_pdfow = ""
            for plik in wgrane_pliki:
                czytnik = PdfReader(plik)
                for strona in czytnik.pages:
                    tekst_z_pdfow += strona.extract_text() + "\n"
        
        with st.spinner('Krok 2/4: Generowanie zapytań wyszukiwania...'):
            prompt_slowa_kluczowe = f"""
            Na podstawie poniższego tekstu, podaj JEDNO zapytanie po angielsku (max 3-4 słowa), 
            aby znaleźć podobne badania na platformie Arxiv. Podaj TYLKO zapytanie.
            Tekst: {tekst_z_pdfow[:4000]}
            """
            # Pierwsze zapytanie do AI
            zapytanie = model.generate_content(prompt_slowa_kluczowe).text.strip()
            st.info(f"🔍 Szukam nowej literatury dla hasła: **{zapytanie}**")

        with st.spinner('Krok 3/4: Pobieranie najnowszych badań z bazy Arxiv...'):
            klient_arxiv = arxiv.Client()
            wyszukiwanie = arxiv.Search(query=zapytanie, max_results=5, sort_by=arxiv.SortCriterion.SubmittedDate)
            
            nowa_literatura_tekst = ""
            aktualny_rok = datetime.now().year
            for wynik in klient_arxiv.results(wyszukiwanie):
                if wynik.published.year >= (aktualny_rok - 2):
                    nowa_literatura_tekst += f"- Tytuł: {wynik.title} ({wynik.published.year})\n  Podsumowanie: {wynik.summary}\n\n"
                    
            if not nowa_literatura_tekst:
                nowa_literatura_tekst = "Nie znaleziono odpowiednich badań z ostatnich 2 lat. Pomiń ten krok w raporcie."

        # MAGIczna PAUZA ratująca przed błędem 429
        with st.spinner('Krok 3.5/4: Chłodzenie silników AI... Czekam 45 sekund na odświeżenie darmowych limitów (nie wyłączaj strony) ☕'):
            time.sleep(45)

        with st.spinner('Krok 4/4: Pisanie ostatecznego raportu. AI łączy kropki...'):
            prompt_glowny = f"""
            Jesteś wybitnym profesorem i analitykiem. Oto pełen tekst dostarczonych mi badań (PDF):
            {tekst_z_pdfow}

            Oto abstrakty badań z ostatnich 2 lat (z bazy Arxiv):
            {nowa_literatura_tekst}

            Napisz profesjonalny raport w języku polskim, zawierający:
            1. **Obszerny opis:** Streszczenie dostarczonych plików PDF i znalezienie tego, co je łączy.
            2. **Kontekst najnowszych badań:** Jak wgrane PDFy mają się do literatury pobranej z Arxiv.
            3. **Future Directions:** Kierunki rozwoju na przyszłość opierając się na obu źródłach.

            Format: użyj Markdown, pogrubień i wypunktowań.
            """
            # Drugie (największe) zapytanie do AI
            raport = model.generate_content(prompt_glowny)

        # Wyświetlenie wyniku
        st.success("✅ Analiza zakończona sukcesem!")
        st.markdown("---")
        st.markdown(raport.text)

    except Exception as e:
        st.error(f"Wystąpił błąd podczas przetwarzania: {e}")
