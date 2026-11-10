# Práctica 2 – API REST de la Tienda Online (FastAPI)

Evolución de la Práctica 1: la lógica de `TiendaService` y los modelos de dominio se exponen ahora mediante una API REST con FastAPI y esquemas Pydantic.

## Estructura

```text
P2/
├── Tienda_online/              API REST (servidor)
│   ├── main.py                 Aplicación FastAPI y endpoints (capa de exposición)
│   ├── schemas.py              Esquemas Pydantic de petición (Create) y respuesta (Read)
│   ├── models/
│   │   ├── producto.py         Producto, ProductoElectronico, ProductoRopa
│   │   ├── usuario.py          Usuario, Cliente, Administrador
│   │   └── pedido.py           Pedido
│   ├── services/
│   │   └── tienda_service.py   TiendaService + excepciones de negocio
│   └── requirements.txt
├── cliente/
│   └── cliente.py              Cliente Python con requests (Parte 2 - Parte 1)
└── frontend/
    ├── index.html              Frontend web (Parte 2 - Parte 3)
    ├── app.js                  Peticiones a la API con fetch
    └── styles.css
```

La API, el cliente y el frontend están en carpetas separadas: los dos clientes solo se comunican con la API por HTTP.

Flujo de una petición: `main.py` recibe los datos ya validados por `schemas.py`, llama a `TiendaService` y convierte el resultado en un esquema `Read`. Si el servicio lanza una excepción de negocio (`UsuarioNoEncontrado`, `StockInsuficiente`...), `main.py` la traduce al código HTTP correspondiente.

## Ejecutar

Desde la carpeta `Tienda_online`:

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Abrir http://127.0.0.1:8000/docs para probar los endpoints con Swagger.

Al arrancar se cargan unos datos de ejemplo (2 clientes, 1 administrador y 5 productos) para poder probar sin crear nada. Los ids son UUID: se consultan con `GET /usuarios` y `GET /productos`. Los datos se guardan en memoria y se pierden al reiniciar el servidor.

## Endpoints

| Método | Ruta | Descripción | Códigos |
| --- | --- | --- | --- |
| POST | `/usuarios` | Crea un usuario | 201, 409 email repetido, 422 |
| GET | `/usuarios` | Lista los usuarios; admite `?nombre=` | 200 |
| GET | `/usuarios/{usuario_id}` | Devuelve un usuario | 200, 404 |
| POST | `/productos` | Crea un producto | 201, 422 |
| GET | `/productos` | Lista los productos; admite `?nombre=` | 200 |
| GET | `/productos/{producto_id}` | Devuelve un producto | 200, 404 |
| DELETE | `/productos/{producto_id}` | Elimina un producto | 204, 404 |
| POST | `/pedidos` | Crea un pedido | 201, 400 no es cliente, 404 cliente/producto, 409 sin stock, 422 |
| GET | `/usuarios/{cliente_id}/pedidos` | Historial de pedidos del cliente | 200, 400 no es cliente, 404 |

422 = datos que no cumplen el esquema (FastAPI lo devuelve automáticamente).

## Filtro por nombre (parámetro de consulta)

Igual que `GET /items/?name=...` en el repositorio de la asignatura, los listados admiten un parámetro de consulta opcional `nombre` que filtra por nombre exacto:

```text
GET /productos?nombre=Tablet
GET /usuarios?nombre=sofia
```

Sin el parámetro se devuelve la lista completa. `main.py` recibe el parámetro y se lo pasa a `TiendaService`, que es quien hace el filtrado (igual que `crud.get_items` en el ejemplo).

## Ejemplos de cuerpos

```json
POST /usuarios
{"nombre": "lucia", "email": "lucia@tienda.com", "tipo": "cliente", "direccion": "Calle Mar 3"}

POST /productos
{"tipo": "electronico", "nombre": "Tablet", "precio": 299.9, "stock": 5, "meses_garantia": 24}
{"tipo": "ropa", "nombre": "Gorra", "precio": 15, "stock": 10, "talla": "U", "color": "Rojo"}
{"tipo": "generico", "nombre": "Boli", "precio": 1.2, "stock": 100}

POST /pedidos
{"cliente_id": "<id de un cliente>", "items": [{"producto_id": "<id>", "cantidad": 2}]}
```

## Decisiones de validación

- `tipo` de usuario solo admite `cliente` o `administrador`; la dirección es obligatoria para clientes.
- Cada tipo de producto exige sus atributos (`meses_garantia` para electrónicos, `talla` y `color` para ropa) y rechaza los de otro tipo.
- Precio > 0, stock ≥ 0 y cantidades de pedido > 0.
- Un pedido se valida entero antes de descontar stock: si una línea falla, no se modifica ningún producto. Si un producto aparece en varias líneas, se suman las cantidades.

