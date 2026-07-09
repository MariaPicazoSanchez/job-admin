# Buscador de Empleo

Aplicación de escritorio en Python para buscar ofertas de empleo, analizarlas y guardarlas en un flujo privado y local. El proyecto combina varias fuentes de empleo, filtros conversacionales, enriquecimiento heurístico de resultados y seguimiento de candidaturas sin necesidad de backend.

## Características

- Búsqueda en lenguaje natural, por ejemplo: `Desarrollador Python senior, remoto, mínimo 60k EUR`.
- Agregación de ofertas desde múltiples fuentes.
- Filtros por país, modalidad, salario, moneda y nivel de experiencia.
- Dedupe, reranking y enriquecimiento de resultados.
- Panel lateral con análisis de la oferta seleccionada.
- Guardado local de candidaturas y seguimiento del proceso.
- Interfaz de escritorio moderna con `CustomTkinter`.

## Fuentes de empleo

El buscador consulta varias fuentes públicas y/o APIs, entre ellas:

- Remotive
- Adzuna
- Arbeitnow
- LinkedIn Jobs
- Computrabajo
- InfoJobs

La disponibilidad de algunas fuentes puede depender de la región o de la configuración de la API correspondiente.

## Requisitos

- Python 3.10 o superior.
- Conexión a internet para consultar las fuentes de empleo.

## Instalación

1. Crea y activa un entorno virtual.
2. Instala las dependencias:

```bash
pip install -r requirements.txt
```

## Uso

Ejecuta la aplicación desde la raíz del proyecto:

```bash
python app.py
```

Luego escribe tu búsqueda en lenguaje natural y ajusta los filtros desde la interfaz.

## Configuración opcional de Adzuna

La fuente Adzuna requiere credenciales válidas para devolver resultados. Si no están configuradas, la aplicación seguirá funcionando con el resto de fuentes.

Puedes habilitarla creando un archivo `config.json` en la raíz del proyecto con esta estructura:

```json
{
  "adzuna_app_id": "tu_app_id",
  "adzuna_app_key": "tu_app_key"
}
```

## Persistencia local

La aplicación guarda la información localmente en estos archivos:

- `saved_jobs.json`: candidaturas y su estado.
- `config.json`: configuración opcional de la app.

Esto permite usar la herramienta de forma privada y mantener el historial entre sesiones.

## Funcionalidades principales

- Búsqueda multi-fuente con expansión de consulta.
- Enriquecimiento automático de ofertas con seniority, rol y señales útiles.
- Detección de salario y modalidad cuando la información está disponible.
- Guardado de ofertas con estados del pipeline de selección.
- Métricas básicas del seguimiento personal de candidaturas.

## Estructura del proyecto

```text
app.py
requirements.txt
saved_jobs.json
search/
  __init__.py
  adzuna.py
  aggregator.py
  analyzer.py
  arbeitnow.py
  enricher.py
  expander.py
  linkedin.py
  models.py
  parser.py
  remotive.py
  reranker.py
  salary.py
  scraper.py
  store.py
  taxonomies.py
```

## Notas

- Si alguna fuente no responde o bloquea peticiones, la aplicación continúa con el resto de orígenes disponibles.
- El proyecto no necesita backend propio para funcionar.
- El diseño está pensado para uso en escritorio, no para navegador.
