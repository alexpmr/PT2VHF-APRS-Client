(() => {
  'use strict';

  const $ = sel => document.querySelector(sel);
  const $$ = sel => Array.from(document.querySelectorAll(sel));
  const esc = value => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  const TNC_I18N = {
    en: {
      'KISS Serial/TCP, monitor AX.25, Digipeater, iGate e análise adaptativa de quem fala com quem.':'KISS Serial/TCP, AX.25 monitor, Digipeater, iGate and adaptive communication analysis.',
      'Atualizar portas':'Refresh ports','Conectar TNC':'Connect TNC','Desconectar':'Disconnect','PARAR TX':'STOP TX','Liberar TX':'Resume TX',
      'Estado':'Status',
      'RX KISS/AX.25':'RX KISS/AX.25','TX entregue ao TNC':'TX delivered to TNC','Diagnóstico do transporte:':'Transport diagnostics:',
      'Serial conectada':'Serial connected','Serial operacional — RX KISS ativo':'Serial operational — KISS RX active','Serial conectada — sem KISS':'Serial connected — no KISS','Serial conectada — AX.25 inválido':'Serial connected — invalid AX.25','Serial conectada — aguardando dados':'Serial connected — waiting for data','KISS TCP operacional — RX ativo':'KISS TCP operational — RX active','KISS TCP conectado — aguardando frames':'KISS TCP connected — waiting for frames','RX KISS ativo':'KISS RX active','Serial sem KISS':'Serial no KISS','AX.25 inválido':'Invalid AX.25','Serial aguardando':'Serial waiting','KISS aguardando':'KISS waiting','KISS TCP conectado':'KISS TCP connected','RX ativo':'RX active','Aguardando dados do TNC.':'Waiting for TNC data.',
      'Transporte desconectado.':'Transport disconnected.','bytes recebidos pela serial, mas nenhum frame KISS válido foi reconhecido.':'bytes received over serial, but no valid KISS frame was recognized.',
      'frame(s) AX.25 inválido(s)':'invalid AX.25 frame(s)','Nenhum frame entregue ao TNC nesta conexão.':'No frame delivered to the TNC in this connection.',
      'bytes entregues ao transporte':'bytes delivered to transport','emissão RF não confirmada pelo Client':'RF transmission not confirmed by the Client',
      'Desconectado.':'Disconnected.','Transporte operacional: frames KISS/AX.25 válidos estão chegando ao Client.':'Transport operational: valid KISS/AX.25 frames are reaching the Client.',
      'A porta está aberta e há bytes chegando, mas não em KISS reconhecível. Verifique modo PKT/KISS, protocolo e baud rate; não mude o rádio para TNC interno apenas para fazer o indicador ficar ativo.':'The port is open and bytes are arriving, but not as recognizable KISS. Check PKT/KISS mode, protocol and baud rate; do not switch the radio to its internal TNC just to make the indicator active.',
      'Há frames KISS chegando, mas o conteúdo AX.25 não está sendo validado. Consulte o erro exibido e revise o modo/protocolo do equipamento.':'KISS frames are arriving, but the AX.25 content is not validating. Check the displayed error and review the device mode/protocol.',
      'Porta serial aberta; aguardando o primeiro byte/frame. “Conectado” confirma apenas a abertura da porta.':'Serial port open; waiting for the first byte/frame. “Connected” only confirms that the port opened.',
      'KISS TCP conectado; aguardando o primeiro frame válido.':'KISS TCP connected; waiting for the first valid frame.',
      'Kenwood TM-D700:':'Kenwood TM-D700:',
      'quando usado pela serial neste fluxo, mantenha o rádio no modo':'when used over serial in this workflow, keep the radio in',
      'apropriado à interface. O Client não força o modo TNC/digipeater interno. “Serial conectada” não significa, por si só, que frames KISS/AX.25 estejam chegando ou que a emissão RF tenha sido confirmada.':'mode as appropriate for the interface. The Client does not force the internal TNC/digipeater mode. “Serial connected” alone does not mean KISS/AX.25 frames are arriving or that RF transmission has been confirmed.',
      'Duplicatas evitadas':'Duplicates avoided','janela configurável':'configurable window','Fila TX':'TX queue','Otimizador':'Optimizer',
      'Conexão KISS':'KISS connection','Transporte':'Transport','Conectar TNC ao iniciar':'Connect TNC at startup','Porta TCP':'TCP port','Porta serial':'Serial port','Selecione…':'Select…',
      'Compatível com TNC físico em KISS e softwares como Dire Wolf por KISS TCP. APRS-IS e RF podem operar de forma independente.':'Compatible with physical KISS TNCs and software such as Dire Wolf over KISS TCP. APRS-IS and RF can operate independently.',
      'Papel RF e segurança de TX':'RF role and TX safety','Papel principal':'Primary role','Somente monitor':'Monitor only','Estação local':'Local station','iGate bidirecional':'Bidirectional iGate',
      'Retenção do histórico':'History retention','dias':'days','Habilitar transmissão automática em RF':'Enable automatic RF transmission',
      'Confirmo que revisei indicativo, rádio, frequência e regras antes de permitir TX automático':'I confirm that I reviewed callsign, radio, frequency and rules before allowing automatic TX',
      'Segurança:':'Safety:','TX automático, Digipeater e iGate Internet→RF vêm desligados por padrão. O botão PARAR TX interrompe imediatamente novas transmissões sem derrubar o monitor RX.':'Automatic TX, Digipeater and Internet→RF iGate are off by default. STOP TX immediately blocks new transmissions without stopping RX monitoring.',
      'Digipeater inteligente':'Smart Digipeater','Ativar Digipeater':'Enable Digipeater','Perfil':'Profile','Personalizado':'Custom','Aliases personalizados':'Custom aliases',
      'Separados por vírgula; usados no perfil Personalizado.':'Comma-separated; used by the Custom profile.','Máximo de hops repetidos':'Maximum repeated hops','Janela de duplicatas':'Duplicate window','segundos':'seconds',
      'Rate limit por origem':'Rate limit per source','pacotes/min':'packets/min','O digi usa supressão de duplicatas, bloqueio de loop, limite de hops e fila com prioridade para mensagens/ACK/REJ.':'The digi uses duplicate suppression, loop blocking, hop limits and a queue that prioritizes messages/ACK/REJ.',
      'iGate inteligente':'Smart iGate','APRS-IS → RF restritivo':'Restricted APRS-IS → RF','Janela “ouvido por RF”':'RF-heard window','minutos':'minutes','Path RF do iGate':'iGate RF path','vazio = direto':'empty = direct',
      'Ex.: WIDE1-1. Prefira vazio quando a cobertura direta for suficiente.':'Example: WIDE1-1. Prefer empty when direct coverage is sufficient.',
      'Internet→RF só considera mensagens cujo destino tenha sido ouvido diretamente por RF dentro da janela configurada. Tráfego Internet genérico não é despejado no canal.':'Internet→RF only considers messages whose destination was heard directly over RF within the configured window. Generic Internet traffic is not dumped onto the channel.',
      'Otimização “quem fala com quem”':'“Who talks to whom” optimization','Modo':'Mode','Desligado':'Off','Observação / recomendação':'Observation / recommendation','Automático conservador':'Conservative automatic',
      'O grafo usa mensagens, ACK/REJ e presença RF para priorizar tráfego útil e evitar repetição desnecessária. Ele não reescreve arbitrariamente paths de terceiros nem inventa enlaces RF.':'The graph uses messages, ACK/REJ and RF presence to prioritize useful traffic and avoid unnecessary repetition. It does not arbitrarily rewrite third-party paths or invent RF links.',
      'Aguardando dados.':'Waiting for data.','Aplicar configuração':'Apply settings','Alterações de transporte reconectam o TNC se ele já estiver em uso. Ativar funções de TX exige a confirmação explícita acima.':'Transport changes reconnect the TNC if it is already in use. Enabling TX functions requires the explicit confirmation above.',
      'Salvar TNC / RF':'Save TNC / RF','Monitor TNC':'TNC monitor','Frames AX.25/APRS recebidos e transmitidos.':'Received and transmitted AX.25/APRS frames.','Atualizar':'Refresh',
      'Hora':'Time','Dir.':'Dir.','Origem':'Source','Destino':'Destination','Tipo':'Type','Pacote TNC2':'TNC2 packet','Sem frames.':'No frames.',
      'Decisões Digi / iGate':'Digi / iGate decisions','Auditoria do que foi enviado, suprimido ou bloqueado.':'Audit of what was sent, suppressed or blocked.','Ação':'Action','Decisão':'Decision','Motivo':'Reason','Sem decisões.':'No decisions.',
      'Estações ouvidas por RF':'Stations heard over RF','Presença local usada pelo iGate inteligente.':'Local presence used by the smart iGate.','Estação':'Station','Última RF':'Last RF','Direta':'Direct','Contagem':'Count','Recepções':'Receptions','Pacotes RF':'RF packets','Distância':'Distance','Último tipo':'Last type','Nenhuma estação ouvida pelo TNC.':'No stations heard by the TNC.',
      'Quem fala com quem':'Who talks to whom','Grafo textual consolidado das interações RF e APRS-IS.':'Consolidated textual graph of RF and APRS-IS interactions.','Meio':'Medium','Interações':'Interactions','Última':'Last','Aguardando interações.':'Waiting for interactions.',
      'Ativado':'Enabled','Desconectado':'Disconnected','Observação':'Observation','TX automático desligado':'Automatic TX off','não detectada agora':'not detected now','Configuração TNC / RF salva.':'TNC / RF settings saved.','Sim':'Yes','Via digi':'Via digi',
      'TX automático, Digipeater e iGate Internet→RF vêm desligados por padrão. O botão':'Automatic TX, Digipeater and Internet→RF iGate are off by default. The button',
      'interrompe imediatamente novas transmissões sem derrubar o monitor RX.':'immediately blocks new transmissions without stopping RX monitoring.',
      'Internet→RF só considera mensagens cujo destino tenha sido ouvido':'Internet→RF only considers messages whose destination was heard',
      'diretamente':'directly','por RF dentro da janela configurada. Tráfego Internet genérico não é despejado no canal.':'over RF within the configured window. Generic Internet traffic is not dumped onto the channel.',
      'Liberar novamente a transmissão automática em RF com a configuração atual?':'Resume automatic RF transmission with the current configuration?',
      'Equipamentos seriais detectados':'Detected serial devices','Portas encontradas pelo pyserial e, no Windows, também pela enumeração nativa do sistema.':'Ports found by pyserial and, on Windows, by native system enumeration too.',
      'Reescanear':'Rescan','Equipamento':'Device','Interface':'Interface','Fabricante':'Manufacturer','Nº de série / HWID':'Serial no. / HWID','Status':'Status','Usar':'Use',
      'Aguardando leitura das portas seriais.':'Waiting for serial port scan.','Nenhum equipamento serial lido ainda.':'No serial device read yet.',
      'O Client não atribui um modelo de rádio apenas pelo chipset USB. Quando o Windows não informar o modelo real, a interface é mostrada de forma genérica, por exemplo USB Serial — CH9102.':'The Client does not assign a radio model from the USB chipset alone. When Windows does not report the real model, the interface is shown generically, for example USB Serial — CH9102.',
      'Selecione um equipamento detectado abaixo ou informe manualmente uma porta COM.':'Select a detected device below or manually enter a COM port.',
      'Conectado pelo Client':'Connected by Client','Configurado':'Configured','Erro do dispositivo':'Device error','Detectado':'Detected',
      'equipamento/porta detectado':'device/port detected','equipamentos/portas detectados':'devices/ports detected',
      'Nenhuma porta serial detectada pelo sistema.':'No serial port detected by the system.','Nenhum equipamento serial detectado. Você ainda pode informar a COM manualmente.':'No serial device detected. You can still enter the COM port manually.',
      'Equipamento serial não identificado':'Unidentified serial device','Não foi possível listar as portas seriais:':'Could not list serial ports:',
      'Radtel RT-950 Pro detectado: no modo TNC UART, use normalmente 115200 bps e TNC Type/KISS habilitado no rádio.':'Radtel RT-950 Pro detected: in TNC UART mode, normally use 115200 bps with TNC Type/KISS enabled on the radio.',
      'Interface CH9102 detectada. Se esta porta pertencer a um Radtel RT-950 Pro em TNC UART, configure 115200 bps e habilite TNC/KISS no rádio.':'CH9102 interface detected. If this port belongs to a Radtel RT-950 Pro in TNC UART mode, set 115200 bps and enable TNC/KISS on the radio.'
    },
    es: {
      'KISS Serial/TCP, monitor AX.25, Digipeater, iGate e análise adaptativa de quem fala com quem.':'KISS Serial/TCP, monitor AX.25, Digipeater, iGate y análisis adaptativo de quién habla con quién.',
      'Atualizar portas':'Actualizar puertos','Conectar TNC':'Conectar TNC','Desconectar':'Desconectar','PARAR TX':'DETENER TX','Liberar TX':'Reanudar TX',
      'Estado':'Estado',
      'RX KISS/AX.25':'RX KISS/AX.25','TX entregue ao TNC':'TX entregado al TNC','Diagnóstico do transporte:':'Diagnóstico del transporte:',
      'Serial conectada':'Serie conectada','Serial operacional — RX KISS ativo':'Serie operativa — RX KISS activo','Serial conectada — sem KISS':'Serie conectada — sin KISS','Serial conectada — AX.25 inválido':'Serie conectada — AX.25 inválido','Serial conectada — aguardando dados':'Serie conectada — esperando datos','KISS TCP operacional — RX ativo':'KISS TCP operativo — RX activo','KISS TCP conectado — aguardando frames':'KISS TCP conectado — esperando tramas','RX KISS ativo':'RX KISS activo','Serial sem KISS':'Serie sin KISS','AX.25 inválido':'AX.25 inválido','Serial aguardando':'Serie esperando','KISS aguardando':'KISS esperando','KISS TCP conectado':'KISS TCP conectado','RX ativo':'RX activo','Aguardando dados do TNC.':'Esperando datos del TNC.',
      'Transporte desconectado.':'Transporte desconectado.','bytes recebidos pela serial, mas nenhum frame KISS válido foi reconhecido.':'bytes recibidos por serie, pero no se reconoció ninguna trama KISS válida.',
      'frame(s) AX.25 inválido(s)':'trama(s) AX.25 inválida(s)','Nenhum frame entregue ao TNC nesta conexão.':'Ninguna trama entregada al TNC en esta conexión.',
      'bytes entregues ao transporte':'bytes entregados al transporte','emissão RF não confirmada pelo Client':'transmisión RF no confirmada por el Client',
      'Desconectado.':'Desconectado.','Transporte operacional: frames KISS/AX.25 válidos estão chegando ao Client.':'Transporte operativo: están llegando tramas KISS/AX.25 válidas al Client.',
      'A porta está aberta e há bytes chegando, mas não em KISS reconhecível. Verifique modo PKT/KISS, protocolo e baud rate; não mude o rádio para TNC interno apenas para fazer o indicador ficar ativo.':'El puerto está abierto y llegan bytes, pero no como KISS reconocible. Revise modo PKT/KISS, protocolo y baud rate; no cambie la radio al TNC interno solo para activar el indicador.',
      'Há frames KISS chegando, mas o conteúdo AX.25 não está sendo validado. Consulte o erro exibido e revise o modo/protocolo do equipamento.':'Llegan tramas KISS, pero el contenido AX.25 no se valida. Revise el error mostrado y el modo/protocolo del equipo.',
      'Porta serial aberta; aguardando o primeiro byte/frame. “Conectado” confirma apenas a abertura da porta.':'Puerto serie abierto; esperando el primer byte/trama. “Conectado” solo confirma que el puerto está abierto.',
      'KISS TCP conectado; aguardando o primeiro frame válido.':'KISS TCP conectado; esperando la primera trama válida.',
      'Duplicatas evitadas':'Duplicados evitados','janela configurável':'ventana configurable','Fila TX':'Cola TX','Otimizador':'Optimizador',
      'Conexão KISS':'Conexión KISS','Transporte':'Transporte','Conectar TNC ao iniciar':'Conectar TNC al iniciar','Porta TCP':'Puerto TCP','Porta serial':'Puerto serie','Selecione…':'Seleccione…',
      'Compatível com TNC físico em KISS e softwares como Dire Wolf por KISS TCP. APRS-IS e RF podem operar de forma independente.':'Compatible con TNC físicos KISS y software como Dire Wolf mediante KISS TCP. APRS-IS y RF pueden operar de forma independiente.',
      'Papel RF e segurança de TX':'Función RF y seguridad TX','Papel principal':'Función principal','Somente monitor':'Solo monitor','Estação local':'Estación local','iGate bidirecional':'iGate bidireccional',
      'Retenção do histórico':'Retención del historial','dias':'días','Habilitar transmissão automática em RF':'Habilitar transmisión automática por RF',
      'Confirmo que revisei indicativo, rádio, frequência e regras antes de permitir TX automático':'Confirmo que revisé indicativo, radio, frecuencia y reglas antes de permitir TX automático',
      'Segurança:':'Seguridad:','Digipeater inteligente':'Digipeater inteligente','Ativar Digipeater':'Activar Digipeater','Perfil':'Perfil','Personalizado':'Personalizado','Aliases personalizados':'Alias personalizados',
      'Separados por vírgula; usados no perfil Personalizado.':'Separados por comas; usados en el perfil Personalizado.','Máximo de hops repetidos':'Máximo de hops repetidos','Janela de duplicatas':'Ventana de duplicados','segundos':'segundos',
      'Rate limit por origem':'Límite por origen','pacotes/min':'paquetes/min','iGate inteligente':'iGate inteligente','APRS-IS → RF restritivo':'APRS-IS → RF restrictivo','Janela “ouvido por RF”':'Ventana “oído por RF”','minutos':'minutos','Path RF do iGate':'Path RF del iGate','vazio = direto':'vacío = directo',
      'Otimização “quem fala com quem”':'Optimización “quién habla con quién”','Modo':'Modo','Desligado':'Desactivado','Observação / recomendação':'Observación / recomendación','Automático conservador':'Automático conservador',
      'Aguardando dados.':'Esperando datos.','Aplicar configuração':'Aplicar configuración','Salvar TNC / RF':'Guardar TNC / RF','Monitor TNC':'Monitor TNC','Frames AX.25/APRS recebidos e transmitidos.':'Tramas AX.25/APRS recibidas y transmitidas.','Atualizar':'Actualizar',
      'Hora':'Hora','Dir.':'Dir.','Origem':'Origen','Destino':'Destino','Tipo':'Tipo','Pacote TNC2':'Paquete TNC2','Sem frames.':'Sin tramas.',
      'Decisões Digi / iGate':'Decisiones Digi / iGate','Auditoria do que foi enviado, suprimido ou bloqueado.':'Auditoría de lo enviado, suprimido o bloqueado.','Ação':'Acción','Decisão':'Decisión','Motivo':'Motivo','Sem decisões.':'Sin decisiones.',
      'Estações ouvidas por RF':'Estaciones oídas por RF','Presença local usada pelo iGate inteligente.':'Presencia local usada por el iGate inteligente.','Estação':'Estación','Última RF':'Última RF','Direta':'Directa','Contagem':'Conteo','Recepções':'Recepciones','Pacotes RF':'Paquetes RF','Distância':'Distancia','Último tipo':'Último tipo','Nenhuma estação ouvida pelo TNC.':'Ninguna estación oída por el TNC.',
      'Quem fala com quem':'Quién habla con quién','Grafo textual consolidado das interações RF e APRS-IS.':'Grafo textual consolidado de interacciones RF y APRS-IS.','Meio':'Medio','Interações':'Interacciones','Última':'Última','Aguardando interações.':'Esperando interacciones.',
      'TX automático, Digipeater e iGate Internet→RF vêm desligados por padrão. O botão PARAR TX interrompe imediatamente novas transmissões sem derrubar o monitor RX.':'TX automático, Digipeater e iGate Internet→RF vienen desactivados por defecto. DETENER TX bloquea inmediatamente nuevas transmisiones sin detener el monitor RX.',
      'O digi usa supressão de duplicatas, bloqueio de loop, limite de hops e fila com prioridade para mensagens/ACK/REJ.':'El digi usa supresión de duplicados, bloqueo de bucles, límite de hops y cola con prioridad para mensajes/ACK/REJ.',
      'Ex.: WIDE1-1. Prefira vazio quando a cobertura direta for suficiente.':'Ej.: WIDE1-1. Prefiera vacío cuando la cobertura directa sea suficiente.',
      'Internet→RF só considera mensagens cujo destino tenha sido ouvido diretamente por RF dentro da janela configurada. Tráfego Internet genérico não é despejado no canal.':'Internet→RF solo considera mensajes cuyo destino haya sido oído directamente por RF dentro de la ventana configurada. El tráfico genérico de Internet no se vuelca al canal.',
      'O grafo usa mensagens, ACK/REJ e presença RF para priorizar tráfego útil e evitar repetição desnecessária. Ele não reescreve arbitrariamente paths de terceiros nem inventa enlaces RF.':'El grafo usa mensajes, ACK/REJ y presencia RF para priorizar tráfico útil y evitar repeticiones innecesarias. No reescribe arbitrariamente paths de terceros ni inventa enlaces RF.',
      'Alterações de transporte reconectam o TNC se ele já estiver em uso. Ativar funções de TX exige a confirmação explícita acima.':'Los cambios de transporte reconectan el TNC si ya está en uso. Activar funciones TX requiere la confirmación explícita anterior.',
      'Ativado':'Activado','Desconectado':'Desconectado','Observação':'Observación','TX automático desligado':'TX automático desactivado','não detectada agora':'no detectado ahora','Configuração TNC / RF salva.':'Configuración TNC / RF guardada.','Sim':'Sí','Via digi':'Vía digi',
      'TX automático, Digipeater e iGate Internet→RF vêm desligados por padrão. O botão':'TX automático, Digipeater e iGate Internet→RF vienen desactivados por defecto. El botón',
      'interrompe imediatamente novas transmissões sem derrubar o monitor RX.':'bloquea inmediatamente nuevas transmisiones sin detener el monitor RX.',
      'Internet→RF só considera mensagens cujo destino tenha sido ouvido':'Internet→RF solo considera mensajes cuyo destino haya sido oído',
      'diretamente':'directamente','por RF dentro da janela configurada. Tráfego Internet genérico não é despejado no canal.':'por RF dentro de la ventana configurada. El tráfico genérico de Internet no se vuelca al canal.',
      'Liberar novamente a transmissão automática em RF com a configuração atual?':'¿Reanudar la transmisión RF automática con la configuración actual?',
      'Equipamentos seriais detectados':'Equipos serie detectados','Portas encontradas pelo pyserial e, no Windows, também pela enumeração nativa do sistema.':'Puertos encontrados por pyserial y, en Windows, también por la enumeración nativa del sistema.',
      'Reescanear':'Volver a buscar','Equipamento':'Equipo','Interface':'Interfaz','Fabricante':'Fabricante','Nº de série / HWID':'N.º de serie / HWID','Status':'Estado','Usar':'Usar',
      'Aguardando leitura das portas seriais.':'Esperando lectura de puertos serie.','Nenhum equipamento serial lido ainda.':'Aún no se ha leído ningún equipo serie.',
      'O Client não atribui um modelo de rádio apenas pelo chipset USB. Quando o Windows não informar o modelo real, a interface é mostrada de forma genérica, por exemplo USB Serial — CH9102.':'El Client no asigna un modelo de radio solo por el chipset USB. Si Windows no informa el modelo real, la interfaz se muestra de forma genérica, por ejemplo USB Serial — CH9102.',
      'Selecione um equipamento detectado abaixo ou informe manualmente uma porta COM.':'Seleccione un equipo detectado abajo o introduzca manualmente un puerto COM.',
      'Conectado pelo Client':'Conectado por el Client','Configurado':'Configurado','Erro do dispositivo':'Error del dispositivo','Detectado':'Detectado',
      'equipamento/porta detectado':'equipo/puerto detectado','equipamentos/portas detectados':'equipos/puertos detectados',
      'Nenhuma porta serial detectada pelo sistema.':'No se detectó ningún puerto serie.','Nenhum equipamento serial detectado. Você ainda pode informar a COM manualmente.':'No se detectó ningún equipo serie. Aún puede introducir el puerto COM manualmente.',
      'Equipamento serial não identificado':'Equipo serie no identificado','Não foi possível listar as portas seriais:':'No fue posible listar los puertos serie:',
      'Radtel RT-950 Pro detectado: no modo TNC UART, use normalmente 115200 bps e TNC Type/KISS habilitado no rádio.':'Radtel RT-950 Pro detectado: en modo TNC UART, use normalmente 115200 bps y TNC Type/KISS habilitado en la radio.',
      'Interface CH9102 detectada. Se esta porta pertencer a um Radtel RT-950 Pro em TNC UART, configure 115200 bps e habilite TNC/KISS no rádio.':'Interfaz CH9102 detectada. Si este puerto pertenece a un Radtel RT-950 Pro en TNC UART, configure 115200 bps y habilite TNC/KISS en la radio.'
    },
    fr: {
      'KISS Serial/TCP, monitor AX.25, Digipeater, iGate e análise adaptativa de quem fala com quem.':'KISS série/TCP, moniteur AX.25, Digipeater, iGate et analyse adaptative des communications.',
      'Atualizar portas':'Actualiser les ports','Conectar TNC':'Connecter le TNC','Desconectar':'Déconnecter','PARAR TX':'ARRÊTER TX','Liberar TX':'Reprendre TX',
      'Estado':'État',
      'RX KISS/AX.25':'RX KISS/AX.25','TX entregue ao TNC':'TX remis au TNC','Diagnóstico do transporte:':'Diagnostic du transport :',
      'Serial conectada':'Série connectée','Serial operacional — RX KISS ativo':'Série opérationnelle — RX KISS actif','Serial conectada — sem KISS':'Série connectée — sans KISS','Serial conectada — AX.25 inválido':'Série connectée — AX.25 invalide','Serial conectada — aguardando dados':'Série connectée — en attente','KISS TCP operacional — RX ativo':'KISS TCP opérationnel — RX actif','KISS TCP conectado — aguardando frames':'KISS TCP connecté — en attente de trames','RX KISS ativo':'RX KISS actif','Serial sem KISS':'Série sans KISS','AX.25 inválido':'AX.25 invalide','Serial aguardando':'Série en attente','KISS aguardando':'KISS en attente','KISS TCP conectado':'KISS TCP connecté','RX ativo':'RX actif','Aguardando dados do TNC.':'En attente des données du TNC.',
      'Transporte desconectado.':'Transport déconnecté.','bytes recebidos pela serial, mas nenhum frame KISS válido foi reconhecido.':'octets reçus sur le port série, mais aucune trame KISS valide n’a été reconnue.',
      'frame(s) AX.25 inválido(s)':'trame(s) AX.25 invalide(s)','Nenhum frame entregue ao TNC nesta conexão.':'Aucune trame remise au TNC pendant cette connexion.',
      'bytes entregues ao transporte':'octets remis au transport','emissão RF não confirmada pelo Client':'émission RF non confirmée par le Client',
      'Desconectado.':'Déconnecté.','Transporte operacional: frames KISS/AX.25 válidos estão chegando ao Client.':'Transport opérationnel : des trames KISS/AX.25 valides arrivent au Client.',
      'A porta está aberta e há bytes chegando, mas não em KISS reconhecível. Verifique modo PKT/KISS, protocolo e baud rate; não mude o rádio para TNC interno apenas para fazer o indicador ficar ativo.':'Le port est ouvert et des octets arrivent, mais pas sous forme KISS reconnue. Vérifiez le mode PKT/KISS, le protocole et le débit ; ne passez pas la radio sur son TNC interne uniquement pour activer l’indicateur.',
      'Há frames KISS chegando, mas o conteúdo AX.25 não está sendo validado. Consulte o erro exibido e revise o modo/protocolo do equipamento.':'Des trames KISS arrivent, mais le contenu AX.25 n’est pas validé. Consultez l’erreur affichée et vérifiez le mode/protocole de l’équipement.',
      'Porta serial aberta; aguardando o primeiro byte/frame. “Conectado” confirma apenas a abertura da porta.':'Port série ouvert ; en attente du premier octet/trame. « Connecté » confirme uniquement l’ouverture du port.',
      'KISS TCP conectado; aguardando o primeiro frame válido.':'KISS TCP connecté ; en attente de la première trame valide.',
      'Duplicatas evitadas':'Doublons évités','janela configurável':'fenêtre configurable','Fila TX':'File TX','Otimizador':'Optimiseur',
      'Conexão KISS':'Connexion KISS','Transporte':'Transport','Conectar TNC ao iniciar':'Connecter le TNC au démarrage','Porta TCP':'Port TCP','Porta serial':'Port série','Selecione…':'Sélectionner…',
      'Compatível com TNC físico em KISS e softwares como Dire Wolf por KISS TCP. APRS-IS e RF podem operar de forma independente.':'Compatible avec les TNC physiques KISS et les logiciels comme Dire Wolf via KISS TCP. APRS-IS et RF peuvent fonctionner indépendamment.',
      'Papel RF e segurança de TX':'Rôle RF et sécurité TX','Papel principal':'Rôle principal','Somente monitor':'Moniteur uniquement','Estação local':'Station locale','iGate bidirecional':'iGate bidirectionnel',
      'Retenção do histórico':'Rétention de l’historique','dias':'jours','Habilitar transmissão automática em RF':'Activer la transmission RF automatique',
      'Confirmo que revisei indicativo, rádio, frequência e regras antes de permitir TX automático':'Je confirme avoir vérifié l’indicatif, la radio, la fréquence et les règles avant d’autoriser le TX automatique',
      'Segurança:':'Sécurité :','Digipeater inteligente':'Digipeater intelligent','Ativar Digipeater':'Activer le Digipeater','Perfil':'Profil','Personalizado':'Personnalisé','Aliases personalizados':'Alias personnalisés',
      'Separados por vírgula; usados no perfil Personalizado.':'Séparés par des virgules ; utilisés avec le profil Personnalisé.','Máximo de hops repetidos':'Nombre maximal de hops répétés','Janela de duplicatas':'Fenêtre des doublons','segundos':'secondes',
      'Rate limit por origem':'Limite par source','pacotes/min':'paquets/min','iGate inteligente':'iGate intelligent','APRS-IS → RF restritivo':'APRS-IS → RF restrictif','Janela “ouvido por RF”':'Fenêtre « entendu en RF »','minutos':'minutes','Path RF do iGate':'Path RF de l’iGate','vazio = direto':'vide = direct',
      'Otimização “quem fala com quem”':'Optimisation « qui parle à qui »','Modo':'Mode','Desligado':'Désactivé','Observação / recomendação':'Observation / recommandation','Automático conservador':'Automatique conservateur',
      'Aguardando dados.':'En attente de données.','Aplicar configuração':'Appliquer la configuration','Salvar TNC / RF':'Enregistrer TNC / RF','Monitor TNC':'Moniteur TNC','Frames AX.25/APRS recebidos e transmitidos.':'Trames AX.25/APRS reçues et transmises.','Atualizar':'Actualiser',
      'Hora':'Heure','Dir.':'Dir.','Origem':'Source','Destino':'Destination','Tipo':'Type','Pacote TNC2':'Paquet TNC2','Sem frames.':'Aucune trame.',
      'Decisões Digi / iGate':'Décisions Digi / iGate','Auditoria do que foi enviado, suprimido ou bloqueado.':'Audit de ce qui a été envoyé, supprimé ou bloqué.','Ação':'Action','Decisão':'Décision','Motivo':'Motif','Sem decisões.':'Aucune décision.',
      'Estações ouvidas por RF':'Stations entendues en RF','Presença local usada pelo iGate inteligente.':'Présence locale utilisée par l’iGate intelligent.','Estação':'Station','Última RF':'Dernière RF','Direta':'Directe','Contagem':'Nombre','Recepções':'Réceptions','Pacotes RF':'Paquets RF','Distância':'Distance','Último tipo':'Dernier type','Nenhuma estação ouvida pelo TNC.':'Aucune station entendue par le TNC.',
      'Quem fala com quem':'Qui parle à qui','Grafo textual consolidado das interações RF e APRS-IS.':'Graphe textuel consolidé des interactions RF et APRS-IS.','Meio':'Média','Interações':'Interactions','Última':'Dernière','Aguardando interações.':'En attente d’interactions.',
      'TX automático, Digipeater e iGate Internet→RF vêm desligados por padrão. O botão PARAR TX interrompe imediatamente novas transmissões sem derrubar o monitor RX.':'Le TX automatique, le Digipeater et l’iGate Internet→RF sont désactivés par défaut. ARRÊTER TX bloque immédiatement les nouvelles transmissions sans arrêter le moniteur RX.',
      'O digi usa supressão de duplicatas, bloqueio de loop, limite de hops e fila com prioridade para mensagens/ACK/REJ.':'Le digi utilise la suppression des doublons, le blocage des boucles, une limite de hops et une file prioritaire pour les messages/ACK/REJ.',
      'Ex.: WIDE1-1. Prefira vazio quando a cobertura direta for suficiente.':'Ex. : WIDE1-1. Laissez vide lorsque la couverture directe est suffisante.',
      'Internet→RF só considera mensagens cujo destino tenha sido ouvido diretamente por RF dentro da janela configurada. Tráfego Internet genérico não é despejado no canal.':'Internet→RF ne considère que les messages dont le destinataire a été entendu directement en RF dans la fenêtre configurée. Le trafic Internet générique n’est pas injecté sur le canal.',
      'O grafo usa mensagens, ACK/REJ e presença RF para priorizar tráfego útil e evitar repetição desnecessária. Ele não reescreve arbitrariamente paths de terceiros nem inventa enlaces RF.':'Le graphe utilise les messages, ACK/REJ et la présence RF pour prioriser le trafic utile et éviter les répétitions inutiles. Il ne réécrit pas arbitrairement les paths tiers et n’invente pas de liaisons RF.',
      'Alterações de transporte reconectam o TNC se ele já estiver em uso. Ativar funções de TX exige a confirmação explícita acima.':'Les changements de transport reconnectent le TNC s’il est déjà utilisé. L’activation des fonctions TX exige la confirmation explicite ci-dessus.',
      'Ativado':'Activé','Desconectado':'Déconnecté','Observação':'Observation','TX automático desligado':'TX automatique désactivé','não detectada agora':'non détecté actuellement','Configuração TNC / RF salva.':'Configuration TNC / RF enregistrée.','Sim':'Oui','Via digi':'Via digi',
      'TX automático, Digipeater e iGate Internet→RF vêm desligados por padrão. O botão':'Le TX automatique, le Digipeater et l’iGate Internet→RF sont désactivés par défaut. Le bouton',
      'interrompe imediatamente novas transmissões sem derrubar o monitor RX.':'bloque immédiatement les nouvelles transmissions sans arrêter le moniteur RX.',
      'Internet→RF só considera mensagens cujo destino tenha sido ouvido':'Internet→RF ne considère que les messages dont le destinataire a été entendu',
      'diretamente':'directement','por RF dentro da janela configurada. Tráfego Internet genérico não é despejado no canal.':'en RF dans la fenêtre configurée. Le trafic Internet générique n’est pas injecté sur le canal.',
      'Liberar novamente a transmissão automática em RF com a configuração atual?':'Reprendre la transmission RF automatique avec la configuration actuelle ?',
      'Equipamentos seriais detectados':'Équipements série détectés','Portas encontradas pelo pyserial e, no Windows, também pela enumeração nativa do sistema.':'Ports trouvés par pyserial et, sous Windows, également par l’énumération native du système.',
      'Reescanear':'Réanalyser','Equipamento':'Équipement','Interface':'Interface','Fabricante':'Fabricant','Nº de série / HWID':'N° de série / HWID','Status':'État','Usar':'Utiliser',
      'Aguardando leitura das portas seriais.':'En attente de l’analyse des ports série.','Nenhum equipamento serial lido ainda.':'Aucun équipement série lu pour le moment.',
      'O Client não atribui um modelo de rádio apenas pelo chipset USB. Quando o Windows não informar o modelo real, a interface é mostrada de forma genérica, por exemplo USB Serial — CH9102.':'Le Client n’attribue pas un modèle de radio à partir du seul chipset USB. Si Windows n’indique pas le modèle réel, l’interface est affichée de façon générique, par exemple USB Serial — CH9102.',
      'Selecione um equipamento detectado abaixo ou informe manualmente uma porta COM.':'Sélectionnez un équipement détecté ci-dessous ou saisissez manuellement un port COM.',
      'Conectado pelo Client':'Connecté par le Client','Configurado':'Configuré','Erro do dispositivo':'Erreur du périphérique','Detectado':'Détecté',
      'equipamento/porta detectado':'équipement/port détecté','equipamentos/portas detectados':'équipements/ports détectés',
      'Nenhuma porta serial detectada pelo sistema.':'Aucun port série détecté par le système.','Nenhum equipamento serial detectado. Você ainda pode informar a COM manualmente.':'Aucun équipement série détecté. Vous pouvez toujours saisir manuellement le port COM.',
      'Equipamento serial não identificado':'Équipement série non identifié','Não foi possível listar as portas seriais:':'Impossible de lister les ports série :',
      'Radtel RT-950 Pro detectado: no modo TNC UART, use normalmente 115200 bps e TNC Type/KISS habilitado no rádio.':'Radtel RT-950 Pro détecté : en mode TNC UART, utilisez normalement 115200 bps avec TNC Type/KISS activé sur la radio.',
      'Interface CH9102 detectada. Se esta porta pertencer a um Radtel RT-950 Pro em TNC UART, configure 115200 bps e habilite TNC/KISS no rádio.':'Interface CH9102 détectée. Si ce port appartient à un Radtel RT-950 Pro en TNC UART, réglez 115200 bps et activez TNC/KISS sur la radio.'
    }
  };

  function tncLanguage() {
    const lang = String(document.documentElement.lang || 'pt-BR').toLowerCase();
    if (lang.startsWith('en')) return 'en';
    if (lang.startsWith('es')) return 'es';
    if (lang.startsWith('fr')) return 'fr';
    return 'pt-BR';
  }

  function tr(pt) {
    const lang = tncLanguage();
    return lang === 'pt-BR' ? pt : (TNC_I18N[lang]?.[pt] || pt);
  }

  function translateTncStatic() {
    for (const root of [$('#tab-tnc'), $('#tncHeaderStatus')].filter(Boolean)) {
      const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
      const nodes = [];
      while (walker.nextNode()) nodes.push(walker.currentNode);
      for (const node of nodes) {
        const parent = node.parentElement;
        if (!parent || ['SCRIPT','STYLE','CODE'].includes(parent.tagName)) continue;
        if (node._pt2vhfTncOriginal === undefined) {
          node._pt2vhfTncOriginal = node._pt2vhfOriginalText !== undefined ? node._pt2vhfOriginalText : node.nodeValue;
        }
        const original = node._pt2vhfOriginalText !== undefined ? node._pt2vhfOriginalText : node._pt2vhfTncOriginal;
        const trimmed = original.trim();
        if (!trimmed) continue;
        const lead = original.match(/^\s*/)?.[0] || '';
        const trail = original.match(/\s*$/)?.[0] || '';
        node.nodeValue = lead + tr(trimmed) + trail;
      }
      for (const el of root.querySelectorAll?.('[placeholder],[title],[aria-label]') || []) {
        for (const attr of ['placeholder','title','aria-label']) {
          if (!el.hasAttribute(attr)) continue;
          const key = 'tncOriginal' + attr.replace(/[^a-z0-9]/gi,'_');
          const appKey = 'i18n' + attr.replace(/[^a-z0-9]/gi,'_');
          if (!(key in el.dataset)) el.dataset[key] = el.dataset[appKey] || el.getAttribute(attr) || '';
          el.setAttribute(attr, tr(el.dataset[appKey] || el.dataset[key]));
        }
      }
    }
  }

  function localizeBackendMessage(value) {
    const text = String(value || '');
    const maps = {
      en: {
        'Confirme explicitamente a habilitação de transmissão automática em RF.':'Confirm explicit enablement of automatic RF transmission.',
        'Digipeater/iGate TX exige a chave Transmissão automática habilitada.':'Digipeater/iGate TX requires Automatic transmission to be enabled.',
        'Selecione a porta serial do TNC.':'Select the TNC serial port.',
        'Informe o host do KISS TCP.':'Enter the KISS TCP host.',
        'TX automático não está habilitado e confirmado na configuração.':'Automatic TX is not enabled and confirmed in settings.',
        'TNC desconectado.':'TNC disconnected.'
      },
      es: {
        'Confirme explicitamente a habilitação de transmissão automática em RF.':'Confirme explícitamente la habilitación de transmisión RF automática.',
        'Digipeater/iGate TX exige a chave Transmissão automática habilitada.':'Digipeater/iGate TX requiere Transmisión automática habilitada.',
        'Selecione a porta serial do TNC.':'Seleccione el puerto serie del TNC.',
        'Informe o host do KISS TCP.':'Informe el host de KISS TCP.',
        'TX automático não está habilitado e confirmado na configuração.':'TX automático no está habilitado y confirmado en la configuración.',
        'TNC desconectado.':'TNC desconectado.'
      },
      fr: {
        'Confirme explicitamente a habilitação de transmissão automática em RF.':'Confirmez explicitement l’activation de la transmission RF automatique.',
        'Digipeater/iGate TX exige a chave Transmissão automática habilitada.':'Digipeater/iGate TX exige que Transmission automatique soit activée.',
        'Selecione a porta serial do TNC.':'Sélectionnez le port série du TNC.',
        'Informe o host do KISS TCP.':'Indiquez l’hôte KISS TCP.',
        'TX automático não está habilitado e confirmado na configuração.':'Le TX automatique n’est pas activé et confirmé dans la configuration.',
        'TNC desconectado.':'TNC déconnecté.'
      }
    };
    const lang = tncLanguage();
    return lang === 'pt-BR' ? text : (maps[lang]?.[text] || text);
  }

  let lastConfig = null;
  let lastSerialPorts = [];
  let initialized = false;
  let pollTimer = null;
  let serialPollTick = 0;

  async function requestJson(url, options = {}) {
    const response = await fetch(url, {
      cache: 'no-store',
      headers: {'Content-Type':'application/json', ...(options.headers || {})},
      ...options,
    });
    let payload = {};
    try { payload = await response.json(); } catch (_) {}
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.error || `HTTP ${response.status}`);
    }
    return payload;
  }

  function showError(error = '') {
    const box = $('#tncError');
    if (!box) return;
    box.textContent = localizeBackendMessage(error);
    box.classList.toggle('hidden', !error);
  }

  function statusClass(connected, paused, rxState = 'waiting') {
    if (paused || !connected) return 'status disconnected';
    return rxState === 'active' ? 'status connected' : 'status warning';
  }

  function humanTime(value) {
    if (!value) return '—';
    const d = new Date(value);
    if (Number.isNaN(d.getTime())) return String(value);
    return d.toLocaleString();
  }

  function roleLabel(role) {
    return ({
      monitor:tr('Somente monitor'), station:tr('Estação local'), digi:'Digipeater',
      igate_rx:'iGate RX-only', igate_bidir:tr('iGate bidirecional'), digi_igate:'Digi + iGate'
    })[role] || role || '—';
  }

  function optimizerLabel(mode) {
    return ({off:tr('Desligado'), observe:tr('Observação / recomendação'), automatic:tr('Automático conservador')})[mode] || mode || '—';
  }

  function setStatus(payload = {}) {
    const status = payload.status || payload;
    const connected = !!status.connected;
    const transportMode = String(status.transport || '');
    const serial = connected && transportMode === 'serial';
    const agwpe = connected && transportMode === 'agwpe';
    const rxState = String(status.rx_state || (connected ? 'waiting' : 'disconnected'));
    const txState = String(status.tx_state || (connected ? 'waiting' : 'disconnected'));
    const bytesRx = Number(status.transport_bytes_rx || 0);
    const bytesTx = Number(status.transport_bytes_tx || 0);
    const kissFrames = Number(status.kiss_frames_rx || 0);
    const invalidFrames = Number(status.invalid_frames_rx || 0);

    const transportLabel = !connected
      ? tr('Desconectado')
      : serial
        ? (rxState === 'active'
          ? tr('Serial operacional — RX KISS ativo')
          : rxState === 'terminal_bytes_active'
            ? 'Serial terminal ativa'
          : rxState === 'bytes_without_kiss'
            ? tr('Serial conectada — sem KISS')
            : rxState === 'invalid'
              ? tr('Serial conectada — AX.25 inválido')
              : tr('Serial conectada — aguardando dados'))
        : agwpe
          ? (rxState === 'active' ? 'AGWPE · ' + tr('RX ativo') : 'AGWPE · ' + tr('Aguardando dados do TNC.'))
          : (rxState === 'active'
            ? tr('KISS TCP operacional — RX ativo')
            : tr('KISS TCP conectado — aguardando frames'));

    let rxDetail = tr('Aguardando dados do TNC.');
    let diagnosticState = 'waiting';
    if (!connected) {
      rxDetail = tr('Transporte desconectado.');
      diagnosticState = 'idle';
    } else if (rxState === 'active') {
      rxDetail = `${tr('RX ativo')} · ${status.last_rx_at ? `${tr('Última')}: ${humanTime(status.last_rx_at)}` : ''}`;
      diagnosticState = 'good';
    } else if (rxState === 'terminal_bytes_active') {
      rxDetail = `${bytesRx.toLocaleString()} bytes recebidos em protocolo terminal/PKT`;
      diagnosticState = 'good';
    } else if (rxState === 'bytes_without_kiss') {
      rxDetail = `${bytesRx.toLocaleString()} ${tr('bytes recebidos pela serial, mas nenhum frame KISS válido foi reconhecido.')}`;
      diagnosticState = 'warn';
    } else if (rxState === 'invalid') {
      rxDetail = `${kissFrames.toLocaleString()} KISS · ${invalidFrames.toLocaleString()} ${tr('frame(s) AX.25 inválido(s)')}${status.last_rx_error ? ` · ${status.last_rx_error}` : ''}`;
      diagnosticState = 'warn';
    }

    let txDetail = tr('Nenhum frame entregue ao TNC nesta conexão.');
    if (!connected) {
      txDetail = tr('Transporte desconectado.');
    } else if (txState === 'delivered') {
      txDetail = `${bytesTx.toLocaleString()} ${tr('bytes entregues ao transporte')} · ${status.last_tx_at ? `${tr('Última')}: ${humanTime(status.last_tx_at)}` : ''} · ${tr('emissão RF não confirmada pelo Client')}`;
    }

    const header = $('#tncHeaderStatus');
    if (header) {
      header.className = `${statusClass(connected, !!status.tx_paused, rxState)} tnc-header-status`;
      const text = header.querySelector('span:last-child');
      if (text) {
        text.textContent = !connected
          ? 'TNC offline'
          : rxState === 'active'
            ? `TNC · ${tr('RX KISS ativo')}`
            : serial && rxState === 'terminal_bytes_active'
              ? 'TNC · Terminal ativo'
            : serial && rxState === 'bytes_without_kiss'
              ? `TNC · ${tr('Serial sem KISS')}`
              : serial && rxState === 'invalid'
                ? `TNC · ${tr('AX.25 inválido')}`
                : serial
                  ? `TNC · ${tr('Serial aguardando')}`
                  : agwpe ? 'TNC · AGWPE' : `TNC · ${tr('KISS aguardando')}`;
      }
      header.title = [status.state, status.endpoint, rxDetail, status.last_error].filter(Boolean).join(' · ');
    }

    const pairs = [
      ['#tncMetricState', transportLabel],
      ['#tncMetricEndpoint', status.endpoint || '—'],
      ['#tncMetricRx', Number(status.frames_rx || 0).toLocaleString()],
      ['#tncMetricTx', Number(status.frames_tx || 0).toLocaleString()],
      ['#tncMetricDuplicates', Number(status.duplicates_suppressed || 0).toLocaleString()],
      ['#tncMetricQueue', Number(status.tx_queue || 0).toLocaleString()],
      ['#tncMetricLastRx', rxDetail],
      ['#tncMetricLastTx', txDetail],
      ['#tncMetricTxState', status.tx_paused ? tr('PARAR TX') : (lastConfig?.auto_tx_enabled ? tr('Ativado') : tr('Desligado'))],
      ['#tncMetricOptimizer', optimizerLabel(status.optimizer_mode || lastConfig?.optimizer_mode)],
      ['#tncMetricRole', roleLabel(status.role || lastConfig?.role)],
    ];
    for (const [selector, value] of pairs) {
      const el = $(selector);
      if (el) el.textContent = value;
    }

    const diagnostic = $('#tncTransportDiagnostic');
    const diagnosticText = $('#tncTransportDiagnosticText');
    if (diagnostic) diagnostic.dataset.state = diagnosticState;
    if (diagnosticText) {
      if (!connected) {
        diagnosticText.textContent = tr('Desconectado.');
      } else if (rxState === 'active') {
        diagnosticText.textContent = tr('Transporte operacional: frames KISS/AX.25 válidos estão chegando ao Client.');
      } else if (rxState === 'terminal_bytes_active') {
        const profile=String(status.device_profile||lastConfig?.device_profile||'');
        diagnosticText.textContent = profile==='kenwood_tm_d700'
          ? 'Kenwood TM-D700 em modo terminal/PKT: porta aberta e bytes chegando. Isto é compatível com o perfil selecionado; não existe exigência de menu KISS neste modo. Serial e packet RF possuem velocidades independentes.'
          : 'Porta serial ativa em protocolo terminal/TNC. Bytes estão chegando; KISS não é o protocolo esperado para este perfil.';
      } else if (rxState === 'bytes_without_kiss') {
        diagnosticText.textContent = 'A porta está aberta e há bytes chegando, mas KISS é o protocolo esperado e nenhum frame KISS foi reconhecido. Verifique protocolo/configuração e baud rate da interface.';
      } else if (rxState === 'invalid') {
        diagnosticText.textContent = tr('Há frames KISS chegando, mas o conteúdo AX.25 não está sendo validado. Consulte o erro exibido e revise o modo/protocolo do equipamento.');
      } else {
        diagnosticText.textContent = serial
          ? tr('Porta serial aberta; aguardando o primeiro byte/frame. “Conectado” confirma apenas a abertura da porta.')
          : agwpe
            ? 'AGWPE conectado; aguardando frame AX.25 bruto (raw mode).'
            : tr('KISS TCP conectado; aguardando o primeiro frame válido.');
      }
    }

    const sampleBox=$('#tncDiagnosticSample'),sampleAscii=$('#tncDiagnosticAscii'),sampleHex=$('#tncDiagnosticHex');
    const sampleA=String(status.last_transport_sample_ascii||''),sampleH=String(status.last_transport_sample_hex||'');
    if(sampleBox)sampleBox.classList.toggle('hidden',!connected||(!sampleA&&!sampleH));
    if(sampleAscii)sampleAscii.textContent=sampleA||'—';
    if(sampleHex)sampleHex.textContent=sampleH||'—';

    $('#tncConnect')?.toggleAttribute('disabled', connected);
    $('#tncDisconnect')?.toggleAttribute('disabled', !connected);
    $('#tncEmergencyStop')?.toggleAttribute('disabled', !!status.tx_paused);
    $('#tncResumeTx')?.toggleAttribute('disabled', !status.tx_paused);
  }

  function field(id) { return document.getElementById(id); }
  function checked(id) { return !!field(id)?.checked; }
  function val(id, fallback = '') { return field(id)?.value ?? fallback; }

  function collectConfig() {
    return {
      transport: val('tncTransport', 'tcp'),
      serial_port: val('tncSerialPort'),
      serial_baud: Number(val('tncSerialBaud', 9600)),
      device_profile: val('tncDeviceProfile', 'generic_kiss'),
      serial_protocol: val('tncSerialProtocol', 'kiss'),
      packet_rf_baud: Number(val('tncPacketRfBaud', 1200)),
      tcp_host: String(val('tncTcpHost', '127.0.0.1')).trim(),
      tcp_port: Number(val('tncTcpPort', 8001)),
      agwpe_host: String(val('tncAgwpeHost', '127.0.0.1')).trim(),
      agwpe_port: Number(val('tncAgwpePort', 8000)),
      agwpe_radio_port: Number(val('tncAgwpeRadioPort', 0)),
      auto_connect: checked('tncAutoConnect'),
      role: val('tncRole', 'monitor'),
      auto_tx_enabled: checked('tncAutoTxEnabled'),
      tx_confirmed: checked('tncTxConfirmed'),
      digi_enabled: checked('tncDigiEnabled'),
      digi_profile: val('tncDigiProfile', 'fill'),
      digi_aliases: String(val('tncDigiAliases')).trim(),
      digi_max_hops: Number(val('tncDigiMaxHops', 3)),
      duplicate_window_seconds: Number(val('tncDuplicateWindow', 30)),
      source_rate_limit_per_minute: Number(val('tncSourceRate', 30)),
      igate_rx_enabled: checked('tncIgateRx'),
      igate_tx_enabled: checked('tncIgateTx'),
      igate_heard_window_minutes: Number(val('tncIgateHeardWindow', 30)),
      igate_rf_path: String(val('tncIgateRfPath')).trim(),
      optimizer_mode: val('tncOptimizerMode', 'observe'),
      retention_days: Number(val('tncRetentionDays', 14)),
    };
  }

  function applyConfig(cfg = {}) {
    lastConfig = cfg;
    const values = {
      tncTransport: cfg.transport || 'tcp',
      tncSerialBaud: cfg.serial_baud ?? 9600,
      tncDeviceProfile: cfg.device_profile || 'generic_kiss',
      tncSerialProtocol: cfg.serial_protocol || 'kiss',
      tncPacketRfBaud: cfg.packet_rf_baud ?? 1200,
      tncTcpHost: cfg.tcp_host || '127.0.0.1',
      tncTcpPort: cfg.tcp_port ?? 8001,
      tncAgwpeHost: cfg.agwpe_host || '127.0.0.1',
      tncAgwpePort: cfg.agwpe_port ?? 8000,
      tncAgwpeRadioPort: cfg.agwpe_radio_port ?? 0,
      tncRole: cfg.role || 'monitor',
      tncDigiProfile: cfg.digi_profile || 'fill',
      tncDigiAliases: cfg.digi_aliases || '',
      tncDigiMaxHops: cfg.digi_max_hops ?? 3,
      tncDuplicateWindow: cfg.duplicate_window_seconds ?? 30,
      tncSourceRate: cfg.source_rate_limit_per_minute ?? 30,
      tncIgateHeardWindow: cfg.igate_heard_window_minutes ?? 30,
      tncIgateRfPath: cfg.igate_rf_path || '',
      tncOptimizerMode: cfg.optimizer_mode || 'observe',
      tncRetentionDays: cfg.retention_days ?? 14,
    };
    for (const [id, value] of Object.entries(values)) if (field(id)) field(id).value = String(value);
    const booleans = {
      tncAutoConnect: cfg.auto_connect,
      tncAutoTxEnabled: cfg.auto_tx_enabled,
      tncTxConfirmed: cfg.tx_confirmed,
      tncDigiEnabled: cfg.digi_enabled,
      tncIgateRx: cfg.igate_rx_enabled,
      tncIgateTx: cfg.igate_tx_enabled,
    };
    for (const [id, value] of Object.entries(booleans)) if (field(id)) field(id).checked = !!value;
    if (field('tncSerialPort') && cfg.serial_port) field('tncSerialPort').value = cfg.serial_port;
    syncTransportFields();
    updateSerialProfileHint();
  }

  function syncTransportFields() {
    const mode = val('tncTransport', 'tcp');
    const serialMode = mode === 'serial';
    const tcpMode = mode === 'tcp';
    const agwpeMode = mode === 'agwpe';
    $$('.tnc-serial-field').forEach(el => el.classList.toggle('hidden', !serialMode));
    $$('.tnc-tcp-field').forEach(el => el.classList.toggle('hidden', !tcpMode));
    $$('.tnc-agwpe-field').forEach(el => el.classList.toggle('hidden', !agwpeMode));
    if (serialMode) void loadPorts({quiet:true});
  }

  function applyRolePreset() {
    const role = val('tncRole', 'monitor');
    if (role === 'monitor' || role === 'station') {
      field('tncDigiEnabled').checked = false;
      field('tncIgateRx').checked = false;
      field('tncIgateTx').checked = false;
    } else if (role === 'digi') {
      field('tncDigiEnabled').checked = true;
      field('tncIgateRx').checked = false;
      field('tncIgateTx').checked = false;
    } else if (role === 'igate_rx') {
      field('tncDigiEnabled').checked = false;
      field('tncIgateRx').checked = true;
      field('tncIgateTx').checked = false;
    } else if (role === 'igate_bidir') {
      field('tncDigiEnabled').checked = false;
      field('tncIgateRx').checked = true;
      field('tncIgateTx').checked = true;
    } else if (role === 'digi_igate') {
      field('tncDigiEnabled').checked = true;
      field('tncIgateRx').checked = true;
      field('tncIgateTx').checked = true;
    }
  }

  function serialStatusBadge(port) {
    const status = String(port?.status || 'detected');
    const labels = {
      connected: tr('Conectado pelo Client'),
      configured: tr('Configurado'),
      device_error: port?.status_label || tr('Erro do dispositivo'),
      detected: tr('Detectado'),
    };
    const cls = status === 'connected' ? 'good' : (status === 'device_error' ? 'bad' : (status === 'configured' ? 'warn' : ''));
    return `<span class="tnc-badge ${cls}">${esc(labels[status] || port?.status_label || status)}</span>`;
  }

  function updateSerialProfileHint(port = null) {
    const hint = $('#tncSerialProfileHint');
    if (!hint) return;
    const profile=String(val('tncDeviceProfile','generic_kiss'));
    if(profile==='kenwood_tm_d700'||profile==='kenwood_tm_d710'){
      hint.textContent='Kenwood '+(profile==='kenwood_tm_d700'?'TM-D700':'TM-D710')+': o baud rate serial e o packet RF são parâmetros diferentes. Em modo terminal/PKT, KISS não é obrigatório.';
      hint.classList.remove('hidden');return;
    }
    if(profile==='kantronics'){
      hint.textContent='TNC terminal: bytes ASCII/comandos podem ser esperados. Use KISS apenas quando o equipamento estiver realmente configurado para KISS.';
      hint.classList.remove('hidden');return;
    }
    const device = String(val('tncSerialPort') || '').trim().toUpperCase();
    const item = port || lastSerialPorts.find(row => String(row.device || '').toUpperCase() === device);
    if (!device) { hint.textContent='';hint.classList.add('hidden');return; }
    const equipment=String(item?.equipment||''),chipset=String(item?.chipset||'');
    if (/RADTEL.*950|RT-950|RT950/i.test(equipment)) {
      hint.textContent=tr('Radtel RT-950 Pro detectado: no modo TNC UART, use normalmente 115200 bps e TNC Type/KISS habilitado no rádio.');
      hint.classList.remove('hidden');
      if (field('tncSerialBaud')) field('tncSerialBaud').value = '115200';
      return;
    }
    if (chipset==='CH9102') {
      hint.textContent=tr('Interface CH9102 detectada. Se esta porta pertencer a um Radtel RT-950 Pro em TNC UART, configure 115200 bps e habilite TNC/KISS no rádio.');
      hint.classList.remove('hidden');return;
    }
    hint.textContent='';hint.classList.add('hidden');
  }

  function renderSerialDevices(ports = []) {
    lastSerialPorts = Array.isArray(ports) ? ports : [];
    const body = $('#tncSerialDevicesBody');
    const summary = $('#tncSerialScanSummary');
    if (summary) summary.textContent = lastSerialPorts.length
      ? `${lastSerialPorts.length} ${lastSerialPorts.length === 1 ? tr('equipamento/porta detectado') : tr('equipamentos/portas detectados')}.`
      : tr('Nenhuma porta serial detectada pelo sistema.');
    if (!body) return;
    if (!lastSerialPorts.length) {
      body.innerHTML = `<tr><td colspan="8">${esc(tr('Nenhum equipamento serial detectado. Você ainda pode informar a COM manualmente.'))}</td></tr>`;
      updateSerialProfileHint();
      return;
    }
    body.innerHTML = lastSerialPorts.map(port => {
      const vidpid = [port.vid, port.pid].filter(Boolean).join(':') || '—';
      const serialHwid = [port.serial_number, port.hwid || port.pnp_device_id].filter(Boolean).join(' · ') || '—';
      const iface = port.chipset || port.interface || port.product || port.description || '—';
      const source = Array.isArray(port.sources) ? port.sources.join(', ') : '';
      return `<tr data-serial-device="${esc(port.device)}">
        <td><strong>${esc(port.device)}</strong></td>
        <td><strong>${esc(port.equipment || port.description || tr('Equipamento serial não identificado'))}</strong><small class="tnc-serial-source">${esc(source)}</small></td>
        <td>${esc(iface)}</td>
        <td>${esc(port.manufacturer || '—')}</td>
        <td><code>${esc(vidpid)}</code></td>
        <td class="tnc-serial-id" title="${esc(serialHwid)}">${esc(serialHwid)}</td>
        <td>${serialStatusBadge(port)}</td>
        <td><button type="button" class="btn secondary tnc-use-serial" data-tnc-use-port="${esc(port.device)}">${esc(tr('Usar'))}</button></td>
      </tr>`;
    }).join('');
    updateSerialProfileHint();
  }

  async function loadPorts({force = false, quiet = false, quick = false} = {}) {
    const input = field('tncSerialPort');
    const list = field('tncSerialPortList');
    if (!input || !list) return;
    const wanted = String(input.value || lastConfig?.serial_port || '').trim();
    try {
      const params = new URLSearchParams();
      if (force) params.set('refresh', '1');
      if (quick) params.set('quick', '1');
      const suffix = params.toString() ? `?${params.toString()}` : '';
      const data = await requestJson(`/api/tnc/ports${suffix}`);
      const ports = data.ports || [];
      list.innerHTML = '';
      for (const port of ports) {
        const opt = document.createElement('option');
        opt.value = port.device;
        opt.label = port.equipment && port.equipment !== port.device
          ? `${port.device} — ${port.equipment}`
          : (port.description ? `${port.device} — ${port.description}` : port.device);
        list.appendChild(opt);
      }
      input.value = wanted;
      renderSerialDevices(ports);
      if (!quiet) showError('');
    } catch (error) {
      if (!quiet) showError(tr('Não foi possível listar as portas seriais:') + ' ' + error.message);
    }
  }

  async function saveConfig({quiet = false} = {}) {
    const payload = collectConfig();
    const data = await requestJson('/api/tnc/config', {method:'POST', body:JSON.stringify(payload)});
    applyConfig(data.config || payload);
    setStatus(data.status || {});
    if (!quiet) {
      const out = $('#tncSaveStatus');
      if (out) {
        out.textContent = tr('Configuração TNC / RF salva.');
        setTimeout(() => { if (out.textContent.includes('salva')) out.textContent = ''; }, 3500);
      }
    }
    showError('');
    return data;
  }

  function renderFrames(rows = []) {
    const body = $('#tncFramesBody'); if (!body) return;
    if (!rows.length) { body.innerHTML = '<tr><td colspan="7">Sem frames.</td></tr>'; return; }
    body.innerHTML = rows.map(row => `<tr>
      <td>${esc(humanTime(row.timestamp))}</td><td><span class="tnc-badge ${row.direction==='TX'?'warn':'good'}">${esc(row.direction)}</span></td>
      <td>${esc(row.source)}</td><td>${esc(row.destination)}</td><td>${esc(row.packet_type)}</td>
      <td>${esc((row.path || []).join(', '))}</td><td title="${esc(row.reason)}"><code>${esc(row.raw_tnc2)}</code></td>
    </tr>`).join('');
  }

  function renderDecisions(rows = []) {
    const body = $('#tncDecisionsBody'); if (!body) return;
    if (!rows.length) { body.innerHTML = `<tr><td colspan="6">${tr('Sem decisões.')}</td></tr>`; return; }
    body.innerHTML = rows.map(row => {
      const cls = row.decision === 'sent' || row.decision === 'queued' ? 'good' : (row.decision === 'blocked' || row.decision === 'error' ? 'bad' : 'warn');
      return `<tr><td>${esc(humanTime(row.timestamp))}</td><td>${esc(row.action)}</td><td><span class="tnc-badge ${cls}">${esc(row.decision)}</span></td>
      <td>${esc(row.source)}</td><td>${esc(row.destination)}</td><td>${esc(row.reason)}</td></tr>`;
    }).join('');
  }

  function renderHeard(rows = []) {
    const body = $('#tncHeardBody'); if (!body) return;
    if (!rows.length) { body.innerHTML = `<tr><td colspan="8">${tr('Nenhuma estação ouvida pelo TNC.')}</td></tr>`; return; }
    body.innerHTML = rows.map(row => {
      const directLabel = row.direct_known === false ? '—' : (row.direct ? tr('Sim') : tr('Via digi'));
      const directClass = row.direct_known === false ? '' : (row.direct ? 'good' : 'warn');
      const hasDistance = row.distance_km !== null && row.distance_km !== undefined && row.distance_km !== '';
      const distance = hasDistance && Number.isFinite(Number(row.distance_km))
        ? `${Number(row.distance_km).toLocaleString(undefined,{maximumFractionDigits:2})} km`
        : '—';
      const path = (row.path || []).map(p => typeof p === 'string' ? p : (p.value || '') + (p.repeated ? '*' : '')).join(', ');
      return `<tr>
        <td><strong>${esc(row.callsign)}</strong></td>
        <td>${esc(humanTime(row.last_heard))}</td>
        <td><span class="tnc-badge ${directClass}">${esc(directLabel)}</span></td>
        <td>${Number(row.heard_count||0).toLocaleString()}</td>
        <td>${Number(row.rf_packet_count||0).toLocaleString()}</td>
        <td>${esc(distance)}</td>
        <td>${esc(row.last_packet_type || '')}</td>
        <td>${esc(path)}</td>
      </tr>`;
    }).join('');
  }

  function renderOptimizer(report = {}) {
    const stats = report.statistics || {};
    const body = $('#tncEdgesBody');
    if (body) {
      const edges = stats.top_edges || [];
      body.innerHTML = edges.length ? edges.map(row => `<tr><td>${esc(row.source)}</td><td>${esc(row.destination)}</td>
        <td><span class="tnc-badge ${row.medium==='RF'?'good':'warn'}">${esc(row.medium)}</span></td>
        <td>${Number(row.interactions||0).toLocaleString()}</td><td>${Number(row.ack_count||0).toLocaleString()}</td><td>${esc(humanTime(row.last_seen))}</td></tr>`).join('')
        : `<tr><td colspan="6">${tr('Aguardando interações.')}</td></tr>`;
    }
    const rec = $('#tncRecommendations');
    if (rec) {
      const rows = report.recommendations || [];
      rec.innerHTML = rows.map(item => `<div class="tnc-recommendation"><strong>${esc(item.title)}</strong><span>${esc(item.detail)}</span></div>`).join('') || `<span class="hint">${tr('Aguardando dados.')}</span>`;
    }
    const opt = $('#tncMetricOptimizer'); if (opt) opt.textContent = optimizerLabel(report.mode);
  }

  async function refreshStatus() {
    try {
      const data = await requestJson('/api/tnc/status');
      if (!lastConfig) applyConfig(data.config || {});
      setStatus(data.status || {});
    } catch (error) {
      const header = $('#tncHeaderStatus');
      if (header) {
        header.className = 'status disconnected tnc-header-status';
        const text = header.querySelector('span:last-child');
        if (text) text.textContent = 'TNC erro';
        header.title = error.message;
      }
    }
  }

  async function refreshData() {
    try {
      const [frames, decisions, heard, optimizer] = await Promise.all([
        requestJson('/api/tnc/frames?limit=200'),
        requestJson('/api/tnc/decisions?limit=200'),
        requestJson('/api/tnc/heard?limit=150'),
        requestJson('/api/tnc/optimizer'),
      ]);
      renderFrames(frames);
      renderDecisions(decisions);
      renderHeard(heard);
      renderOptimizer(optimizer);
      showError('');
    } catch (error) {
      showError(error.message);
    }
  }

  async function initialLoad() {
    try {
      const data = await requestJson('/api/tnc/status');
      applyConfig(data.config || {});
      setStatus(data.status || {});
      await loadPorts();
      await refreshData();
    } catch (error) { showError(error.message); }
  }

  function bind() {
    if (initialized) return;
    initialized = true;
    field('tncTransport')?.addEventListener('change', syncTransportFields);
    field('tncRole')?.addEventListener('change', applyRolePreset);
    field('tncSerialPort')?.addEventListener('input', () => updateSerialProfileHint());
    field('tncDeviceProfile')?.addEventListener('change',()=>{
      const profile=val('tncDeviceProfile','generic_kiss');
      if(['kenwood_tm_d700','kenwood_tm_d710','kantronics'].includes(profile)&&field('tncSerialProtocol'))field('tncSerialProtocol').value='terminal';
      if(profile==='kenwood_tm_d700'&&field('tncPacketRfBaud'))field('tncPacketRfBaud').value='1200';
      updateSerialProfileHint();
    });
    field('tncSerialProtocol')?.addEventListener('change',()=>updateSerialProfileHint());
    $('#tncRefreshPorts')?.addEventListener('click', () => loadPorts({force:true}));
    $('#tncRescanDevices')?.addEventListener('click', () => loadPorts({force:true}));
    $('#tncSerialDevicesBody')?.addEventListener('click', event => {
      const button = event.target.closest?.('[data-tnc-use-port]');
      if (!button) return;
      const port = String(button.dataset.tncUsePort || '').trim();
      if (!port || !field('tncSerialPort')) return;
      field('tncSerialPort').value = port;
      updateSerialProfileHint(lastSerialPorts.find(item => String(item.device || '').toUpperCase() === port.toUpperCase()));
      field('tncSerialPort').focus();
    });
    $('#tncRefreshData')?.addEventListener('click', refreshData);
    $('#tncSave')?.addEventListener('click', async () => {
      try { await saveConfig(); await refreshData(); } catch (error) { showError(error.message); }
    });
    $('#tncConnect')?.addEventListener('click', async () => {
      try {
        await saveConfig({quiet:true});
        const data = await requestJson('/api/tnc/connect', {method:'POST', body:'{}'});
        setStatus(data.status || {});
        setTimeout(refreshStatus, 500);
      } catch (error) { showError(error.message); }
    });
    $('#tncDisconnect')?.addEventListener('click', async () => {
      try { const data = await requestJson('/api/tnc/disconnect', {method:'POST', body:'{}'}); setStatus(data.status || {}); }
      catch (error) { showError(error.message); }
    });
    $('#tncEmergencyStop')?.addEventListener('click', async () => {
      try {
        const data = await requestJson('/api/tnc/tx/stop', {method:'POST', body:'{}'});
        setStatus(data.status || {}); await refreshData();
      } catch (error) { showError(error.message); }
    });
    $('#tncResumeTx')?.addEventListener('click', async () => {
      if (!confirm(tr('Liberar novamente a transmissão automática em RF com a configuração atual?'))) return;
      try {
        const data = await requestJson('/api/tnc/tx/resume', {method:'POST', body:'{}'});
        setStatus(data.status || {}); await refreshData();
      } catch (error) { showError(error.message); }
    });
    document.addEventListener('click', event => {
      const tab = event.target.closest?.('.tab[data-tab="tnc"]');
      if (tab) setTimeout(refreshData, 80);
    });
  }

  document.addEventListener('pt2vhf-language-changed', () => {
    translateTncStatic();
    refreshStatus();
    if ($('.tab.active[data-tab="tnc"]')) refreshData();
  });
  translateTncStatic();
  bind();
  initialLoad();
  pollTimer = setInterval(() => {
    refreshStatus();
    if ($('.tab.active[data-tab="tnc"]')) {
      refreshData();
      serialPollTick += 1;
      if (serialPollTick % 10 === 0 && val('tncTransport', 'tcp') === 'serial') {
        void loadPorts({quiet:true, quick:true});
      }
    }
  }, 3000);
  window.addEventListener('beforeunload', () => { if (pollTimer) clearInterval(pollTimer); });
})();
