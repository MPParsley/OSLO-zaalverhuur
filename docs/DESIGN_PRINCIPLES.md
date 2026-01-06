# Design Principles: Query Generator voor Voorzieningen

## Kernprincipe: Data vs Model

⚠️ **Cruciaal**: Voorzieningen zijn **data**, geen **schema**.

Het model mag **GEEN** domeinkennis bevatten over:
- Welke voorzieningen bestaan (beamer, wifi, piano, etc.)
- Synoniemen tussen voorzieningen (beamer ↔ projector)
- Specifieke terminologie

## Waar leeft welke kennis?

| Kennis | Locatie | Reden |
|--------|---------|-------|
| **Voorzieningen lijst** | RDF Data | Dynamisch, per installatie verschillend |
| **Synoniemen** | RDF Data (SKOS/RDFS) | Domeinkennis die data is |
| **Query patroon** | Model | Generiek, herbruikbaar |
| **SPARQL syntax** | Model | Structurele kennis |
| **OSLO vocabularium** | Model | Schema kennis |

## Architectuur

```
┌─────────────────────────────────────────────────────────────┐
│ User: "Ik zoek een zaal met projector"                       │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            v
┌─────────────────────────────────────────────────────────────┐
│ Fine-tuned Model (Query Generator)                           │
│                                                               │
│ Leert:                                                        │
│ ✓ SPARQL query patroon voor voorzieningen                   │
│ ✓ UNION van voorziening_type + rdfs:label                   │
│ ✓ Case-insensitive matching                                 │
│                                                               │
│ Leert NIET:                                                  │
│ ✗ Specifieke voorzieningen (beamer, wifi, etc.)             │
│ ✗ Synoniemen (projector = beamer)                           │
│ ✗ Welke voorzieningen bestaan                               │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            v
┌─────────────────────────────────────────────────────────────┐
│ Generated SPARQL Query                                        │
│                                                               │
│ ?voorziening a zaalreservatie:Voorziening .                  │
│ {                                                             │
│   ?voorziening zaalreservatie:voorziening_type ?type .       │
│   FILTER(CONTAINS(LCASE(STR(?type)), "projector"))          │
│ } UNION {                                                     │
│   ?voorziening rdfs:label ?label .                           │
│   FILTER(CONTAINS(LCASE(?label), "projector"))              │
│ }                                                             │
│                                                               │
│ → Gebruikt letterlijke term uit user input                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            v
┌─────────────────────────────────────────────────────────────┐
│ RDF Triplestore                                               │
│                                                               │
│ :voorziening_123 a zaalreservatie:Voorziening ;              │
│     zaalreservatie:voorziening_type :Beamer ;                │
│     rdfs:label "Beamer"@nl, "Projector"@nl, "Projector"@en . │
│                                                               │
│ → Synoniemen in de data via SKOS/RDFS labels                 │
│ → Query matcht via label: "projector" ✓                      │
└─────────────────────────────────────────────────────────────┘
```

## Query Patroon (Template)

Het model leert dit **generieke patroon**:

```sparql
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?zaal ?naam WHERE {
  ?zaal a zaalreservatie:Zaal ;
        zaalreservatie:naam ?naam ;
        zaalreservatie:heeftVoorziening ?voorziening .

  ?voorziening a zaalreservatie:Voorziening .
  {
    # Path 1: Via voorziening_type property
    ?voorziening zaalreservatie:voorziening_type ?type .
    FILTER(CONTAINS(LCASE(STR(?type)), "{{TERM_FROM_USER_INPUT}}"))
  } UNION {
    # Path 2: Via rdfs:label
    ?voorziening rdfs:label ?label .
    FILTER(CONTAINS(LCASE(?label), "{{TERM_FROM_USER_INPUT}}"))
  }
}
```

**Belangrijk**:
- `{{TERM_FROM_USER_INPUT}}` wordt **letterlijk** overgenomen uit de vraag
- **Geen** hardcoded synoniemen in de query
- **CONTAINS**: Substring matching (flexibeler dan exact match)
- **LCASE**: Case-insensitive
- **UNION**: Zoek in zowel type als label

