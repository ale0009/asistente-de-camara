# -*- coding: utf-8 -*-
from unittest.mock import Mock, patch
from core.web_reader import WebReader

@patch('core.web_reader.requests')
def test_web_reader_clean_html(mock_requests):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.encoding = 'utf-8'
    mock_response.text = """
    <html>
        <head><style>body { color: red; }</style></head>
        <body>
            <header>Logo</header>
            <nav><a href="/">Inicio</a></nav>
            <main>
                <h1>Avance en fusión</h1>
                <p>La fusión nuclear es la energía del futuro.</p>
            </main>
            <script>console.log("test");</script>
            <footer>Pie de página</footer>
        </body>
    </html>
    """
    mock_requests.get.return_value = mock_response

    reader = WebReader()
    result = reader.read_url("https://example.com/fusion")

    assert "Avance en fusión" in result
    assert "La fusión nuclear es la energía del futuro" in result
    # Deberían haberse eliminado las cabeceras, menús y estilos
    assert "Logo" not in result
    assert "Inicio" not in result
    assert "Pie de página" not in result
    assert "console.log" not in result
