# nicolasmorazo-devops-practica

**Autor:** Nicolás Morazo
**Asignatura:** Arquitectura del Software – Prácticas 3.1 y 3.2

## Descripción

Repositorio de las prácticas de DevOps. Contiene la aplicación Python desarrollada en la
Práctica 2: una **API REST de una tienda online** construida con **FastAPI**. Permite
gestionar usuarios (clientes y administradores), un catálogo de productos (genéricos,
electrónicos y de ropa) y pedidos con control de stock. Incluye además un cliente de
consola hecho con `requests` y un frontend web (HTML + JavaScript) que consume la API.

## Estructura

```text
.
├── src/
│   ├── Tienda_online/       API REST (FastAPI): main.py, schemas.py, models/, services/
│   ├── cliente/cliente.py   Cliente de consola con requests
│   └── frontend/            Frontend web (index.html, app.js, styles.css)
├── requirements.txt         Dependencias de Python
└── README.md
```

## Ejecución local (sin Docker)

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cd src/Tienda_online
uvicorn main:app --reload
```

- Frontend: http://127.0.0.1:8000
- Documentación Swagger: http://127.0.0.1:8000/docs

## Flujo de trabajo con Git

- `main`: rama principal, solo recibe cambios mediante Pull Request.
- `feature/<nombre>`: una rama por funcionalidad (p. ej. `feature/docker`).
