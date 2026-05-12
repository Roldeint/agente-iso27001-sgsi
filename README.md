# Agente Conversacional ISO/IEC 27001:2022 — SGSI

## Descripción del proyecto

Este proyecto corresponde a la Opción C — Agente Conversacional Avanzado del ejercicio académico.

La aplicación implementa un chatbot especializado en ISO/IEC 27001:2022 y en la implementación de Sistemas de Gestión de Seguridad de la Información (SGSI), utilizando:

- Gemini (Google Generative AI)
- LangChain
- Gradio
- DuckDuckGo Search
- Memoria conversacional

El agente permite:

- Explicar formas prácticas de implementar un SGSI.
- Ayudar a definir el alcance del SGSI.
- Diagnosticar el estado actual del SGSI mediante preguntas guiadas.
- Calcular el avance cuantitativo de controles del Anexo A ISO/IEC 27001:2022.
- Consultar información actualizada mediante búsqueda web.
- Mantener memoria contextual durante la conversación.

---

# Funcionalidades principales

## Memoria conversacional

El chatbot recuerda el contexto reciente de la conversación para mantener continuidad en las respuestas.

---

## Herramienta de búsqueda web

La aplicación integra búsquedas usando DuckDuckGo para consultar información actualizada relacionada con:

- ISO 27001:2022
- SGSI
- Buenas prácticas
- Cambios recientes
- Implementación de controles

---

## Herramienta de cálculo

El agente puede:

- calcular porcentajes,
- realizar operaciones matemáticas,
- estimar avance de controles del Anexo A.

Ejemplo:

```text
Tengo 45 controles implementados de 93
```

---

## Interfaz gráfica

La aplicación utiliza Gradio para proporcionar una interfaz intuitiva y sencilla.

---

# Tecnologías utilizadas

- Python
- Gradio
- LangChain
- Google Gemini
- DuckDuckGo Search
- AST Safe Calculator

---

# Estructura del proyecto

```text
app.py
requirements.txt
README.md
```

---

# Instalación local

## 1. Clonar o descargar el proyecto

```bash
git clone <repositorio>
```

o descargar el ZIP del proyecto.

---

## 2. Crear entorno virtual

### Windows PowerShell

```powershell
py -3.14 -m venv venv
```

---

## 3. Activar entorno virtual

```powershell
.\venv\Scripts\activate
```

---

## 4. Instalar dependencias

```powershell
pip install -r requirements.txt
```

---

# Configuración de API Key

La aplicación utiliza Gemini mediante Google AI Studio.

Crear una API Key en:

https://aistudio.google.com/app/apikey

Configurar la variable de entorno:

```powershell
$env:GOOGLE_API_KEY="TU_API_KEY"
```

La API Key nunca debe almacenarse directamente dentro del código fuente.

---

# Ejecución

Ejecutar:

```powershell
python app.py
```

La aplicación quedará disponible en:

```text
http://127.0.0.1:7860
```

---

# Ejemplos de uso

## Implementación SGSI

```text
¿Cómo implementar un SGSI basado en ISO 27001:2022?
```

---

## Diagnóstico SGSI

```text
Hazme preguntas para evaluar el estado actual del SGSI.
```

---

## Alcance SGSI

```text
Ayúdame a definir el alcance del SGSI para una empresa de telecomunicaciones y ciberseguridad.
```

---

## Controles Anexo A

```text
Tengo 42 controles implementados de 93. Calcula mi porcentaje de avance.
```

---

# Deployment en Hugging Face Spaces

La aplicación fue diseñada para desplegarse usando:

- Hugging Face Spaces
- SDK: Gradio
- Hardware: CPU Basic

## Configuración requerida

En:

```text
Settings > Secrets
```

agregar:

```text
GOOGLE_API_KEY = TU_API_KEY
```

---

# Criterios de evaluación cubiertos

## Funcionalidad

- Validación de entradas
- Manejo de errores
- Flujo conversacional completo
- Herramientas funcionales

---

## Uso de IA generativa

- Integración Gemini + LangChain
- Uso de prompts especializados
- Respuestas dinámicas
- Memoria contextual

---

## UI/UX

- Interfaz clara
- Ejemplos de uso
- Labels descriptivos
- Flujo intuitivo

---

## Documentación

- README estructurado
- Type hints
- Docstrings
- Instrucciones de instalación

---

## Deployment

- Compatible con Hugging Face Spaces
- Manejo seguro de secretos
- Sin API Keys hardcodeadas

---

# Consideraciones

Este chatbot tiene fines académicos y de apoyo orientativo.

No reemplaza:
- auditorías oficiales,
- interpretación legal,
- certificaciones formales,
- evaluación profesional especializada.

---

# Autor

Proyecto académico enfocado en IA aplicada a ISO/IEC 27001:2022 y SGSI.
