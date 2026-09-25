from __future__ import annotations

from typing import Any

VERSION_NOTES: dict[str, dict[str, Any]] = {
    "1.6.4": {
        "title": "Correções de Mensagens e Replay",
        "items": [
            "Corrigido o envio de mensagens pelo botão Enviar e pela tecla Enter.",
            "Corrigido o filtro por origem na aba Mensagens.",
            "Replay volta a mostrar os pacotes trafegando entre os nós, com rastro visual.",
            "Estações móveis continuam deixando tracklog progressivo durante o replay.",
            "Incluído teste de regressão para evitar replay apenas com highlight das estações.",
            "Release somente Windows x64 Portable.",
        ],
    },
    "1.6.3": {
        "title": "Replay móvel e seleção rápida de período",
        "items": [
            "Seleção rápida do replay: 1 h, 12 h, 24 h, 7 dias ou todo o histórico.",
            "Removidos os campos manuais De/Até e compactada a área de período.",
            "Estações móveis agora se deslocam durante o replay e deixam o tracklog progressivamente.",
            "Build desta versão restrito ao Windows x64, sem geração de PDF.",
        ],
    },
    "1.6.2": {
        "title": "Replay da Rede e melhorias de estabilidade",
        "items": [
            "Replay da Rede com linha do tempo, seek e velocidades de 0,25x a 20x.",
            "Controles de animação movidos para a parte inferior do Mapa.",
            "Som e animação de atividade limitados às estações visíveis no enquadramento atual.",
            "Indicador RX/TX de atividade na barra superior.",
            "Legenda do Mapa sincronizada com cores e espessuras configuradas.",
            "Correção da espessura da topologia e salvamento centralizado no rodapé da Configuração.",
            "Auto-update removido: o cliente apenas informa quando há uma nova versão.",
            "Verificação de versão com timeout e recuperação automática após falhas.",
            "Botão Ver logs no popup da estação.",
        ],
    },
}


def notes_for(version: str) -> dict[str, Any]:
    data = VERSION_NOTES.get(str(version or "").strip(), {})
    return {
        "version": str(version or "").strip(),
        "title": str(data.get("title") or ""),
        "items": list(data.get("items") or []),
    }
