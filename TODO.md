# TODO Scrapy & VIVO

- Bugfix GESIS Personen & Publikationen
- Publikationen ZBW
- RDF-Export Publikationen
- Web of science button ausblenden
- Zuordnung HIIG zu den 4 "Division"s, ausgehend von dem, was unterhalb der Personen-Fotos steht, Divisions müsssen noch Gescraped/Geparsed werden, das vor dem doppeltpunkt ist name/label der "DivisonRole"
- Zuordnung Organisation und Abteilung GESIS - Zuordnung nach ähnlichem Mechanismus wie Department_Role.
- Bilder von Personen scrapen und ablegen
- Ergänzung Publikationen mit mehr gescrapten Infos (von weiterführenden Links auf die Verlagsseiten, v.a. für HIIG)
- "Kanarienvogel" - Testen, ob der Scraper noch Daten zurückliefert, oder sich die Webseite geändert hat
- Export Verlage/Journale
- Daten-Cleanup:
    + KnowCenter
        * Veröffentlichungsorte sind nicht einheitlich: Einige sind nur Städte, andere sind Komma- oder Space-getrennt Stadt und US-Bundesstaat, usw. Kann mit Lookup-Table und einigen Regeln vereinheitlicht werden.
        * Organ ist wild durcheinander - muss mit Hilfe eines Bibliotheks-Erfahrendnen menschen gesäubert und geordnet und mit Regeln versehen werden. Teilweise ist nur aus dem organ ersichtlich, dass es sich um einen konferenzbeitrag handelt, "Academic Article" also nicht richtig ist.
- VIVO mit deutschen Übersetzungen anlegen
    + Installation von Git auf Development-Server
    + Checkout 
    + Sprachdateien aus Repository kopieren
    + Build
    + Sources in SVN einchecken
