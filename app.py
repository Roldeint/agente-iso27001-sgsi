"""
Agente Conversacional ISO/IEC 27001:2022
Versión con menú desplegable para seleccionar herramienta.

Herramientas:
- Chatbot SGSI con memoria conversacional.
- Cálculo de avance del Anexo A por tipo de control.
- Diagnóstico inicial SGSI.
- Generador de alcance inicial SGSI.
- Búsqueda web.
- Cumplimiento de cláusulas ISO/IEC 27001:2022.

Variable requerida:
    GOOGLE_API_KEY o GEMINI_API_KEY
"""

from __future__ import annotations

import ast
import operator
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
from duckduckgo_search import DDGS
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


TOTAL_CONTROLES_ANEXO_A_2022 = 93
CONTROLES_ORGANIZACIONALES = 37
CONTROLES_PERSONAS = 8
CONTROLES_FISICOS = 14
CONTROLES_TECNOLOGICOS = 34

MAX_HISTORY_MESSAGES = 10
MAX_USER_MESSAGE_LENGTH = 2500

OPCIONES_HERRAMIENTA = [
    "Chatbot SGSI",
    "Cálculo de avance del Anexo A",
    "Diagnóstico inicial del SGSI",
    "Generador de alcance inicial del SGSI",
    "Búsqueda web",
    "Cumplimiento de cláusulas",
    "Generador de políticas de ejemplo",
]


SYSTEM_PROMPT = f"""
Eres un agente conversacional especializado en ISO/IEC 27001:2022 y en implementación de Sistemas de Gestión de Seguridad de la Información SGSI.

Tu propósito es ayudar al usuario a:
1. Comprender formas prácticas de implementar un SGSI.
2. Diagnosticar el estado actual de un SGSI mediante preguntas guiadas.
3. Ayudar a determinar un alcance inicial del SGSI.
4. Calcular el avance cuantitativo de controles cumplidos del Anexo A ISO/IEC 27001:2022, tomando como referencia {TOTAL_CONTROLES_ANEXO_A_2022} controles.
5. Orientar la preparación de evidencias, políticas, riesgos, controles, auditorías y mejora continua.

Reglas de respuesta:
- Responde siempre en español.
- No reproduzcas texto completo de normas ISO ni controles protegidos por copyright.
- Explica con enfoque práctico, académico y empresarial.
- Cuando falten datos, indica claramente qué información falta.
- Cuando uses resultados de herramientas, aclara el uso de la herramienta.
- No inventes certificaciones, porcentajes ni resultados de auditoría.
- Para temas legales, auditoría formal o certificación, aclara que la respuesta es orientativa y debe validarse con el auditor o responsable del SGSI.
"""


def sanitize_message(message: str) -> str:
    """Valida y limpia el mensaje del usuario."""
    if not message or not message.strip():
        raise ValueError("Por favor escribe una pregunta o instrucción.")
    clean_message = message.strip()
    if len(clean_message) > MAX_USER_MESSAGE_LENGTH:
        raise ValueError(f"El mensaje es demasiado largo. Usa máximo {MAX_USER_MESSAGE_LENGTH} caracteres.")
    return clean_message


def safe_calculator(expression: str) -> str:
    """Evalúa operaciones aritméticas básicas de forma segura."""
    allowed_operators: dict[type[Any], Any] = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.Mod: operator.mod,
    }

    def eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in allowed_operators:
            return float(allowed_operators[type(node.op)](eval_node(node.left), eval_node(node.right)))
        if isinstance(node, ast.UnaryOp) and type(node.op) in allowed_operators:
            return float(allowed_operators[type(node.op)](eval_node(node.operand)))
        raise ValueError("Expresión no permitida. Usa solo números y operadores +, -, *, /, %, **.")

    try:
        tree = ast.parse(expression, mode="eval")
        result = eval_node(tree.body)
        return f"Resultado calculado: {result:.2f}"
    except Exception as exc:
        return f"No pude calcular la expresión. Detalle: {exc}"


def interpretar_porcentaje(porcentaje: float) -> tuple[str, str]:
    """Interpreta el porcentaje de avance."""
    if porcentaje < 30:
        return (
            "Inicial o bajo",
            "Priorizar diagnóstico, alcance, inventario de activos, matriz de riesgos y políticas base.",
        )
    if porcentaje < 60:
        return (
            "En desarrollo",
            "Fortalecer evidencias, responsables, medición de controles y tratamiento de riesgos.",
        )
    if porcentaje < 85:
        return (
            "Avanzado",
            "Validar eficacia, auditoría interna, indicadores, revisión por la dirección y acciones correctivas.",
        )
    return (
        "Alto o cercano a preparación de auditoría",
        "Realizar revisión final de evidencias, SoA, auditoría interna y cierre de hallazgos.",
    )


def generar_grafica_controles(
    organizacionales: int,
    personas: int,
    fisicos: int,
    tecnologicos: int,
):
    """Genera una gráfica de avance por tipo de control."""
    categorias = ["Organizacionales", "Personas", "Físicos", "Tecnológicos"]
    totales = [
        CONTROLES_ORGANIZACIONALES,
        CONTROLES_PERSONAS,
        CONTROLES_FISICOS,
        CONTROLES_TECNOLOGICOS,
    ]
    cumplidos = [organizacionales, personas, fisicos, tecnologicos]
    porcentajes = [(cumplidos[i] / totales[i]) * 100 for i in range(len(categorias))]

    fig, ax = plt.subplots(figsize=(8, 4.5))
    barras = ax.bar(categorias, porcentajes)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Porcentaje de cumplimiento")
    ax.set_title("Cumplimiento por tipo de control del Anexo A")
    ax.bar_label(barras, labels=[f"{p:.1f}%" for p in porcentajes], padding=3)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    return fig


