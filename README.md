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
├── requirements.txt         Dependencias de Python (versiones fijadas)
├── Dockerfile               Imagen de la API
├── .dockerignore            Ficheros excluidos del contexto de build
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

## Docker

La aplicación está contenerizada con el `Dockerfile` de la raíz del repositorio:

- Imagen base `python:3.12-slim`.
- Instala las dependencias de `requirements.txt` (versiones fijadas) con `pip install --no-cache-dir`.
- Copia el código de `src/` y lo asigna a un usuario sin privilegios (`appuser`).
- Arranca la API con `uvicorn` en el puerto 8000.
- `.dockerignore` excluye `.git`, `__pycache__`, entornos virtuales, tests, etc.

### 1. Construir la imagen

```bash
docker build -t tienda-online-api:1.0.0 -t tienda-online-api:latest .
```

### 2. Ejecutar el contenedor

```bash
# En primer plano (Ctrl+C para parar)
docker run --rm -p 8000:8000 tienda-online-api:1.0.0

# En segundo plano, con nombre
docker run -d --name tienda -p 8000:8000 tienda-online-api:1.0.0
docker logs -f tienda
docker stop tienda && docker rm tienda

# Cambiando el puerto interno con la variable de entorno PORT
docker run --rm -e PORT=9000 -p 9000:9000 tienda-online-api:1.0.0
```

### 3. Variables de entorno

| Variable | Valor por defecto | Descripción |
| --- | --- | --- |
| `PORT` | `8000` | Puerto en el que escucha uvicorn dentro del contenedor |

La aplicación no usa secretos ni claves; los datos se guardan en memoria y se pierden al parar el contenedor.

### 4. Probar que funciona

Con el contenedor en marcha:

| Prueba | Resultado esperado |
| --- | --- |
| Abrir http://localhost:8000 | Frontend web de la tienda |
| Abrir http://localhost:8000/docs | Swagger con todos los endpoints |
| `curl http://localhost:8000/productos` | JSON con 5 productos de ejemplo (Portátil Pro, Smartphone X, Sudadera, Vaquero, Cuaderno) |
| `curl http://localhost:8000/usuarios` | JSON con 3 usuarios de ejemplo (alejandro, sofia, marta) |
| `python src/cliente/cliente.py` | Recorre todos los endpoints e imprime p. ej. `POST /usuarios -> 201`, `GET /productos -> 200` |

En los logs del contenedor (`docker logs tienda`) debe aparecer:

```text
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     172.17.0.1:43038 - "GET /productos HTTP/1.1" 200 OK
```

### 5. Publicar la imagen en Docker Hub (push)

```bash
docker login
docker tag tienda-online-api:1.0.0 DOCKERHUB_USER/tienda-online-api:1.0.0
docker tag tienda-online-api:1.0.0 DOCKERHUB_USER/tienda-online-api:latest
docker push DOCKERHUB_USER/tienda-online-api:1.0.0
docker push DOCKERHUB_USER/tienda-online-api:latest
```

### 6. Descargar y ejecutar la imagen publicada (pull)

```bash
docker pull DOCKERHUB_USER/tienda-online-api:1.0.0
docker run --rm -p 8000:8000 DOCKERHUB_USER/tienda-online-api:1.0.0
```

Flujo seguido: **build → run → test → push**.

## Flujo de trabajo con Git

- `main`: rama principal, solo recibe cambios mediante Pull Request.
- `feature/<nombre>`: una rama por funcionalidad (p. ej. `feature/docker`).
