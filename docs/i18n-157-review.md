# Issue #157 / PR #158 review

Base: v1.15.5 (`1941b8b`); original PR head `64d8c1d`.

The original PR corrects the six reference flags, including the Union Jack,
preserves all ten language options, and adds a useful initial audit. It does
not complete localization. Keep #157 open.

Additional corrections:

- Observe text updates, bare inserted text nodes and placeholder/title/aria-label
  changes, including attributes on the inserted root element.
- Remember the latest externally supplied text instead of restoring a stale
  status on a language switch. Avoid writing unchanged DOM values, so observer
  notifications terminate.
- Respect `translate="no"`, `.notranslate` and `data-i18n-skip`; protect received
  message bodies, station information, popup names/callsigns and raw packet logs.
- Add 30 keyed translations in EN/ES/FR/DE/IT for connection states, operations,
  database health, message search and closing dialogs. Leave positional legacy
  catalog order untouched and retain JA/PL/NL/ZH.
- Add a browser regression using the real catalogs in all six target languages.
  It checks switching back, inserted and changed text, changed attributes,
  preserved form values and excluded received data. An additional isolated HTTP
  test opens all nine tabs in six languages and checks flags and saved language
  after reload. Full visible content/modal coverage remains pending.
- Add a consolidated catalog inventory and a CI baseline for new missing
  literal candidates. The report identifies modules and unchanged-source entries.
  Module-local dictionaries, technical terms and dynamic expressions still need
  review. The baseline records existing debt; it is not acceptance of that debt.

Run `node tools/i18n_inventory.cjs --output i18n-inventory.json` to compare against
the baseline. Updating the baseline deliberately requires `--write-baseline`;
do not regenerate it simply to make CI pass. The legacy Python strict audit
remains enabled separately.

Remaining acceptance work: review the complete visible-string inventory,
translate the missing static/dynamic content in all modules, protect remaining
received/user content, test every tab/modal and persisted language against a
running application, and verify installer/portable outputs on supported systems.
Do not advertise complete localization from catalog counts alone.

Release/publication must use a successful GitHub Actions build at the final
reviewed commit, a new version, binary hashes/sizes and the matching site OTA
manifest. Verify the actual Hostinger downloads and update endpoint afterwards.
At the live inspection during this work, the site still advertised v1.15.5.

Local validation: 707 pytest tests and 12 subtests passed; DOM browser regression
and real-application six-language/nine-tab persistence test passed.
