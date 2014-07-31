# Web-Scraper für VIVO-Daten

Dieses Projekt durchsucht Webseiten des Science 2.0 Forschungsverbundes nach Daten über Personen, Organisationen und Publikationen und exportiert diese Daten in RDF, das von [VIVO][1] gelesen werden kann. Dazu wird das Python-Scraping Framework [Scrapy][2] verwendet.

## Verwendung
### Installation
Installieren Sie die VirtualBox-Datei `SCRAPY.OVA` in VirtualBox über das Menü "Datei -> Appliance importieren ...". Starten Sie die virtuelle Maschine. Die ersten Meldungen über Maus und Tastatur ignorieren. Benutzername und Passwort: `vagrant`. Während der Eingabe vom Passwort bleibt der Cursor auf einer Stelle.

Nach dem erfolgreichen Login im VirtualBox können Sie sich mit [Putty][5] auf die Kommandozeile der virtuellen Maschine verbinden. Geben Sie im [Putty][5]-Configuration-Fenster den Host/Severname `localhost` ein, der Port ist `2222`. Mit der Schaltfläche "Open" aktivieren Sie die Kommandozeile. Die Angaben sollen entweder  jedes Mal eingegeben, oder können gespeichert werden (Schaltfläche "Save", Namen eingeben). Gespeicherte Einstellungen werden mit  "Load" ausgewählt und dann mit "Open" aktiviert. Benutzername und Passwort sind `vagrant`. Das Einfügen von kopierten Befehlen in die Kommandozeile passiert durch Rechtsklick. Strg+V funktioniert nicht. 

### Gemeinsamen Ordner einrichten
Damit Sie die Scraper-Dateien mit einem Editor auf ihrem PC berabeiten können, schalten Sie die Virtuelle Maschine aus und richten Sie einen gemeinsamen Ordner ein. Klicken Sie in der VirtualBox-Oberfläche auf "Gemeinsame Ordner" und das Hinzufügen-Icon. Wählen Sie einen Ordner aus. Unterhalb des Ordner-Namens sehen Sie den Namen des Ordners in der Virtuellen Maschine. Sie können ihn ändern, z.B. auf `scrapy`. "Automatisch einbinden" anhacken. In der folgenden Dokumentation wird der name `scrapy` verwendet. Auf der Virtuellen maschine finden Sie dann denn Ordner unter `/media/sf_scrapy`.

