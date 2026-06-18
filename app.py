from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from src.cleaner import clean_frequency_dictionary, prepare_hutsul_dictionary
from src.components import (
    load_css,
    render_author_cards,
    render_empty_state,
    render_export_card,
    render_hero,
    render_info_cards,
    render_metric_card,
    render_processing_summary,
    render_html,
    render_section_title,
    render_word_cards,
)
from src.exporter import export_results_to_excel
from src.loader import load_frequency_dictionary, load_hutsul_dictionary, table_info
from src.matcher import build_author_result, build_combined_result
from src.statistics import calculate_statistics


APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
OUTPUT_DIR = APP_DIR / "output"
ASSETS_DIR = APP_DIR / "assets"

SECTIONS = ["Вхідні дані", "Очищення", "Словник", "Статистика", "Контексти", "Експорт"]

DICTIONARY_DISPLAY_COLUMNS = {
    "dialectism": "Діалектизм",
    "frequency": "Частота",
    "author": "Автор",
    "dialectism_type": "Тип діалектизму",
    "meaning": "Тлумачення",
    "dictionary_source": "Джерело",
}


st.set_page_config(
    page_title="Частотний словник гуцулізмів",
    page_icon=str(ASSETS_DIR / "favicon.svg"),
    layout="wide",
    initial_sidebar_state="expanded",
)
load_css(ASSETS_DIR / "styles.css")

st.session_state.setdefault("processed", False)
st.session_state.setdefault("section", "Словник")


def go_to(section: str) -> None:
    st.session_state.processed = True
    st.session_state.section = section


def load_default_or_uploaded(uploaded_file, default_path: Path, loader_func):
    if uploaded_file is not None:
        return loader_func(uploaded_file, uploaded_file.name)
    return loader_func(default_path, default_path.name)


def fragment_caption(total: int, shown: int) -> None:
    if total > shown:
        st.caption(f"Показано фрагмент таблиці: {shown} із {total} рядків.")
    else:
        st.caption(f"Показано всі рядки: {total}.")


def raw_input_preview(title: str, df: pd.DataFrame, missing: list[str]) -> None:
    info = table_info(df)
    st.markdown(f"#### {title}")
    cols = st.columns(3)
    with cols[0]:
        render_metric_card("Рядків", info["rows"], "у вхідному файлі")
    with cols[1]:
        render_metric_card("Колонок", len(info["columns"]), "структура таблиці")
    with cols[2]:
        render_metric_card("Порожніх значень", info["empty_values"], "для перевірки")
    if missing:
        st.warning("Відсутні колонки додано як порожні: " + ", ".join(missing))
    st.caption("Колонки: " + ", ".join(info["columns"]))
    st.dataframe(info["preview"], width="stretch")
    fragment_caption(len(df), len(info["preview"]))


def cleaned_input_preview(title: str, cleaned: pd.DataFrame) -> None:
    st.markdown(f"#### {title}")
    columns = [c for c in ["original_lexeme", "class", "frequency", "semantics"] if c in cleaned.columns]
    view = cleaned[columns].rename(
        columns={
            "original_lexeme": "Лексема",
            "class": "Частина мови",
            "frequency": "Частота",
            "semantics": "Семантика",
        }
    )
    preview = view.head(50)
    st.dataframe(preview, width="stretch")
    fragment_caption(len(view), len(preview))


def top_chart(df: pd.DataFrame, title: str) -> None:
    st.markdown(f"#### {title}")
    if df.empty:
        st.info("Немає даних для графіка.")
        return
    top = df.sort_values("frequency", ascending=False).head(20)
    chart_df = top[["dialectism", "frequency"]].set_index("dialectism")
    st.bar_chart(chart_df, color="#7A3B2E")


def distribution_chart(df: pd.DataFrame, label_col: str, value_col: str, title: str) -> None:
    st.markdown(f"#### {title}")
    if df.empty or label_col not in df.columns:
        st.info("Немає даних для графіка.")
        return
    chart_df = df[[label_col, value_col]].copy()
    chart_df[label_col] = chart_df[label_col].replace("", "не визначено")
    chart_df = chart_df.groupby(label_col)[value_col].sum().sort_values(ascending=False)
    st.bar_chart(chart_df, color="#3F5A4A")


