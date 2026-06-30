# Rapport de qualite des donnees

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
{
  "raw_rows": 256916,
  "empty_removed": 116,
  "duplicates_removed": 10390,
  "generic_removed": 2877,
  "too_long_removed": 290,
  "final_rows": 243243,
  "train_rows": 194594,
  "validation_rows": 48649
}
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

- Longueur moyenne prompt : 432.97 caracteres
- Longueur moyenne completion : 531.36 caracteres
- Longueur moyenne approximate : 230.94 tokens

## Recommandation

Pour la remise finale :

- cote DATA : garder le dataset clean complet et le rapport qualite
- cote IA : utiliser `train.jsonl` et `validation.jsonl`