def calcular_cumplimiento_por_tipo(
    organizacionales: int,
    personas: int,
    fisicos: int,
    tecnologicos: int,
):
    """Calcula cumplimiento del Anexo A por tipo de control y genera gráfica."""
    errores = []
    if organizacionales < 0 or organizacionales > CONTROLES_ORGANIZACIONALES:
        errores.append(f"Organizacionales debe estar entre 0 y {CONTROLES_ORGANIZACIONALES}.")
    if personas < 0 or personas > CONTROLES_PERSONAS:
        errores.append(f"Personas debe estar entre 0 y {CONTROLES_PERSONAS}.")
    if fisicos < 0 or fisicos > CONTROLES_FISICOS:
        errores.append(f"Físicos debe estar entre 0 y {CONTROLES_FISICOS}.")
    if tecnologicos < 0 or tecnologicos > CONTROLES_TECNOLOGICOS:
        errores.append(f"Tecnológicos debe estar entre 0 y {CONTROLES_TECNOLOGICOS}.")

    if errores:
        fig = generar_grafica_controles(0, 0, 0, 0)
        return "\n".join(errores), fig

    total_cumplidos = organizacionales + personas + fisicos + tecnologicos
    total_pendientes = TOTAL_CONTROLES_ANEXO_A_2022 - total_cumplidos
    porcentaje_total = (total_cumplidos / TOTAL_CONTROLES_ANEXO_A_2022) * 100
    nivel, recomendacion = interpretar_porcentaje(porcentaje_total)

    porcentaje_organizacionales = (organizacionales / CONTROLES_ORGANIZACIONALES) * 100
    porcentaje_personas = (personas / CONTROLES_PERSONAS) * 100
    porcentaje_fisicos = (fisicos / CONTROLES_FISICOS) * 100
    porcentaje_tecnologicos = (tecnologicos / CONTROLES_TECNOLOGICOS) * 100

    resultado = (
        "Resultado de cumplimiento del Anexo A ISO/IEC 27001:2022 por tipo de control:\n\n"
        f"- Controles organizacionales: {organizacionales}/{CONTROLES_ORGANIZACIONALES} ({porcentaje_organizacionales:.2f}%)\n"
        f"- Controles de personas: {personas}/{CONTROLES_PERSONAS} ({porcentaje_personas:.2f}%)\n"
        f"- Controles físicos: {fisicos}/{CONTROLES_FISICOS} ({porcentaje_fisicos:.2f}%)\n"
        f"- Controles tecnológicos: {tecnologicos}/{CONTROLES_TECNOLOGICOS} ({porcentaje_tecnologicos:.2f}%)\n\n"
        f"Consolidado general:\n"
        f"- Total de controles cumplidos: {total_cumplidos}/{TOTAL_CONTROLES_ANEXO_A_2022}\n"
        f"- Total de controles pendientes: {total_pendientes}\n"
        f"- Porcentaje general estimado: {porcentaje_total:.2f}%\n"
        f"- Nivel interpretativo: {nivel}\n"
        f"- Recomendación: {recomendacion}\n\n"
        "Lectura del resultado:\n"
        "- Si el porcentaje tecnológico es alto pero el organizacional es bajo, el SGSI puede tener herramientas, pero falta gobierno, políticas, roles y gestión documental.\n"
        "- Si el porcentaje organizacional es alto pero el tecnológico es bajo, puede existir documentación, pero falta implementación técnica o evidencia operativa.\n"
        "- Si personas y físico están bajos, se deben revisar cultura, formación, control de acceso físico, protección de instalaciones y responsabilidades.\n\n"
        "Nota: este cálculo es cuantitativo. La conformidad real depende de evidencia, eficacia, aplicabilidad y revisión del auditor."
    )

    fig = generar_grafica_controles(organizacionales, personas, fisicos, tecnologicos)
    return resultado, fig


def calcular_cumplimiento_desde_texto(texto: str) -> str:
    """Extrae número de controles desde texto y calcula avance general."""
    numeros = [int(numero) for numero in re.findall(r"\d+", texto)]
    if not numeros:
        return "No encontré un número de controles cumplidos. Ejemplo válido: 'Tengo 35 controles cumplidos'."
    cumplidos = numeros[0]
    if cumplidos < 0 or cumplidos > TOTAL_CONTROLES_ANEXO_A_2022:
        return f"El número de controles cumplidos debe estar entre 0 y {TOTAL_CONTROLES_ANEXO_A_2022}."
    porcentaje = (cumplidos / TOTAL_CONTROLES_ANEXO_A_2022) * 100
    pendientes = TOTAL_CONTROLES_ANEXO_A_2022 - cumplidos
    nivel, recomendacion = interpretar_porcentaje(porcentaje)
    return (
        f"Controles cumplidos: {cumplidos}/{TOTAL_CONTROLES_ANEXO_A_2022}\n"
        f"Porcentaje estimado: {porcentaje:.2f}%\n"
        f"Pendientes: {pendientes}\n"
        f"Nivel: {nivel}\n"
        f"Recomendación: {recomendacion}"
    )


def search_web_duckduckgo(query: str) -> str:
    """Consulta DuckDuckGo."""
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=4))

        if not results:
            return "No se encontraron resultados web relevantes."

        formatted_results = []
        for index, result in enumerate(results, start=1):
            title = result.get("title", "Sin título")
            body = result.get("body", "Sin resumen disponible")
            href = result.get("href", "Sin URL")
            formatted_results.append(f"{index}. {title}\nResumen: {body}\nURL: {href}")

        return "\n\n".join(formatted_results)
    except Exception as exc:
        return f"No fue posible realizar la búsqueda web en este momento. Detalle: {exc}"


def should_use_web_search(message: str) -> bool:
    """Determina si debe usar búsqueda web."""
    keywords = [
        "actual", "actualizado", "vigente", "reciente", "último", "ultima",
        "última", "buscar", "consulta web", "internet", "noticia", "versión",
        "version", "nueva norma", "cambio reciente",
    ]
    return any(keyword in message.lower() for keyword in keywords)


def should_use_calculator(message: str) -> bool:
    """Determina si debe usar calculadora."""
    text = message.lower()
    return any(keyword in text for keyword in ["calcula", "porcentaje", "controles cumplidos", "avance", "cumplimiento"]) or bool(
        re.search(r"\d+\s*[+\-*/]\s*\d+", text)
    )


def create_llm() -> ChatGoogleGenerativeAI:
    """Crea cliente Gemini."""
    api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise EnvironmentError("Falta configurar GOOGLE_API_KEY o GEMINI_API_KEY.")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        temperature=0.2,
        max_retries=2,
    )


def build_tool_context(message: str) -> tuple[str, list[str]]:
    """Ejecuta herramientas cuando aplica."""
    tool_context = ""
    used_tools: list[str] = []

    if should_use_calculator(message):
        if "control" in message.lower() or "anexo" in message.lower():
            calculation_result = calcular_cumplimiento_desde_texto(message)
        else:
            expression = re.sub(r"[^0-9+\-*/().% ]", "", message).replace("%", "/100")
            calculation_result = safe_calculator(expression)
        used_tools.append("Calculadora")
        tool_context += f"\n\n[Herramienta: Calculadora]\n{calculation_result}"

    if should_use_web_search(message):
        search_result = search_web_duckduckgo(message)
        used_tools.append("Búsqueda web DuckDuckGo")
        tool_context += f"\n\n[Herramienta: Búsqueda web DuckDuckGo]\n{search_result}"

    return tool_context, used_tools


def history_to_messages(history: list[dict[str, str]]) -> list[Any]:
    """Convierte memoria interna a mensajes LangChain."""
    messages: list[Any] = [SystemMessage(content=SYSTEM_PROMPT)]
    for item in history[-MAX_HISTORY_MESSAGES:]:
        if item.get("user"):
            messages.append(HumanMessage(content=item["user"]))
        if item.get("assistant"):
            messages.append(AIMessage(content=item["assistant"]))
    return messages


