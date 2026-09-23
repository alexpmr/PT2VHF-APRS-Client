# PT2VHF APRS Client — v0.1.0

Cliente APRS-IS em Python com interface web local, banco SQLite e mapa de estações.

## O que já está implementado

- **MAPA** com OpenStreetMap/Leaflet.
- Estações adicionadas ao mapa conforme são recebidas do APRS-IS.
- Símbolos APRS conforme `symbol_table` + `symbol` recebidos no pacote.
- Suporte visual a símbolos da tabela primária, secundária e overlays recebidos.
- Tracklog automático quando uma estação muda de posição (limiar de 10 m).
- Pop-up por estação com indicativo, hora, posição, velocidade, curso, altitude, comentário/informação e path.
- Centro e zoom do mapa persistidos no SQLite.
- **Mensagens** recebidas e enviadas, com De, Para, Mensagem, Hora e Status.
- Ordenação das colunas ao clicar no cabeçalho.
- Filtro parcial pelo remetente (`PT2`, `PY2A`, etc.).
- Campo de destino com autocomplete usando indicativos já conhecidos, sem impedir indicativos novos.
- Mensagens enviadas com identificador APRS e tratamento de `ack`/`rej`.
- ACK automático para mensagens recebidas com ID e endereçadas exatamente ao indicativo configurado.
- **Estações** com nome/indicativo, última recepção, distância, velocidade, curso, altitude e informação.
- Filtro parcial de estações e ordenação por qualquer coluna.
- Distância calculada em linha reta a partir da latitude/longitude da estação local.
- **Configuração** persistida no SQLite.
- Indicativo, SSID, comentário, latitude, longitude, altitude, e-mail, ícone APRS, intervalo de beacon, servidor, porta, passcode, filtro e conexão automática.
- Seletor gráfico de símbolos APRS.
- Servidor padrão: `brazil.aprs2.net`.
- Porta padrão: `14580`.
- Atalho de filtro: `r/500` é expandido para `r/LAT/LON/500` usando a posição configurada.
- Botão Conectar/Desconectar.
- Beacon periódico e botão **Enviar beacon agora**.
- Reconexão automática com backoff em caso de queda.
- Exportação e importação da configuração em JSON.
- Histórico bruto de pacotes no SQLite para futura auditoria/diagnóstico.

## Requisitos

- Python 3.10 ou superior.
- Acesso à Internet para APRS-IS, tiles do OpenStreetMap, Leaflet e sprites dos símbolos APRS.
- Passcode APRS-IS válido para transmitir mensagens e beacons.

## Instalação — Linux

```bash
git clone https://github.com/alexpmr/PT2VHF-APRS-Client.git
cd PT2VHF-APRS-Client
chmod +x install_linux.sh run_linux.sh
./install_linux.sh
./run_linux.sh
```

Abra `http://127.0.0.1:8080`.

## Instalação — Windows

```bat
git clone https://github.com/alexpmr/PT2VHF-APRS-Client.git
cd PT2VHF-APRS-Client
install_windows.bat
run_windows.bat
```

## Banco local

O banco é criado automaticamente em:

```text
data/pt2vhf_aprs.db
```

As tabelas principais são `config`, `map_state`, `stations`, `tracks`, `messages` e `packets`.

## Segurança

A exportação JSON da configuração pode incluir o passcode APRS-IS. Não publique arquivos de configuração exportados no repositório.

Por padrão a interface escuta apenas em `127.0.0.1`. Não exponha esta versão diretamente à Internet.

## Créditos e fontes técnicas

- APRS-IS: https://www.aprs-is.net/
- aprslib: https://pypi.org/project/aprslib/
- Leaflet: https://leafletjs.com/
- OpenStreetMap: https://www.openstreetmap.org/

## Roadmap

- Monitor de pacotes TNC2 bruto.
- Exportação CSV/GPX/KML.
- Conversas agrupadas por indicativo.
- Retentativa configurável de mensagens sem ACK.
- Estatísticas de estações, mensagens, paths e gateways.
- Integração opcional RF por Dire Wolf/KISS/TNC.
- Autenticação web e HTTPS.