def filter_dictionary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    render_section_title("Пошук і фільтри")
    cols = st.columns([1.4, 1, 1, 1, 1])
    query = cols[0].text_input("Пошук за словом", placeholder="Наприклад: ґазда")
    authors = cols[1].multiselect("Автор", sorted(df["author"].dropna().unique()))
    types = cols[2].multiselect("Тип", sorted(x for x in df["dialectism_type"].dropna().unique() if str(x).strip()))
    match_types = cols[3].multiselect("Збіг", sorted(df["match_type"].dropna().unique()))
    max_frequency = int(df["frequency"].max()) if not df.empty else 0
    min_frequency = cols[4].slider("Мін. частота", 0, max_frequency, 0)

    result = df.copy()
    if query:
        q = query.lower().strip()
        result = result[
            result["dialectism"].astype(str).str.lower().str.contains(q, na=False)
            | result["original_lexeme"].astype(str).str.lower().str.contains(q, na=False)
        ]
    if authors:
        result = result[result["author"].isin(authors)]
    if types:
        result = result[result["dialectism_type"].isin(types)]
    if match_types:
        result = result[result["match_type"].isin(match_types)]
    result = result[result["frequency"] >= min_frequency]
    return result


def dictionary_table(df: pd.DataFrame) -> None:
    columns = [c for c in DICTIONARY_DISPLAY_COLUMNS if c in df.columns]
    view = df[columns].rename(columns=DICTIONARY_DISPLAY_COLUMNS)
    st.dataframe(view, width="stretch")
    st.caption("Колонки: діалектизм, частота, автор, тип, тлумачення, джерело.")


def render_file_upload_area():
    with st.sidebar:
        st.header("Вхідні файли")
        st.caption("Завантажте власні файли або скористайтеся прикладами з папки data.")
        matios_file = st.file_uploader("Частотний словник М. Матіос", type=["txt", "csv"], key="matios")
        prokhasko_file = st.file_uploader("Частотний словник Т. Прохаська", type=["txt", "csv"], key="prokhasko")
        hutsul_file = st.file_uploader("Реєстр гуцулізмів", type=["csv", "xlsx"], key="hutsul")
        use_defaults = st.checkbox("Використати файли з папки data", value=True)
        files_ready = matios_file is not None and prokhasko_file is not None and hutsul_file is not None
        can_run = use_defaults or files_ready
        if use_defaults:
            status = "Буде використано приклади з папки data."
            status_class = "ready"
        elif files_ready:
            status = "Усі три файли завантажено. Можна запускати обробку."
            status_class = "ready"
        else:
            status = "Завантажте всі три файли або увімкніть приклади з папки data."
            status_class = "warning"
        render_html(f'<div class="sidebar-status {status_class}">{status}</div>')
        if not can_run:
            render_html(
                '<div class="sidebar-hint">Кнопка стане активною, коли буде вибрано джерело даних.</div>'
            )
        run_processing = st.button(
            "Опрацювати дані", type="primary", disabled=not can_run, use_container_width=True
        )
    return matios_file, prokhasko_file, hutsul_file, use_defaults, run_processing


render_hero()

render_html('<div class="hero-actions-live"></div>')
hero_cols = st.columns([1, 1, 1, 2])
with hero_cols[0]:
    if st.button("Завантажити файли", key="hero_upload", use_container_width=True):
        st.toast("Панель завантаження файлів — ліворуч. Там можна додати власні файли або взяти приклади з папки data.")
with hero_cols[1]:
    if st.button("Переглянути результати", key="hero_results", type="primary", use_container_width=True):
        go_to("Словник")
        st.rerun()
with hero_cols[2]:
    if st.button("Статистика", key="hero_stats", use_container_width=True):
        go_to("Статистика")
        st.rerun()

render_section_title("Про проєкт")
render_info_cards()
render_section_title("Авторський матеріал")
render_author_cards()

matios_file, prokhasko_file, hutsul_file, use_defaults, run_processing = render_file_upload_area()
if run_processing:
    go_to("Словник")

if not st.session_state.processed:
    render_section_title("Робоча область")
    render_empty_state(
        "Завантажте файли на панелі ліворуч або залиште приклади з папки data, після чого натисніть "
        "«Опрацювати дані». Можна також скористатися кнопками вгорі. Після обробки тут з’являться "
        "словникові картки, статистика та експортні файли."
    )
    st.stop()