def responder_texto(message: str, history: list[dict[str, str]]) -> str:
    """Consulta Gemini con memoria y herramientas."""
    clean_message = sanitize_message(message)
    tool_context, used_tools = build_tool_context(clean_message)

    messages = history_to_messages(history)
    final_question = clean_message

    if tool_context:
        final_question += (
            "\n\nInformación obtenida de herramientas para apoyar la respuesta. "
            "Úsala solo si es relevante y no inventes datos adicionales:"
            f"{tool_context}"
        )

    messages.append(HumanMessage(content=final_question))
    llm = create_llm()
    response = llm.invoke(messages).content

    if used_tools:
        response += "\n\nHerramientas usadas: " + ", ".join(used_tools)

    return response


def formato_historial(history: list[dict[str, str]]) -> str:
    """Da formato legible al historial."""
    if not history:
        return "Aún no hay conversación. Escribe una consulta y presiona Enviar."

    texto = []
    for index, item in enumerate(history, start=1):
        texto.append(f"Consulta {index}:\n{item.get('user', '')}\n")
        texto.append(f"Respuesta {index}:\n{item.get('assistant', '')}\n")
        texto.append("-" * 90)
    return "\n".join(texto)


def enviar_chat(message: str, history: list[dict[str, str]] | None) -> tuple[str, str, list[dict[str, str]]]:
    """Procesa una consulta del chat."""
    if history is None:
        history = []

    try:
        response = responder_texto(message, history)
    except ValueError as exc:
        response = f"Entrada no válida: {exc}"
    except EnvironmentError as exc:
        response = f"Configuración pendiente: {exc}"
    except Exception as exc:
        response = f"Ocurrió un error inesperado. Detalle técnico: {exc}"

    history.append({"user": message, "assistant": response})
    return "", formato_historial(history), history


def limpiar_chat() -> tuple[str, str, list[dict[str, str]]]:
    """Limpia el chat."""
    return "", "Aún no hay conversación. Escribe una consulta y presiona Enviar.", []


def diagnostico_sgsi(contexto: str, alcance: str, riesgos: str, activos: str, controles: str, evidencias: str, auditoria: str) -> str:
    """Diagnóstico orientativo de madurez SGSI."""
    puntajes = {
        "contexto": 1 if contexto == "Sí" else 0.5 if contexto == "Parcial" else 0,
        "alcance": 1 if alcance == "Sí" else 0.5 if alcance == "Parcial" else 0,
        "riesgos": 1 if riesgos == "Sí" else 0.5 if riesgos == "Parcial" else 0,
        "activos": 1 if activos == "Sí" else 0.5 if activos == "Parcial" else 0,
        "controles": 1 if controles == "Sí" else 0.5 if controles == "Parcial" else 0,
        "evidencias": 1 if evidencias == "Sí" else 0.5 if evidencias == "Parcial" else 0,
        "auditoria": 1 if auditoria == "Sí" else 0.5 if auditoria == "Parcial" else 0,
    }

    porcentaje = (sum(puntajes.values()) / len(puntajes)) * 100

    if porcentaje < 30:
        nivel = "Inicial"
        recomendacion = "Formalizar el proyecto SGSI, definir alcance, responsables, inventario de activos y metodología de riesgos."
    elif porcentaje < 60:
        nivel = "En construcción"
        recomendacion = "Consolidar matriz de riesgos, declaración de aplicabilidad, evidencias y responsables de control."
    elif porcentaje < 80:
        nivel = "Gestionado"
        recomendacion = "Fortalecer medición, auditoría interna, revisión por la dirección y tratamiento de hallazgos."
    else:
        nivel = "Avanzado"
        recomendacion = "Preparar auditoría interna, validar eficacia de controles y cerrar brechas documentales."

    return (
        "Diagnóstico inicial del SGSI:\n\n"
        f"- Nivel estimado: {nivel}\n"
        f"- Puntaje referencial: {porcentaje:.2f}%\n"
        f"- Recomendación principal: {recomendacion}\n\n"
        "Lectura por componente:\n"
        f"- Contexto organizacional: {contexto}\n"
        f"- Alcance SGSI: {alcance}\n"
        f"- Gestión de riesgos: {riesgos}\n"
        f"- Inventario de activos: {activos}\n"
        f"- Controles implementados: {controles}\n"
        f"- Evidencias documentadas: {evidencias}\n"
        f"- Auditoría interna o revisión: {auditoria}\n\n"
        "Nota: este diagnóstico es orientativo y no reemplaza una auditoría formal."
    )


def generar_alcance_sgsi(organizacion: str, servicios: str, sedes: str, procesos: str, exclusiones: str) -> str:
    """Genera propuesta inicial de alcance."""
    organizacion = organizacion.strip() or "la organización"
    servicios = servicios.strip() or "los servicios definidos por la organización"
    sedes = sedes.strip() or "las ubicaciones incluidas por la dirección"
    procesos = procesos.strip() or "los procesos críticos y de soporte definidos para el SGSI"
    exclusiones = exclusiones.strip() or "no se identifican exclusiones iniciales"

    return (
        "Propuesta inicial de alcance del SGSI:\n\n"
        f"El Sistema de Gestión de Seguridad de la Información de {organizacion} aplica a la gestión, protección y tratamiento de la información asociada a {servicios}, "
        f"considerando las actividades ejecutadas en {sedes}. El alcance incluye los procesos de {procesos}, así como los activos de información, infraestructura tecnológica, "
        "personas, proveedores, aplicaciones, servicios y controles necesarios para preservar la confidencialidad, integridad y disponibilidad de la información.\n\n"
        f"Exclusiones o límites iniciales identificados: {exclusiones}.\n\n"
        "Recomendaciones para validar el alcance:\n"
        "- Confirmar procesos críticos incluidos.\n"
        "- Identificar partes interesadas internas y externas.\n"
        "- Relacionar activos de información relevantes.\n"
        "- Validar dependencias con proveedores y terceros.\n"
        "- Alinear el alcance con objetivos de negocio, riesgos y requisitos legales."
    )


def buscar_web_interfaz(consulta: str) -> str:
    """Búsqueda web desde la interfaz."""
    try:
        return search_web_duckduckgo(sanitize_message(consulta))
    except Exception as exc:
        return f"No fue posible ejecutar la búsqueda. Detalle: {exc}"


