# MANGFALL Karten

## So funktioniert es

Die App läuft bei jedem Start von Home Assistant kurz durch und beendet sich dann wieder:

1. Sie legt die Datei `mangfall-cards.js` unter `/config/www/mangfall/` ab (bzw. aktualisiert sie).
2. Sie trägt die Datei als Dashboard-Ressource ein.
3. Hast du die Karten schon über HACS oder eine eigene Datei, bleibt alles, wie es ist.

Beim allerersten Mal kann ein Neustart von Home Assistant nötig sein – das steht dann im Protokoll.

## Karten verwenden

Dashboard öffnen → **Bearbeiten → Karte hinzufügen →** nach „MANGFALL“ suchen. Jede Karte zeigt sofort
etwas an; im Editor kannst du Sensoren und Bilder anpassen.

## Datenschutz

Die Karten und die App senden keine Daten nach außen. Das MANGFALL-Zeichen auf den Karten ist ein Link
zu mangfall.eu – er öffnet sich nur, wenn du darauf tippst.

## Dashboards im YAML-Modus

Trage die Ressource selbst ein:

```yaml
lovelace:
  resources:
    - url: /local/mangfall/mangfall-cards.js
      type: module
```
