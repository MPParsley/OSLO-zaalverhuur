#!/usr/bin/env python3
"""
OSLO Zaalreservatie Fine-tuning Script

Dit script handelt het fine-tuning proces af voor het SPARQL query-genererende model.
Het model leert om natuurlijke taalvragen te vertalen naar SPARQL queries conform
het OSLO Zaalreservatie vocabularium.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict
import openai
from openai import OpenAI


def validate_training_data(file_path: Path) -> bool:
    """
    Valideer de trainingsdata op correctheid.

    Args:
        file_path: Pad naar het JSONL trainingsbestand

    Returns:
        True als de data geldig is, anders False
    """
    print(f"📋 Valideren van trainingsdata: {file_path}")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        if len(lines) < 10:
            print(f"⚠️  Waarschuwing: Slechts {len(lines)} voorbeelden gevonden. Minimaal 10 aanbevolen.")

        for idx, line in enumerate(lines, 1):
            try:
                data = json.loads(line)

                # Valideer structuur
                if 'messages' not in data:
                    print(f"❌ Regel {idx}: 'messages' key ontbreekt")
                    return False

                messages = data['messages']
                if len(messages) < 2:
                    print(f"❌ Regel {idx}: Minimaal 2 messages vereist (system/user en assistant)")
                    return False

                # Valideer dat er een assistant response is
                has_assistant = any(msg.get('role') == 'assistant' for msg in messages)
                if not has_assistant:
                    print(f"❌ Regel {idx}: Geen assistant response gevonden")
                    return False

                # Valideer dat assistant response SPARQL bevat
                for msg in messages:
                    if msg.get('role') == 'assistant':
                        content = msg.get('content', '')
                        if 'PREFIX' not in content or 'SELECT' not in content:
                            print(f"⚠️  Regel {idx}: Assistant response lijkt geen SPARQL query te bevatten")

            except json.JSONDecodeError as e:
                print(f"❌ Regel {idx}: Ongeldige JSON - {e}")
                return False

        print(f"✅ Trainingsdata gevalideerd: {len(lines)} voorbeelden")
        return True

    except FileNotFoundError:
        print(f"❌ Bestand niet gevonden: {file_path}")
        return False
    except Exception as e:
        print(f"❌ Validatiefout: {e}")
        return False


def upload_training_file(client: OpenAI, file_path: Path) -> str:
    """
    Upload het trainingsbestand naar OpenAI.

    Args:
        client: OpenAI client instance
        file_path: Pad naar het JSONL trainingsbestand

    Returns:
        File ID van het geüploade bestand
    """
    print(f"📤 Uploaden van trainingsbestand...")

    try:
        with open(file_path, 'rb') as f:
            response = client.files.create(
                file=f,
                purpose='fine-tune'
            )

        file_id = response.id
        print(f"✅ Bestand geüpload: {file_id}")
        return file_id

    except Exception as e:
        print(f"❌ Upload gefaald: {e}")
        sys.exit(1)


def create_fine_tune_job(
    client: OpenAI,
    file_id: str,
    model: str = "gpt-4o-mini-2024-07-18",
    suffix: str = "oslo-zaalreservatie"
) -> str:
    """
    Start een fine-tuning job.

    Args:
        client: OpenAI client instance
        file_id: ID van het geüploade trainingsbestand
        model: Basis model om te fine-tunen
        suffix: Suffix voor het model name

    Returns:
        Fine-tune job ID
    """
    print(f"🚀 Starten van fine-tuning job...")
    print(f"   Basis model: {model}")
    print(f"   Suffix: {suffix}")

    try:
        response = client.fine_tuning.jobs.create(
            training_file=file_id,
            model=model,
            suffix=suffix,
            hyperparameters={
                "n_epochs": 3  # Kan aangepast worden op basis van data grootte
            }
        )

        job_id = response.id
        print(f"✅ Fine-tuning job gestart: {job_id}")
        print(f"   Status: {response.status}")
        return job_id

    except Exception as e:
        print(f"❌ Fine-tuning job gefaald: {e}")
        sys.exit(1)


def check_job_status(client: OpenAI, job_id: str) -> Dict:
    """
    Controleer de status van een fine-tuning job.

    Args:
        client: OpenAI client instance
        job_id: Fine-tune job ID

    Returns:
        Job status informatie
    """
    try:
        response = client.fine_tuning.jobs.retrieve(job_id)

        status_info = {
            'id': response.id,
            'status': response.status,
            'model': response.model,
            'fine_tuned_model': response.fine_tuned_model,
            'created_at': response.created_at,
            'finished_at': response.finished_at
        }

        return status_info

    except Exception as e:
        print(f"❌ Status check gefaald: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Fine-tune een model voor OSLO Zaalreservatie SPARQL query generatie'
    )
    parser.add_argument(
        '--training-file',
        type=Path,
        default=Path('training-data/examples.jsonl'),
        help='Pad naar JSONL trainingsbestand'
    )
    parser.add_argument(
        '--model',
        type=str,
        default='gpt-4o-mini-2024-07-18',
        help='Basis model om te fine-tunen'
    )
    parser.add_argument(
        '--suffix',
        type=str,
        default='oslo-zaalreservatie',
        help='Suffix voor het model name'
    )
    parser.add_argument(
        '--check-status',
        type=str,
        help='Controleer status van bestaande job (geef job ID)'
    )
    parser.add_argument(
        '--api-key',
        type=str,
        help='OpenAI API key (of gebruik OPENAI_API_KEY env var)'
    )

    args = parser.parse_args()

    # Setup API key
    api_key = args.api_key or os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OpenAI API key is vereist. Gebruik --api-key of OPENAI_API_KEY env var")
        sys.exit(1)

    client = OpenAI(api_key=api_key)

    # Check status mode
    if args.check_status:
        print(f"🔍 Controleren van job status: {args.check_status}")
        status = check_job_status(client, args.check_status)
        print("\n📊 Job Status:")
        print(f"   ID: {status['id']}")
        print(f"   Status: {status['status']}")
        print(f"   Basis model: {status['model']}")
        print(f"   Fine-tuned model: {status['fine_tuned_model']}")
        print(f"   Aangemaakt: {status['created_at']}")
        print(f"   Voltooid: {status['finished_at']}")
        return

    # Fine-tuning mode
    print("🎯 OSLO Zaalreservatie Fine-tuning")
    print("=" * 50)

    # Valideer trainingsdata
    if not validate_training_data(args.training_file):
        sys.exit(1)

    # Upload bestand
    file_id = upload_training_file(client, args.training_file)

    # Start fine-tuning
    job_id = create_fine_tune_job(
        client,
        file_id,
        model=args.model,
        suffix=args.suffix
    )

    print("\n" + "=" * 50)
    print("✅ Fine-tuning proces gestart!")
    print(f"\n💡 Volg de voortgang met:")
    print(f"   python scripts/fine_tune.py --check-status {job_id}")
    print(f"\n📝 Job ID voor GitHub Actions output:")
    print(f"   {job_id}")

    # Schrijf job ID naar output file voor GitHub Actions
    output_file = Path('fine_tune_job_id.txt')
    output_file.write_text(job_id)
    print(f"\n💾 Job ID opgeslagen in: {output_file}")


if __name__ == '__main__':
    main()
