from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st


def render_html(markup: str) -> None:
    st.html(markup)


def load_css(path: str | Path) -> None:
    css_path = Path(path)
    if css_path.exists():
        render_html(f"<style>{css_path.read_text(encoding='utf-8')}</style>")


def esc(value: object) -> str:
    return html.escape("" if value is None else str(value))


def render_hero() -> None:
    render_html(
        """
        <section class="hero">
          <div class="mountain-line" aria-hidden="true"></div>
          <div class="lexeme-cloud" aria-hidden="true">
            <span>ґазда</span><span>плай</span><span>ліжник</span><span>ватра</span>
            <span>трембіта</span><span>будз</span><span>ґражда</span><span>смерека</span>
            <span>кептар</span><span>афини</span>
          </div>
          <div class="hero-content">
            <div class="hero-kicker">Digital Hutsul Archive</div>
            <h1 class="hero-title">Частотний словник гуцульських діалектизмів</h1>
            <div class="hero-subtitle">
              Автоматизований аналіз художніх текстів Марії Матіос і Тараса Прохаська:
              очищення частотних словників, точне зіставлення з реєстром гуцулізмів,
              порівняльна статистика й Excel-експорт результатів.
            </div>
            <div class="hero-metrics">
              <span>2 авторські корпуси</span>
              <span>64 діалектні одиниці</span>
              <span>точне зіставлення</span>
              <span>Excel-експорт</span>
            </div>
          </div>
        </section>
        <div class="ornament"></div>
        """,
    )


def render_section_title(title: str) -> None:
    render_html(
        f"""
        <div class="section-title">
          <span class="section-mark"></span>
          <h2>{esc(title)}</h2>
        </div>
        """
    )


def render_info_cards() -> None:
    cards = [
        ("Корпус текстів", "текстовий матеріал", "Авторські частотні словники є основою для кількісного аналізу гуцульської лексики."),
        ("Частотні словники", "таблична база", "Застосунок очищає реєстри, нормалізує лексеми й зберігає абсолютні частоти."),
        ("Гуцульські діалектизми", "словниковий реєстр", "Реєстр містить тлумачення, джерело, тип діалектизму й коментар."),
        ("Автоматизоване зіставлення", "алгоритм exact match", "Точні збіги потрапляють до результату, часткові збіги йдуть на ручну перевірку."),
    ]
    html_cards = "".join(
        f"""
        <article class="info-card">
          <div class="card-marker"></div>
          <span class="mini-badge">{esc(badge)}</span>
          <h3>{esc(title)}</h3>
          <p>{esc(text)}</p>
        </article>
        """
        for title, badge, text in cards
    )
    render_html(f'<div class="card-grid">{html_cards}</div>')


def render_metric_card(label: str, value: object, note: str = "") -> None:
    render_html(
        f"""
        <div class="metric-card">
          <div class="metric-label">{esc(label)}</div>
          <div class="metric-value">{esc(value)}</div>
          <div class="metric-note">{esc(note)}</div>
        </div>
        """
    )


def render_author_cards(
    matios_cleaned: int | None = None,
    matios_found: int | None = None,
    prokhasko_cleaned: int | None = None,
    prokhasko_found: int | None = None,
    matios_unique: int | None = None,
    prokhasko_unique: int | None = None,
) -> None:
    def value(cleaned, found, unique=None):
        if cleaned is None:
            return '<span class="author-stat muted">дані з’являться після обробки</span>'
        unique_part = f'<span><strong>{esc(unique)}</strong><small>унікальні лексеми</small></span>' if unique is not None else ""
        return (
            f'<span><strong>{esc(cleaned)}</strong><small>токени після очищення</small></span>'
            f'{unique_part}'
            f'<span><strong>{esc(found)}</strong><small>знайдені гуцулізми</small></span>'
        )

    cards = [
        (
            "Марія Матіос",
            "Художня проза з виразним родинно-побутовим і регіональним мовним шаром.",
            ["Солодка Даруся", "Нація", "Майже ніколи не навпаки"],
            value(matios_cleaned, matios_found, matios_unique),
        ),
        (
            "Тарас Прохасько",
            "Медитативна проза, у якій карпатський простір і предметна лексика мають особливу вагу.",
            ["НепрОсті", "FM Галичина"],
            value(prokhasko_cleaned, prokhasko_found, prokhasko_unique),
        ),
    ]
    html_cards = ""
    for name, desc, corpus, stats in cards:
        badges = "".join(f'<span class="badge green">{esc(item)}</span>' for item in corpus)
        html_cards += f"""
        <article class="author-card">
          <div class="author-initial">{esc(name[0])}</div>
          <h3>{esc(name)}</h3>
          <p>{esc(desc)}</p>
          <div class="badge-row">{badges}</div>
          <div class="author-stats">{stats}</div>
        </article>
        """
    render_html(f'<div class="card-grid">{html_cards}</div>')


