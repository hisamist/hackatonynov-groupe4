"""Prepare a simple prompt/completion medical dataset in the target repo layout."""

import json
import math
import random
import re
from html import unescape
from pathlib import Path

from datasets import load_dataset, load_from_disk


ROOT = Path(__file__).resolve().parents[2]
DATASET_PATH = ROOT / "medical_dataset" / "source"
MEDICAL_DATASET_DIR = ROOT / "medical_dataset"
REPORTS_DIR = MEDICAL_DATASET_DIR / "tests_quality_report"
CLEAN_PATH = MEDICAL_DATASET_DIR / "medical_dataset_clean_simple.jsonl"
SPLIT_DIR = MEDICAL_DATASET_DIR / "prompt_completion"
SUMMARY_PATH = REPORTS_DIR / "dataset_summary_simple.json"
REPORT_PATH = REPORTS_DIR / "data_quality_report_simple.md"
LIVRABLES_REPORT_PATH = ROOT / "Livrables" / "rapport_qualite_donnees.md"
RANDOM_SEED = 42
MAX_APPROX_TOKENS = 1024


GENERIC_DOCTOR_PATTERNS = [
    re.compile(r"^for further information consult\b", re.IGNORECASE),
    re.compile(r"^for more information consult\b", re.IGNORECASE),
    re.compile(r"^revert back\b", re.IGNORECASE),
    re.compile(r"^please (consult|revert)\b", re.IGNORECASE),
]


def normalize_text(text: str) -> str:
    """Normalize raw text before filtering and export."""
    text = "" if text is None else str(text)
    text = unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("\xa0", " ")
    text = text.replace("`", "'")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\s+([,.;:?!])", r"\1", text)
    if text and text[0].isalpha():
        text = text[0].upper() + text[1:]
    return text


def is_generic_doctor_reply(text: str) -> bool:
    """Remove answers that are too short or too generic to be useful."""
    lowered = text.strip().lower()
    if len(lowered) < 80:
        return True
    return any(pattern.search(lowered) for pattern in GENERIC_DOCTOR_PATTERNS)


def approx_token_count(prompt: str, completion: str) -> int:
    """Estimate token count without requiring a local tokenizer."""
    return math.ceil(len(f"{prompt} {completion}".split()) * 1.35)


def load_medical_dataset():
    """Load the dataset from local disk when available, otherwise from Hugging Face."""
    if DATASET_PATH.exists():
        return load_from_disk(str(DATASET_PATH))
    return load_dataset("ruslanmv/ai-medical-chatbot")


