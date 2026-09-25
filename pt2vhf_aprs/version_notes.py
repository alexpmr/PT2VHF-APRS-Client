from __future__ import annotations

from typing import Any

VERSION_NOTES: dict[str, dict[str, Any]] = {
    "1.6.8": {
        "title": "Fila de transmissão e estabilidade",
        "items": [
            "Envio de mensagens passa a usar fila assíncrona no backend, evitando travamento da interface.",
            "Cliques repetidos na mesma mensagem em poucos segundos são deduplicados.",
            "O botão Enviar fica bloqueado enquanto a solicitação é registrada.",
            "Falhas de socket deixam de prender a requisição web e passam a acionar recuperação da conexão.",
            "Ao encerrar, a aplicação cancela filas pendentes e executa manutenção leve do SQLite.",
            "A logo APRS oficial passa a ser referenciada diretamente no template.",
            "Release para Windows x64 e Linux x86_64, sem macOS e sem PDF.",
        ],
    },
    "1.6.7": {
        "title": "Primeira release Linux atualizada",
        "items": [
            "Build Linux x86_64 com pacote TAR.GZ, AppImage e DEB.",
            "Aplicadas no Linux as correções acumuladas das versões 1.6.4 a 1.6.6.",
            "A logo APRS oficial é usada na interface e no ícone dos pacotes Linux.",
            "Incluídos testes smoke em Ubuntu 22.04 e 24.04.",
            "Release somente Linux, sem Windows, macOS ou PDF.",
        ],
    },
    "1.6.6": {
        "title": "Configuração, manutenção e identidade visual",
        "items": [
            "Corrigido o salvamento da aba Configuração e o fluxo Salvar e sair.",
            "Seletor de idioma passa a exibir bandeiras reais do Brasil e dos EUA no Windows.",
            "Adicionado Limpar tudo com destaque e confirmação dupla, preservando configuração e favoritos.",
            "A logo APRS fornecida passa a ser usada na aplicação e como base do ícone Windows.",
            "Release somente Windows x64, sem PDF.",
        ],
    },
    "1.6.5": {
        "title": "Manutenção e notificações",
        "items": [
            "Novo bloco Manutenção centraliza as ações de limpeza do banco.",
            "Notificações do navegador agora têm volume, seleção de som e botão de teste.",
            "A barra de histórico/replay do Mapa fica oculta por padrão e pode ser aberta pelo cabeçalho.",
            "Corrigido o envio para destinatários com sufixo alfanumérico, incluindo PY2OFU-D.",
            "Release somente Windows x64, sem PDF.",
        ],
    },
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
