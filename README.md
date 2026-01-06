# OSLO Zaalreservatie Query Model

Query-genererend taalmodel voor het OSLO Zaalreservatie vocabularium. Dit model vertaalt natuurlijke taalvragen naar SPARQL queries die RDF-data kunnen bevragen.

## 🎯 Doel

Dit project traint een taalmodel dat:
- ✅ Natuurlijke taalvragen begrijpt over zaalverhuur
- ✅ SPARQL queries genereert conform het [OSLO Zaalreservatie vocabularium](https://data.vlaanderen.be/ns/zaalreservatie/)
- ✅ Het [OSLO Zaalreservatie applicatieprofiel](https://data.vlaanderen.be/standaarden/applicatieprofiel-zaalreservatie) respecteert
- ✅ Geen zaaldata internaliseert (queries actuele RDF-bronnen)

## 📁 Projectstructuur

```
OSLO-zaalverhuur/
├── .github/
│   └── workflows/
│       └── fine-tune-model.yml    # GitHub Action voor fine-tuning
├── docs/
│   └── CONTEXT.md                 # Uitgebreide context documentatie
├── scripts/
│   ├── fine_tune.py               # Fine-tuning script
│   └── validate_queries.py        # SPARQL validatie
├── training-data/
│   └── examples.jsonl             # Trainingsvoorbeelden
├── requirements.txt               # Python dependencies
└── README.md                      # Deze file
```

## 🚀 Quick Start

### 1. Vereisten

- Python 3.11+
- OpenAI API key met fine-tuning toegang
- Git

### 2. Installatie

```bash
# Clone repository
git clone https://github.com/MPParsley/OSLO-zaalverhuur.git
cd OSLO-zaalverhuur

# Installeer dependencies
pip install -r requirements.txt

# Configureer API key
export OPENAI_API_KEY='your-api-key-here'
```

### 3. Lokaal fine-tunen

```bash
# Valideer trainingsdata
python scripts/validate_queries.py

# Start fine-tuning
python scripts/fine_tune.py \
  --training-file training-data/examples.jsonl \
  --model gpt-4o-mini-2024-07-18 \
  --suffix oslo-zaalreservatie

# Controleer status (vervang JOB_ID)
python scripts/fine_tune.py --check-status ftjob-xxxxx
```

### 4. Via GitHub Actions

1. **Configureer secrets**:
   - Ga naar repository Settings > Secrets > Actions
   - Voeg toe: `OPENAI_API_KEY`

2. **Start workflow**:
   - Ga naar Actions tab
   - Selecteer "Fine-tune OSLO Zaalreservatie Model"
   - Klik "Run workflow"
   - Kies basis model en suffix
   - Start workflow

3. **Monitor progress**:
   - Bekijk workflow logs
   - Download artifacts met job informatie
   - Gebruik job ID voor status checks

## 📊 Trainingsdata

### Formaat

JSONL bestand met conversaties:

```jsonl
{
  "messages": [
    {
      "role": "system",
      "content": "Je bent een SPARQL-query generator voor het OSLO Zaalreservatie vocabularium..."
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

### Voorbeelden toevoegen

1. Edit `training-data/examples.jsonl`
2. Voeg nieuwe JSONL regel toe met systeem, user en assistant messages
3. Zorg dat assistant response een geldige SPARQL query bevat
4. Valideer met `python scripts/validate_queries.py`
5. Commit en push (triggert automatisch workflow)

### Validatie

Elke query wordt gevalideerd op:
- ✅ Syntactische correctheid (SPARQL parser)
- ✅ OSLO namespace aanwezig
- ✅ Correcte PREFIX declaraties
- ✅ JSON structuur

## 🔧 Fine-tuning Configuratie

### Basis modellen

Beschikbare modellen:
- **gpt-4o-mini-2024-07-18** (aanbevolen, goedkoop, snel)
- **gpt-4o-2024-08-06** (krachtigste, duurder)
- **gpt-3.5-turbo-0125** (legacy)

### Hyperparameters

In `scripts/fine_tune.py`:

```python
hyperparameters={
    "n_epochs": 3  # Aantal training epochs
}
```

Aanbevelingen:
- **< 100 voorbeelden**: 3-4 epochs
- **100-1000 voorbeelden**: 2-3 epochs
- **> 1000 voorbeelden**: 1-2 epochs

## 📖 Gebruik van het Model

### Via OpenAI API

```python
from openai import OpenAI

client = OpenAI(api_key="your-api-key")

response = client.chat.completions.create(
    model="ft:gpt-4o-mini-2024-07-18:org:oslo-zaalreservatie:xxxxx",
    messages=[
        {
            "role": "system",
            "content": "Je bent een SPARQL-query generator voor het OSLO Zaalreservatie vocabularium."
        },
        {
            "role": "user",
            "content": "Welke zalen zijn beschikbaar morgen tussen 14u en 18u?"
        }
    ]
)

query = response.choices[0].message.content
print(query)
```

### Via cURL

```bash
curl https://api.openai.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "ft:gpt-4o-mini-2024-07-18:org:oslo-zaalreservatie:xxxxx",
    "messages": [
      {
        "role": "system",
        "content": "Je bent een SPARQL-query generator voor het OSLO Zaalreservatie vocabularium."
      },
      {
        "role": "user",
        "content": "Welke zalen hebben wifi?"
      }
    ]
  }'
```

## 🔍 SPARQL Query Voorbeelden

### Capaciteit filter

**Input**: "Ik zoek een zaal voor 80 personen"

**Output**:
```sparql
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>

SELECT ?zaal ?naam ?capaciteit WHERE {
  ?zaal a zaalreservatie:Zaal ;
        zaalreservatie:naam ?naam ;
        zaalreservatie:capaciteit ?capaciteit .

  FILTER(?capaciteit >= 80)
}
```

### Voorzieningen filter

**Input**: "Welke zalen hebben wifi en een beamer?"

**Output**:
```sparql
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>

SELECT ?zaal ?naam WHERE {
  ?zaal a zaalreservatie:Zaal ;
        zaalreservatie:naam ?naam ;
        zaalreservatie:heeftVoorziening ?wifi ;
        zaalreservatie:heeftVoorziening ?beamer .

  ?wifi zaalreservatie:voorziening_type "wifi" .
  ?beamer zaalreservatie:voorziening_type "beamer" .
}
```

### Beschikbaarheid + tijd

**Input**: "Welke zalen zijn beschikbaar vrijdagavond?"

**Output**:
```sparql
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?zaal ?naam WHERE {
  ?zaal a zaalreservatie:Zaal ;
        zaalreservatie:naam ?naam ;
        zaalreservatie:heeftBeschikbaarheid ?beschikbaarheid .

  ?beschikbaarheid zaalreservatie:tijdsslot ?tijdsslot .
  ?tijdsslot zaalreservatie:dagVanWeek zaalreservatie:Vrijdag ;
             zaalreservatie:startTijd ?start .

  FILTER(HOURS(?start) >= 18)
}
```

## 🧪 Testing

### Valideer trainingsdata

```bash
python scripts/validate_queries.py
```

### Test een query

```python
from rdflib.plugins.sparql import prepareQuery

query = """
PREFIX zaalreservatie: <https://data.vlaanderen.be/ns/zaalreservatie#>
SELECT ?zaal WHERE { ?zaal a zaalreservatie:Zaal }
"""

try:
    prepareQuery(query)
    print("✅ Valid SPARQL")
except Exception as e:
    print(f"❌ Invalid: {e}")
```

## 📚 Documentatie

- [Context & Fine-tuning Guide](docs/CONTEXT.md)
- [OSLO Zaalreservatie Vocabularium](https://data.vlaanderen.be/ns/zaalreservatie/)
- [OSLO Zaalreservatie Applicatieprofiel](https://data.vlaanderen.be/standaarden/applicatieprofiel-zaalreservatie)
- [OpenAI Fine-tuning Docs](https://platform.openai.com/docs/guides/fine-tuning)

## 🤝 Bijdragen

### Trainingsdata uitbreiden

1. Fork de repository
2. Voeg voorbeelden toe in `training-data/examples.jsonl`
3. Valideer: `python scripts/validate_queries.py`
4. Maak pull request

### Richtlijnen

- Gebruik correcte OSLO namespace
- Queries moeten syntactisch correct zijn
- Diversiteit in vraagtypen (capaciteit, voorzieningen, tijd, locatie)
- Nederlands voor user input
- SPARQL voor assistant output

## 📝 Licentie

Dit project is onderdeel van het OSLO-programma en volgt de [Modellicentie Gratis Hergebruik](https://data.vlaanderen.be/docs/modellicentie-gratis-hergebruik.html).

## ⚠️ Belangrijke Opmerkingen

1. **Geen data in model**: Het model bevat zelf geen zaaldata, alleen query-generatie logica
2. **Live data vereist**: Gegenereerde queries moeten uitgevoerd worden op een RDF triplestore
3. **Tijdsafhandeling**: Relatieve tijden ("morgen", "volgende week") vereisen runtime verwerking
4. **API Kosten**: Fine-tuning en gebruik kosten OpenAI credits

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/MPParsley/OSLO-zaalverhuur/issues)
- **OSLO Support**: https://www.vlaanderen.be/digitaal-vlaanderen/onze-oplossingen/oslo

## 🔗 Links

- [OSLO Homepage](https://www.vlaanderen.be/digitaal-vlaanderen/onze-oplossingen/oslo)
- [Data Vlaanderen](https://data.vlaanderen.be/)
- [OpenAI Platform](https://platform.openai.com/)

---

**Status**: 🚧 In ontwikkeling

**Laatste update**: 2026-01-06
