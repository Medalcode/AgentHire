# AgentHire

AgentHire es una plataforma automatizada basada en agentes inteligentes que busca, evalúa y postula a ofertas de trabajo de manera autónoma. Está diseñada para interactuar con sitios web de empleo (LinkedIn, Computrabajo, Laborum, etc.), extraer oportunidades, generar currículums y cartas de presentación personalizadas, y completar formularios de postulación.

## 🚀 Arquitectura

El sistema se compone de una arquitectura distribuida impulsada por Docker, estructurada en un "Majestic Monolith" para el backend:

- **n8n:** Orquestador de flujos y tareas programadas (cron jobs) accesible en `http://localhost:5679`.
- **Dashboard (Next.js):** Interfaz gráfica para revisar el progreso, métricas y ofertas encontradas, accesible en `http://localhost:3000`.
- **Backend Central (`agent-backend`):** Servidor unificado FastAPI (puerto 8000) que expone todos los sub-agentes lógicos como APIRouters:
  - `/discovery`: Navega los portales de empleo buscando vacantes.
  - `/ranking`: Evalúa la compatibilidad de cada oferta usando modelos locales.
  - `/cv` & `/cover`: Generan documentos personalizados por oferta.
  - `/apply`: Rellena automáticamente los formularios de postulación.
  - `/tracker` & `/profiles`: Gestionan el seguimiento y la actualización de perfiles.
- **Agent-Browser:** Servidor interno que traduce comandos de los agentes hacia el navegador web real para la interacción con los portales de empleo.
- **Base de Datos & Caché:** PostgreSQL y Redis para persistencia y mensajería rápida.
- **Modelos de IA Locales:** Integración nativa con **Ollama** utilizando el modelo `qwen2.5-coder:7b` para garantizar privacidad y eliminar costos de API.

## 🛠️ Instalación y Uso

1. Copia el archivo `.env.example` a `.env` y configura tus variables.
2. Asegúrate de tener Docker instalado.
3. Ejecuta el script de configuración inicial:
   ```bash
   chmod +x scripts/setup.sh
   ./scripts/setup.sh
   ```
4. Levanta todos los servicios:
   ```bash
   docker compose --profile dev up -d --build
   ```
5. Accede a las interfaces:
   - Dashboard: `http://localhost:3000`
   - n8n: `http://localhost:5679`

### Configuración de n8n (Orquestación)
1. Ingresa a `http://localhost:5679` y configura tu cuenta inicial.
2. En el menú izquierdo, ve a **Workflows** y selecciona **Import from File**.
3. Importa los flujos `01_discovery_cron.json` y `02_application_pipeline.json` ubicados en la carpeta `n8n/workflows/`.
4. Configura la credencial de PostgreSQL dentro del flujo `02_Application_Pipeline` (usando las credenciales de tu `.env`).
5. Activa ambos flujos en la esquina superior derecha ("Active").

## 📈 Mejoras Recientes

- **CI/CD & DevOps:** Pipeline de GitHub Actions (Lint, Test, Docker Build), `.dockerignore` configurado y adopción de *Conventional Commits*.
- **Migración a Monolito:** Reducción de 7 contenedores a 1 (`agent-backend`), optimizando drásticamente el consumo de recursos (RAM/CPU) y eliminando deuda técnica.
- **Estrategia QA:** Refactorización de pruebas eliminando mocks frágiles, integrando *Pure Functions* para parsing de LLMs, y *Smoke/Integration Tests*.
- **Resolución de Bugs Críticos:** Corrección del parseo de LLMs (soportando Markdown y Arrays), corrección de inyección de comandos en `agent-browser` y resolución de hidratación SVG en Next.js.
- **Refactorización & Buenas Prácticas:** Centralización de lógica de extracción con LLM (`_extract_jobs_llm`) en la clase `BaseConnector`.
- **Compatibilidad FastAPI & n8n:** Migración de `TypedDict` a `pydantic.BaseModel` con `model_validator` personalizado para procesar payloads JSON stringificados desde n8n.
- **Estabilidad de Contenedores:** Resolución de rutas de importación en `Dockerfile` (`WORKDIR`), corrección de middlewares en routers de FastAPI, y sincronización de contraseñas de PostgreSQL.

## 🧭 SDD Reorientation (Fase de Diseño)

Actualmente el proyecto se encuentra en una fase de rediseño arquitectónico impulsada por **SDD (Specification-Driven Development)**:
- **Candidate Knowledge Base**: Migración de `cv-master.json` hacia un esquema relacional estructurado (`002_candidate_kb.sql`) con modelo de **Evidencias**.
- **Job Intelligence**: Formalización de un modelo de abstracción para transformar descripciones en crudo en un conjunto de `JobRequirement`s estructurados.
- **Matching Determinista**: Eliminación de alucinaciones del LLM mediante el cruce de `JobRequirement`s contra las Evidencias del candidato utilizando SQL y lógica predecible, manteniendo al LLM confinado únicamente a tareas de refinamiento de presentación.


## 👨‍💻 Autor

Jonatthan Medalla (jonatthan.medalla@inacapmail.cl)