## Data Modeling Vereisten

Voor correcte werking moet de RDF data:

### 1. SKOS/RDFS Labels gebruiken

```turtle
:voorziening_beamer_001 a zaalreservatie:Voorziening ;
    zaalreservatie:voorziening_type :concept_beamer ;
    rdfs:label "Beamer"@nl, "Projector"@nl, "Projector"@en ;
    skos:prefLabel "Beamer"@nl ;
    skos:altLabel "Projector"@nl, "Beamer"@en, "Video projector"@en .
```

### 2. Concepten bij voorkeur via SKOS

```turtle
:concept_beamer a skos:Concept ;
    skos:prefLabel "Beamer"@nl ;
    skos:altLabel "Projector"@nl ;
    skos:altLabel "Projektor"@nl ;
    skos:altLabel "Video projector"@en ;
    skos:inScheme :VoorzieningenScheme ;
    skos:definition "Apparaat voor het projecteren van beelden"@nl .
```

### 3. Minimum vereiste

Als SKOS niet beschikbaar is, **minimaal** `rdfs:label`:

```turtle
:voorziening_xyz a zaalreservatie:Voorziening ;
    zaalreservatie:voorziening_type "wifi" ;
    rdfs:label "WiFi"@nl, "Wi-Fi"@en, "Draadloos internet"@nl .
```

## Feedback Loop voor Ontbrekende Termen

### Scenario: User zoekt "smartboard", data heeft het niet

1. **User vraag**: "Ik zoek een zaal met smartboard"
2. **Model genereert**:
   ```sparql
   FILTER(CONTAINS(LCASE(?label), "smartboard"))
   ```
3. **Query result**: Geen matches
4. **Systeem response**: "Geen zalen gevonden met 'smartboard'"

### Feedback proces

```
┌──────────────────────────────────────────────────────────┐
│ 1st Line Support Tool                                      │
├──────────────────────────────────────────────────────────┤
│                                                            │
│ ⚠️ Query retourneerde 0 resultaten                        │
│                                                            │
│ Gezocht naar: "smartboard"                                │
│                                                            │
│ Mogelijke acties:                                         │
│                                                            │
│ ○ Term bestaat niet in deze installatie                   │
│ ● Term bestaat wel, maar label ontbreekt                  │
│                                                            │
│ [ Voeg label toe aan bestaande voorziening ]             │
│                                                            │
│ Voorziening: [Interactive whiteboard ▼]                   │
│ Nieuw label: smartboard                                   │
│ Taal: [nl ▼]                                              │
│                                                            │
│ [ Opslaan ]                                               │
└──────────────────────────────────────────────────────────┘
```

### Data update (geen model retraining!)

Support medewerker voegt label toe:

```turtle
# Voor de update
:voorziening_iwb_001 a zaalreservatie:Voorziening ;
    rdfs:label "Interactive whiteboard"@en .

# Na de update
:voorziening_iwb_001 a zaalreservatie:Voorziening ;
    rdfs:label "Interactive whiteboard"@en ;
    rdfs:label "Smartboard"@nl ;        # ← Nieuw label
    rdfs:label "Digitaal schoolbord"@nl . # ← Nog een variant
```

**Resultaat**: Volgende query met "smartboard" werkt direct, **zonder model retraining**.

## Voordelen van deze aanpak

| Aspect | Voordeel |
|--------|----------|
| **Schaalbaarheid** | Nieuwe voorzieningen werken zonder retraining |
| **Onderhoudbaarheid** | Synoniemen bijwerken in data, niet in model |
| **Transparantie** | Query toont exact wat gezocht wordt |
| **Flexibiliteit** | Per installatie eigen voorzieningen |
| **Data kwaliteit** | Feedback verbetert data, niet model |
| **Herbruikbaarheid** | Patroon werkt voor andere OSLO domeinen |

## Trade-offs en Beperkingen

### ⚠️ Vereist goede data kwaliteit

- Data **moet** rdfs:label bevatten voor alle voorzieningen
- Synoniemen **moeten** als labels toegevoegd worden
- Zonder labels: geen matches

