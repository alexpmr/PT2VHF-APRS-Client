# Changelog

## v0.2.8 — 2026-09-23

- Release de manutenção baseada na v0.2.7, sem alterações no formato do banco local.
- Mantidos os ajustes da tela de Mensagens, incluindo **Lido** em verde, lista com rolagem própria e área de envio adaptada à altura da janela.
- Distribuição mantida apenas em **Instalador EXE** e **Portable EXE**.
- As descrições dos downloads permanecem em português na página da Release.
- Esta versão continua **sem assinatura Authenticode** enquanto o projeto aguarda a ativação do SignPath Foundation; portanto, o Smart App Control do Windows ainda pode bloquear os executáveis.

## v0.2.7 — 2026-09-23

- Política de privacidade atualizada para documentar a consulta automática ao GitHub usada pelo verificador de novas versões; nenhum indicativo, posição, mensagem ou passcode é enviado nessa consulta.
- Na aba **Mensagens**, o status `ACK` passa a ser exibido como **Lido** em verde, mantendo `ACK` apenas internamente no protocolo APRS.
- Ajustada a aba **Mensagens** para caber integralmente na altura disponível da janela.
- A lista de mensagens passa a usar automaticamente o espaço restante e possui **barra de rolagem própria**.
- A área de composição fica presa ao rodapé da aba e se adapta à altura disponível.
- O botão **Enviar** foi reposicionado para permanecer sempre visível em telas largas.
- Em janelas de menor altura, o compositor reduz automaticamente sua altura sem empurrar controles para fora da tela.
- O arquivo **Portable ZIP** deixa de ser gerado e publicado.
- As próximas versões passam a oferecer apenas **Instalador EXE** e **Portable EXE** como opções para usuários Windows.
- A página de cada Release passa a apresentar em **português** a descrição dos arquivos disponíveis.
- O instalador é identificado como a opção recomendada para a maioria dos usuários.
- O Portable EXE é descrito como versão em arquivo único, sem necessidade de instalação.
- SBOM e inventário de licenças continuam disponíveis como arquivos técnicos da Release.

## v0.2.6 — 2026-09-23

- Botão **Limpar mensagens** na aba Mensagens, com confirmação antes de apagar todo o histórico local de mensagens e boletins.
- Botão **Limpar estações** na aba Estações, removendo estações e tracklogs locais com confirmação.
- A limpeza de mensagens não afeta estações; a limpeza de estações não afeta mensagens, configurações ou Log APRS-IS.
- O mapa remove imediatamente marcadores e tracklogs apagados, sem exigir reinício.
- Área de composição de mensagem aumentada para aproximadamente três vezes a altura anterior.
- Campo de mensagem alterado para editor multilinha com contador de caracteres.
- **Enter** cria nova linha durante a edição e **Ctrl+Enter** envia a mensagem.
- Mantidos todos os recursos da v0.2.5, incluindo Ajuda integrada, Portable EXE, brilho do mapa, aviso sonoro, atualização automática de versão e envio de mensagens a partir do mapa.
- Telemetria/estatísticas anônimas **não fazem parte desta versão** e permanecem para desenvolvimento posterior.
- Esta release permanece **não assinada** enquanto o projeto aguarda aprovação do SignPath Foundation.

## v0.2.5 — 2026-09-23

- Nova aba **Ajuda** com guia de primeiros passos, configuração da estação, APRS-IS, mapa, mensagens, boletins, estações, Log, atualizações, banco/backup e diagnóstico rápido.
- A Ajuda inclui contato para dúvidas, dificuldades e sugestões: Alex — WhatsApp 61 98402-3634 — alexpmr@gmail.com.
- Novo artefato `PT2VHF_APRS_Client_Portable_x64.exe`: versão portátil em executável único, sem necessidade de descompactar o ZIP.
- O Portable EXE continua usando o banco SQLite em `%LOCALAPPDATA%\PT2VHF APRS Client\data`, compartilhando configurações e histórico com a instalação normal.
- O instalador agora encerra automaticamente a versão anterior do PT2VHF APRS Client antes de substituir os arquivos, evitando falhas de atualização por arquivos em uso.
- O instalador também tenta interromper um eventual serviço Windows `PT2VHF_APRS_Client`, preparando o mecanismo para uma futura execução como serviço.
- Controle de **Brilho do mapa** em Configuração → Mapa, de 30% a 150%, com pré-visualização imediata.
- Opção de **sinal sonoro** ao receber nova mensagem individual destinada ao `CALL-SSID` configurado.
- O sinal sonoro é gerado nativamente pelo Windows quando chega uma mensagem individual para a estação configurada, funcionando mesmo com a interface no navegador minimizada.
- Botão **Enviar mensagem** no popup das estações do mapa; abre a aba Mensagens com o indicativo de destino já preenchido e o cursor no campo de texto.
- Indicador de versão no cabeçalho da aplicação.
- Mostra **Última versão** quando a instalação corresponde à release mais recente publicada.
- Mostra **Nova versão vX.Y.Z** quando houver uma release mais nova no GitHub.
- O aviso de nova versão abre diretamente a página da Release.
- Builds de desenvolvimento mais novos que a última release são identificados como **Build vX.Y.Z**.
- Falhas de consulta não afetam o APRS e são mostradas como **Versão não verificada**.
- Consulta feita pelo backend local com cache de 15 minutos; a interface revalida periodicamente.

## v0.2.4 — 2026-09-23

