# Pente fino após v1.15.6 — issue #157

## Alterações

- Catálogo por chave para PT-BR/EN/ES/FR/DE/IT, carregado depois dos pacotes legados. Os idiomas JA/PL/NL/ZH e as dez opções de seleção continuam presentes; os vetores antigos não são reordenados.
- Caminho único de consulta para os módulos de configuração, planejamento, TNC, mensagens e recursos adicionais. O planejamento deixa de usar inglês como alternativa ao francês.
- Correspondência de mensagens parametrizadas, incluindo erros do servidor. Os parâmetros são preservados, inclusive indicativos e identificadores; nenhum serviço de tradução é chamado durante o uso.
- Observação de novos textos e atributos, preservação de espaços e reversão ao idioma anterior. O tradutor independente do TNC foi removido para evitar caches concorrentes.
- Correção de vocabulário: porta de comunicação, cliente de software, pacotes/frames, camadas de mapa, avisos de transmissão e confirmações de exclusão. Foram acrescentadas centenas de correções editoriais nos cinco idiomas de destino. A revisão incluiu a leitura de 1.360 rótulos curtos, o vocabulário de rádio e os avisos operacionais.
- Proteção adicional de mensagens recebidas, prévias de conversa, indicativos, nomes de listas, nomes de objetos, códigos de símbolos e arquivos escolhidos. O seletor de arquivo da restauração usa um rótulo traduzido; nenhuma restauração faz parte dos testes.
- Rótulos condicionais de tabela de símbolos e tipos de enlace passam por tradução explícita, em vez de esconder palavras da interface dentro de parâmetros.

## Reprodução

Instale os requisitos normais da aplicação, Playwright 1.62.1 e Acorn 8.15.0. Instale o navegador Chromium do Playwright. Execute da raiz:

```text
node tools/extract_i18n_javascript.cjs
python tools/export_i18n_sources.py
node tools/assemble_i18n_catalog.cjs
python tools/write_i18n_catalog.py
node tests/i18n_catalog.cjs
node tests/i18n_dom.browser.cjs
python tools/smoke_i18n_ui.py
python tools/smoke_i18n_ui.py --audit
```

`tools/i18n_translations.json` contém as traduções por chave; `tools/i18n_reviewed_overrides.json` registra as correções editoriais. O gerador produz `static/js/i18n_catalog.js`. O CI exige reprodução exata desse arquivo. Não são necessários modelos, pesos ou serviços externos para gerar o catálogo a partir dos arquivos versionados.

O extrator lê a árvore sintática JavaScript, fragmentos HTML, textos/atributos dos templates e campos de mensagens Python. O teste estrito exige entradas para todos os textos inventariados e preservação dos parâmetros, sem baseline de lacunas. Também detecta palavras próprias da interface escondidas em condicionais interpoladas. Unidades, protocolos, marcas e nomes próprios podem legitimamente coincidir entre idiomas.

O teste de navegador usa banco temporário e servidor local. Bloqueia conexões externas e operações de transmissão, conexão, restauração e gravação de agendamentos. Permite apenas configuração e operações auxiliares locais da interface no banco de teste. Navega pelas abas, sub-abas, ferramentas e modais; compara textos e atributos visíveis com suas origens. Os relatórios ficam em `.test-runtime/` e nos artefatos do GitHub Actions.

`tools/audit_i18n_language.py` é uma revisão linguística auxiliar opcional (Lingua). Seus achados exigem leitura: nomes próprios e palavras compartilhadas entre idiomas podem produzir falsos positivos. Por exemplo, “unsaved” e “introuvable” preservam uma negação sem usar uma palavra separada equivalente a “não”.

## Limite de aceite

Validação local em 01/11/2026: **707 testes e 12 subtestes aprovados**; sintaxe de todos os módulos JavaScript válida; teste de DOM e teste da aplicação real aprovados, com seis idiomas, nove abas, bandeiras exatas, dez opções preservadas e idioma salvo após recarregar. O teste estrito passou para **2.579 chaves de origem**, incluindo parâmetros. A auditoria visível passou em **174 estados (29 por idioma)**, sem resíduos pelos critérios do teste. Inclui configurações, modais de símbolos, filtros de mensagens, quatro tipos de agendamento, listas de destinatários, prévia de divulgação e três ferramentas de planejamento. Nenhuma transmissão, conexão, restauração ou gravação de agendamentos ocorreu.

Cobertura do extrator e ausência de resíduos nos estados testados são evidências verificáveis, não uma garantia matemática sobre todos os dados e estados possíveis. A issue #157 não deve ser encerrada apenas por contagem de chaves ou testes de navegação. Traduções iniciais foram auxiliadas por modelo local M2M100; avisos, parâmetros e achados linguísticos foram revisados e corrigidos. O aplicativo distribuído não inclui esse modelo.

Esta alteração é posterior à v1.15.6 publicada. Não substituir os binários da versão existente nem anunciar uma nova versão no site antes de concluir o build, verificar os pacotes e confirmar a publicação real.

A execução [41327742124](https://github.com/alexpmr/PT2VHF-APRS-Client/actions/runs/41327742124) aprovou a revisão ampliada no Linux do GitHub Actions: regressão, aplicação real, auditoria visível e reprodução do catálogo. A inclusão posterior de 33 textos retornados pelo servidor aumenta o inventário de 2.546 para 2.579 chaves e deve passar novamente pelo mesmo workflow. As 799 entradas editoriais são mantidas no arquivo de revisão e incorporadas ao catálogo principal; não dependem de caches locais de tradução.

A criação automática do PR foi recusada pela configuração do repositório: `GitHub Actions is not permitted to create or approve pull requests`. A branch está disponível para [revisão e abertura do PR](https://github.com/alexpmr/PT2VHF-APRS-Client/compare/main...fix/i18n-complete-audit). Nenhuma credencial foi extraída e nenhuma configuração de permissão foi alterada.
