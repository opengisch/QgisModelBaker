
Du kannst deine physikalischen Daten direkt in QGIS gegenüber den INTERLIS Modellen validieren. Öffne das Model Baker Validator Bedienfeld über *Datenbank > Model Baker > Data Validator* oder *Ansicht > Bedienfelder > Model Baker Data Validator*.

![validation](../assets/validation.gif)

## Datenbank
Die Datenbankverbindungsparameter werden vom aktuell angewählten Layer genommen. Meistens sind die repräsentativ für das gesamte Projekt, da ein Projekt meist auf einem einzigen Datenbankschema bzw. einer einzigen Datenbankdatei basiert. Im Falle mehrere verwendeter Datenquellen ist es aber möglich, zwischen den Validierungsergebnis zu *wechseln* indem man einen anderen Layer anwählt.

## Filter
Du kanst die zu validierenden Daten filtern *entweder* nach Modellen *oder* - sofern die Datenbank das [Dataset und Basket Handling](../../background_info/basket_handling/) berücksichtigt - nach Datasets oder Baskets. Du kannst auch mehrere Modelle / Datasets / Baskets auswählen. Aber nur eine arte der Filterung (`--model`, `--dataset`, `--basket`) wird dem `ili2db` Kommando übergeben (es würde auch keine Konjunktion (AND) sondern eine Disjunktion machen (OR), wenn mehrere Parameter angegeben würden (dies wird aber eigentlich nicht gebraucht). Eine Konjunktion (also die Schnittmenge) kann aber durch die filterung nach der  kleinsten Instanz (Baskets) erfolgen).

## Resultat
Nach dem Ausführen der Validierung mit dem ![checkmark](../assets/checkmark_button.png) werden die Resultate aufgelistet.

Mit *Rechtsklick* auf die Fehlermeldungen wird ein Menu geöffnet mit den folgenden Optionen:
- Auf Koordinaten zoomen (wenn Koordinaten verfügbar sind)
- Öffne Attributformular (wenn eine stabile t_ili_tid verfügbar ist)
- Setze auf gelöst (markiert den Eintrag grün, was den Überblick über den Fehlerlösungsprozess verbessert)

## ili2db mit `--validate` im Hintergrund
Bei der Validierung wird `ili2db` verwendet mit dem Parameter `--validate`. Dies bedeutet, dass kein Export der Daten benötigt wird. Der Output wird vom Model Baker geparsed und in der Resultatliste zur Verfügung gestellt.

Einträge vom Typ `Error` und `Warning` werden angezeigt.