def calcular_cumplimiento_clausulas(
    c4: str,
    c5: str,
    c6: str,
    c7: str,
    c8: str,
    c9: str,
    c10: str,
):
    """Calcula cumplimiento de cláusulas 4 a 10 de ISO/IEC 27001:2022."""
    estados = {
        "Cláusula 4 - Contexto de la organización": c4,
        "Cláusula 5 - Liderazgo": c5,
        "Cláusula 6 - Planificación": c6,
        "Cláusula 7 - Apoyo": c7,
        "Cláusula 8 - Operación": c8,
        "Cláusula 9 - Evaluación del desempeño": c9,
        "Cláusula 10 - Mejora": c10,
    }

    valores = {"Cumple": 1.0, "Parcial": 0.5, "No cumple": 0.0}
    puntajes = [valores[estado] for estado in estados.values()]
    porcentaje = (sum(puntajes) / len(puntajes)) * 100

    if porcentaje < 30:
        nivel = "Bajo"
        recomendacion = "Iniciar formalización del SGSI desde contexto, liderazgo, alcance y planificación."
    elif porcentaje < 60:
        nivel = "Medio bajo"
        recomendacion = "Cerrar brechas documentales y fortalecer planificación, soporte y operación."
    elif porcentaje < 85:
        nivel = "Medio alto"
        recomendacion = "Consolidar evaluación del desempeño, auditoría interna, revisión por la dirección y mejora."
    else:
        nivel = "Alto"
        recomendacion = "Preparar revisión final de evidencias, auditoría interna y tratamiento de no conformidades."

    detalle = "\n".join([f"- {clausula}: {estado}" for clausula, estado in estados.items()])

    resultado = (
        "Resultado de cumplimiento de cláusulas ISO/IEC 27001:2022:\n\n"
        f"{detalle}\n\n"
        f"Porcentaje estimado de cumplimiento: {porcentaje:.2f}%\n"
        f"Nivel interpretativo: {nivel}\n"
        f"Recomendación: {recomendacion}\n\n"
        "Nota: este resultado es una estimación orientativa. La conformidad real requiere evidencia documentada y validación mediante auditoría."
    )

    fig = generar_grafica_clausulas(estados)
    return resultado, fig


def generar_grafica_clausulas(estados: dict[str, str]):
    """Genera gráfica de cumplimiento por cláusula."""
    valores = {"Cumple": 100, "Parcial": 50, "No cumple": 0}
    etiquetas = ["C4", "C5", "C6", "C7", "C8", "C9", "C10"]
    porcentajes = [valores[estado] for estado in estados.values()]

    fig, ax = plt.subplots(figsize=(8, 4))
    barras = ax.bar(etiquetas, porcentajes)
    ax.set_ylim(0, 100)
    ax.set_ylabel("Cumplimiento estimado")
    ax.set_title("Cumplimiento por cláusula ISO/IEC 27001:2022")
    ax.bar_label(barras, labels=[f"{p}%" for p in porcentajes], padding=3)
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    return fig



POLITICAS_ESPECIFICAS = [
    "Política de control de acceso",
    "Política de gestión de activos de información",
    "Política de clasificación y manejo de la información",
    "Política de uso aceptable de activos tecnológicos",
    "Política de seguridad para proveedores",
    "Política de gestión de incidentes de seguridad de la información",
    "Política de copias de respaldo",
    "Política de seguridad en la nube",
    "Política de seguridad física y ambiental",
    "Política de gestión de vulnerabilidades",
    "Política de continuidad de la seguridad de la información",
    "Política de desarrollo seguro",
    "Política de protección de datos personales",
    "Política de seguridad en teletrabajo y acceso remoto",
]


def cambiar_tipo_politica(tipo_politica: str):
    """Muestra u oculta la lista de políticas específicas según el tipo seleccionado."""
    return gr.update(visible=tipo_politica == "Política específica")


def generar_nombre_archivo_politica(nombre_politica: str) -> str:
    """Genera un nombre de archivo seguro para la política."""
    nombre = nombre_politica.lower()
    reemplazos = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
        " ": "_",
        "/": "_",
    }
    for origen, destino in reemplazos.items():
        nombre = nombre.replace(origen, destino)
    nombre = re.sub(r"[^a-z0-9_]+", "", nombre)
    return f"{nombre}.md"


def construir_prompt_politica(tipo_politica: str, politica_especifica: str, organizacion: str, alcance: str) -> str:
    """Construye el prompt para generar una política de ejemplo con IA."""
    organizacion = organizacion.strip() or "la organización"
    alcance = alcance.strip() or "los procesos, activos de información, servicios tecnológicos, colaboradores, proveedores y terceros incluidos en el SGSI"

    if tipo_politica == "Política general":
        nombre_politica = "Política General de Seguridad de la Información"
        enfoque = (
            "Genera una política general de seguridad de la información alineada a ISO/IEC 27001:2022. "
            "Debe servir como documento marco del SGSI."
        )
    else:
        nombre_politica = politica_especifica or "Política específica de seguridad de la información"
        enfoque = (
            f"Genera una política específica denominada '{nombre_politica}', alineada a ISO/IEC 27001:2022 y buenas prácticas de SGSI. "
            "Debe ser un documento de ejemplo aplicable a una organización real."
        )

    return f"""
Actúa como consultor senior en implementación de ISO/IEC 27001:2022.

{enfoque}

Datos base:
- Organización: {organizacion}
- Alcance o contexto: {alcance}

Condiciones:
- Responde en español.
- No copies texto literal de la norma ISO.
- El documento debe ser de ejemplo académico, pero con estructura profesional.
- Usa formato Markdown.
- Incluye secciones claras y completas.

Estructura requerida:
1. Nombre de la política
2. Código del documento
3. Versión
4. Fecha
5. Objetivo
6. Alcance
7. Declaración de política
8. Lineamientos
9. Roles y responsabilidades
10. Cumplimiento
11. Excepciones
12. Evidencias esperadas
13. Relación con ISO/IEC 27001:2022
14. Revisión y mejora
15. Control de cambios

No incluyas emojis ni stickers.
"""


def generar_politica_ia(
    tipo_politica: str,
    politica_especifica: str,
    organizacion: str,
    alcance: str,
):
    """Genera una política de ejemplo con Gemini y devuelve texto y archivo descargable."""
    try:
        if tipo_politica == "Política específica" and not politica_especifica:
            return "Debes seleccionar una política específica.", None

        nombre_politica = (
            "Política General de Seguridad de la Información"
            if tipo_politica == "Política general"
            else politica_especifica
        )

        prompt = construir_prompt_politica(tipo_politica, politica_especifica, organizacion, alcance)
        llm = create_llm()
        contenido = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]).content

        encabezado = (
            f"# {nombre_politica}\n\n"
            "Documento generado como ejemplo académico mediante IA generativa.\n\n"
            "Nota: este documento debe ser revisado, ajustado y aprobado por la organización antes de su uso real.\n\n"
            "---\n\n"
        )

        documento = encabezado + contenido

        filename = generar_nombre_archivo_politica(nombre_politica)
        output_path = Path(tempfile.gettempdir()) / filename
        output_path.write_text(documento, encoding="utf-8")

        return documento, str(output_path)

    except EnvironmentError as exc:
        return f"Configuración pendiente: {exc}", None
    except Exception as exc:
        return f"No fue posible generar la política. Detalle técnico: {exc}", None



def cambiar_herramienta(opcion: str):
    """Muestra únicamente la herramienta seleccionada."""
    return (
        gr.update(visible=opcion == "Chatbot SGSI"),
        gr.update(visible=opcion == "Cálculo de avance del Anexo A"),
        gr.update(visible=opcion == "Diagnóstico inicial del SGSI"),
        gr.update(visible=opcion == "Generador de alcance inicial del SGSI"),
        gr.update(visible=opcion == "Búsqueda web"),
        gr.update(visible=opcion == "Cumplimiento de cláusulas"),
        gr.update(visible=opcion == "Generador de políticas de ejemplo"),
    )



