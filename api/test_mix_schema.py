"""A model trained on the mix schema (12 emotions + 5 named mixes, team
decision 2026-10-30) is understood by the classifier, and a predicted mix
plays that mix's songs."""
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from api.input_validation import decide_after_crisis
from ml.emotion_classifier import EmotionClassifier
from ml.emotion_labels import EMOTIONS, MIX_LABEL_EMOTIONS, MIX_MODEL_LABELS


def _mix_scores(top_label, confidence=0.9):
    rest = (1 - confidence) / (len(MIX_MODEL_LABELS) - 1)
    return {label: (confidence if label == top_label else rest) for label in MIX_MODEL_LABELS}


def _model_with_labels(labels):
    return SimpleNamespace(config=SimpleNamespace(
        id2label={index: label for index, label in enumerate(labels)}, num_labels=len(labels),
    ))


class MixSchemaClassifierTests(SimpleTestCase):
    def _result(self, scores):
        return EmotionClassifier()._build_result(
            scores, prediction_source='bert', prediction_strategy='bert_high_confidence',
            fallback_used=False, fallback_reason=None, uncertain=False,
        )

    def test_a_mix_schema_model_is_accepted_and_the_old_one_still_is(self):
        classifier = EmotionClassifier()
        self.assertEqual(
            classifier._resolve_model_label_map(_model_with_labels(MIX_MODEL_LABELS)),
            MIX_MODEL_LABELS,
        )
        self.assertEqual(classifier._resolve_model_label_map(_model_with_labels(EMOTIONS)), EMOTIONS)

    def test_a_predicted_mix_becomes_its_two_emotions(self):
        for mix_label, (first, second) in MIX_LABEL_EMOTIONS.items():
            result = self._result(_mix_scores(mix_label))
            self.assertEqual(result['mix_label'], mix_label)
            self.assertEqual((result['emotion'], result['secondary_emotion']), (first, second))
            self.assertAlmostEqual(result['confidence'], 0.9)
            self.assertEqual(set(result['all_scores']), set(EMOTIONS))
            self.assertEqual(result['label_schema_version'], 'mix')

    def test_a_single_emotion_from_a_mix_model_stays_single(self):
        result = self._result(_mix_scores('sad'))
        self.assertIsNone(result['mix_label'])
        self.assertEqual(result['emotion'], 'sad')
        self.assertNotIn(result['top_emotions'][1]['emotion'], MIX_LABEL_EMOTIONS)

    def test_the_decision_follows_the_predicted_mix(self):
        result = self._result(_mix_scores('bittersweet', 0.8))
        decision = decide_after_crisis('I graduated today and it feels strange', lambda _t: result)
        self.assertEqual((decision.status, decision.emotion, decision.second_emotion), ('ok', 'happy', 'sad'))
        self.assertEqual(decision.reason, 'model_mix_label')


class MixSchemaAnalyzeTests(APITestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(
            username='mixschema', email='mixschema@example.com', password='pw12345!',
        )
        self.client.force_authenticate(user=user)

    @patch('api.views.get_classifier')
    def test_a_predicted_mix_plays_that_mixs_songs(self, mock_classifier):
        classifier = EmotionClassifier()
        mock_classifier.return_value.predict.return_value = classifier._build_result(
            _mix_scores('tender', 0.85), prediction_source='bert',
            prediction_strategy='bert_high_confidence', fallback_used=False,
            fallback_reason=None, uncertain=False,
        )

        body = self.client.post(
            '/api/analyze/', {'text': 'we watched the rain together and it felt so gentle'},
            format='json',
        ).json()

        self.assertEqual(body['emotion_pair']['display_name'], 'Tender')
        self.assertEqual(
            [t['name'] for t in body['tracks']],
            ['Palagi', 'Pasilyo', 'Tahanan', 'Mahika', 'Tadhana'],
        )
