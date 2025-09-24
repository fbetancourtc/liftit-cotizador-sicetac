# Liftit Cotizador SICETAC

Sistema de cotización de tarifas de transporte de carga conectado al webservice SICETAC del Ministerio de Transporte de Colombia.

## 🚀 Características

- **Cotización en tiempo real**: Consulta directa al webservice SICETAC del RNDC
- **Persistencia de datos**: Almacenamiento local de cotizaciones históricas en SQLite
- **Interfaz web moderna**: UI intuitiva y responsiva para gestión de cotizaciones
- **API REST completa**: CRUD endpoints para integración con otros sistemas
- **Autenticación flexible**: Modo desarrollo para testing local o JWT Supabase para producción
- **Cálculo automático**: Incluye horas logísticas en el valor mínimo a pagar

## 📋 Requisitos

- Python 3.10+
- pip (gestor de paquetes)
- Credenciales SICETAC (opcional para desarrollo)

## 🛠️ Instalación Rápida

```bash
# Clonar repositorio
git clone <repository-url>
cd liftit-cotizador-sicetac

# Instalar dependencias
pip install -e .

# Configurar entorno (ya incluido .env de desarrollo)
# Editar .env si tienes credenciales reales de SICETAC

# Ejecutar servidor
uvicorn app.main:app --host 0.0.0.0 --port 5050 --reload
```

Acceder a: **http://localhost:5050**

## 🖥️ Interfaz Web

La plataforma incluye una interfaz web completa ubicada en http://localhost:5050 con:

### Funcionalidades
- Formulario de cotización con validación en tiempo real
- Visualización de resultados con múltiples cotizaciones
- Historial de cotizaciones guardadas
- Filtros por estado (activas/archivadas)
- Modo desarrollo sin autenticación

### Uso de la Interfaz
1. Al abrir la aplicación, aparecerá un modal de autenticación
2. Para desarrollo: Click en "Omitir (Desarrollo)"
3. Completar el formulario con:
   - **Período**: AAAAMM (ej: 202401)
   - **Configuración**: Tipo de vehículo (2, 3, 2S2, 2S3, 3S2, 3S3)
   - **Origen/Destino**: Códigos DIVIPOLA de 8 dígitos terminando en 000
   - **Tipo de Carga** (opcional): General, Contenedor, Carga Refrigerada, Granel Sólido
   - **Tipo de Unidad** (opcional): Estacas, Trayler, Termoking
   - **Horas Logísticas**: Tiempo de cargue/descargue/espera
4. Click en "Obtener Cotización"

## 🔌 API REST

### Endpoints Disponibles

#### Health Check
```bash
GET /api/healthz
```

#### Cotización Rápida (sin persistencia)
```bash
POST /api/quote
Content-Type: application/json
Authorization: Bearer development-token

{
  "period": "202401",
  "configuration": "3S3",
  "origin": "11001000",
  "destination": "05001000",
  "cargo_type": "GENERAL",
  "unit_type": "ESTACAS",
  "logistics_hours": 2.5
}
```

#### CRUD de Cotizaciones

**Crear y Guardar Cotización**
```bash
POST /api/quotes/
{
  "request": {
    "period": "202401",
    "configuration": "3S3",
    "origin": "11001000",
    "destination": "05001000",
    "logistics_hours": 2
  },
  "company_name": "Empresa XYZ",
  "notes": "Cotización para cliente importante"
}
```

**Listar Cotizaciones**
```bash
GET /api/quotes/?status=active&limit=10&skip=0
```

**Obtener Cotización Específica**
```bash
GET /api/quotes/{id}
```

**Actualizar Cotización**
```bash
PATCH /api/quotes/{id}
{
  "notes": "Actualización de notas",
  "selected_quote_index": 0,
  "status": "archived"
}
```

**Eliminar Cotización (Soft Delete)**
```bash
DELETE /api/quotes/{id}
```

## 📊 Parámetros SICETAC

### Configuraciones de Vehículos
| Código | Descripción |
|--------|-------------|
| 2 | Camión de 2 ejes |
| 3 | Camión de 3 ejes |
| 2S2 | Tractocamión 2 ejes + semirremolque 2 ejes |
| 2S3 | Tractocamión 2 ejes + semirremolque 3 ejes |
| 3S2 | Tractocamión 3 ejes + semirremolque 2 ejes |
| 3S3 | Tractocamión 3 ejes + semirremolque 3 ejes |

