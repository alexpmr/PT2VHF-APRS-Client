# Changelog

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