Starten Sie die virtuelle Maschine und kopieren Sie die Scrapy-Dateien auf der Kommandozeile mit folgendem Befehl:

    cp -r /usr/local/vivo2014/* /media/sf_scrapy

Nach der Installation ist das Letzte nicht mehr notwendig.

### Scraper aufrufen
Wechseln Sie auf der Kommandozeile in den Ordner `/media/sf_scrapy` mit folgendem Befehl:

    cd /media/sf_scrapy

Rufen Sie dann die zur Seite passende Spider auf, z.B.

    scrapy crawl zbw_spider

, bekommen Sie dann die Ergebnisse der Crawling. Weitere gültige Spider-Namen sind `hiig_spider` und `gesis_spider`.

### Speichern der Änderungen mit git

Wechseln Sie auf der Kommandozeile in den Ordner `/media/sf_scrapy` mit folgendem Befehl:

    cd /media/sf_scrapy

Holen Sie sich die neueste Version vom Server mit

    git pull

Wenn Sie einen Scraper geändert haben (auch wenn es nur ein funktionierender Zwischenstand ist), speichern Sie ihn ab mit

    git commit -a -m "Beschreibung der Änderungen"

Beschreiben Sie kurz auf englisch was geändert wurde und stellen Sie den Namen der Spider voran, z.B. "[ZBW] Add email to organization" oder "[HIIG] parse publication author".

Um die Änderungen auf den Server zu überspielen, geben Sie folgenden Befehl ein:

    git push

## Konzepte
Um die Daten einer Webseite zu speichern, benötigt Scrapy zunächst eine Datenstruktur, in der die Daten gespeichert werden sollen. Diese Datenstruktur heißt **Item**. Die verschiedenen Typen von Items sind in der Datei `items.py` gespeichert.

Um die Webseite nach Daten zu durchsuchen, benutzt Scrapy eine sogenannte **Spider**. Eine Spider bekommt eine Liste von URLs als Start-Daten, lädt die Inhalte der HTML-Seiten herunter,  verarbeitet sie und erzeugt dabei entweder eine weitere URL, die abgearbeitet werden muss oder ein Item, das gespeichert werden soll. Zum Verarbeiten von HTML-Daten benutzt Scrapy **Selektoren**, mit denen mit Hilfe von [XPATH][3]-Ausdrücken oder [CSS-Selektoren][4] in der Struktur des HTML-Dokuments navigiert und spezifische Inhalte abgerufen werden können. Wenn es mehrere gleichnamige Elemente im Quellcode gibt, wäre sinnvoll lieber XPATH zu benutzen 
Die Spider-Programme sind im Ordner `spiders` gespeichert. Jede Webseite braucht aufgrund ihrer individuellen HTML-Struktur eine eigene Spider.

Die Items werden nach dem Erzeugen durch die Spider nicht sofort gespeichert, sondern durchlaufen erst noch die **Pipeline**. Dort können sie nachbearbeitet werden. Im konkreten Fall nutzt das Projekt die Pipeline, um eindeutige IDs zu vergeben und die Items ins RDF-Format zu konvertieren.

## Aufbau einer Spider
Eine Spider beginnt immer mit der Deklaration des Namens, der erlaubten Domains (URLs außerhalb der erlaubten Domains werden nicht abgerufen) und der Start-URLs. 
```
class HiigSpider(Spider):
    name = "hiig_spider"
    allowed_domains = ["www.hiig.de"]
    start_urls = [
        "http://www.hiig.de/institute/organisation/",
        "http://www.hiig.de/personen/",
        "http://www.hiig.de/publikationen-des-hiig/",
    ]
```
Außerdem muss sie immer die Methode `parse` enthalten. In unserem Projekt verzweigt sich `parse` in Methoden zum Verarbeiten der Informationen über die Haupt-Organisation und zum Verarbeiten der Abteilungen der Organisation. 
Um während der Bearbeitung die Ergebnisse nur eines Teils der Webseite zu bekommen, könnte man die übrigen URLs auskommentieren.
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
Es kommt häufiger vor, dass Informationen auf mehreren Seiten verteilt (z.B. bei Personen, bei denen Kontakt-Informationen und Informationen zu Biografie und Publikationen auf verschiedenen Seiten stehen) sind oder Sie für jeden Link auf einer Übersichtsseite eine Detail-Seite aufrufen möchten.

Um eine neue Seite des Webauftritts zu crawlen, erzeugen Sie ein `Request` Objekt und liefern es mit `yield` zurück. Das `Request` Objekt benötigt eine URL. Wenn das Ergebnis des Abrufs nicht von der `parse` Methode verarbeitet werden soll, müssen Sie außerdem den `callback` Parameter verwenden und eine andere Methode zum Verarbeiten der Inhalte angeben. Wenn Sie das aktuell verarbeitete Item in mit weiteren Daten befüllen wollen, müssen Sie außerdem den `meta` Parameter verwenden. Das folgende Beispiel zeigt einen URL-Aufruf mit `callback` und `meta`:

```python
yield Request(url, callback=self.parse_person_details, meta={'person':person} )
```

In der Methode `parse_person_details` können Sie dann die Daten wie folgt verwenden:

```python
def parse_person_details(self, response):
    person = response.meta['person']
    # ...
```

### Mehrere Items verarbeiten
Wenn auf einer Seite mehrere Items zu verarbeiten sind, müssen Sie eine `for`-Schleife benutzen. Das folgende Beispiel zeigt, wie Sie

- einen CSS-Selektor-Ausdruck, der mehrere Elemente zurückliefert, mit einer `for`-Schleife durchlaufen
- für jedes Element ein neues Item erzeugen (in diesem Fall eine Publikation)
- aus dem aktuellen Element Informationen extrahieren
- Informationen an die aktuelle URL anfügen, um als sie als eindeutige `source_url` für das Item benutzen zu können.
- das Item mit `yield` zurückliefern

```python
def parse_publications(self, response):
    sel = Selector(response)
    for pub_content in sel.css("#main ul.publications li"):
        publi = Publication()
        title = join(pub_content.xpath("span[1]/text()").extract(), "")
        publi["source_url"] = response.url + "#" + title
        publi["title"] = title
        publi["author"] = join(pub_content.xpath("span[2]/text()").extract(), "")
        yield publi
```

Sie müssen nicht zwangsläufig ein Item erzeugen, Sie können auch wie im vorigen Abschnitt gezeigt, ein `Request`-Objekt erzeugen und eine weiter führende URL aufrufen.

## Nachbearbeitung der Items in der Pipeline
### Vergeben von IDs
### RDF-Export

[1]: http://www.vivoweb.org/
[2]: http://doc.scrapy.org/en/latest/
[3]: http://de.wikipedia.org/wiki/XPath
[4]: http://de.wikipedia.org/wiki/Cascading_Style_Sheets#Selektoren
[5]: http://www.putty.org/