def render_processing_summary(
    matios_tokens: int,
    matios_unique: int,
    matios_found: int,
    matios_frequency: int,
    prokhasko_tokens: int,
    prokhasko_unique: int,
    prokhasko_found: int,
    prokhasko_frequency: int,
    shared_count: int,
    matios_only: int,
    prokhasko_only: int,
    combined_count: int,
) -> None:
    items = [
        ("Матіос: токени", matios_tokens, "після очищення"),
        ("Матіос: унікальні", matios_unique, "лексеми"),
        ("Матіос: гуцулізми", matios_found, f"сумарна частота {matios_frequency}"),
        ("Прохасько: токени", prokhasko_tokens, "після очищення"),
        ("Прохасько: унікальні", prokhasko_unique, "лексеми"),
        ("Прохасько: гуцулізми", prokhasko_found, f"сумарна частота {prokhasko_frequency}"),
        ("Спільні одиниці", shared_count, "в обох авторів"),
        ("Лише Матіос", matios_only, f"із {combined_count} у спільному реєстрі"),
        ("Лише Прохасько", prokhasko_only, f"із {combined_count} у спільному реєстрі"),
    ]
    cards = "".join(
        f"""
        <article class="metric-card metric-card-strong">
          <div class="metric-label">{esc(label)}</div>
          <div class="metric-value">{esc(value)}</div>
          <div class="metric-note">{esc(note)}</div>
        </article>
        """
        for label, value, note in items
    )
    render_html(f'<div class="metric-grid">{cards}</div>')


def render_word_cards(df: pd.DataFrame, limit: int = 24) -> None:
    if df.empty:
        render_empty_state("Після зіставлення тут з’являться словникові картки знайдених гуцулізмів.")
        return
    rows = df.sort_values("frequency", ascending=False).head(limit)
    cards = ""
    for _, row in rows.iterrows():
        cards += f"""
        <article class="word-card">
          <div class="word-head">
            <div class="word">{esc(row.get('dialectism', ''))}</div>
            <div class="freq">{esc(row.get('frequency', 0))}</div>
          </div>
          <div class="meaning">{esc(row.get('meaning', '') or 'Тлумачення не подано')}</div>
          <div class="badge-row">
            <span class="badge">{esc(row.get('author', ''))}</span>
            <span class="badge green">{esc(row.get('dialectism_type', '') or 'тип не визначено')}</span>
            <span class="badge gold">{esc(row.get('match_type', ''))}</span>
          </div>
          <div class="meta">
            <span><strong>Автор:</strong> {esc(row.get('author', '') or 'не визначено')}</span>
            <span><strong>Тип діалектизму:</strong> {esc(row.get('dialectism_type', '') or 'не визначено')}</span>
            <span><strong>Частина мови:</strong> {esc(row.get('class', '') or 'не визначено')}</span>
            <span><strong>Семантика:</strong> {esc(row.get('semantics', '') or 'не визначено')}</span>
            <span><strong>Джерело:</strong> {esc(row.get('dictionary_source', '') or 'не подано')}</span>
            <span><strong>Тип збігу:</strong> {esc(row.get('match_type', '') or 'не визначено')}</span>
          </div>
        </article>
        """
    render_html(f'<div class="word-grid">{cards}</div>')


def render_export_card(path: Path, description: str, key: str) -> None:
    render_html(
        f"""
        <article class="export-card">
          <h3>{esc(path.name)}</h3>
          <p>{esc(description)}</p>
        </article>
        """
    )
    mime = (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        if path.suffix == ".xlsx"
        else "application/zip"
    )
    with open(path, "rb") as file:
        st.download_button(
            label=f"Завантажити {path.name}",
            data=file,
            file_name=path.name,
            mime=mime,
            key=f"download_{key}",
        )


def render_empty_state(text: str) -> None:
    render_html(f'<div class="empty-card"><p>{esc(text)}</p></div>')
