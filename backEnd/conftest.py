def pytest_addoption(parser):
    parser.addoption("--postman", action="store_true", help="Ejecuta la colección Postman con Newman")
    parser.addoption("--api-evidence", default=None, help="Ruta del resumen JSON de Postman sin cookies ni claves")
