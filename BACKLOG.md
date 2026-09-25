# Backlog

## Concluído na v1.6.1

- atualização OTA com preferências configuráveis;
- verificação automática da Release a cada 5 minutos;
- mensagens longas sem marcadores visíveis de parte;
- aba **Análise** com métricas e rankings;
- período **Completo** da topologia;
- favoritos com estrela amarela;
- filtro **Não lidas** em Mensagens;
- botão **Mostrar log** no popup da estação;
- legenda de linhas no Mapa;
- animação inicial de tráfego APRS;
- som/destaque visual de atividade.

## Concluído na v1.6.2 — 25/09/2026

- **Replay da Rede** com timeline arrastável, densidade de tráfego, seek, intervalo personalizado e velocidades de 0,25x a 20x.
- Controles de replay/animação movidos para a **parte inferior do Mapa**.
- Removido **Animar período** da aba Análise.
- Pacotes multi-hop podem percorrer múltiplos enlaces simultaneamente.
- Som, destaque e ondas de atividade limitados às estações visíveis no enquadramento/zoom atual.
- Ondas/círculos concêntricos animados ao redor do marcador da estação que transmite.
- Indicador **RX/TX** de atividade de tráfego na barra superior.
- Legenda do Mapa sincronizada com as cores e espessuras configuradas.
- Correção da **espessura da topologia** refletindo imediatamente no Mapa.
- Botão **Ver logs** no popup da estação, abrindo o Log filtrado pelo indicativo/SSID.
- Um único botão **Salvar configuração** no rodapé da aba Configuração.
- Confirmação visual após salvar e proteção ao trocar de aba com alterações pendentes.
- **Auto-update desativado**; o cliente somente informa quando existe uma versão nova.
- Verificação de versão com timeout, recuperação automática e sem cache persistente de falhas.
- Popup de **novidades da versão** exibido uma única vez após atualização.
- Release Windows-only conforme solicitado: Setup x64 + Portable x64, sem nova documentação PDF/Linux/macOS.

Novas demandas devem ser adicionadas abaixo deste ponto e continuar na série **1.6.x** até indicação explícita para avançar para **1.7**.


## Corrigir espessura da Topologia observada no Mapa

**Objetivo:** garantir que a espessura configurada para os enlaces da topologia seja aplicada imediatamente e de forma consistente no mapa.

- Corrigir o caso em que **Configuração → Mapa e Topologia → Espessura da topologia** é alterada, mas o mapa continua exibindo os enlaces com a espessura anterior.
- Ao salvar/aplicar a configuração, atualizar imediatamente todas as linhas de topologia já desenhadas.
- Aplicar a espessura configurada também aos novos enlaces carregados posteriormente.
- Manter a legenda sincronizada com a mesma espessura usada no mapa.
- A correção deve valer para enlaces RF, IGate/APRS-IS e demais linhas da topologia que usem essa preferência.


## Botão “Salvar configuração” no rodapé e confirmação visual de salvamento

**Objetivo:** tornar o fluxo de edição da Configuração mais claro e evitar perda acidental de alterações.

- Mover o botão **Salvar configuração** para o **rodapé da aba Configuração**, após todas as seções.
- Manter o botão visível e acessível ao final da página, sem duplicá-lo no topo.
- Ao salvar com sucesso, exibir uma confirmação visual clara, por exemplo **Configuração salva**.
- A confirmação deve desaparecer automaticamente após alguns segundos e não bloquear a interface.
- Se houver qualquer alteração não salva e o usuário tentar mudar de aba, exibir confirmação com opções:
  - **Salvar e sair**;
  - **Cancelar** a troca de aba e continuar editando;
  - **Descartar alterações** quando aplicável.
- Não perder valores digitados quando o salvamento falhar.


## Popup “Atualizado para esta versão” após a primeira inicialização

**Objetivo:** informar claramente ao usuário que o cliente foi atualizado e apresentar as novidades da versão recém-instalada.

- Após iniciar pela primeira vez uma nova versão, exibir um popup informando **Atualizado para vX.Y.Z**.
- Mostrar no popup um resumo das **novidades da versão atual**, preferencialmente derivado do changelog/release notes embutido no aplicativo.
- Exibir o popup somente **uma vez por versão instalada**.
- Persistir localmente qual foi a última versão cujo popup de novidades já foi exibido.
- Incluir botão **OK/Fechar** e, quando houver, opção para abrir a página oficial da Release.
- O popup não deve depender de acesso à Internet para mostrar as novidades básicas da versão instalada.
- Atualizações futuras devem reutilizar a mesma estrutura automaticamente.
