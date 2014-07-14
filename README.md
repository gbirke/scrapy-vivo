# Web-Scraper für VIVO-Daten

Dieses Projekt durchsucht Webseiten des Science 2.0 Forschungsverbundes nach Daten über Personen, Organisationen und Publikationen und exportiert diese Daten in RDF, das von [VIVO][1] gelesen werden kann. Dazu wird das Python-Scraping Framework [Scrapy][2] verwendet.

## Installation
TODO

## Konzepte
Um die Daten einer Webseite zu speichern, benötigt Scrapy zunächst eine Datenstruktur, in der die Daten gespeichert werden sollen. Diese Datenstruktur heißt **Item**. Die verschiedenen Typen von Items sind in der Datei `items.py` gespeichert.

Um die Webseite nach Daten zu durchsuchen, benutzt Scrapy eine sogenannte **Spider**. Eine Spider bekommt eine Liste von URLs als Start-Daten, lädt die Inhalte der HTML-Seiten herunter,  verarbeitet sie und erzeugt dabei entweder eine weitere URL, die abgearbeitet werden muss oder ein Item, das gespeichert werden soll. Zum Verarbeiten von HTML-Daten benutzt Scrapy **Selektoren**, mit denen mit Hilfe von [XPATH][3]-Ausdrücken oder [CSS-Selektoren][4] in der Struktur des HTML-Dokuments navigiert und spezifische Inhalte abgerufen werden können.  
Die Spider-Programme sind im Ordner `spiders` gespeichert. Jede Webseite braucht aufgrund ihrer individuellen HTML-Struktur eine eigene Spider.

Die Items werden nach dem Erzeugen durch die Spider nicht sofort gespeichert, sondern durchlaufen erst noch die **Pipeline**. Dort können sie nachbearbeitet werden. Im konkreten Fall nutzt das Projekt die Pipeline, um eindeutige IDs zu vergeben und die Items ins RDF-Format zu konvertieren.

## Aufbau einer Spider
Eine Spider beginnt immer mit der Deklaration des Namens, der erlaubten Domains (URLs außerhalb der erlaubten Domains werden nicht abgerufen) und der Start-URLs. Außerdem muss sie immer die Methode `parse` enthalten. In unserem Projekt verzweigt sich `parse` in Methoden zum Verarbeiten der Informationen über die Haupt-Organisation und zum Verarbeiten der Abteilungen der Organisation. 

### Daten extrahieren
Egal ob ein XPATH oder ein CSS-Selektor verwendet wird, am Ende des Ausdrucks muss, wenn Daten erzeugt werden sollen, die Methode `extract()` stehen. Die Methode liefert stets ein Array zurück, auch wenn der Selektor-Ausdruck nur genau einen Inhalt extrahiert. Um das Array in eine Zeichenkette umzuwandeln, verwenden Sie die Funktion `join`. Ein typischer Ausdruck zum Extrahieren einer Zeichenkette sieht wie folgt aus:

```python
url = join(link.xpath("@href").extract(), "") 
```

Beachten Sie bei der Formulierung von Ausdrücken, dass Sie entweder den Inhalt von Attributen zurück liefern müssen, oder den Inhalt von Elementen. Für den Inhalt von Elementen verwenden Sie bei XPATH-Ausdrücken `elementname/text()` und bei CSS-Ausdrücken `elementname::text` (`elementname` ist der HTMl-Elementname wie `h1` oder `p`). *Wenn Sie diese Ausdrück nicht verwenden, wird das HTML-Element zusammen mit dem Text extrahiert und führt zu unsauberen Daten!*

### Items zurückliefern
Wenn ein Item fertig gestellt ist, liefern Sie es mit dem Schlüsselwort `yield` zurück. Wenn Sie in einer Methode in Unter-Methoden verzweigen, die `yield` benutzen, müssen Sie entweder `return name_der_untermethode()` verwenden oder (besser) folgenden Code:

```python
for item in name_der_untermethode():
    yield item
```

### Items über mehrere Seiten hinweg mit Inhalt füllen
Um eine neue Seite des Webauftritts zu crawlen, erzeugen Sie ein `Request` Objekt und liefern es mit `yield` zurück. Das `Request` Objekt benötigt eine URL. Da die URL nicht von der `parse` Methode verarbeitet werden soll, müssen Sie außerdem noch den `callback` Parameter verwenden und eine andere Methode zum Verarbeiten der Inhalte angeben. Wenn Sie das aktuell verarbeitete Item in mit weiteren Daten befüllen wollen, müssen Sie außerdem den `meta` Parametere verwenden. Das folgende Beispiel zeigt einen URL-Aufruf mit `callback` und `meta`:

```python
yield Request(url, callback=self.parse_person_details, meta={'person':person} )
```

In der Methode `parse_person_details` können Sie dann die Daten wie folgt verwenden:

```python
def parse_person_details(self, response):
    person = response.meta['person']
    # ...
```

## Nachbearbeitung der Items in der Pipeline
### Vergeben von IDs
### RDF-Export

[1]: http://www.vivoweb.org/
[2]: http://doc.scrapy.org/en/latest/
[3]: http://de.wikipedia.org/wiki/XPath
[4]: http://de.wikipedia.org/wiki/Cascading_Style_Sheets#Selektoren