def cerrar_ventana_bienvenida():
    """Oculta la ventana de bienvenida inicial."""
    return gr.update(visible=False)




def extraer_texto_archivo_sgsi(file_path: str) -> str:
    """Extrae texto de archivos TXT, MD, PDF y DOCX para análisis SGSI."""
    if not file_path:
        raise ValueError("Debes cargar un archivo para analizar.")

    path = Path(file_path)
    extension = path.suffix.lower()

    if extension in [".txt", ".md", ".csv"]:
        return path.read_text(encoding="utf-8", errors="ignore")

    if extension == ".pdf":
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages_text = []
            for page in reader.pages[:20]:
                pages_text.append(page.extract_text() or "")
            return "\n".join(pages_text)
        except Exception as exc:
            raise ValueError(
                "No fue posible leer el PDF. Verifica que el archivo tenga texto seleccionable y no sea una imagen escaneada. "
                f"Detalle: {exc}"
            )

    if extension == ".docx":
        try:
            from docx import Document
            document = Document(str(path))
            paragraphs = [paragraph.text for paragraph in document.paragraphs]
            return "\n".join(paragraphs)
        except Exception as exc:
            raise ValueError(
                "No fue posible leer el DOCX. Verifica que el archivo no esté protegido o corrupto. "
                f"Detalle: {exc}"
            )

    raise ValueError("Formato no soportado. Usa archivos .txt, .md, .pdf o .docx.")


def construir_prompt_analisis_documento_sgsi(nombre_archivo: str, contenido: str) -> str:
    """Construye el prompt para analizar un documento del SGSI."""
    contenido_limitado = contenido[:12000]

    return f"""
Actúa como consultor senior y auditor interno de ISO/IEC 27001:2022.

Analiza el siguiente documento del SGSI y entrega una revisión estructurada.

Nombre del archivo: {nombre_archivo}

Contenido extraído:
{contenido_limitado}

Instrucciones:
- Responde en español.
- No inventes información que no esté en el documento.
- Si falta información, indícalo claramente.
- Determina el tipo de documento: política, procedimiento, manual, instructivo, matriz, plan, formato, registro, alcance, declaración de aplicabilidad u otro.
- Evalúa si el documento está bien estructurado para un SGSI alineado a ISO/IEC 27001:2022.
- No copies texto literal de la norma.
- Enfócate en suficiencia documental, claridad, alcance, responsabilidades, cumplimiento, evidencias, control documental y mejora.
- Da ejemplos concretos de qué está bien y qué falta.

Estructura de respuesta obligatoria:
1. Tipo de documento identificado
2. Propósito aparente del documento
3. Evaluación general
4. Aspectos que están bien definidos
5. Aspectos débiles, incompletos o ausentes
6. Recomendaciones de mejora
7. Elementos mínimos que debería incluir este tipo de documento
8. Relación orientativa con ISO/IEC 27001:2022
9. Nivel estimado de madurez documental: Bajo, Medio bajo, Medio, Medio alto o Alto
10. Conclusión ejecutiva
"""


def analizar_documento_sgsi(file_obj):
    """Analiza un documento SGSI cargado por el usuario usando Gemini."""
    try:
        if file_obj is None:
            return "Debes cargar un archivo antes de analizar.", None

        file_path = file_obj.name if hasattr(file_obj, "name") else str(file_obj)
        path = Path(file_path)

        texto = extraer_texto_archivo_sgsi(file_path)
        if not texto or len(texto.strip()) < 100:
            return (
                "El archivo no contiene suficiente texto para realizar un análisis confiable. "
                "Si es un PDF escaneado, conviértelo a texto o usa un archivo DOCX/TXT.",
                None,
            )

        prompt = construir_prompt_analisis_documento_sgsi(path.name, texto)
        llm = create_llm()
        analisis = llm.invoke([SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=prompt)]).content

        documento_resultado = (
            f"# Análisis de documento SGSI\n\n"
            f"Archivo analizado: {path.name}\n\n"
            "Documento generado como apoyo académico mediante IA generativa.\n\n"
            "Nota: el resultado debe ser revisado por el responsable del SGSI antes de tomar decisiones formales.\n\n"
            "---\n\n"
            f"{analisis}"
        )

        output_path = Path(tempfile.gettempdir()) / f"analisis_sgsi_{path.stem}.md"
        output_path.write_text(documento_resultado, encoding="utf-8")

        return analisis, str(output_path)

    except EnvironmentError as exc:
        return f"Configuración pendiente: {exc}", None
    except Exception as exc:
        return f"No fue posible analizar el documento. Detalle técnico: {exc}", None



def mostrar_menu_herramientas():
    """Muestra el menú principal y oculta todos los paneles de herramientas."""
    return (
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_chatbot_sgsi():
    """Abre la herramienta Chatbot SGSI."""
    return (
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_calculo_anexo_a():
    """Abre la herramienta de cálculo del Anexo A."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_diagnostico_sgsi():
    """Abre la herramienta de diagnóstico SGSI."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_generador_alcance():
    """Abre la herramienta de generador de alcance."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_busqueda_web():
    """Abre la herramienta de búsqueda web."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_cumplimiento_clausulas():
    """Abre la herramienta de cumplimiento de cláusulas."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
        gr.update(visible=False),
    )


def abrir_generador_politicas():
    """Abre la herramienta de generador de políticas."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
        gr.update(visible=False),
    )


def abrir_analizador_documentos():
    """Abre la herramienta de análisis de documentos SGSI."""
    return (
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=False),
        gr.update(visible=True),
    )


CSS = """
.gradio-container {
    max-width: 1180px !important;
    margin: auto !important;
    font-family: Arial, sans-serif !important;
}

#main-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 55%, #f97316 100%);
    padding: 28px 34px;
    border-radius: 18px;
    color: white;
    margin-bottom: 22px;
    box-shadow: 0 10px 28px rgba(15, 23, 42, 0.25);
}

#main-header h1 {
    color: white !important;
    margin-bottom: 8px !important;
}

#main-header p {
    color: #f8fafc !important;
    font-size: 16px !important;
}

#guide-box {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-left: 6px solid #f97316;
    padding: 16px 20px;
    border-radius: 14px;
    margin-bottom: 18px;
}

#tool-menu {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 24px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.tool-card {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 18px;
    min-height: 175px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.08);
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}

.tool-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 12px 26px rgba(15, 23, 42, 0.16);
    border-color: #f97316;
}

.tool-card button {
    width: 100% !important;
    min-height: 54px !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    background: #0f172a !important;
    color: white !important;
    border: none !important;
}

.tool-card button:hover {
    background: #f97316 !important;
    color: white !important;
}

.tool-card p {
    font-size: 14px !important;
    line-height: 1.5 !important;
    color: #334155 !important;
}

.section-panel {
    background: #ffffff;
    border: 1px solid #e5e7eb;
    border-radius: 18px;
    padding: 22px;
    box-shadow: 0 8px 24px rgba(15, 23, 42, 0.08);
}

.back-button button {
    max-width: 230px !important;
    border-radius: 12px !important;
    background: #f1f5f9 !important;
    color: #0f172a !important;
    border: 1px solid #cbd5e1 !important;
    font-weight: 600 !important;
}

.back-button button:hover {
    background: #e2e8f0 !important;
}

.primary-note {
    background: #fff7ed;
    border: 1px solid #fed7aa;
    border-radius: 14px;
    padding: 14px 18px;
    color: #7c2d12;
}

textarea, input {
    border-radius: 12px !important;
}
"""