### ⚠️ Gebruikerservaring hangt af van data

- User moet term gebruiken die in data staat
- Of: UI moet autocomplete/suggesties bieden
- Of: Feedback loop voor ontbrekende termen

### ✅ Mitigatie: Gradual improvement

1. **Start**: Basis voorzieningen met enkele labels
2. **Feedback**: Support registreert ontbrekende termen
3. **Verrijking**: Labels worden toegevoegd aan data
4. **Iteratie**: Data wordt steeds beter
5. **Geen retraining**: Model blijft werken

## Training Data Strategie

### Wat leren we het model?

**✓ Wel**:
- Het query patroon (UNION, FILTER, CONTAINS)
- SPARQL syntax voor voorzieningen zoeken
- Term extractie uit user input
- Verschillende vraagformuleringen

**✗ Niet**:
- Specifieke voorzieningen
- Synoniemen tussen termen
- Welke voorzieningen bestaan

### Training voorbeelden (diverse PATTERNS, niet diverse VOORZIENINGEN)

```json
{
  "user": "Ik zoek een zaal met beamer",
  "assistant": "...FILTER(CONTAINS(LCASE(?label), \"beamer\"))..."
}

{
  "user": "Heeft deze zaal wifi?",
  "assistant": "...FILTER(CONTAINS(LCASE(?label), \"wifi\"))..."
}

{
  "user": "Welke zalen hebben een piano?",
  "assistant": "...FILTER(CONTAINS(LCASE(?label), \"piano\"))..."
}
```

**Doel**: Model leert het patroon, niet de specifieke termen.

## Implementatie Checklist

### Model (Fine-tuning)

- [ ] Training voorbeelden met **diverse query patterns**
- [ ] Voorbeelden met **diverse voorzieningen** (niet alleen beamer/wifi)
- [ ] **Geen** synoniemen in queries (alleen letterlijke term)
- [ ] UNION van `voorziening_type` en `rdfs:label`
- [ ] Case-insensitive CONTAINS matching

### Data (RDF Triplestore)

- [ ] Alle voorzieningen hebben `rdfs:label`
- [ ] Labels bevatten Nederlandse + Engelse varianten
- [ ] Bij voorkeur SKOS concepten voor voorzieningen
- [ ] Synoniemen als `skos:altLabel` of extra `rdfs:label`

### Support Tool

- [ ] Detectie van lege query resultaten
- [ ] Suggestie om labels toe te voegen
- [ ] Interface voor label management
- [ ] Logging van gezochte termen (analytics)

### Monitoring

- [ ] Track queries zonder resultaten
- [ ] Identificeer ontbrekende termen
- [ ] Meet data coverage (welke % queries succesvol)
- [ ] Feedback naar data team voor verrijking

## Voorbeeld: Complete Flow

### 1. User vraag
> "Ik heb een videoconferentiesysteem nodig"

### 2. Model output
```sparql
FILTER(CONTAINS(LCASE(?label), "videoconferentiesysteem"))
```

### 3. Data check
```turtle
# Data heeft dit concept, maar ander label
:voorziening_vc_001 a zaalreservatie:Voorziening ;
    rdfs:label "Video conferencing"@en ;
    rdfs:label "Videoconferentie"@nl .
```

**Resultaat**: Geen match (letterlijke term niet in labels)

### 4. Feedback loop
Support ziet: "videoconferentiesysteem" leverde 0 resultaten

Action: Voeg label toe
```turtle
:voorziening_vc_001 a zaalreservatie:Voorziening ;
    rdfs:label "Video conferencing"@en ;
    rdfs:label "Videoconferentie"@nl ;
    rdfs:label "Videoconferentiesysteem"@nl . # ← Nieuw
```

### 5. Volgende keer
Query met "videoconferentiesysteem" werkt nu ✓

**Geen model retraining nodig!**

## Conclusie

Deze aanpak scheidt **structurele kennis** (in het model) van **domeinkennis** (in de data).

Het model is een **patroon generator**, geen **kennisbank**.

De data is de **single source of truth** voor voorzieningen en hun synoniemen.
