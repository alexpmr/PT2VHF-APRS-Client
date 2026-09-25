from __future__ import annotations

from typing import Any

VERSION_NOTES: dict[str, dict[str, Any]] = {
    "1.6.16": {
        "title": "Correção da consulta de topologia que saturava o backend",
        "items": [
            "Remove UPPER() dos JOINs de topologia para permitir lookup indexado pelo callsign.",
            "Impede consultas /api/topology concorrentes com coalescência/cache curto.",
            "Adiciona limite interno de tempo à consulta para que nenhum worker fique preso por minutos.",
            "Adiciona single-flight ao carregamento de topologia no frontend.",
            "Inclui índices auxiliares de topologia para bancos existentes e novos.",
            "Release de teste somente Windows x64 Portable, sem instalador e sem documentação.",
        ],
    },
    "1.6.15": {
        "title": "Correção do fan-out do Mapa e medidores de recursos",
        "items": [
            "Remove o refresh completo do mapa disparado por cada estação sem marcador.",
            "Impede execuções simultâneas de loadMapData com trava single-flight.",
            "Limita animações ao vivo e deduplica indicadores visuais por estação em cada ciclo.",
            "Adiciona indicadores de CPU e RAM em tempo real na barra superior.",
            "CPU/RAM somam o processo principal e processos filhos do WebView2.",
            "Release de teste somente Windows x64 Portable, sem instalador e sem documentação.",
        ],
    },
    "1.6.14": {
        "title": "RX em transação única",
        "items": [
            "Consolida o processamento de cada pacote APRS recebido em uma única transação SQLite.",
            "Log RX, histórico de pacotes, topologia e estação/track deixam de abrir conexões e commits independentes por pacote.",
            "Mantém o housekeeping em lotes introduzido na v1.6.13.",
            "Registra transações RX lentas no diagnóstico para identificar gargalos residuais.",
            "Objetivo principal: reduzir CPU, contenção do banco e starvation das rotas HTTP.",
            "Release de teste somente Windows x64 Portable, sem instalador e sem documentação.",
        ],
    },
    "1.6.13": {
        "title": "Redução de CPU e housekeeping SQLite",
        "items": [
            "Remove as limpezas de tabelas grandes executadas a cada pacote APRS recebido.",
            "Housekeeping de packets, aprs_log e topology_events passa a ocorrer em lotes a cada 1.000 registros ou 5 minutos.",
            "A remoção do histórico excedente passa a usar corte por chave primária, evitando varreduras completas repetidas.",
            "Reduz a frequência de pollings pesados e atualiza mapa, mensagens, estações e log principalmente quando a aba correspondente está ativa.",
            "Mantém a instrumentação diagnóstica da v1.6.12 para acompanhar eventuais travamentos residuais.",
            "Release de teste somente Windows x64 Portable, sem instalador e sem documentação.",
        ],
    },
    "1.6.12": {
        "title": "Portable de diagnóstico do travamento",
        "items": [
            "Instrumenta cada request do backend local com endpoint, thread, duração e quantidade de requests ativos.",
            "Watchdog interno testa o servidor local e gera dump de todas as threads após falhas consecutivas ou saturação.",
            "Operações SQLite acima de 750 ms e erros de banco passam a ser registrados no diagnóstico.",
            "O log persistente fica na pasta de dados como diagnostics.log e pode ser baixado por /api/diagnostics/log.",
            "A mensagem de timeout informa qual endpoint deixou de responder.",
            "Release de diagnóstico somente Windows x64 Portable, sem instalador e sem documentação.",
        ],
    },
    "1.6.11": {
        "title": "Teste de estabilidade do Portable",
        "items": [
            "Remove PRAGMA journal_mode=WAL do caminho de cada request e deixa a configuração WAL somente na inicialização.",
            "Mensagens multipartes passam a ser registradas em uma única transação SQLite.",
            "Pollings da interface deixam de se sobrepor quando uma chamada demora.",
            "Chamadas ao backend local ganham timeout de 10 segundos em vez de permanecer indefinidamente presas.",
            "Após enfileirar uma mensagem, o botão Enviar é liberado sem aguardar a recarga da lista.",
            "Release de teste somente Windows x64 Portable, sem instalador e sem documentação.",
        ],
    },
    "1.6.10": {
        "title": "Release completa multiplataforma",
        "items": [
            "Consolida a correção do envio de mensagens com fila assíncrona e deduplicação.",
            "Mantém a rotina segura de encerramento e manutenção leve do SQLite.",
            "Corrige definitivamente o pipeline do ícone Windows usando a identidade visual estável.",
            "Aplica todos os patches acumulados também aos builds macOS e à geração do manual.",
            "Publica Windows Setup e Portable, Linux TAR.GZ/AppImage/DEB, macOS ARM64/Intel e Manual PDF.",
        ],
    },
    "1.6.9": {
        "title": "Estabilidade de mensagens e build",
        "items": [
            "Mantidas as correções de fila assíncrona e deduplicação no envio de mensagens.",
            "Mantida a rotina de encerramento e manutenção leve do SQLite.",
            "Corrigido o teste legado de identidade visual que impedia os builds Windows e Linux.",
            "O build usa temporariamente a logo estável anterior até a logo oficial ser reintegrada com arquivo validado.",
            "Release para Windows x64 e Linux x86_64, sem macOS e sem PDF.",
        ],
    },
    "1.6.8": {
        "title": "Fila de transmissão e estabilidade",
        "items": [
            "Envio de mensagens passa a usar fila assíncrona no backend, evitando travamento da interface.",
            "Cliques repetidos na mesma mensagem em poucos segundos são deduplicados.",
            "O botão Enviar fica bloqueado enquanto a solicitação é registrada.",
            "Falhas de socket deixam de prender a requisição web e passam a acionar recuperação da conexão.",
            "Ao encerrar, a aplicação cancela filas pendentes e executa manutenção leve do SQLite.",
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