def main() -> None:
    """Build the cleaned dataset and prompt/completion splits."""
    random.seed(RANDOM_SEED)
    MEDICAL_DATASET_DIR.mkdir(parents=True, exist_ok=True)
    SPLIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    LIVRABLES_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    dataset = load_medical_dataset()
    df = dataset["train"].to_pandas()
    raw_rows = len(df)

    for column in ["Description", "Patient", "Doctor"]:
        df[column] = df[column].map(normalize_text)

    df = df.dropna(subset=["Patient", "Doctor"])
    df = df[(df["Patient"].str.len() > 20) & (df["Doctor"].str.len() > 20)].copy()
    empty_removed = raw_rows - len(df)

    deduped_df = df.drop_duplicates(subset=["Patient", "Doctor"]).copy()
    duplicates_removed = len(df) - len(deduped_df)

    filtered_df = deduped_df[~deduped_df["Doctor"].map(is_generic_doctor_reply)].copy()
    generic_removed = len(deduped_df) - len(filtered_df)

    filtered_df["approx_token_count"] = filtered_df.apply(
        lambda row: approx_token_count(row["Patient"], row["Doctor"]),
        axis=1,
    )
    length_filtered_df = filtered_df[filtered_df["approx_token_count"] <= MAX_APPROX_TOKENS].copy()
    too_long_removed = len(filtered_df) - len(length_filtered_df)

    length_filtered_df = length_filtered_df.sample(frac=1.0, random_state=RANDOM_SEED).reset_index(drop=True)

    total = len(length_filtered_df)
    train_end = int(total * 0.8)

    train_df = length_filtered_df.iloc[:train_end].copy()
    val_df = length_filtered_df.iloc[train_end:].copy()

    with CLEAN_PATH.open("w", encoding="utf-8") as handle:
        for record in length_filtered_df.to_dict(orient="records"):
            payload = {
                "Description": record["Description"],
                "prompt": record["Patient"],
                "completion": record["Doctor"],
                "approx_token_count": int(record["approx_token_count"]),
            }
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    for split_name, split_df in [("train", train_df), ("validation", val_df)]:
        with (SPLIT_DIR / f"{split_name}.jsonl").open("w", encoding="utf-8") as handle:
            for record in split_df.to_dict(orient="records"):
                payload = {
                    "prompt": record["Patient"],
                    "completion": record["Doctor"],
                }
                handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    avg_prompt_len = round(length_filtered_df["Patient"].str.len().mean(), 2)
    avg_completion_len = round(length_filtered_df["Doctor"].str.len().mean(), 2)
    avg_tokens = round(length_filtered_df["approx_token_count"].mean(), 2)

    summary = {
        "raw_rows": raw_rows,
        "empty_removed": empty_removed,
        "duplicates_removed": duplicates_removed,
        "generic_removed": generic_removed,
        "too_long_removed": too_long_removed,
        "final_rows": total,
        "train_rows": len(train_df),
        "validation_rows": len(val_df),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    report = f"""# Rapport de qualite des donnees

## Contexte

Ce rapport est genere automatiquement par le pipeline DATA retenu.

Le perimetre retenu est volontairement simple :

- normalisation des textes
- suppression des lignes vides ou trop courtes
- suppression des doublons
- suppression des reponses trop generiques
- filtrage des exemples trop longs
- export final en `prompt` / `completion`

Script de reference :

- `scripts/data/prepare_datasets_simple.py`

## Source de donnees

- Dataset : `ruslanmv/ai-medical-chatbot`
- Chargement local : utilise seulement si `medical_dataset/source` existe
- Sinon : chargement direct depuis Hugging Face
- Split utilise : `train`

Colonnes d'origine :

- `Description`
- `Patient`
- `Doctor`

## Resultats chiffres

```json
{json.dumps(summary, ensure_ascii=False, indent=2)}
```

## Interpretation

- `raw_rows` : nombre de lignes presentes dans le dataset brut
- `empty_removed` : lignes supprimees car vides ou trop courtes
- `duplicates_removed` : doublons supprimes sur `Patient` + `Doctor`
- `generic_removed` : reponses trop generiques retirees
- `too_long_removed` : exemples ecartes pour longueur excessive
- `final_rows` : taille finale du dataset retenu
- `train_rows` : taille du split d'entrainement
- `validation_rows` : taille du split de validation

## Fichiers produits

### Dataset nettoye complet

- `medical_dataset/medical_dataset_clean_simple.jsonl`

Colonnes principales :

- `Description`
- `prompt`
- `completion`
- `approx_token_count`

### Splits remis a l'equipe IA

- `medical_dataset/prompt_completion/train.jsonl`
- `medical_dataset/prompt_completion/validation.jsonl`

Format final :

```text
{"prompt": "...", "completion": "..."}
```

Le fichier `medical_dataset_clean_simple.jsonl` est la source propre complete dont sont issus `train.jsonl` et `validation.jsonl`.

### Artefacts de controle qualite

- `medical_dataset/tests_quality_report/dataset_summary_simple.json`
- `medical_dataset/tests_quality_report/data_quality_report_simple.md`

## Livrables de remise

- `Livrables/dataset_medical_prepare_nettoye/medical_dataset_clean_simple.jsonl`
- `Livrables/dataset_medical_prepare_nettoye/medical_dataset_prompt_completion/train.jsonl`
- `Livrables/dataset_medical_prepare_nettoye/medical_dataset_prompt_completion/validation.jsonl`
- `Livrables/rapport_qualite_donnees.md`

## Statistiques complementaires

- Longueur moyenne prompt : {avg_prompt_len} caracteres
- Longueur moyenne completion : {avg_completion_len} caracteres
- Longueur moyenne approximate : {avg_tokens} tokens

## Recommandation

Pour la remise finale :

- cote DATA : garder le dataset clean complet et le rapport qualite
- cote IA : utiliser `train.jsonl` et `validation.jsonl`
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    LIVRABLES_REPORT_PATH.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
