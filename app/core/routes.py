from flask import render_template

from . import core_bp
from ..data.demo import component_examples, navigation_items


@core_bp.get("/")
def index():
    return render_template(
        "foundation/index.html",
        page_title="Fundação visual",
        page_description=(
            "Componentes e estados compartilhados que sustentam as próximas "
            "etapas do sistema."
        ),
        navigation_items=navigation_items,
        examples=component_examples,
        active_navigation="inicio",
    )


@core_bp.get("/componentes")
def components():
    return render_template(
        "foundation/components.html",
        page_title="Referência de componentes",
        page_description=(
            "Variações visuais, mensagens e controles reutilizáveis da interface."
        ),
        navigation_items=navigation_items,
        examples=component_examples,
        active_navigation="componentes",
    )

