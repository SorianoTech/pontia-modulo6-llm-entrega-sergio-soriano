from __future__ import annotations

from uuid import uuid4

import requests
import streamlit as st

from app.core.config import get_settings
from app.services.content import get_info_cards
from app.ui.streamlit_helpers import build_api_url, format_sources


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
    st.title("Descubre Tenerife con un chat conversacional")
    st.write(
        "Consulta lugares para visitar, rutas, playas, gastronomía y clima. "
        "Las respuestas documentales incluyen fuentes del PDF base."
    )

    columns = st.columns(3)
    for column, card in zip(columns, get_info_cards(), strict=True):
        column.markdown(f"### {card.title}")
        column.write(card.description)


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
