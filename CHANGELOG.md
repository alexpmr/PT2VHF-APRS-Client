# Changelog

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