- Nova seção **Aparência** em Configuração.
- Ajuste independente da **família da fonte** da aba Mensagens.
- Ajuste independente do **tamanho da fonte** da aba Mensagens, de 10 a 20 px.
- Ajuste independente da **família da fonte** da aba Estações.
- Ajuste independente do **tamanho da fonte** da aba Estações, de 10 a 20 px.
- Fontes disponíveis: Sistema, Segoe UI, Arial, Verdana, Tahoma e Consolas.
- Alterações de aparência são visualizadas imediatamente e persistidas no SQLite após salvar.
- Configuração incluída na exportação/importação JSON.
- Mantidas todas as melhorias da v0.2.3, incluindo boletins APRS, Minhas mensagens, popup de mensagens, mapas alternativos, tracklogs configuráveis, passcode automático e nova identidade visual.
- Esta release permanece **não assinada** enquanto o projeto aguarda aprovação do SignPath Foundation.


## v0.2.3 — 2026-09-23

- Suporte nativo a **boletim APRS geral** (`BLN0`–`BLN9`) sem ACK.
- Suporte a **boletim APRS de grupo**, com identificador e grupo de até 5 caracteres.
- Histórico de mensagens distingue mensagem individual, boletim e boletim de grupo.
- Botão **Minhas mensagens** mostra apenas mensagens individuais de ou para o `CALL-SSID` configurado.
- Popup para nova mensagem individual destinada à estação configurada, com remetente, horário, texto e botão **Responder**.
- Aba **Estações** sem a coluna Nome; Indicativo passa a ser a identificação principal.
- Clique em uma estação abre a aba MAPA, centraliza a posição e abre o popup correspondente.
- **Última recepção** permanece em uma única linha com data e hora.
- **Distância** mantém valor e `km` na mesma linha.
- Nova seção **Mapa** nas configurações.
- Seleção de mapa: OpenStreetMap, OpenTopoMap e Esri World Imagery.
- Configuração de cor e espessura dos tracklogs, persistida no SQLite.
- Passcode APRS-IS movido para junto do Indicativo e exibido em texto normal.
- Cálculo automático do passcode APRS-IS enquanto o indicativo é digitado.
- Nova identidade visual quadrada do PT2VHF APRS Client no cabeçalho, favicon, bandeja, executável e instalador.
- Geração automática do ícone Windows durante o build.
- Logo validada novamente no pipeline após correção do ativo PNG usado para gerar o ícone Windows.
- Mantidos SBOM CycloneDX, inventário de licenças e preparação para futura assinatura SignPath.
- Esta release ainda é **não assinada** enquanto o projeto aguarda aprovação do SignPath Foundation.


## v0.2.2 — 2026-09-23

Build Windows de teste enquanto o projeto aguarda aprovação do SignPath Foundation.

- Código autoral formalizado sob licença MIT.
- Política de assinatura de código publicada.
- Política de privacidade e política de segurança adicionadas.
- Avisos e licenças de componentes de terceiros documentados.
- `CODEOWNERS` configurado para o mantenedor do projeto.
- Instalador passa a exibir a licença MIT e o aviso de privacidade.
- Geração automática de SBOM CycloneDX no build Windows.
- Inventário automático das licenças das dependências.
- SBOM e inventário de licenças incluídos nos artefatos do GitHub Actions.
- Página de Release passa a informar explicitamente o status de assinatura.
- Documentação de onboarding e candidatura ao SignPath Foundation adicionada.
- Esta versão permanece **não assinada** enquanto a aprovação do SignPath estiver pendente.


## v0.2.1 — 2026-09-23

- Correção dos tiles do mapa exibidos fora de posição/“embaralhados”.
- CSS do Leaflet empacotado localmente com a aplicação para evitar falhas do CDN.
- Proteção CSS adicional para o posicionamento absoluto dos tiles.
- Botão **Minha localização** no mapa, usando a geolocalização do navegador.
- Exibição de marcador e raio de precisão da localização do navegador.
- Versão exibida no título da aplicação e na aba do navegador.
- Aba **Log** com todo o tráfego APRS-IS bruto em RX/TX.
- Filtro textual, filtro por direção, quantidade de linhas e auto-rolagem no Log.
- Histórico do Log persistido no SQLite, com retenção dos 100.000 registros mais recentes.
- Passcode APRS-IS mascarado antes de registrar a linha de login no Log.
- Reconexão automática ao alterar parâmetros de conexão/filtro enquanto conectado.
- Contadores de pacotes recebidos e filtro APRS-IS ativo exibidos no mapa para diagnóstico.

## v0.2.0 — 2026-09-23

Versão Windows-first.

- Aplicativo Windows sem console, com servidor local Waitress.
- Ícone na bandeja com abrir, conectar, desconectar, abrir pasta de dados e sair.
- Banco SQLite movido para `%LOCALAPPDATA%\PT2VHF APRS Client\data` no Windows.
- Empacotamento PyInstaller em modo onedir.
- Instalador Inno Setup x64 e ZIP portátil.
- Workflow GitHub Actions para gerar artefatos e anexá-los automaticamente às Releases criadas por tags `v*`.
- Dados locais preservados durante atualização/desinstalação.

## v0.1.0 — 2026-09-23

Primeira versão funcional do PT2VHF APRS Client.

- Cliente TCP APRS-IS com conexão, desconexão e reconexão automática.
- SQLite local para configuração, mapa, estações, trilhas, mensagens e pacotes brutos.
- Mapa Leaflet/OpenStreetMap com símbolos APRS e tracklog.
- Mensagens APRS com autocomplete, filtro, ordenação, ACK/REJ e envio.
- Lista de estações com distância, velocidade, curso, altitude e informação.
- Configuração completa, seletor de símbolo, beacon e importação/exportação JSON.
