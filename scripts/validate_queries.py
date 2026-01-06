#!/usr/bin/env python3
"""
SPARQL Query Validator

Dit script valideert de SPARQL queries in de trainingsdata op:
- Syntactische correctheid
- Gebruik van correcte OSLO Zaalreservatie namespace
- Aanwezigheid van vereiste prefixes
"""

import json
import sys
from pathlib import Path
from typing import List, Tuple
from rdflib.plugins.sparql import prepareQuery
from rdflib.plugins.sparql.parser import ParseException


REQUIRED_NAMESPACE = "https://data.vlaanderen.be/ns/zaalreservatie#"


def extract_queries_from_jsonl(file_path: Path) -> List[Tuple[int, str]]:
    """
    Extraheer SPARQL queries uit JSONL trainingsdata.

    Args:
        file_path: Pad naar JSONL bestand

    Returns:
        List van (line_number, query) tuples
    """
    queries = []

    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f, 1):
            data = json.loads(line)
            messages = data.get('messages', [])

            for msg in messages:
                if msg.get('role') == 'assistant':
                    content = msg.get('content', '')
                    if 'SELECT' in content or 'CONSTRUCT' in content or 'ASK' in content:
                        queries.append((idx, content))

    return queries


def validate_query(query: str) -> Tuple[bool, str]:
    """
    Valideer een SPARQL query.

    Args:
        query: SPARQL query string

    Returns:
        (is_valid, error_message) tuple
    """
    # Check voor OSLO namespace
    if REQUIRED_NAMESPACE not in query:
        return False, f"OSLO Zaalreservatie namespace ontbreekt: {REQUIRED_NAMESPACE}"

    # Check voor zaalreservatie prefix
    if "PREFIX zaalreservatie:" not in query:
        return False, "PREFIX zaalreservatie: declaratie ontbreekt"

    # Probeer query te parsen
    try:
        prepareQuery(query)
        return True, ""
    except ParseException as e:
        return False, f"SPARQL syntax error: {e}"
    except Exception as e:
        return False, f"Validatie error: {e}"


def main():
    training_file = Path('training-data/examples.jsonl')

    if not training_file.exists():
        print(f"❌ Trainingsbestand niet gevonden: {training_file}")
        sys.exit(1)

    print("🔍 SPARQL Query Validatie")
    print("=" * 50)

    queries = extract_queries_from_jsonl(training_file)
    print(f"📊 Gevonden queries: {len(queries)}\n")

    all_valid = True
    for line_num, query in queries:
        is_valid, error = validate_query(query)

        if is_valid:
            print(f"✅ Regel {line_num}: Valid")
        else:
            print(f"❌ Regel {line_num}: {error}")
            all_valid = False

    print("\n" + "=" * 50)
    if all_valid:
        print("✅ Alle queries zijn geldig!")
        sys.exit(0)
    else:
        print("❌ Sommige queries zijn ongeldig")
        sys.exit(1)


if __name__ == '__main__':
    main()
