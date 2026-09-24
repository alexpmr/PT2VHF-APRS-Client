# Privacy policy

## Summary

PT2VHF APRS Client is designed as a local desktop application. It does not contain advertising, analytics, behavioral tracking, or developer-operated telemetry.

The application **does communicate with external network services when the user enables or uses features that require them**. Those connections are described below.

## Local data

On Windows, persistent application data is stored under:

```text
%LOCALAPPDATA%\PT2VHF APRS Client\data\pt2vhf_aprs.db
```

The local SQLite database may contain:

- application configuration;
- APRS callsigns and station information;
- received positions and tracklogs;
- APRS messages;
- raw APRS packets;
- APRS-IS RX/TX log entries;
- saved map position and zoom.

This data remains on the user's computer unless the user explicitly copies, exports, backs up, or transmits it.

## APRS-IS

When the user connects to APRS-IS, the application communicates with the APRS-IS server configured by the user.

Depending on configuration and actions, this may transmit:

- the configured amateur-radio callsign and SSID;
- APRS-IS authentication/passcode data;
- the selected APRS-IS filter;
- APRS messages sent by the user;
- beacons containing the configured station position, altitude, symbol, and comment;
- APRS acknowledgements.

Received APRS-IS traffic is processed and may be stored locally.

The application's Log tab masks the APRS-IS passcode before storing or displaying the login line.

## Browser geolocation

The **My location** map control uses the browser's Geolocation API only after the user invokes it and the browser grants permission.

The resulting position:

- is used to center the map;
- may be stored locally as the saved map center/zoom;
- does **not** automatically replace the configured APRS station position;
- does **not** automatically cause an APRS beacon to be transmitted.

## OpenStreetMap

Map tiles are requested from OpenStreetMap tile servers when the map is displayed. Tile requests inherently expose network information such as the user's IP address and the map tile coordinates being requested to the tile provider.

OpenStreetMap services are governed by their own policies.

## External web resources

The current application may request browser resources from third-party infrastructure used by the interface, including:

- OpenStreetMap tile servers for map imagery;
- `unpkg.com` for the Leaflet JavaScript library;
- `raw.githubusercontent.com` for APRS symbol sprite images.

These services receive normal HTTP request metadata such as the requesting IP address and user-agent information.

Future releases may vendor more of these resources locally.

## Verificação de atualizações no GitHub

O aplicativo consulta periodicamente a API pública de Releases do GitHub para verificar se existe uma versão mais recente do PT2VHF APRS Client.

Essa consulta envia apenas os metadados normais de uma requisição HTTPS, incluindo informações como endereço IP, cabeçalhos HTTP e o identificador do aplicativo/versão no User-Agent.

A verificação de atualização **não envia** ao GitHub:

- indicativo ou SSID configurado;
- posição da estação;
- mensagens APRS;
- passcode APRS-IS;
- filtro APRS-IS;
- conteúdo do banco SQLite ou do Log.

A consulta é feita diretamente ao GitHub e não passa por um servidor operado pelo desenvolvedor. O resultado é armazenado temporariamente em cache local para reduzir requisições.

## Configuration export

The JSON configuration export is intended to allow full backup and restore. It may contain the APRS-IS passcode in readable form.

Users should treat exported configuration files as sensitive and must not publish them in GitHub issues, public repositories, forums, or screenshots.

## No developer-operated collection

The PT2VHF APRS Client project does not operate a server that collects user application data.

Network traffic goes to services selected or required for the features described above.

## Changes to this policy

Material changes to network behavior or data handling should be reflected in this document as part of the same release that introduces them.
