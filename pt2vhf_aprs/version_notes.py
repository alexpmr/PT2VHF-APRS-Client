from __future__ import annotations

from typing import Any

VERSION_NOTES: dict[str, dict[str, Any]] = {
    "1.7.6": {
        "title": "Atualizador Windows reforçado, KML com Salvar como e novos rankings",
        "items": [
            "No Windows, a atualização automática passa a usar helper CMD nativo como caminho principal, reduzindo falhas de inicialização do PowerShell.",
            "O KML agora pergunta onde salvar o arquivo no desktop e usa seletor nativo de arquivo quando disponível.",
            "Os botões Histórico e Exportar KML foram movidos para a mesma barra contextual do Mapa, junto de Estações, Tracklog e Topologia.",
            "A aba Estatísticas ganha o ranking Estações que mais interagiram, considerando somente conversas APRS manuais e excluindo beacons, telemetria, ACK/REJ, queries, respostas automáticas, boletins e retries.",
            "A exportação KML continua com Estações, Posições, Tracklogs e Topologia selecionados por padrão e período configurável.",
            "Adicionados testes de regressão para o helper Windows, Salvar como do KML, posição dos controles no Mapa e ranking de conversas manuais.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.7.5": {
        "title": "Exportação KML, validação de posições e novas análises da rede",
        "items": [
            "Adicionada exportação KML pela barra superior, com Estações, Posições, Tracklogs e Topologia selecionados por padrão e período configurável.",
            "Posições 0,0, inválidas, saltos implausíveis e coordenadas incompatíveis com um iGate RF conhecido deixam de contaminar mapa, tracklogs, topologia, replay e exportações.",
            "A aba Estatísticas ganha os blocos Estações com problemas e Possíveis melhorias, com evidência/recorrência e atalhos para Mapa e Logs.",
            "Indicativos dos rankings Digipeaters mais utilizados e iGates mais ativos passam a abrir diretamente a estação no Mapa.",
            "Conversas da aba Mensagens podem ser ordenadas por Remetente ou Data, em ordem crescente/decrescente, e a ação Apagar todas remove somente o histórico local de mensagens após confirmação.",
            "Adicionados testes de regressão para validação geográfica, KML, navegação das Estatísticas e controles de Mensagens.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.7.4": {
        "title": "Erros do atualizador agora ficam visíveis no próprio modal",
        "items": [
            "Corrigida a camada visual das mensagens do atualizador: o toast agora fica acima do modal e não é mais desfocado pelo overlay.",
            "Falhas de download/instalação passam a ser exibidas também dentro do modal de atualização, em uma caixa destacada e legível.",
            "O estado do modal distingue claramente preparação, sucesso e erro, mantendo os botões disponíveis após uma falha.",
            "A mensagem técnica do backend permanece visível para diagnóstico, sem depender de um aviso temporário.",
            "Adicionados testes de regressão para z-index, mensagem inline e reativação dos controles após erro.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.7.3": {
        "title": "Atualizador reparado e ranking de clientes consolidado por família",
        "items": [
            "Corrigida a geração dos scripts auxiliares do atualizador: as quebras de linha agora são gravadas corretamente em PowerShell e Bash.",
            "O botão Baixar e instalar mostra feedback imediato, dispara diretamente o fluxo de atualização e registra as etapas no diagnóstico.",
            "O updater registra solicitação, asset, URL, caminho temporário, tamanho, SHA-256 e falhas para facilitar diagnóstico.",
            "Estatísticas passa a agrupar versões semânticas do mesmo cliente em uma única família, por exemplo Dire Wolf 1.7, 1.8 e 1.9 em Dire Wolf.",
            "Aliases, nomes originais e TOCALLs continuam preservados internamente para diagnóstico, enquanto a interface mostra o nome canônico consolidado.",
            "Adicionados testes de regressão que geram os helpers reais e validam a consolidação por família.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.7.2": {
        "title": "Mapa mais compacto, tempo relativo e estatísticas consolidadas",
        "items": [
            "Estações, Tracklog e Topologia observada passam para a mesma linha contextual do botão Histórico, liberando mais área vertical para o mapa.",
            "O popup da estação mostra o tempo decorrido desde a última recepção e o atualiza enquanto permanece aberto.",
            "O tempo relativo respeita Português, English, Español e Français, com formatos compactos para minutos, horas e dias.",
            "O ranking de software/dispositivos consolida TOCALLs diferentes que resolvem para o mesmo nome amigável, evitando linhas duplicadas.",
            "Os identificadores técnicos continuam preservados internamente e o destaque do PT2VHF APRS Client é mantido após a consolidação.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.7.1": {
        "title": "Atualizador corrigido, Mapa refinado e nova aba Sobre",
        "items": [
            "O atualizador só encerra a aplicação depois que o helper externo confirma que iniciou; falhas deixam a aplicação aberta.",
            "O indicador de nova versão pulsa e o modal permanece aberto durante o fluxo de atualização.",
            "Tracklogs rejeitam saltos irreais de coordenadas e quebram linhas históricas em relocações/extremos.",
            "Estações, Tracklog e Topologia ganham controles independentes de visibilidade e período; Atividade é removido.",
            "Histórico/Replay passa a aparecer abaixo das abas somente quando o Mapa está ativo.",
            "Mensagens sinaliza novas mensagens diretas na aba e Estações mais ativas ganha atalho clicável para mensagem rápida.",
            "Nova aba Sobre reúne autor, contatos, tiny.cc/aprs e divulgação manual por Announcement APRS.",
            "Revisadas e ampliadas as traduções PT/EN/ES/FR.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.7": {
        "title": "Nova linha 1.7: mensagens seguras, idiomas e interface refinada",
        "items": [
            "Os controles Atividade e Topologia observada ficam acima do mapa, sem cobrir o canvas.",
            "A animação de tráfego ao vivo vem ativada por padrão em novas instalações e pode ser desligada em Configurações.",
            "A conversa em foco e o campo Destinatário ficam sincronizados para reduzir o risco de envio à estação errada.",
            "Os filtros da aba Mensagens ficam mais compactos e com rótulos em uma única linha.",
            "A interface passa a oferecer Português, English, Español e Français.",
            "Estatísticas mostra somente nomes amigáveis dos aplicativos e ganha fonte maior com controle de tamanho em Configurações.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.6.24": {
        "title": "Logo APRS oficial única e consolidação visual",
        "items": [
            "A logo APRS enviada pelo projeto passa a ser a fonte visual única da aplicação.",
            "Cabeçalho, favicon, bandeja do Windows, ícones Windows/Linux/macOS e capa do Manual PDF passam a derivar do mesmo arquivo PNG oficial.",
            "O ícone do macOS deixa de ser desenhado por código e passa a ser gerado diretamente da logo oficial.",
            "As notas internas da v1.6.23 são incorporadas para manter o histórico de novidades coerente.",
            "O backlog é consolidado, removendo itens já concluídos e mantendo abertas somente as validações e melhorias ainda pendentes.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.6.23": {
        "title": "Identidade visual, filtro de atividade e legenda do mapa",
        "items": [
            "Padroniza a identidade visual da aplicação nos artefatos e documentação existentes.",
            "Adiciona no Mapa filtro por última interação: Tudo, menos de 2 h, 2 a 24 h e mais de 24 h.",
            "Marcadores, tracklogs e enlaces de estações conhecidas respeitam o filtro de atividade.",
            "A legenda do Mapa pode ser minimizada ou expandida e preserva a preferência local.",
            "Corrige o rate-limit para permitir corretamente a primeira resposta automática a query APRS após a inicialização.",
            "Release completa multiplataforma.",
        ],
    },
    "1.6.22": {
        "title": "Atualização integrada por plataforma",
        "items": [
            "Clicar em Nova versão passa a baixar e instalar automaticamente o pacote correto da plataforma e arquitetura em uso.",
            "O download é feito somente da Release oficial e é validado por tamanho e SHA-256 antes da instalação.",
            "Um updater auxiliar encerra a instância anterior, força somente o PID correto após timeout quando necessário, instala/substitui e abre a nova versão.",
            "Windows Portable mantém backup para rollback; Windows Setup executa o instalador correspondente.",
            "Linux AppImage/DEB/TAR.GZ e macOS DMG recebem fluxos próprios de atualização e relançamento.",
            "Um lock com PID impede atualizações concorrentes entre instâncias e se recupera de locks obsoletos após crash.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.6.21": {
        "title": "Estatísticas da rede e ranking de estações ativas",
        "items": [
            "A aba Análise passa a se chamar Estatísticas em toda a interface e documentação.",
            "A nova seção Estações mais ativas ordena o tráfego útil por indicativo no período selecionado.",
            "Pacotes de telemetria são excluídos do ranking para evitar distorção por transmissões automáticas frequentes.",
            "iGates e digipeaters também são excluídos do ranking principal e permanecem nas estatísticas dedicadas.",
            "O ranking exibe posição, indicativo, pacotes válidos e percentual sobre o total considerado.",
            "Release de teste somente Windows x64 Portable.",
        ],
    },
    "1.6.20": {
        "title": "Nomes amigáveis APRS, ranking do cliente, idioma compacto e RF correto",
        "items": [
            "A aba Análise passa a resolver TOCALLs para nomes amigáveis de software/dispositivo usando um snapshot local da base APRS Device Identification.",
            "O ranking mostra os Top 20 e, se o PT2VHF APRS Client estiver fora do corte, acrescenta sua posição real, quantidade e percentual em uma linha destacada.",
            "O PT2VHF APRS Client passa a transmitir o identificador experimental APZVHF para permitir medir sua adoção sem depender do TOCALL genérico APRS.",
            "O seletor de idioma no topo passa a mostrar somente o idioma atual e abre um menu com Português/Brasil e English/Inglaterra.",
            "Corrige enlaces qAR/qAO até o IGate: quando o caminho é RF, a linha permanece contínua e o IGate fica apenas como metadado do enlace.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.6.19": {
        "title": "Análise de clientes, respostas de queries e idioma no topo",
        "items": [
            "A aba Análise passa a mostrar clientes/versões APRS detectados pelo TOCALL do último pacote de cada estação, em ordem do mais usado para o menos usado.",
            "O popup da estação passa a exibir uma área clara e persistente com o resultado da última query, incluindo status, RTT, resposta e caminho do Trace quando disponível.",
            "Adiciona histórico de queries por estação diretamente no popup do Mapa.",
            "Ao reabrir o popup, a última query registrada daquela estação é recuperada do banco local.",
            "Restaura o controle rápido de idioma no topo, com Português/Brasil e English/Inglaterra, preservando a escolha do usuário.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.6.18": {
        "title": "Queries APRS, Ping/ACK e Trace no mapa",
        "items": [
            "Adiciona consultas APRS direcionadas de posição, status, estações ouvidas e trace diretamente pelo popup do mapa.",
            "Adiciona Ping/ACK com medição de RTT e timeout.",
            "O Trace recebido é interpretado e desenhado no mapa somente nos hops com posição conhecida, sem inventar localização para nós desconhecidos.",
            "Adiciona histórico local das queries, respostas e tempos de resposta.",
            "Prepara o cliente para responder automaticamente a queries APRS de posição, status e trace, com opção em Configurações e rate-limit.",
            "Release completa para Windows, Linux, macOS e Manual PDF.",
        ],
    },
    "1.6.17": {
        "title": "Release completa multiplataforma com correções de estabilidade",
        "items": [
            "Consolida as correções de CPU e travamento introduzidas nas versões 1.6.13 a 1.6.16.",
            "Mantém o pipeline RX otimizado, o refresh de mapa single-flight e a consulta de topologia indexada com proteção de timeout.",
            "Mantém os indicadores de CPU e RAM em tempo real na barra superior para diagnóstico operacional.",
            "Publica Windows x64 Setup + Portable, Linux x86_64 TAR.GZ/AppImage/DEB, macOS ARM64/Intel e Manual PDF versionado.",
            "O manual é regenerado com screenshots da própria versão e validado no workflow antes da publicação.",
        ],
    },
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