with gr.Blocks(css=CSS, title="Agente ISO 27001") as demo:
    chat_state = gr.State([])

    with gr.Group(visible=True) as ventana_bienvenida:
        gr.Markdown(
            """
# Bienvenido al Agente ISO/IEC 27001:2022 - SGSI

Esta plataforma permite consultar y generar apoyos relacionados con la implementación de un Sistema de Gestión de Seguridad de la Información.

## Herramientas disponibles

### Chatbot SGSI
Permite realizar preguntas sobre ISO/IEC 27001:2022, implementación de un SGSI, diagnóstico, alcance, controles, riesgos, auditoría y mejora continua. Mantiene memoria de la conversación durante la sesión.

### Cálculo de avance del Anexo A
Permite registrar controles cumplidos por tipo: organizacionales, personas, físicos y tecnológicos. Calcula el porcentaje de avance y muestra una gráfica de cumplimiento.

### Diagnóstico inicial del SGSI
Permite seleccionar el estado actual de componentes clave del SGSI y genera un diagnóstico orientativo de madurez.

### Generador de alcance inicial del SGSI
Permite ingresar organización, servicios, sedes, procesos y exclusiones para generar una propuesta inicial de alcance.

### Búsqueda web
Permite consultar información actualizada relacionada con ISO 27001, SGSI, controles, auditorías o buenas prácticas.

### Cumplimiento de cláusulas
Permite evaluar de forma orientativa el cumplimiento de las cláusulas principales de ISO/IEC 27001:2022, desde contexto hasta mejora.

### Generador de políticas de ejemplo
Permite generar con IA una política general de seguridad de la información o políticas específicas de ejemplo alineadas con ISO/IEC 27001:2022. El documento generado se puede descargar.

### Analizador de documentos SGSI
Permite cargar documentos como políticas, procedimientos, manuales, matrices, planes o documentos de alcance del SGSI. La herramienta identifica el tipo de documento, evalúa fortalezas, aspectos incompletos, brechas frente a buenas prácticas de ISO/IEC 27001:2022 y genera recomendaciones de mejora.

## Recomendación de uso

Selecciona una herramienta en el menú principal, completa los campos solicitados y revisa el resultado generado. Los resultados son orientativos y deben ser revisados antes de usarse en un contexto real.
            """
        )
        cerrar_bienvenida = gr.Button("Cerrar guía inicial")
        cerrar_bienvenida.click(
            cerrar_ventana_bienvenida,
            inputs=None,
            outputs=ventana_bienvenida,
        )


    gr.HTML(
        """
<div id="main-header">
    <h1>Agente Conversacional ISO/IEC 27001:2022 - SGSI</h1>
    <p>Aplicación académica para apoyar la implementación de un Sistema de Gestión de Seguridad de la Información, diagnóstico inicial, definición de alcance, cálculo de avance, cumplimiento de cláusulas, generación de políticas y búsqueda de información actualizada.</p>
</div>
<div id="guide-box">
    <strong>Cómo usar la aplicación:</strong> selecciona una herramienta en el menú principal, completa los campos solicitados y revisa el resultado generado. Puedes volver al menú sin perder el historial de la sesión.
</div>
        """
    )

    with gr.Group(visible=True, elem_id="tool-menu") as menu_herramientas:
        gr.Markdown(
            """
## Menú principal de herramientas

Selecciona una opción para abrir únicamente la herramienta que necesitas. El historial y los datos ingresados se conservan mientras no recargues la página.
            """
        )

        with gr.Row():
            with gr.Column(elem_classes=["tool-card"]):
                btn_chatbot = gr.Button("Chatbot SGSI")
                gr.Markdown("Consultas sobre ISO 27001, SGSI, riesgos, controles, alcance, auditoría, evidencias y mejora continua.")

            with gr.Column(elem_classes=["tool-card"]):
                btn_anexo = gr.Button("Cálculo Anexo A")
                gr.Markdown("Calcula el avance por tipo de control: organizacionales, personas, físicos y tecnológicos. Incluye gráfica.")

            with gr.Column(elem_classes=["tool-card"]):
                btn_diagnostico = gr.Button("Diagnóstico SGSI")
                gr.Markdown("Evalúa el estado inicial del SGSI mediante preguntas guiadas y obtiene una lectura de madurez.")

        with gr.Row():
            with gr.Column(elem_classes=["tool-card"]):
                btn_alcance = gr.Button("Alcance SGSI")
                gr.Markdown("Genera una propuesta inicial de alcance considerando organización, servicios, sedes, procesos y exclusiones.")

            with gr.Column(elem_classes=["tool-card"]):
                btn_web = gr.Button("Búsqueda web")
                gr.Markdown("Consulta información actualizada sobre ISO 27001, SGSI, auditorías, controles y buenas prácticas.")

            with gr.Column(elem_classes=["tool-card"]):
                btn_clausulas = gr.Button("Cumplimiento de cláusulas")
                gr.Markdown("Evalúa de forma orientativa el cumplimiento de las cláusulas 4 a 10 de ISO/IEC 27001:2022.")

        with gr.Row():
            with gr.Column(elem_classes=["tool-card"]):
                btn_politicas = gr.Button("Generador de políticas")
                gr.Markdown("Genera políticas generales o específicas de ejemplo con IA y descarga el documento generado.")

            with gr.Column(elem_classes=["tool-card"]):
                btn_documentos = gr.Button("Analizador de documentos SGSI")
                gr.Markdown("Carga una política, procedimiento, manual u otro documento SGSI para identificar fortalezas, brechas y mejoras.")

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_chat:
        with gr.Row(elem_classes=["back-button"]):
            volver_chat = gr.Button("Volver al menú")
        gr.Markdown("## Chatbot SGSI")
        conversacion = gr.Textbox(
            label="Conversación con el agente ISO 27001",
            value="Aún no hay conversación. Escribe una consulta y presiona Enviar.",
            lines=18,
            interactive=False,
        )
        mensaje = gr.Textbox(
            label="Escribe tu consulta",
            placeholder="Ejemplo: ¿Cómo implementar un SGSI ISO 27001:2022?",
            lines=3,
        )
        with gr.Row():
            enviar = gr.Button("Enviar")
            limpiar = gr.Button("Limpiar conversación")

        gr.Examples(
            examples=[
                "Explícame una ruta práctica para implementar un SGSI ISO 27001:2022 en una empresa de servicios.",
                "Hazme preguntas para diagnosticar el estado actual de mi SGSI.",
                "Ayúdame a definir el alcance del SGSI para una nueva línea de negocio de ciberseguridad.",
                "Tengo 35 controles cumplidos del Anexo A. Calcula mi porcentaje de avance.",
                "Busca información actualizada sobre ISO/IEC 27001:2022 y buenas prácticas de SGSI.",
            ],
            inputs=mensaje,
        )

        enviar.click(enviar_chat, inputs=[mensaje, chat_state], outputs=[mensaje, conversacion, chat_state])
        mensaje.submit(enviar_chat, inputs=[mensaje, chat_state], outputs=[mensaje, conversacion, chat_state])
        limpiar.click(limpiar_chat, inputs=None, outputs=[mensaje, conversacion, chat_state])

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_calculo:
        with gr.Row(elem_classes=["back-button"]):
            volver_calculo = gr.Button("Volver al menú")
        gr.Markdown("## Cálculo de avance del Anexo A por tipo de control")
        gr.Markdown(
            "Ingresa cuántos controles se encuentran cumplidos en cada categoría del Anexo A. Totales de referencia: organizacionales 37, personas 8, físicos 14 y tecnológicos 34."
        )

        controles_org = gr.Slider(
            minimum=0,
            maximum=CONTROLES_ORGANIZACIONALES,
            step=1,
            value=0,
            label=f"Controles organizacionales cumplidos de {CONTROLES_ORGANIZACIONALES}",
        )
        controles_per = gr.Slider(
            minimum=0,
            maximum=CONTROLES_PERSONAS,
            step=1,
            value=0,
            label=f"Controles de personas cumplidos de {CONTROLES_PERSONAS}",
        )
        controles_fis = gr.Slider(
            minimum=0,
            maximum=CONTROLES_FISICOS,
            step=1,
            value=0,
            label=f"Controles físicos cumplidos de {CONTROLES_FISICOS}",
        )
        controles_tec = gr.Slider(
            minimum=0,
            maximum=CONTROLES_TECNOLOGICOS,
            step=1,
            value=0,
            label=f"Controles tecnológicos cumplidos de {CONTROLES_TECNOLOGICOS}",
        )

        boton_calcular = gr.Button("Calcular avance")
        salida_calculo = gr.Textbox(label="Resultado del cálculo", lines=16)
        grafica_controles = gr.Plot(label="Gráfica de cumplimiento por tipo de control")

        boton_calcular.click(
            calcular_cumplimiento_por_tipo,
            inputs=[controles_org, controles_per, controles_fis, controles_tec],
            outputs=[salida_calculo, grafica_controles],
        )

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_diagnostico:
        with gr.Row(elem_classes=["back-button"]):
            volver_diagnostico = gr.Button("Volver al menú")
        gr.Markdown("## Diagnóstico inicial del SGSI")
        gr.Markdown(
            "Selecciona el estado actual de cada componente. El resultado es una estimación orientativa para identificar brechas iniciales."
        )
        opciones = ["Sí", "Parcial", "No"]
        contexto = gr.Radio(opciones, label="¿La organización tiene identificado su contexto, partes interesadas y requisitos relevantes?", value="No")
        alcance = gr.Radio(opciones, label="¿Existe un alcance formal del SGSI?", value="No")
        riesgos = gr.Radio(opciones, label="¿Existe una metodología y matriz de riesgos de seguridad de la información?", value="No")
        activos = gr.Radio(opciones, label="¿Existe inventario de activos de información?", value="No")
        controles = gr.Radio(opciones, label="¿Hay controles implementados y responsables asignados?", value="No")
        evidencias = gr.Radio(opciones, label="¿Se conservan evidencias documentadas del SGSI?", value="No")
        auditoria = gr.Radio(opciones, label="¿Se han realizado auditorías internas o revisiones del SGSI?", value="No")
        boton_diagnostico = gr.Button("Generar diagnóstico")
        salida_diagnostico = gr.Textbox(label="Resultado del diagnóstico", lines=13)

        boton_diagnostico.click(
            diagnostico_sgsi,
            inputs=[contexto, alcance, riesgos, activos, controles, evidencias, auditoria],
            outputs=salida_diagnostico,
        )

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_alcance:
        with gr.Row(elem_classes=["back-button"]):
            volver_alcance = gr.Button("Volver al menú")
        gr.Markdown("## Generador de alcance inicial del SGSI")
        gr.Markdown(
            "Completa la información base para generar una propuesta inicial de alcance del SGSI."
        )
        org = gr.Textbox(label="Nombre de la organización", placeholder="Ejemplo: ENERCOM")
        serv = gr.Textbox(label="Servicios o línea de negocio", placeholder="Ejemplo: telecomunicaciones, ciberseguridad, canales satelitales, telemetría")
        sed = gr.Textbox(label="Sedes o ubicaciones incluidas", placeholder="Ejemplo: Bogotá, operación nacional, nube corporativa")
        proc = gr.Textbox(label="Procesos incluidos", placeholder="Ejemplo: TIC, ciberseguridad, operaciones, infraestructura, soporte")
        exc = gr.Textbox(label="Exclusiones o límites conocidos", placeholder="Ejemplo: procesos no incluidos en la primera fase")
        boton_alcance = gr.Button("Generar alcance")
        salida_alcance = gr.Textbox(label="Propuesta de alcance", lines=13)

        boton_alcance.click(
            generar_alcance_sgsi,
            inputs=[org, serv, sed, proc, exc],
            outputs=salida_alcance,
        )

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_web:
        with gr.Row(elem_classes=["back-button"]):
            volver_web = gr.Button("Volver al menú")
        gr.Markdown("## Búsqueda web")
        gr.Markdown(
            "Usa esta herramienta para buscar información actualizada relacionada con ISO 27001, SGSI, controles, auditorías o buenas prácticas."
        )
        consulta_web = gr.Textbox(label="Consulta", placeholder="Ejemplo: ISO 27001 2022 buenas prácticas SGSI")
        boton_web = gr.Button("Buscar")
        salida_web = gr.Textbox(label="Resultados de búsqueda", lines=12)
        boton_web.click(buscar_web_interfaz, inputs=consulta_web, outputs=salida_web)

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_clausulas:
        with gr.Row(elem_classes=["back-button"]):
            volver_clausulas = gr.Button("Volver al menú")
        gr.Markdown("## Cumplimiento de cláusulas ISO/IEC 27001:2022")
        gr.Markdown(
            "Selecciona el estado de cumplimiento para las cláusulas principales del SGSI. Esta herramienta genera un porcentaje orientativo y una gráfica por cláusula."
        )

        opciones_clausulas = ["Cumple", "Parcial", "No cumple"]
        clausula_4 = gr.Radio(opciones_clausulas, label="Cláusula 4 - Contexto de la organización", value="No cumple")
        clausula_5 = gr.Radio(opciones_clausulas, label="Cláusula 5 - Liderazgo", value="No cumple")
        clausula_6 = gr.Radio(opciones_clausulas, label="Cláusula 6 - Planificación", value="No cumple")
        clausula_7 = gr.Radio(opciones_clausulas, label="Cláusula 7 - Apoyo", value="No cumple")
        clausula_8 = gr.Radio(opciones_clausulas, label="Cláusula 8 - Operación", value="No cumple")
        clausula_9 = gr.Radio(opciones_clausulas, label="Cláusula 9 - Evaluación del desempeño", value="No cumple")
        clausula_10 = gr.Radio(opciones_clausulas, label="Cláusula 10 - Mejora", value="No cumple")

        boton_clausulas = gr.Button("Calcular cumplimiento de cláusulas")
        salida_clausulas = gr.Textbox(label="Resultado de cumplimiento de cláusulas", lines=14)
        grafica_clausulas = gr.Plot(label="Gráfica de cumplimiento por cláusula")

        boton_clausulas.click(
            calcular_cumplimiento_clausulas,
            inputs=[
                clausula_4,
                clausula_5,
                clausula_6,
                clausula_7,
                clausula_8,
                clausula_9,
                clausula_10,
            ],
            outputs=[salida_clausulas, grafica_clausulas],
        )

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_politicas:
        with gr.Row(elem_classes=["back-button"]):
            volver_politicas = gr.Button("Volver al menú")
        gr.Markdown("## Generador de políticas de ejemplo")
        gr.Markdown(
            "Esta herramienta genera documentos de política de ejemplo con IA generativa. Selecciona el tipo de política y completa los campos que se habilitan de forma progresiva."
        )

        tipo_politica = gr.Radio(
            ["Política general", "Política específica"],
            label="Paso 1. Selecciona el tipo de política",
            value=None,
        )
        boton_tipo_politica = gr.Button("Continuar")

        with gr.Group(visible=False) as grupo_politica_especifica:
            politica_especifica = gr.Dropdown(
                choices=POLITICAS_ESPECIFICAS,
                label="Paso 2. Selecciona la política específica",
                value=POLITICAS_ESPECIFICAS[0],
            )
            boton_politica_especifica = gr.Button("Continuar con la política seleccionada")

        with gr.Group(visible=False) as grupo_organizacion_politica:
            organizacion_politica = gr.Textbox(
                label="Paso 3. Nombre de la organización",
                placeholder="Ejemplo: ENERCOM",
            )
            boton_organizacion_politica = gr.Button("Continuar con la organización")

        with gr.Group(visible=False) as grupo_alcance_politica:
            alcance_politica = gr.Textbox(
                label="Paso 4. Contexto o alcance de referencia",
                placeholder="Ejemplo: procesos de TIC, ciberseguridad, infraestructura, operaciones y servicios tecnológicos",
                lines=3,
            )
            boton_contexto_politica = gr.Button("Continuar con el contexto")

        with gr.Group(visible=False) as grupo_generar_politica:
            boton_generar_politica = gr.Button("Generar política de ejemplo")
            salida_politica = gr.Textbox(label="Vista previa de la política generada", lines=22)
            archivo_politica = gr.File(label="Descargar política generada")

        def continuar_tipo_politica(tipo):
            """Avanza el flujo según el tipo de política seleccionado."""
            if tipo == "Política general":
                return (
                    gr.update(visible=False),
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                )

            if tipo == "Política específica":
                return (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    gr.update(visible=False),
                    gr.update(visible=False),
                )

            return (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=False),
            )

        def continuar_politica_especifica(politica):
            """Muestra el campo de organización después de escoger la política específica."""
            if politica:
                return gr.update(visible=True)
            return gr.update(visible=False)

        def continuar_organizacion(nombre_organizacion):
            """Muestra el campo de contexto después de escribir la organización."""
            if nombre_organizacion and nombre_organizacion.strip():
                return gr.update(visible=True)
            return gr.update(visible=False)

        def continuar_contexto(contexto_politica):
            """Muestra la generación final después de escribir el contexto."""
            if contexto_politica and contexto_politica.strip():
                return gr.update(visible=True)
            return gr.update(visible=False)

        boton_tipo_politica.click(
            continuar_tipo_politica,
            inputs=tipo_politica,
            outputs=[
                grupo_politica_especifica,
                grupo_organizacion_politica,
                grupo_alcance_politica,
                grupo_generar_politica,
            ],
        )

        boton_politica_especifica.click(
            continuar_politica_especifica,
            inputs=politica_especifica,
            outputs=grupo_organizacion_politica,
        )

        boton_organizacion_politica.click(
            continuar_organizacion,
            inputs=organizacion_politica,
            outputs=grupo_alcance_politica,
        )

        boton_contexto_politica.click(
            continuar_contexto,
            inputs=alcance_politica,
            outputs=grupo_generar_politica,
        )

        boton_generar_politica.click(
            generar_politica_ia,
            inputs=[tipo_politica, politica_especifica, organizacion_politica, alcance_politica],
            outputs=[salida_politica, archivo_politica],
        )

    with gr.Group(visible=False, elem_classes=["section-panel"]) as panel_documentos:
        with gr.Row(elem_classes=["back-button"]):
            volver_documentos = gr.Button("Volver al menú")

        gr.Markdown("## Analizador de documentos SGSI")
        gr.Markdown(
            "Carga un documento del SGSI en formato TXT, MD, PDF o DOCX. La herramienta intentará identificar el tipo de documento y analizará qué aspectos están bien definidos, cuáles están incompletos y qué mejoras se recomiendan."
        )

        archivo_sgsi = gr.File(
            label="Carga el documento SGSI",
            file_types=[".txt", ".md", ".pdf", ".docx"],
        )
        boton_analizar_documento = gr.Button("Analizar documento")
        salida_analisis_documento = gr.Textbox(label="Resultado del análisis", lines=22)
        archivo_analisis_documento = gr.File(label="Descargar análisis generado")

        boton_analizar_documento.click(
            analizar_documento_sgsi,
            inputs=archivo_sgsi,
            outputs=[salida_analisis_documento, archivo_analisis_documento],
        )

    btn_chatbot.click(abrir_chatbot_sgsi, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_anexo.click(abrir_calculo_anexo_a, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_diagnostico.click(abrir_diagnostico_sgsi, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_alcance.click(abrir_generador_alcance, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_web.click(abrir_busqueda_web, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_clausulas.click(abrir_cumplimiento_clausulas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_politicas.click(abrir_generador_politicas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    btn_documentos.click(abrir_analizador_documentos, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])

    volver_chat.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_calculo.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_diagnostico.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_alcance.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_web.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_clausulas.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_politicas.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])
    volver_documentos.click(mostrar_menu_herramientas, inputs=None, outputs=[menu_herramientas, panel_chat, panel_calculo, panel_diagnostico, panel_alcance, panel_web, panel_clausulas, panel_politicas, panel_documentos])

    gr.Markdown(
        """
## Nota de uso

Este asistente tiene fines académicos y orientativos. No reemplaza una auditoría formal, asesoría legal ni la interpretación oficial de una entidad certificadora.
        """
    )


if __name__ == "__main__":
    demo.launch()
