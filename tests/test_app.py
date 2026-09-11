from app import create_app
from app.config import TestConfig


def test_foundation_pages_render():
    client = create_app(TestConfig).test_client()
    index_response = client.get("/")
    components_response = client.get("/componentes")
    assert index_response.status_code == 200
    assert "Fundação visual" in index_response.get_data(as_text=True)
    assert components_response.status_code == 200
    assert "Referência de componentes" in components_response.get_data(as_text=True)


def test_unknown_page_uses_custom_error():
    client = create_app(TestConfig).test_client()
    response = client.get("/pagina-inexistente")
    assert response.status_code == 404
    assert "Página não encontrada" in response.get_data(as_text=True)