### Tipos de Carga
- **GENERAL**: Carga general
- **CONTENEDOR**: Contenedor
- **CARGA REFRIGERADA**: Carga refrigerada
- **GRANEL SÓLIDO**: Granel sólido

### Tipos de Unidad
- **ESTACAS**: Camión con estacas/Furgón
- **TRAYLER**: Tractocamión con semirremolque
- **TERMOKING**: Unidad refrigerada

### Códigos DIVIPOLA
Códigos de 8 dígitos (últimos 3 deben ser "000"):
- Bogotá: `11001000`
- Medellín: `05001000`
- Cali: `76001000`
- Barranquilla: `08001000`
- Cartagena: `13001000`
- Bucaramanga: `68001000`

## 🐳 Docker

### Desarrollo con Docker Compose
```bash
docker-compose up
```

### Producción
```bash
docker build -t cotizador-sicetac .
docker run -p 5050:5050 --env-file .env cotizador-sicetac
```

## 📁 Estructura del Proyecto

```
liftit-cotizador-sicetac/
├── app/
│   ├── api/              # Endpoints REST
│   │   ├── routes.py     # Rutas principales
│   │   └── quotes_crud.py # CRUD de cotizaciones
│   ├── core/             # Configuración central
│   │   ├── auth.py       # Autenticación JWT
│   │   ├── auth_dev.py   # Auth para desarrollo
│   │   └── config.py     # Settings
│   ├── models/           # Modelos de datos
│   │   ├── quotes.py     # Esquemas Pydantic
│   │   └── database.py   # Modelos SQLAlchemy
│   ├── services/         # Lógica de negocio
│   │   └── sicetac.py    # Cliente SOAP SICETAC
│   ├── static/           # Frontend
│   │   ├── index.html    # UI principal
│   │   ├── styles.css    # Estilos
│   │   └── app.js        # Lógica frontend
│   └── main.py           # FastAPI app
├── tests/                # Pruebas
├── docs/                 # Documentación SICETAC
├── docker-compose.yml    # Orquestación Docker
├── Dockerfile           # Imagen Docker
├── pyproject.toml       # Configuración Python
└── .env                 # Variables de entorno
```

## ⚙️ Configuración

### Variables de Entorno (.env)

```env
# Entorno
ENVIRONMENT=local

# Supabase (opcional)
SUPABASE_PROJECT_URL=https://your-project-ref.supabase.co
SUPABASE_JWT_AUDIENCE=authenticated

# SICETAC
SICETAC_USERNAME=tu_usuario
SICETAC_PASSWORD=tu_password
SICETAC_ENDPOINT=http://rndcws.mintransporte.gov.co:8080/ws/rndcService
SICETAC_TIMEOUT_SECONDS=20
SICETAC_VERIFY_SSL=false
```

## 🧪 Testing

```bash
# Instalar dependencias de desarrollo
pip install .[dev]

# Ejecutar pruebas
pytest tests/

# Linting
ruff app/

# Formateo
ruff format app/
```

## 📚 Documentación API

Con el servidor en ejecución:
- **Swagger UI**: http://localhost:5050/docs
- **ReDoc**: http://localhost:5050/redoc

## 🔧 Solución de Problemas

### Puerto 5050 en uso
```bash
lsof -i :5050
kill <PID>
```

### Error de autenticación SICETAC
Verificar credenciales en `.env`:
- `SICETAC_USERNAME`
- `SICETAC_PASSWORD`

### "Documento no encontrado"
La ruta/configuración no tiene tarifas SICETAC para el período especificado.

## 🔐 Seguridad

- Credenciales SICETAC nunca expuestas en logs
- Tokens JWT almacenados en localStorage
- CORS configurado para producción
- Soft delete para preservar historial
- Validación de entrada en todos los endpoints

## 🚀 Próximos Pasos

1. Migrar a PostgreSQL para producción
2. Implementar caché Redis para consultas frecuentes
3. Agregar exportación a Excel/PDF
4. Sistema de notificaciones para cambios de tarifas
5. Dashboard analytics para métricas de uso

## 📄 Licencia

Proprietary - Liftit

## 📞 Soporte

Para consultas y soporte, contactar al equipo de desarrollo de Liftit.