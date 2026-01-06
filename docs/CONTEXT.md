# Context & Fine-tuning Guide
## Query-Genererend Taalmodel voor Zaalverhuur (OSLO Zaalreservatie)

### Doel van dit document

Dit document beschrijft de **conceptuele en technische context** voor het fine-tunen van een taalmodel dat kan optreden als **intelligente agent voor zaalverhuur**.

⚠️ Belangrijk uitgangspunt:
Het model **bevat zelf geen zaaldata**.
Het model **leert het vocabularium, het applicatieprofiel en de query-logica**, zodat het **dynamische RDF-data kan bevragen** (bv. via SPARQL).

---

## 1. Probleemstelling

Zaalverhuurdata is:

- **Dynamisch**
  - beschikbaarheid verandert continu
  - openingsuren kunnen wijzigen
  - reservaties zijn tijdelijk
- **Gestructureerd**
  - gemodelleerd in RDF
  - gebaseerd op OSLO-standaarden
- **Semantisch rijk**
  - relaties tussen zalen, locaties, tijdsblokken, voorzieningen, prijzen

Een klassiek fine-tuned taalmodel dat deze data *internaliseert* is daarom **conceptueel fout**:
- data veroudert
- beschikbaarheid is per definitie efemeer

➡️ De juiste aanpak is een **query-genererend model** dat:
1. het **OSLO Zaalreservatie-vocabularium** begrijpt
2. het **applicatieprofiel** respecteert
3. natuurlijke taal vertaalt naar **correcte SPARQL-queries**
4. queries uitvoert op **actuele RDF-bronnen**

---

## 2. Gebruikte standaarden

### 2.1 Vocabularium Zaalreservatie (OSLO)

Namespace:
https://data.vlaanderen.be/ns/zaalreservatie/

Het vocabularium beschrijft onder andere:

- Zaal
- Locatie
- Tijdsslot
- Reservatie
- Capaciteit
- Voorzieningen
- Prijsinformatie
- Beschikbaarheid

Het vocabularium definieert:
- klassen
- eigenschappen
- semantische relaties
- verwachte cardinaliteiten

---

### 2.2 Applicatieprofiel Zaalreservatie

URL:
https://data.vlaanderen.be/standaarden/applicatieprofiel-zaalreservatie

Het applicatieprofiel specificeert:

- welke entiteiten **verplicht / optioneel** zijn
- hoe relaties concreet worden toegepast
- welke eigenschappen verwacht worden bij zaalverhuur
- hoe tijd, beschikbaarheid en reservaties gemodelleerd worden

➡️ Dit profiel is **cruciaal** voor correcte query-generatie.

---

## 3. Doel van het taalmodel

Het taalmodel fungeert als **semantische interface** tussen:

- menselijke vragen
- RDF-data conform OSLO Zaalreservatie

Het model moet:

- natuurlijke taal **begrijpen**
- semantisch **mappen naar het vocabularium**
- **SPARQL-queries genereren**
- géén aannames doen buiten het applicatieprofiel

---

## 4. Typische gebruikersvragen (input)

Voorbeelden van vragen die het model moet ondersteunen:

- "Welke zalen zijn beschikbaar op vrijdagavond?"
- "Ik zoek een zaal voor 80 personen met beamer en rolstoeltoegang."
- "Welke zalen kan ik morgen huren tussen 14u en 18u?"
- "Zijn er zalen beschikbaar in Leuven onder de 200 euro?"
- "Welke zalen zijn momenteel vrij én hebben een keuken?"

➡️ De antwoorden komen **niet uit het model**,
➡️ maar uit **live RDF-data via SPARQL**.

---

## 5. Output van het model

De primaire output is **geen tekstueel antwoord**, maar:

- een **correcte SPARQL-query**
- conform:
  - vocabularium Zaalreservatie
  - applicatieprofiel
  - tijdslogica
  - beschikbaarheidslogica

### Voorbeeld (conceptueel):

**Input:**
> Welke zalen zijn beschikbaar morgen na 18u voor minstens 50 personen?

**Output:**
```sparql
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?zaal ?naam WHERE {
  ?zaal a zaalreservatie:Zaal ;
        zaalreservatie:capaciteit ?cap ;
        zaalreservatie:naam ?naam ;
        zaalreservatie:heeftBeschikbaarheid ?beschikbaarheid .

  ?beschikbaarheid zaalreservatie:tijdsslot ?tijdsslot .
  ?tijdsslot zaalreservatie:startTijd ?start .

  FILTER(?cap >= 50)
  FILTER(?start >= "{{MORGEN_18U}}"^^xsd:dateTime)
}
```

---

## 6. Fine-tuning strategie

### 6.1 Trainingsdata

De trainingsdata bestaat uit:

- **input**: natuurlijke taalvraag (Nederlands)
- **output**: correcte SPARQL-query

Voorbeeldformaat (JSON):

```json
{
  "messages": [
    {
      "role": "system",
      "content": "Je bent een SPARQL-query generator voor het OSLO Zaalreservatie vocabularium. Genereer alleen geldige SPARQL queries."
    },
    {
      "role": "user",
      "content": "Welke zalen zijn beschikbaar vrijdagavond?"
    },
    {
      "role": "assistant",
      "content": "PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>..."
    }
  ]
}
```

### 6.2 Validatie

Elke gegenereerde query moet:
- syntactisch correct zijn (SPARQL validator)
- semantisch correct zijn (conform OSLO vocabularium)
- uitvoerbaar zijn op een test RDF-dataset

---

## 7. Implementatie-architectuur

```
┌─────────────────┐
│ Gebruikersvraag │
└────────┬────────┘
         │
         v
┌─────────────────┐
│  Fine-tuned LLM │  ← leert vocabularium + query-patronen
└────────┬────────┘
         │
         v
┌─────────────────┐
│ SPARQL Query    │
└────────┬────────┘
         │
         v
┌─────────────────┐
│ RDF Triplestore │  ← actuele zaaldata
└────────┬────────┘
         │
         v
┌─────────────────┐
│   Resultaten    │
└─────────────────┘
```

---

## 8. Voordelen van deze aanpak

✅ Model blijft actueel (geen verouderde data)
✅ Transparante query-logica (inspecteerbaar)
✅ Herbruikbaar voor andere OSLO-domeinen
✅ Schaalbaar (nieuwe zalen = geen retraining)
✅ Privacy-vriendelijk (geen data in model)

---

## Volgende stappen

1. ✅ Context documenteren
2. 🔄 Trainingsdata samenstellen
3. 🔄 Fine-tuning pipeline opzetten (GitHub Actions)
4. 🔄 Validatie-framework ontwikkelen
5. 🔄 Model evalueren en itereren
