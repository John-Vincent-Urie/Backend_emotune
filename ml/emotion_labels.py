"""Shared emotion label definitions, GoEmotions mapping, and HF loader helper.

Single source of truth for the runtime classifier (``backend/ml/emotion_classifier.py``)
and the BERT training pipeline (``ml_model/train_bert.py``), which both need to agree on
the label list/ids and the GoEmotions -> EmoTune label mapping. This module has no Django
dependency so it can be imported by the standalone training script.
"""
from __future__ import annotations

import warnings

EMOTIONS = [
    'happy',
    'sad',
    'angry',
    'motivational',
    'fear',
    'depressing',
    'surprising',
    'stressed',
    'calm',
    'lonely',
    'romantic',
    'nostalgic',
    'mixed',
]

LABEL2ID = {label: index for index, label in enumerate(EMOTIONS)}
ID2LABEL = {index: label for index, label in enumerate(EMOTIONS)}

# -- Mix schema (team decision, 2026-10-30). The general "mixed" label is split
# into five named mixes, each a pair of emotions felt at once. A model trained
# on this schema predicts the 12 single emotions or one of these five; the
# names match the EmotionPair rows (migration 0016) so a predicted mix maps
# straight to its songs. Emotions are listed in the order the app shows them.
MIX_LABEL_EMOTIONS = {
    'bittersweet': ('happy', 'sad'),
    'romantic_melancholy': ('sad', 'romantic'),
    'tender': ('calm', 'romantic'),
    'bittersweet_nostalgia': ('happy', 'nostalgic'),
    'challenged': ('stressed', 'motivational'),
}
MIX_LABELS = list(MIX_LABEL_EMOTIONS)
SINGLE_EMOTIONS = [emotion for emotion in EMOTIONS if emotion != 'mixed']
MIX_MODEL_LABELS = SINGLE_EMOTIONS + MIX_LABELS

# Model output schemas by name. "v1" is the 13-label model served until a mix
# model is trained and promoted; "mix" is the 17-label schema above. A saved
# checkpoint's id2label says which one it is.
LABEL_SCHEMAS = {
    'v1': list(EMOTIONS),
    'mix': list(MIX_MODEL_LABELS),
}

# GoEmotions label -> EmoTune label. Verified identical between the previous
# copies in ml_model/train_bert.py (GOEMOTIONS_MAP) and
# backend/ml/emotion_classifier.py (GOEMOTIONS_LABEL_MAP) before merging.
GOEMOTIONS_LABEL_MAP = {
    # Happy
    "joy": "happy",
    "amusement": "happy",
    "excitement": "happy",
    "gratitude": "happy",
    "admiration": "happy",

    # Sad
    "sadness": "sad",
    "grief": "sad",
    "disappointment": "sad",
    "remorse": "sad",

    # Angry
    "anger": "angry",
    "annoyance": "angry",
    "disapproval": "angry",
    "disgust": "angry",

    # Fear
    "fear": "fear",
    "nervousness": "fear",

    # Romantic
    "love": "romantic",
    "desire": "romantic",
    "caring": "romantic",

    # Motivational
    "optimism": "motivational",
    "pride": "motivational",
    "approval": "motivational",

    # Calm
    "relief": "calm",

    # Surprising
    "surprise": "surprising",
    "realization": "surprising",

    # Stressed
    "confusion": "stressed",
    "embarrassment": "stressed"
}

HF_RESUME_DOWNLOAD_WARNING = (
    r"`resume_download` is deprecated and will be removed in version 1\.0\.0\."
)


def call_huggingface_loader(loader, *args, **kwargs):
    """Suppress an upstream deprecation warning emitted by older transformers releases."""
    with warnings.catch_warnings():
        warnings.filterwarnings(
            "ignore",
            message=HF_RESUME_DOWNLOAD_WARNING,
            category=FutureWarning,
            module="huggingface_hub.file_download",
        )
        return loader(*args, **kwargs)
