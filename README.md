# AgentHire

AgentHire es una plataforma automatizada basada en agentes inteligentes que busca, evalúa y postula a ofertas de trabajo de manera autónoma. Está diseñada para interactuar con sitios web de empleo (LinkedIn, Computrabajo, Laborum, etc.), extraer oportunidades, generar currículums y cartas de presentación personalizadas, y completar formularios de postulación.

## 🚀 Arquitectura

El sistema se compone de una arquitectura distribuida impulsada por Docker:

- **n8n:** Orquestador de flujos y tareas programadas (cron jobs) accesible en `http://localhost:5679`.
- **Dashboard (Next.js):** Interfaz gráfica para revisar el progreso, métricas y ofertas encontradas, accesible en `http://localhost:3000`.
- **Agentes de Inteligencia Artificial (FastAPI):**
  - `agent-discovery`: Navega los portales de empleo buscando vacantes.
  - `agent-ranking`: Evalúa la compatibilidad de cada oferta usando modelos locales.
  - `agent-cv` & `agent-cover`: Generan documentos personalizados por oferta.
  - `agent-apply`: Rellena automáticamente los formularios de postulación.
  - `agent-tracker` & `agent-profiles`: Gestionan el seguimiento y la actualización de perfiles.
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

## 📈 Mejoras Recientes

- **Resolución de Bugs:** Corrección de inyección de comandos en `agent-browser` y resolución de rutas dinámicas de los agentes.
- **Refactorización & Buenas Prácticas:** Eliminación de sobreingeniería centralizando la lógica de extracción con LLM (`_extract_jobs_llm`) en la clase `BaseConnector`.
- **Dashboard Funcional:** Implementación de peticiones reales al API del Tracker, ordenamiento (sorting) de la tabla y vinculación de botones de acción (Apply).
- **Testeo Automatizado:** Integración de Pytest con tests iniciales para los modelos de datos, base de datos y clientes LLM/Browser.
- **Postulación Automatizada:** Implementación de la lógica base de postulación para el conector de **ChileTrabajos** (navegación y envío de formulario).

## 👨‍💻 Autor

Jonatthan Medalla (jonatthan.medalla@inacapmail.cl)