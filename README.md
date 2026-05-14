---
title: sgsi
sdk: gradio
sdk_version: 6.14.0
app_file: app.py
pinned: false
---

# Agente Conversacional ISO/IEC 27001:2022 - SGSI

## Descripción del proyecto

Este proyecto corresponde a la Opción C — Agente Conversacional Avanzado del ejercicio académico.

La aplicación implementa una plataforma inteligente especializada en ISO/IEC 27001:2022 y Sistemas de Gestión de Seguridad de la Información (SGSI), utilizando inteligencia artificial generativa mediante Google Gemini y LangChain.

La solución permite apoyar procesos relacionados con:

- Implementación de SGSI
- Diagnóstico inicial
- Evaluación documental
- Generación de políticas
- Evaluación de cumplimiento
- Gestión de riesgos
- Definición de alcance
- Consultas técnicas especializadas

La plataforma fue desarrollada con un enfoque práctico orientado a organizaciones que desean implementar o fortalecer un Sistema de Gestión de Seguridad de la Información basado en ISO/IEC 27001:2022.

---

# Aplicación desplegada

La aplicación se encuentra desplegada en Hugging Face Spaces:

https://huggingface.co/spaces/roldeint/sgsi/

---

# Repositorio GitHub

Repositorio público del proyecto:

https://github.com/Roldeint/agente-iso27001-sgsi

---

# Tecnologías utilizadas

Este proyecto fue desarrollado utilizando las siguientes tecnologías:

- Python
- Gradio
- LangChain
- Google Gemini 2.5 Flash
- DuckDuckGo Search
- Matplotlib
- PyPDF
- python-docx
- Hugging Face Spaces

---

# Funcionalidades principales

## 1. Chatbot SGSI

Permite realizar consultas relacionadas con:

- ISO/IEC 27001:2022
- SGSI
- Gestión de riesgos
- Auditoría
- Controles del Anexo A
- Declaración de aplicabilidad
- Implementación práctica
- Mejora continua

Características:

- Memoria conversacional
- Respuestas contextualizadas
- Integración con Gemini
- Prompt especializado en SGSI

---

## 2. Cálculo de avance del Anexo A

Permite calcular el porcentaje de cumplimiento del Anexo A de ISO/IEC 27001:2022.

Clasifica controles por tipo:

- Organizacionales
- Personas
- Físicos
- Tecnológicos

Características:

- Cálculo automático
- Porcentaje global
- Generación de gráficas
- Recomendaciones automáticas

---

## 3. Diagnóstico inicial del SGSI

Herramienta orientada a evaluar el estado actual del SGSI.

Evalúa aspectos relacionados con:

- Gobierno
- Gestión documental
- Gestión de riesgos
- Controles
- Concientización
- Continuidad
- Cumplimiento

Características:

- Evaluación orientativa
- Recomendaciones de mejora
- Diagnóstico inicial de madurez

---

## 4. Generador de alcance inicial del SGSI

Permite generar propuestas iniciales de alcance del SGSI.

Incluye:

- Organización
- Procesos
- Sedes
- Servicios
- Infraestructura
- Exclusiones
- Contexto organizacional

---

## 5. Cumplimiento de cláusulas ISO/IEC 27001:2022

Permite evaluar de forma orientativa el cumplimiento de las cláusulas:

- Cláusula 4
- Cláusula 5
- Cláusula 6
- Cláusula 7
- Cláusula 8
- Cláusula 9
- Cláusula 10

Características:

- Evaluación visual
- Porcentaje de cumplimiento
- Generación de gráficas

---

## 6. Generador de políticas de ejemplo

Permite generar mediante IA:

- Política general de seguridad de la información
- Políticas específicas alineadas con ISO/IEC 27001:2022

Ejemplos:

- Control de acceso
- Gestión de activos
- Gestión de incidentes
- Continuidad
- Teletrabajo
- Respaldos
- Clasificación de información

Características:

- Generación automática mediante IA
- Descarga de documentos
- Flujo guiado

---

## 7. Analizador de documentos SGSI

Permite cargar y analizar documentación relacionada con SGSI.

Documentos soportados:

- Políticas
- Procedimientos
- Manuales
- Matrices
- Planes
- Declaración de aplicabilidad

Formatos soportados:

- PDF
- DOCX
- TXT
- MD

La IA analiza:

- Tipo documental
- Fortalezas
- Debilidades
- Aspectos faltantes
- Buenas prácticas ISO 27001
- Recomendaciones de mejora

---

## 8. Búsqueda web

Permite realizar búsquedas técnicas relacionadas con:

- ISO 27001
- SGSI
- Gestión de riesgos
- Controles
- Auditoría
- Buenas prácticas

Características:

- Integración con DuckDuckGo Search
- Filtrado contextual
- Resultados especializados

---

# Arquitectura general

Frontend:
- Gradio

Motor IA:
- Google Gemini 2.5 Flash
- LangChain

Herramientas:
- DuckDuckGo Search
- Matplotlib
- PyPDF
- python-docx

Deployment:
- Hugging Face Spaces

---

# Características avanzadas

- IA generativa aplicada a SGSI
- Memoria conversacional
- Navegación modular
- Descarga de archivos
- Generación automática de gráficas
- Evaluación documental automatizada
- Interfaz visual profesional

---

# Instalación local

## 1. Clonar el repositorio

```bash
git clone https://github.com/Roldeint/agente-iso27001-sgsi.git
```

---

## 2. Crear entorno virtual

```powershell
py -3.14 -m venv venv
```

---

## 3. Activar entorno virtual

```powershell
.\venv\Scripts\Activate.ps1
```

---

## 4. Instalar dependencias

```powershell
pip install -r requirements.txt
```

---

# Configuración API KEY

La aplicación utiliza Gemini mediante Google AI Studio.

Crear API Key en:

https://aistudio.google.com/app/apikey

Configurar:

```powershell
$env:GOOGLE_API_KEY="TU_API_KEY"
```

La API Key nunca debe almacenarse directamente dentro del código fuente.

---

# Ejecución local

```powershell
python app.py
```

La aplicación quedará disponible en:

```text
http://127.0.0.1:7860
```

---

# Estructura del proyecto

```text
app.py
README.md
requirements.txt
```

---

# Criterios de evaluación cubiertos

## Funcionalidad

- Flujo funcional completo
- Herramientas integradas
- Manejo de errores
- Navegación modular

## Uso de IA generativa

- Gemini + LangChain
- Prompts especializados
- Generación documental
- Evaluación documental IA

## UI/UX

- Interfaz visual
- Menú modular
- Navegación intuitiva
- Feedback visual

## Documentación

- README estructurado
- Instrucciones completas
- Arquitectura documentada
- Deployment documentado

## Deployment

- Hugging Face Spaces
- Gestión segura de secretos
- Aplicación pública

---

# Consideraciones

Este proyecto tiene fines académicos y de apoyo orientativo.

No reemplaza:

- auditorías oficiales
- certificaciones formales
- interpretación legal
- evaluación profesional especializada

---

# Autor

Proyecto académico enfocado en IA aplicada a ISO/IEC 27001:2022 y Sistemas de Gestión de Seguridad de la Información.
