# Robuuste Query Patterns - Training Data Verbeteringen

## Probleem

De initiële training data gebruikte **letterlijke string matching** voor voorzieningen:

```sparql
?beamer zaalreservatie:voorziening_type "beamer" .
```

Dit is **fragiel** omdat:
- Het niet matcht met synioniemen ("projector", "projektor")
- Het hoofdlettergevoelig is
- Het afhankelijk is van exacte spelling in de data
- Het niet werkt als de data rdfs:label gebruikt i.p.v. voorziening_type

## Oplossing

### 1. REGEX-based matching met alternatieve termen

```sparql
FILTER(REGEX(?type, "beamer|projector|projektor", "i"))
```

Voordelen:
- **Case-insensitive** (de "i" flag)
- **Multiple alternatieven** via pipe (|) operator
- **Flexibel** voor verschillende schrijfwijzen

### 2. UNION voor meerdere property paths

```sparql
{
  ?voorziening zaalreservatie:voorziening_type ?type .
  FILTER(REGEX(?type, "beamer|projector", "i"))
} UNION {
  ?voorziening rdfs:label ?label .
  FILTER(REGEX(?label, "beamer|projector", "i"))
}
```

Dit matcht:
- `voorziening_type` property (OSLO-specifiek)
- `rdfs:label` (algemene RDF vocabularium)
- Beide patronen via UNION

### 3. Gestandaardiseerde concepten + flexibele matching

```sparql
{
  # Primaire match: OSLO concept
  ?toegankelijkheid zaalreservatie:toegankelijk zaalreservatie:Rolstoeltoegankelijk .
} UNION {
  # Fallback: string matching
  ?toegankelijkheid zaalreservatie:voorziening_type ?type .
  FILTER(REGEX(?type, "rolstoel|wheelchair", "i"))
}
```

## Verbeterde Voorbeelden

### Voor: Fragiele matching

```json
{
  "role": "user",
  "content": "Ik zoek een zaal met beamer en rolstoeltoegang"
}
```

**Output** (oud):
```sparql
?beamer zaalreservatie:voorziening_type "beamer" .
```

❌ Werkt niet voor: "Beamer", "projector", "Projector"

### Na: Robuuste matching

**Output** (nieuw):
```sparql
?beamer a zaalreservatie:Voorziening .
{
  ?beamer zaalreservatie:voorziening_type ?beamerType .
  FILTER(REGEX(?beamerType, "beamer|projector|projektor", "i"))
} UNION {
  ?beamer rdfs:label ?beamerLabel .
  FILTER(REGEX(?beamerLabel, "beamer|projector|projektor", "i"))
}
```

✅ Werkt voor:
- "beamer", "Beamer", "BEAMER"
- "projector", "Projector"
- "projektor"
- Via `voorziening_type` OF `rdfs:label`

## Toegevoegde Variaties

### 1. Terminologie variaties

| Origineel | Alternatieven |
|-----------|---------------|
| beamer | projector, projektor |
| rolstoeltoegang | wheelchair, toegankelijk, accessible |
| keuken | kitchen, kitchenette, pantry |
| wifi | wi-fi, wireless, internet, netwerk, network |

### 2. Vraag variaties

Nieuwe training voorbeelden voor verschillende formuleringen:
- "Heeft deze zaal een projector?" (i.p.v. "beamer")
- "Zoek zalen met toegang voor mensen in een rolstoel" (natuurlijker)
- "Welke zalen hebben een kitchenette of pantry?" (specifieke termen)
- "Ik heb internet nodig" (impliciete wifi vraag)

## SPARQL Pattern Template

Voor voorzieningen met multiple alternatieven:

```sparql
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?zaal ?naam WHERE {
  ?zaal a zaalreservatie:Zaal ;
        zaalreservatie:naam ?naam ;
        zaalreservatie:heeftVoorziening ?voorziening .

  ?voorziening a zaalreservatie:Voorziening .
  {
    # Path 1: OSLO voorziening_type
    ?voorziening zaalreservatie:voorziening_type ?type .
    FILTER(REGEX(?type, "term1|term2|term3", "i"))
  } UNION {
    # Path 2: RDF Schema label
    ?voorziening rdfs:label ?label .
    FILTER(REGEX(?label, "term1|term2|term3", "i"))
  }
}
```

## Training Data Statistieken

| Versie | Voorbeelden | Fragiele matches | Robuuste matches |
|--------|-------------|------------------|------------------|
| v1 (initieel) | 10 | 4 (40%) | 6 (60%) |
| v2 (verbeterd) | 14 | 0 (0%) | 14 (100%) |

### Verbeterde voorbeelden:
- Regel 2: beamer + rolstoeltoegang → REGEX + UNION
- Regel 5: keuken → REGEX + UNION
- Regel 7: voorzieningen lijst → OPTIONAL patterns
- Regel 10: wifi → REGEX + UNION

### Nieuwe voorbeelden:
- Regel 11: "projector" (alternatieve term)
- Regel 12: "mensen in een rolstoel" (natuurlijke formulering)
- Regel 13: "kitchenette of pantry" (specifieke termen)
- Regel 14: "internet nodig" (impliciete vraag)

## Voordelen voor Model Training

1. **Generalisatie**: Model leert patronen, geen exacte strings
2. **Multilingual**: Ondersteunt NL + EN termen
3. **Flexibiliteit**: Werkt met verschillende data modelleringen
4. **Robuustheid**: Minder gevoelig voor spelling variaties
5. **Best practices**: Toont UNION en REGEX technieken

## Best Practices voor Nieuwe Voorbeelden

Bij toevoegen van nieuwe training voorbeelden:

✅ **DO**:
- Gebruik REGEX voor string matching
- Include synoniemen in REGEX pattern
- Gebruik UNION voor alternatieve property paths
- Maak case-insensitive met "i" flag
- Test met verschillende schrijfwijzen

❌ **DON'T**:
- Geen hardcoded strings zonder REGEX
- Niet alleen op één property vertrouwen
- Geen hoofdletter-gevoelige matches
- Niet beperken tot Nederlands alleen

## Voorbeeld: Nieuwe voorziening toevoegen

Voor "whiteboard" met alternatieven:

```sparql
?voorziening a zaalreservatie:Voorziening .
{
  ?voorziening zaalreservatie:voorziening_type ?type .
  FILTER(REGEX(?type, "whiteboard|wit bord|krijtbord|blackboard", "i"))
} UNION {
  ?voorziening rdfs:label ?label .
  FILTER(REGEX(?label, "whiteboard|wit bord|krijtbord|blackboard", "i"))
}
```

## Impact op Model Performance

Verwachte verbeteringen:
- **Precisie**: Minder false negatives door flexibele matching
- **Recall**: Meer matches door synoniemen
- **Generalisatie**: Betere performance op nieuwe data
- **Robustness**: Werkt met diverse RDF modelleringen

## Validatie

Alle queries zijn gevalideerd met:
```bash
python scripts/validate_queries.py
```

✅ Alle 14 queries zijn syntactisch correct
✅ Alle queries bevatten OSLO namespace
✅ Alle voorziening matches zijn robuust