try:
    if not use_defaults and (matios_file is None or prokhasko_file is None or hutsul_file is None):
        st.error("Завантажте всі три файли або увімкніть використання прикладів із папки data.")
        st.stop()

    matios_df, matios_missing = load_default_or_uploaded(
        matios_file, DATA_DIR / "matios_frequency.txt", load_frequency_dictionary
    )
    prokhasko_df, prokhasko_missing = load_default_or_uploaded(
        prokhasko_file, DATA_DIR / "prokhasko_frequency.txt", load_frequency_dictionary
    )
    hutsul_df, hutsul_missing = load_default_or_uploaded(
        hutsul_file, DATA_DIR / "hutsul_dictionary.csv", load_hutsul_dictionary
    )
except Exception as exc:
    st.error(f"Не вдалося завантажити файли: {exc}")
    st.stop()

matios_clean, matios_removed = clean_frequency_dictionary(matios_df)
prokhasko_clean, prokhasko_removed = clean_frequency_dictionary(prokhasko_df)
hutsul_prepared, hutsul_duplicates = prepare_hutsul_dictionary(hutsul_df)

matios_result, matios_manual = build_author_result("Matios", matios_clean, hutsul_prepared)
prokhasko_result, prokhasko_manual = build_author_result("Prokhasko", prokhasko_clean, hutsul_prepared)
manual_review = pd.concat([matios_manual, prokhasko_manual], ignore_index=True)
combined_result = build_combined_result(matios_result, prokhasko_result)
statistics = calculate_statistics(
    matios_result, prokhasko_result, matios_clean, prokhasko_clean, combined_result
)
all_results = pd.concat([matios_result, prokhasko_result], ignore_index=True)

matios_unique = int(matios_clean["normalized_lexeme"].nunique())
prokhasko_unique = int(prokhasko_clean["normalized_lexeme"].nunique())

shared_status = statistics["shared_and_unique"]["status"].value_counts() if "shared_and_unique" in statistics else pd.Series(dtype=int)
shared_count = int(shared_status.get("shared", 0))
matios_only = int(shared_status.get("only_matios", 0))
prokhasko_only = int(shared_status.get("only_prokhasko", 0))

render_section_title("Підсумок обробки")
render_processing_summary(
    int(matios_clean["frequency"].sum()),
    matios_unique,
    len(matios_result),
    int(matios_result["frequency"].sum()) if not matios_result.empty else 0,
    int(prokhasko_clean["frequency"].sum()),
    prokhasko_unique,
    len(prokhasko_result),
    int(prokhasko_result["frequency"].sum()) if not prokhasko_result.empty else 0,
    shared_count,
    matios_only,
    prokhasko_only,
    len(combined_result),
)
summary_cols = st.columns(2)
with summary_cols[0]:
    render_metric_card("Ручна перевірка", len(manual_review), "потенційні похідні форми")
with summary_cols[1]:
    render_metric_card("Спільний реєстр", len(combined_result), "для порівняння авторів")

render_section_title("Авторський матеріал після обробки")
render_author_cards(
    int(matios_clean["frequency"].sum()),
    len(matios_result),
    int(prokhasko_clean["frequency"].sum()),
    len(prokhasko_result),
    matios_unique,
    prokhasko_unique,
)

render_section_title("Розділи аналізу")
st.radio("Розділ аналізу", SECTIONS, horizontal=True, key="section", label_visibility="collapsed")
active = st.session_state.section

if active == "Вхідні дані":
    render_section_title("Перегляд вхідних даних")
    raw_tab, clean_tab = st.tabs(["До очищення", "Після очищення"])
    with raw_tab:
        st.info(
            "Нижче подано фрагмент сирого частотного словника до очищення. "
            "Службові токени (пунктуація, числа, технічні позначки) вилучаються на наступному етапі."
        )
        raw_input_preview("Частотний словник Марії Матіос", matios_df, matios_missing)
        raw_input_preview("Частотний словник Тараса Прохаська", prokhasko_df, prokhasko_missing)
        raw_input_preview("Реєстр гуцульських діалектизмів", hutsul_df, hutsul_missing)
    with clean_tab:
        st.success(
            "Дані після очищення: вилучено пунктуацію, числа, порожні рядки й технічні токени. "
            "Цей перегляд зручний для перевірки підготовлених таблиць."
        )
        cleaned_input_preview("Частотний словник Марії Матіос — після очищення", matios_clean)
        cleaned_input_preview("Частотний словник Тараса Прохаська — після очищення", prokhasko_clean)

