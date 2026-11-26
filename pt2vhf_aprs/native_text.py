"""v2.0.7: textos nativos (bandeja, caixas de diálogo do Windows) no idioma do app.

Antes o menu da bandeja e o "Deseja realmente sair?" saíam sempre em português, mesmo com
o app em outro idioma. O idioma segue a Configuração (ou o do SO, se o usuário não escolheu);
texto sem tradução cai no inglês, nunca no português.
"""
from __future__ import annotations

TEXTS: dict[str, dict[str, str]] = {
    "tray_open": {
        "pt-BR": "Abrir PT2VHF APRS Client", "en": "Open PT2VHF APRS Client", "es": "Abrir PT2VHF APRS Client",
        "fr": "Ouvrir PT2VHF APRS Client", "de-DE": "PT2VHF APRS Client öffnen", "it-IT": "Apri PT2VHF APRS Client",
        "ja-JP": "PT2VHF APRS Client を開く", "pl-PL": "Otwórz PT2VHF APRS Client", "nl-NL": "PT2VHF APRS Client openen",
        "zh-CN": "打开 PT2VHF APRS Client", "th-TH": "เปิด PT2VHF APRS Client",
    },
    "tray_connect": {
        "pt-BR": "Conectar ao APRS-IS", "en": "Connect to APRS-IS", "es": "Conectar a APRS-IS",
        "fr": "Se connecter à APRS-IS", "de-DE": "Mit APRS-IS verbinden", "it-IT": "Connetti ad APRS-IS",
        "ja-JP": "APRS-IS に接続", "pl-PL": "Połącz z APRS-IS", "nl-NL": "Verbinden met APRS-IS",
        "zh-CN": "连接 APRS-IS", "th-TH": "เชื่อมต่อ APRS-IS",
    },
    "tray_disconnect": {
        "pt-BR": "Desconectar do APRS-IS", "en": "Disconnect from APRS-IS", "es": "Desconectar de APRS-IS",
        "fr": "Se déconnecter d’APRS-IS", "de-DE": "Von APRS-IS trennen", "it-IT": "Disconnetti da APRS-IS",
        "ja-JP": "APRS-IS から切断", "pl-PL": "Rozłącz z APRS-IS", "nl-NL": "Verbinding met APRS-IS verbreken",
        "zh-CN": "断开 APRS-IS", "th-TH": "ตัดการเชื่อมต่อ APRS-IS",
    },
    "tray_data_folder": {
        "pt-BR": "Abrir pasta de dados", "en": "Open data folder", "es": "Abrir carpeta de datos",
        "fr": "Ouvrir le dossier des données", "de-DE": "Datenordner öffnen", "it-IT": "Apri cartella dati",
        "ja-JP": "データフォルダーを開く", "pl-PL": "Otwórz folder danych", "nl-NL": "Gegevensmap openen",
        "zh-CN": "打开数据文件夹", "th-TH": "เปิดโฟลเดอร์ข้อมูล",
    },
    "tray_exit": {
        "pt-BR": "Sair", "en": "Exit", "es": "Salir", "fr": "Quitter", "de-DE": "Beenden", "it-IT": "Esci",
        "ja-JP": "終了", "pl-PL": "Zakończ", "nl-NL": "Afsluiten", "zh-CN": "退出", "th-TH": "ออก",
    },
    "confirm_exit": {
        "pt-BR": "Deseja realmente sair do PT2VHF APRS Client?",
        "en": "Do you really want to exit PT2VHF APRS Client?",
        "es": "¿Realmente desea salir de PT2VHF APRS Client?",
        "fr": "Voulez-vous vraiment quitter PT2VHF APRS Client ?",
        "de-DE": "Möchten Sie PT2VHF APRS Client wirklich beenden?",
        "it-IT": "Vuoi davvero uscire da PT2VHF APRS Client?",
        "ja-JP": "PT2VHF APRS Client を終了しますか？",
        "pl-PL": "Czy na pewno chcesz zamknąć PT2VHF APRS Client?",
        "nl-NL": "Wil je PT2VHF APRS Client echt afsluiten?",
        "zh-CN": "确定要退出 PT2VHF APRS Client 吗？",
        "th-TH": "ต้องการออกจาก PT2VHF APRS Client จริงหรือไม่?",
    },
    "details": {
        "pt-BR": "Detalhes", "en": "Details", "es": "Detalles", "fr": "Détails", "de-DE": "Details",
        "it-IT": "Dettagli", "ja-JP": "詳細", "pl-PL": "Szczegóły", "nl-NL": "Details", "zh-CN": "详细信息",
        "th-TH": "รายละเอียด",
    },
    "window_failed": {
        "pt-BR": "Não foi possível iniciar a janela integrada do PT2VHF APRS Client.",
        "en": "The PT2VHF APRS Client window could not be started.",
    },
    "window_failed_browser": {
        "pt-BR": "A interface será aberta no navegador padrão.",
        "en": "The interface will open in the default browser.",
    },
    "window_failed_legacy": {
        "pt-BR": "Windows 7 Legacy permanece em modo desktop; o navegador não será aberto automaticamente.",
        "en": "Windows 7 Legacy stays in desktop mode; the browser will not be opened automatically.",
    },
    "legacy_no_browser": {
        "pt-BR": "O Windows 7 Legacy não encontrou Google Chrome/Chromium/Brave compatível para a janela dedicada.\n\n"
                 "A interface será aberta no navegador padrão, mantendo o PT2VHF APRS Client ativo na bandeja.",
        "en": "Windows 7 Legacy did not find a compatible Google Chrome/Chromium/Brave for the app window.\n\n"
              "The interface will open in the default browser, and PT2VHF APRS Client stays active in the tray.",
    },
    "legacy_shell_failed": {
        "pt-BR": "Não foi possível iniciar a janela dedicada do Windows 7 Legacy.\n\n"
                 "A interface será aberta no navegador padrão e o backend continuará ativo.",
        "en": "The Windows 7 Legacy app window could not be started.\n\n"
              "The interface will open in the default browser and the backend keeps running.",
    },
    "port_failed": {
        "pt-BR": "Não foi possível reservar uma porta local para o PT2VHF APRS Client.",
        "en": "Could not reserve a local port for PT2VHF APRS Client.",
    },
}


def current_language() -> str:
    """Idioma em uso pelo app (Configuração ou SO); inglês se não der para ler."""
    try:
        from . import database as db
        return str(db.get_config().get("language") or "en")
    except Exception:
        try:
            from . import os_language
            return os_language.system_language()
        except Exception:
            return "en"


def text(key: str, language: str | None = None) -> str:
    entry = TEXTS.get(key) or {}
    lang = language or current_language()
    return entry.get(lang) or entry.get("en") or key
