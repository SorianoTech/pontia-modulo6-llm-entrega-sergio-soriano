from __future__ import annotations

from app.models.schemas import InfoCard


def get_info_cards() -> list[InfoCard]:
    """Return the static tourism highlights displayed above the chat interface."""
    return [
        InfoCard(
            title="Tenerife norte",
            description=(
                "La Laguna, Santa Cruz y Puerto de la Cruz concentran patrimonio, "
                "paseos y cultura."
            ),
        ),
        InfoCard(
            title="Teide y naturaleza",
            description=(
                "El Parque Nacional del Teide y sus miradores son uno de los grandes "
                "atractivos de la isla."
            ),
        ),
        InfoCard(
            title="Playas y gastronomia",
            description=(
                "La app combina recomendaciones documentales y consulta de clima "
                "para planificar mejor la visita."
            ),
        ),
    ]
