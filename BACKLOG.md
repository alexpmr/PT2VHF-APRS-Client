# Backlog

Os itens registrados até **24/09/2026** foram incorporados ou consolidados na **v1.6**.

A partir desta versão, novas demandas serão adicionadas novamente neste arquivo à medida que forem solicitadas.

## Concluído na v1.6

- mensagens longas: status agregado, retry individual e política configurável de retry/timeout;
- análises de topologia: rankings, enlaces desaparecidos, comparação por período e animação temporal;
- Linux: AppImage, testes em Ubuntu 22.04/24.04 e notificações nativas quando disponíveis;
- página única de Configuração com seções compartimentalizadas;
- aviso ao sair da Configuração com alterações não salvas;
- restauração da configuração padrão sem apagar dados operacionais;
- botão rápido de tema Claro/Escuro;
- Português/English com bandeiras, Português como padrão;
- coordenadas decimal/DMS e localização do sistema;
- organização de Estação APRS, APRS-IS, Aplicativo, Mapa/Topologia e Backup/Dados;
- editor gráfico APRS-IS ampliado, validação, cópia e filtro manual preservado;
- alerta de filtro APRS-IS vazio;
- filtro padrão de novas instalações para indicativos brasileiros;
- Indicativo obrigatório e passcode automático;
- orientação de campos obrigatórios ao conectar;
- localização automática, centralização inicial e altitude de contingência em 0 m;
- recomendação não bloqueante ao enviar beacon ainda com altitude de contingência em 0 m;
- “Conectar ao iniciar” na seção APRS-IS e habilitado por padrão em novas instalações;
- ordenação A–Z/Z–A das conversas agrupadas;
- preenchimento automático do Destino ao selecionar conversa;
- correção do peso de fonte em De, Para e Tipo;
- Log com data/hora em uma linha, alinhamento consistente e ordenação nos dois sentidos;
- manual PDF profissional com screenshots e validação automática;
- atualização integrada com verificação, download, SHA-256, instalação assistida e rollback onde suportado.


## Pop-up de nova mensagem — botão “Ler mensagem”

**Objetivo:** permitir abrir imediatamente a conversa correspondente à mensagem recebida.

- No pop-up de nova mensagem, manter o botão **OK** e adicionar o botão **Ler mensagem**.
- Ao clicar em **Ler mensagem**, abrir a aba **Mensagens**.
- A mensagem recém-recebida deve ficar visível/focada na tela.
- Se **Agrupar por remetente** estiver ativo, selecionar automaticamente o grupo/conversa do remetente da mensagem recebida.
- Nesse modo agrupado, preencher também o campo **Destino** com o indicativo completo do remetente, incluindo SSID quando houver.
- Se a visualização não estiver agrupada, posicionar a lista na mensagem recém-recebida.
- Marcar a mensagem como vista ao abrir a conversa pelo botão **Ler mensagem**.
- O botão **OK** deve continuar apenas fechando o pop-up, sem mudar de aba.

## Pendente após v1.6

- Popup de nova mensagem: além de **OK**, incluir **Ler mensagem**; ao clicar, abrir a aba **Mensagens** mostrando a mensagem recebida e, se o modo estiver agrupado por remetente, selecionar/focar automaticamente a conversa do remetente.
- Configuração > Estação APRS: reorganizar **coordenadas e altitude verticalmente, uma informação abaixo da outra**, evitando que Latitude/Longitude/Altitude extrapolem os limites do bloco em janelas menores ou com fonte ampliada.
