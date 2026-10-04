# Kenwood TM-D700 — validação física em modo PKT

A v1.10.0 inclui diagnóstico específico para o TM-D700, mas não declara compatibilidade física sem um rádio real.

## Pré-requisitos

- Kenwood TM-D700.
- Cabo/interface serial apropriado e driver funcional.
- Rádio configurado em modo PKT.
- Uma segunda estação APRS, TNC ou monitor RF para confirmar a transmissão no ar.
- PT2VHF APRS Client v1.10.0.

## Sequência

1. Confirmar a porta serial e o baud rate.
2. Abrir **TNC / RF** e usar **Testar TNC**.
3. Executar **Teste TM-D700**.
4. Confirmar no relatório:
   - porta aberta;
   - bytes recebidos;
   - framing/protocolo reconhecido;
   - frames KISS/AX.25 válidos ou indicação clara de incompatibilidade;
   - ausência de erro de acesso/porta ocupada.
5. Receber um pacote APRS real no rádio e verificar se aparece no monitor RX.
6. Enviar um pacote de teste e confirmar a emissão por uma segunda estação/monitor RF.
7. Desconectar e reconectar o cabo.
8. Reiniciar o rádio e repetir RX/TX.
9. Registrar o relatório e o diagnóstico gerado.

## Critério de aprovação

Somente considerar o TM-D700 **fisicamente validado** quando RX e TX forem confirmados no ar em equipamento real. Porta aberta ou bytes entregues à serial não são evidência suficiente de emissão RF.
