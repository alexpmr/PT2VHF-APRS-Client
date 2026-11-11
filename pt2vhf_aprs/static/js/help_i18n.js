/* v1.15.9 (#157): aba Ajuda completa em inglês, por bloco inteiro (os parágrafos têm
   formatação no meio e não se traduzem bem trecho a trecho). Os demais idiomas
   continuam no catálogo por texto até a revisão integral. */
(() => {
  'use strict';
  const EN = {
    h1: 'Help',
    h2: 'Quick guide to set up, use and troubleshoot PT2VHF APRS Client.',
    h3: 'Getting started',
    h4: 'Set up your station before connecting to APRS-IS',
    h5: 'In the <strong>Settings</strong> tab, enter your callsign, SSID, position and APRS-IS parameters. The passcode is calculated automatically from the base callsign.',
    h6: 'Open Settings',
    h7: '1. Station',
    h8: '<strong>Callsign:</strong> enter your amateur radio callsign. The SSID identifies the station’s purpose, for example <code>-9</code> for mobile.',
    h9: '<strong>APRS-IS passcode:</strong> calculated automatically and shown next to the callsign. The SSID does not change this code.',
    h10: '<strong>Latitude/Longitude:</strong> can be entered in decimal or degrees/minutes/seconds. On first run, the client asks the browser/OS for your location to prefill the coordinates and center the map. The <strong>Use my current location</strong> button repeats this later.',
    h11: '<strong>Altitude:</strong> optional. When set, it is sent in the beacon (<code>/A=</code>); in <strong>Settings → Application → Units</strong> you can use feet, miles and mph.',
    h12: '<strong>APRS icon:</strong> choose the symbol that fits your station or vehicle.',
    h13: '2. APRS-IS',
    h14: 'The default server is <code>soam.aprs2.net</code>, port <code>14580</code>, with automatic fallback to <code>rotate.aprs2.net</code> when needed. Settings offers regional suggestions and still accepts a manual server.',
    h15: '<strong>Receive filter:</strong> new installations use the Brazilian prefixes by default. The graphical editor can combine the Brazil filter, radius, geographic area, prefixes, exact callsigns and packet types, while the manual field stays available.',
    h16: 'If the filter is left empty, the program asks for confirmation before saving and explains the possible impact on traffic volume.',
    h17: 'If the Log shows <code>Parse errors on filter spec</code>, review the APRS-IS filter field. Free text such as <code>user</code> is not a valid APRS-IS filter.',
    h18: '<strong>Connect at startup</strong> is enabled in new installations and can be turned off in this section.',
    h19: '<strong>Also open in the browser at startup</strong> keeps the built-in window and opens a second view in the default browser. It is off by default.',
    h20: '3. Map',
    h21: 'Choose between <strong>OpenStreetMap</strong>, <strong>OpenTopoMap</strong>, <strong>Light</strong>, <strong>Dark</strong>, <strong>CyclOSM</strong>, <strong>Humanitarian / HOT</strong>, <strong>OSM.DE</strong>, <strong>ÖPNVKarte</strong> and <strong>Satellite</strong>.',
    h22: 'You can adjust <strong>map brightness</strong>, <strong>color</strong> and <strong>tracklog width</strong>, as well as the <strong>colors and width of the observed topology</strong>.',
    h23: 'Click a station to open its details. Use <strong>Send message</strong>, <strong>View logs</strong> or the <strong>yellow star</strong> to make it a favorite.',
    h24: '<strong>APRS queries:</strong> the station popup has shortcuts to query <strong>Position</strong>, <strong>Status</strong>, <strong>Heard</strong>, run <strong>Ping/ACK</strong> and request a <strong>Trace</strong>. When the trace returns a path with known positions, the hops are highlighted on the map for a while; hops without a position are listed in the reply without an invented location.',
    h25: 'The topology uses the <strong>Complete</strong> period by default, plus hour/day windows, a legend of line types and traffic animation on the map.',
    h26: 'On first run, when permission is granted, the map is centered on your current location. After that, the position and zoom you choose are saved locally and are not re-centered continuously.',
    h27: '4. Messages and bulletins',
    h28: '<strong>Message:</strong> APRS communication addressed to one callsign, with ACK/REJ support.',
    h29: '<strong>Send route:</strong> for individual messages, choose <strong>Automatic</strong>, <strong>APRS-IS</strong>, <strong>Direct RF</strong> or <strong>Custom RF</strong>. The custom RF path accepts values such as <code>WIDE1-1</code> and <code>WIDE1-1,WIDE2-1</code> and applies only to that message.',
    h30: '<strong>Automatic:</strong> prefers APRS-IS, keeping the client’s traditional behavior, and uses direct RF only when APRS-IS is unavailable and the TNC is ready to transmit.',
    h31: '<strong>General bulletin:</strong> uses <code>BLN0</code> to <code>BLN9</code> and does not request an ACK.',
    h32: '<strong>Group bulletin:</strong> lets you enter a group of up to five characters.',
    h33: 'The <strong>My messages</strong> button shows only individual messages from or to your <code>CALL-SSID</code>.',
    h34: 'Messages follow a chat flow, newest at the bottom. <strong>Group by sender</strong> organizes the history into conversations per contact. Right-click a message to copy its text or callsign, or to cancel the retries of a message still waiting for ACK.',
    h35: 'Click any callsign in the <strong>From</strong> or <strong>To</strong> columns to select it as the recipient and reply. If you click your own callsign, the program tries to select the other participant.',
    h36: 'The composer accepts long messages. Press <strong>Enter</strong> to send and <strong>Shift+Enter</strong> for a new line. Longer messages are split automatically without visible numbering, keeping words whole where possible; each part has its own acknowledgment.',
    h37: 'The <strong>Clear messages</strong> button deletes the whole local history of messages and bulletins after confirmation.',
    h38: 'When a new message for your station arrives and the Messages tab is already open, the program shows a small non-blocking notice that closes automatically after the time set in Settings. Outside the Messages tab, the full notice with a reply option is shown.',
    h39: '5. Stations',
    h40: 'The list shows callsign, last heard, distance, speed, course, altitude and known information.',
    h41: 'Click a row to open the <strong>Map</strong>, center the station and show its popup.',
    h42: 'Click the column titles to change the sort order. Favorite stations stay pinned at the top and are marked with a yellow star.',
    h43: 'The <strong>Clear stations</strong> button deletes all local stations and tracklogs; links, heat map and objects are kept, and new stations appear again as they are received.',
    h44: 'Table font and size can be adjusted in <strong>Settings → Appearance</strong>.',
    h45: '6. APRS-IS log',
    h46: 'Use the Log to troubleshoot connection, authentication, filter and received/sent traffic.',
    h47: '<strong>RX</strong> means data received and <strong>TX</strong> means data sent.',
    h48: '<code># logresp ... verified</code> confirms APRS-IS authentication. Lines starting with <code>#</code> are server control messages, not APRS stations.',
    h49: 'The passcode is masked in the Log.',
    h50: '7. Updates',
    h51: 'The header shows whether you are on the <strong>latest version</strong> or a <strong>new version</strong> has been published.',
    h52: 'When an update is available, clicking the notice downloads the package for your platform. The file is verified before installation.',
    h53: 'A helper updater closes the running version, forces it to close after a timeout if needed, installs/replaces the application and opens the new version automatically. The Windows Portable keeps a backup for rollback.',
    h54: '8. Database and backup',
    h55: 'The SQLite database is stored in:',
    h56: 'The installer and the Portable EXE use this same local database.',
    h57: 'In <strong>Settings → Configuration backup</strong> you can save or restore your preferences as JSON.',
    h58: 'The exported JSON contains the APRS-IS passcode in readable text. Keep it in a safe place.',
    h59: 'Quick troubleshooting',
    h60: '<strong>Connects, but no stations appear</strong><span>Check the APRS-IS filter and look for filter errors in the Log.</span>',
    h61: '<strong>Does not connect</strong><span>Read the error shown after the attempts. It points to DNS, TCP/port or server failures; also check the firewall and port 14580.</span>',
    h62: '<strong>Does not transmit</strong><span>Check that the connection is verified and that callsign/passcode are correct. For RF, see Settings → TNC / RF (Dire Wolf, Digirig, Kenwood TS-2000).</span>',
    h63: '<strong>Map does not load</strong><span>Check your Internet connection or blocks to the CDN/tiles. The other tabs keep working even when the map does not load.</span>',
    h64: '<strong>Wrong distances</strong><span>Check your station’s latitude and longitude in Settings.</span>',
    h65: '<strong>No sound alert</strong><span>Check the sound option in Settings → Appearance and the system volume.</span>',
    h66: 'Questions, problems or suggestions?',
    h67: 'Contact me',
    h68: 'If you need help setting up the program, found a problem or have a suggestion, get in touch.',
  };
  const CATALOG = { en: EN };
  const originals = new Map();
  function apply(language) {
    const lang = String(language || document.documentElement.lang || 'pt-BR');
    const table = CATALOG[lang.split('-')[0]] || null;
    for (const el of document.querySelectorAll('#tab-help [data-help-i18n]')) {
      const key = el.dataset.helpI18n;
      if (!originals.has(key)) originals.set(key, el.innerHTML);
      const next = table?.[key] ?? originals.get(key);
      if (el.innerHTML !== next) el.innerHTML = next;
    }
  }
  window.pt2vhfHelpI18n = { apply, keys: () => Object.keys(EN) };
  document.addEventListener('pt2vhf-language-changed', event => apply(event.detail?.language));
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', () => apply());
  else apply();
})();