elif active == "Очищення":
    render_section_title("Очищення даних")
    cols = st.columns(4)
    with cols[0]:
        render_metric_card("Матіос: до", len(matios_df), "рядків")
    with cols[1]:
        render_metric_card("Матіос: після", len(matios_clean), "очищених лексем")
    with cols[2]:
        render_metric_card("Прохасько: до", len(prokhasko_df), "рядків")
    with cols[3]:
        render_metric_card("Прохасько: після", len(prokhasko_clean), "очищених лексем")

    cols = st.columns(2)
    with cols[0]:
        st.markdown("#### Приклади вилучених службових токенів: Матіос")
        st.dataframe(matios_removed[["original_lexeme", "frequency"]].head(20), width="stretch")
        fragment_caption(len(matios_removed), min(20, len(matios_removed)))
    with cols[1]:
        st.markdown("#### Приклади вилучених службових токенів: Прохасько")
        st.dataframe(prokhasko_removed[["original_lexeme", "frequency"]].head(20), width="stretch")
        fragment_caption(len(prokhasko_removed), min(20, len(prokhasko_removed)))

    if not hutsul_duplicates.empty:
        st.warning("У реєстрі гуцулізмів знайдено дублікати. Для обробки залишено перше входження.")
        st.dataframe(hutsul_duplicates, width="stretch")

elif active == "Словник":
    render_section_title("Словник гуцулізмів")
    filtered_results = filter_dictionary(all_results)
    view_mode = st.radio("Режим перегляду", ["Картки", "Таблиця"], horizontal=True)
    if view_mode == "Картки":
        render_word_cards(filtered_results)
    else:
        dictionary_table(filtered_results)
    fragment_caption(len(all_results), len(filtered_results))

    render_section_title("Потребує ручної перевірки")
    st.dataframe(manual_review, width="stretch")
    fragment_caption(len(manual_review), len(manual_review))

elif active == "Статистика":
    render_section_title("Аналітична статистика")
    st.dataframe(statistics["general_stats"], width="stretch")
    cols = st.columns(2)
    with cols[0]:
        top_chart(matios_result, "Топ-20 гуцулізмів у текстах Марії Матіос")
    with cols[1]:
        top_chart(prokhasko_result, "Топ-20 гуцулізмів у текстах Тараса Прохаська")

    st.markdown("#### Порівняння кількості знайдених гуцулізмів")
    compare_df = statistics["general_stats"].set_index("author")[["detected_hutsulisms_count"]]
    st.bar_chart(compare_df, color="#A88A5B")

    cols = st.columns(2)
    with cols[0]:
        distribution_chart(statistics["by_part_of_speech"], "class", "total_frequency", "Розподіл за частинами мови")
    with cols[1]:
        distribution_chart(statistics["by_dialectism_type"], "dialectism_type", "total_frequency", "Розподіл за типами діалектизмів")
    distribution_chart(statistics["by_semantics"], "semantics", "total_frequency", "Розподіл за семантичними групами")

    st.markdown("#### Спільні й унікальні гуцулізми")
    st.dataframe(statistics["shared_and_unique"], width="stretch")

elif active == "Контексти":
    render_section_title("Контексти й приклади вживання")
    render_empty_state(
        "У поточних частотних словниках немає повних текстових контекстів. "
        "Цей блок підготовлено для майбутнього додавання фрагментів тексту з підсвіченим діалектизмом."
    )

elif active == "Експорт":
    render_section_title("Експорт результатів")
    paths = export_results_to_excel(
        matios_result, prokhasko_result, combined_result, manual_review, statistics, OUTPUT_DIR
    )
    st.success("Результати сформовано в папці output.")
    descriptions = {
        "matios": "Окремий електронний частотний словник гуцулізмів у текстах Марії Матіос.",
        "prokhasko": "Окремий електронний частотний словник гуцулізмів у текстах Тараса Прохаська.",
        "combined": "Спільна порівняльна таблиця для двох авторів.",
        "manual": "Кандидати, що потребують ручної перевірки в Excel.",
        "statistics": "Загальна статистика за авторами, частинами мови, типами й семантичними групами.",
        "zip": "Архів усіх сформованих результатів.",
    }
    grid_cols = st.columns(3)
    for idx, (name, path) in enumerate(paths.items()):
        with grid_cols[idx % 3]:
            render_export_card(path, descriptions.get(name, "Файл результатів."), name)