---

# Práctica 2 – Parte 2: clientes de la API

La API, el cliente Python y el frontend están separados. Los clientes **no importan** `TiendaService` ni los modelos: toda la comunicación se hace por HTTP contra los mismos endpoints, así que todos trabajan sobre los mismos datos.

## Parte 1: cliente Python (`cliente/cliente.py`)

Con la API arrancada, desde la carpeta `P2`:

```bash
python cliente/cliente.py                            # usa BASE_URL = http://localhost:8000
python cliente/cliente.py http://192.168.1.34:8000   # API en otro equipo
```

La dirección se define en la constante `BASE_URL` al principio del script (o se pasa como argumento). El script ejecuta este flujo y comprueba el código HTTP de cada respuesta antes de procesar el JSON:

1. `POST /usuarios` → crea un cliente (201)
2. `GET /usuarios` → lista los usuarios (200)
3. `POST /productos` ×3 → crea un electrónico, una prenda de ropa y un genérico (201)
4. `GET /productos` → lista los productos (200)
   - `GET /productos?nombre=Tablet` → busca por nombre con parámetro de consulta (200)
5. `POST /pedidos` → crea un pedido para el cliente nuevo (201)
6. `GET /usuarios/{id}/pedidos` → consulta los pedidos de ese cliente (200)

Si alguna respuesta no tiene el código esperado, se muestra el `detail` devuelto por la API y el script termina.

## Parte 2: comunicación entre dos equipos

**Equipo servidor:**

1. Obtener la IP local: `ipconfig` en Windows (dirección IPv4) o `ip addr` / `ifconfig` en Linux o macOS.
2. Arrancar la API aceptando conexiones de la red:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```
   Con el `--host 127.0.0.1` por defecto solo se aceptan conexiones del propio equipo (`localhost`). Con `0.0.0.0` se escucha en todas las interfaces de red.
3. Si el firewall de Windows lo pide, permitir el acceso a Python en redes privadas.

**Equipo cliente:**

1. Desde la carpeta `P2`, ejecutar `python cliente/cliente.py http://<IP-del-servidor>:8000`, o cambiar `BASE_URL` en el script.
2. Abrir `http://<IP-del-servidor>:8000/docs` en el navegador para comprobar que se accede a la documentación remota.
3. Los usuarios y productos creados desde el cliente aparecen en el servidor, por ejemplo con `GET /usuarios` en `/docs`, porque los datos los gestiona la API remota.

## Parte 3: frontend (`frontend/`)

Con la API arrancada, abrir http://127.0.0.1:8000 (la API sirve la carpeta `frontend/` si está junto a `Tienda_online`) o abrir directamente `frontend/index.html` en el navegador. En la parte superior se puede cambiar la URL de la API (por defecto `http://localhost:8000`) y pulsar **Conectar** para usar la IP de otro equipo.

Funcionalidades: ver productos, buscarlos por nombre, crear productos (los campos se adaptan al tipo), ver usuarios, crear pedidos con varias líneas y consultar los pedidos de un cliente.

**Cómo se hacen las peticiones** (`frontend/app.js`): todas pasan por la función `api(metodo, ruta, cuerpo)`. Esta función usa `fetch`, envía el cuerpo como JSON, comprueba `respuesta.ok` y el código de estado, y devuelve el JSON. Si hay un error, lanza una excepción con el campo `detail` de FastAPI, que se muestra en pantalla.

| Acción en la interfaz | Función / evento | Endpoint |
| --- | --- | --- |
| Listar productos | `cargarProductos()` | `GET /productos` |
| Buscar producto por nombre | submit de `#form-buscar` | `GET /productos?nombre=...` |
| Crear producto | submit de `#form-producto` | `POST /productos` |
| Listar usuarios | `cargarUsuarios()` | `GET /usuarios` |
| Crear pedido | submit de `#form-pedido` | `POST /pedidos` |
| Pedidos de un usuario | submit de `#form-consulta` | `GET /usuarios/{id}/pedidos` |

Para que el navegador permita estas peticiones desde otro origen, `main.py` activa `CORSMiddleware`.

## Comprobación final

Con la API arrancada, se puede acceder a los mismos datos desde `/docs`, desde `cliente/cliente.py` y desde `frontend/index.html`. Por ejemplo, un producto creado desde el frontend aparece al ejecutar el cliente Python y en `GET /productos` de `/docs`.
