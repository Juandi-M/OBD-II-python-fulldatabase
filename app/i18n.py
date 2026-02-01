from __future__ import annotations

from typing import Dict

LANGUAGES: Dict[str, Dict[str, str]] = {
    "en": {
        "app_title": "OBD-II Scanner",
        "select_language": "Select language",
        "select_brand": "Select vehicle brand",
        "brand_generic": "Generic (all codes)",
        "main_menu": "MAIN MENU",
        "connect": "Connect to vehicle",
        "disconnect": "Disconnect",
        "full_scan": "Full scan",
        "read_codes": "Read trouble codes",
        "live_monitor": "Live telemetry",
        "freeze_frame": "Freeze frame",
        "readiness": "Readiness monitors",
        "clear_codes": "Clear codes",
        "lookup_code": "Lookup code",
        "search_codes": "Search codes",
        "uds_tools": "UDS tools",
        "ai_report": "AI diagnostic report",
        "settings": "Settings",
        "exit": "Exit",
        "status": "Status",
        "connected": "Connected",
        "disconnected": "Disconnected",
        "vehicle": "Vehicle",
        "format": "Format",
        "language": "Language",
        "press_enter": "Press Enter to continue...",
        "cancelled": "Cancelled.",
        "not_connected": "Not connected. Connect first.",
        "searching_adapter": "Searching for OBD adapter...",
        "no_ports": "No USB serial ports found.",
        "trying_port": "Trying {port}...",
        "connected_on": "Connected on {port}",
        "connection_failed": "Failed: {error}",
        "no_vehicle_response": "Could not connect to any vehicle.",
        "report_time": "Report time",
        "protocol": "Protocol",
        "elm_version": "ELM327 version",
        "mil_status": "MIL (Check Engine)",
        "dtc_count": "DTC count",
        "no_codes": "No trouble codes stored",
        "save_log": "Save to log file? (y/n)",
        "monitor_interval": "Monitor interval (0.5 - 10s)",
        "interval_set": "Interval set to {value}s",
        "invalid_number": "Invalid number",
        "invalid_range": "Must be between 0.5 and 10",
        "lookup_prompt": "Enter code (e.g., P0118)",
        "search_prompt": "Search term (e.g., throttle)",
        "no_codes_found": "No codes found",
        "uds_menu": "UDS TOOLS",
        "uds_read_standard": "Read standard DIDs",
        "uds_run_routine": "Run routine by name",
        "uds_write_did": "Write DID (advanced)",
        "not_implemented": "Not implemented yet.",
        "confirm_write": "Type YES to confirm write: ",
    },
    "es": {
        "app_title": "Escáner OBD-II",
        "select_language": "Seleccionar idioma",
        "select_brand": "Seleccionar marca del vehículo",
        "brand_generic": "Genérico (todos los códigos)",
        "main_menu": "MENÚ PRINCIPAL",
        "connect": "Conectar al vehículo",
        "disconnect": "Desconectar",
        "full_scan": "Escaneo completo",
        "read_codes": "Leer códigos",
        "live_monitor": "Telemetría en vivo",
        "freeze_frame": "Freeze frame",
        "readiness": "Monitores de preparación",
        "clear_codes": "Borrar códigos",
        "lookup_code": "Buscar código",
        "search_codes": "Buscar códigos",
        "uds_tools": "Herramientas UDS",
        "ai_report": "Reporte diagnóstico IA",
        "settings": "Configuración",
        "exit": "Salir",
        "status": "Estado",
        "connected": "Conectado",
        "disconnected": "Desconectado",
        "vehicle": "Vehículo",
        "format": "Formato",
        "language": "Idioma",
        "press_enter": "Presiona Enter para continuar...",
        "cancelled": "Cancelado.",
        "not_connected": "No conectado. Conecta primero.",
        "searching_adapter": "Buscando adaptador OBD...",
        "no_ports": "No se encontraron puertos USB.",
        "trying_port": "Probando {port}...",
        "connected_on": "Conectado en {port}",
        "connection_failed": "Falló: {error}",
        "no_vehicle_response": "No se pudo conectar al vehículo.",
        "report_time": "Hora del reporte",
        "protocol": "Protocolo",
        "elm_version": "Versión ELM327",
        "mil_status": "MIL (Check Engine)",
        "dtc_count": "Cantidad DTC",
        "no_codes": "No hay códigos almacenados",
        "save_log": "¿Guardar en archivo de log? (y/n)",
        "monitor_interval": "Intervalo de monitoreo (0.5 - 10s)",
        "interval_set": "Intervalo establecido a {value}s",
        "invalid_number": "Número inválido",
        "invalid_range": "Debe estar entre 0.5 y 10",
        "lookup_prompt": "Ingrese código (ej., P0118)",
        "search_prompt": "Buscar término (ej., acelerador)",
        "no_codes_found": "No se encontraron códigos",
        "uds_menu": "HERRAMIENTAS UDS",
        "uds_read_standard": "Leer DIDs estándar",
        "uds_run_routine": "Ejecutar rutina por nombre",
        "uds_write_did": "Escribir DID (avanzado)",
        "not_implemented": "Aún no implementado.",
        "confirm_write": "Escribe YES para confirmar: ",
    },
}

_current_language = "en"


def set_language(code: str) -> None:
    global _current_language
    if code in LANGUAGES:
        _current_language = code


def get_language() -> str:
    return _current_language


def get_available_languages() -> Dict[str, str]:
    return {"en": "English", "es": "Español"}


def t(key: str, **kwargs: str) -> str:
    text = LANGUAGES.get(_current_language, LANGUAGES["en"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text
