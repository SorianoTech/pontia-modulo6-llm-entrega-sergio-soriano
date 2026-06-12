from __future__ import annotations

from uuid import uuid4

import requests
import streamlit as st

from app.core.config import get_settings
from app.services.content import get_info_cards
from app.ui.streamlit_helpers import build_api_url, format_sources


def _inject_theme_styles() -> None:
    """Apply a Tenerife-inspired palette and lightweight component styling."""
    st.markdown(
        """
        <style>
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(0, 123, 167, 0.18), transparent 28%),
                    radial-gradient(circle at top right, rgba(255, 122, 24, 0.20), transparent 25%),
                    linear-gradient(180deg, #f7f3eb 0%, #fcfbf7 100%);
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #0d3b66 0%, #145374 100%);
            }
            [data-testid="stSidebar"] * {
                color: #f8fafc;
            }
            .hero-card {
                padding: 1.2rem 1rem;
                border-radius: 1rem;
                min-height: 12rem;
                background: linear-gradient(
                    180deg,
                    rgba(255, 255, 255, 0.95),
                    rgba(255, 244, 230, 0.92)
                );
                border: 1px solid rgba(255, 122, 24, 0.18);
                box-shadow: 0 12px 28px rgba(13, 59, 102, 0.10);
            }
            .hero-card h3 {
                color: #0d3b66;
                margin-bottom: 0.5rem;
            }
            .hero-card p {
                color: #334155;
                margin-bottom: 0;
            }
            .hero-banner {
                padding: 1.4rem 1.5rem;
                border-radius: 1.25rem;
                background: linear-gradient(135deg, #0d3b66 0%, #117a7e 45%, #34d399 100%);
                color: white;
                box-shadow: 0 18px 36px rgba(13, 59, 102, 0.18);
                margin-bottom: 1rem;
            }
            .hero-banner h1 {
                color: white;
                margin-bottom: 0.35rem;
            }
            .hero-banner p {
                margin-bottom: 0;
                color: rgba(255, 255, 255, 0.92);
                font-size: 1.02rem;
            }
            [data-testid="stChatMessage"] {
                border-radius: 1rem;
                border: 1px solid rgba(13, 59, 102, 0.08);
                box-shadow: 0 10px 24px rgba(15, 23, 42, 0.05);
                background: rgba(255, 255, 255, 0.92);
            }
            [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"],
            [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] li,
            [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] span,
            [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] div,
            [data-testid="stChatMessage"] [data-testid="stCaptionContainer"] {
                color: #1f2937 !important;
            }
            [data-testid="stChatMessage"] small,
            [data-testid="stChatMessage"] code {
                color: #334155 !important;
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
                background: linear-gradient(
                    180deg,
                    rgba(232, 242, 250, 0.95),
                    rgba(220, 252, 231, 0.9)
                );
            }
            [data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) {
                background: linear-gradient(
                    180deg,
                    rgba(255, 255, 255, 0.96),
                    rgba(255, 244, 230, 0.92)
                );
            }
            [data-testid="stChatInput"] textarea {
                border-radius: 0.9rem;
                color: #1f2937;
            }
            .stButton > button {
                background: linear-gradient(135deg, #ff7a18 0%, #f4a261 100%);
                color: white;
                border: none;
                border-radius: 999px;
                font-weight: 600;
            }
            @media (max-width: 768px) {
                [data-testid="stChatMessage"] {
                    background: rgba(255, 255, 255, 0.96);
                }
                [data-testid="stChatInput"] textarea {
                    background: white;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _api_base_url() -> str:
    """Return the backend base URL used by the Streamlit client."""
    settings = get_settings()
    return settings.model_dump().get("streamlit_api_url", "http://127.0.0.1:8000")


def _chat_request(message: str, session_id: str) -> dict:
    """Send a chat turn to the backend API and normalize error payloads."""
    response = requests.post(
        build_api_url(_api_base_url(), "/api/v1/chat"),
        json={
            "message": message,
            "session_id": session_id,
        },
        timeout=120,
    )
    if response.headers.get("content-type", "").startswith("application/json"):
        payload = response.json()
    else:
        payload = {"detail": response.text or "No se pudo completar la consulta."}

    if not response.ok:
        raise RuntimeError(payload.get("detail", "No se pudo completar la consulta."))

    return payload


def _render_sidebar() -> None:
    """Render navigation hints and reset controls in the sidebar."""
    st.sidebar.title("Tenerife RAG")
    st.sidebar.caption("Asistente turistico con RAG, clima y citas documentales.")
    st.sidebar.write("Sugerencias:")
    st.sidebar.markdown(
        "- ¿Qué zonas recomiendas para una primera visita?\n"
        "- ¿Qué playas puedo visitar?\n"
        "- ¿Qué tiempo hará mañana?\n"
        "- ¿Dónde comer cerca de La Laguna?"
    )

    if st.sidebar.button("Nueva conversación"):
        st.session_state.session_id = str(uuid4())
        st.session_state.messages = []
        st.rerun()


def _render_intro() -> None:
    """Render the hero content and informational cards for the landing view."""
    st.markdown(
        """
        <section class="hero-banner">
            <h1>Descubre Tenerife con un chat conversacional</h1>
            <p>
                Consulta lugares para visitar, rutas, playas, gastronomía y clima.
                Las respuestas documentales incluyen fuentes del PDF base.
            </p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    columns = st.columns(3)
    for column, card in zip(columns, get_info_cards(), strict=True):
        column.markdown(
            (
                f"<div class='hero-card'><h3>{card.title}</h3>"
                f"<p>{card.description}</p></div>"
            ),
            unsafe_allow_html=True,
        )


def _render_history() -> None:
    """Render the persisted conversation history stored in the Streamlit session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                st.caption(f"Fuentes: {format_sources(message['sources'])}")
            if message.get("weather"):
                weather = message["weather"]
                if weather.get("ok") and weather.get("data"):
                    data = weather["data"]
                    st.caption(
                        "Clima: "
                        f"{data['fecha']} · {data['ubicacion']} · "
                        f"{data['temperatura_min_c']}°C/{data['temperatura_max_c']}°C · "
                        f"{data['condicion']}"
                    )


def main() -> None:
    """Run the Streamlit application entrypoint."""
    settings = get_settings()
    st.set_page_config(
        page_title=settings.app_name,
        page_icon="🌴",
        layout="wide",
    )

    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = []

    _inject_theme_styles()
    _render_sidebar()
    _render_intro()
    _render_history()

    prompt = st.chat_input("Haz una pregunta sobre Tenerife")
    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    try:
        payload = _chat_request(prompt, st.session_state.session_id)
        st.session_state.session_id = payload["session_id"]
        assistant_message = {
            "role": "assistant",
            "content": payload["answer"],
            "sources": payload.get("sources", []),
            "weather": payload.get("weather"),
        }
        st.session_state.messages.append(assistant_message)

        with st.chat_message("assistant"):
            st.markdown(payload["answer"])
            if payload.get("sources"):
                st.caption(f"Fuentes: {format_sources(payload['sources'])}")
            weather = payload.get("weather")
            if weather and weather.get("ok") and weather.get("data"):
                data = weather["data"]
                st.caption(
                    "Clima: "
                    f"{data['fecha']} · {data['ubicacion']} · "
                    f"{data['temperatura_min_c']}°C/{data['temperatura_max_c']}°C · "
                    f"{data['condicion']}"
                )
    except Exception as exc:  # noqa: BLE001
        error_text = str(exc)
        st.session_state.messages.append({"role": "assistant", "content": error_text})
        with st.chat_message("assistant"):
            st.error(error_text)


if __name__ == "__main__":
    main()
