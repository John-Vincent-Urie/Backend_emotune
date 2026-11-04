"""Score two-emotion detection on dataset/mixed_emotion_eval.csv.

    python manage.py eval_mixed_emotions
    python manage.py eval_mixed_emotions --split test
    python manage.py eval_mixed_emotions --source team      # only the team's rows
    python manage.py eval_mixed_emotions --cache mixed_predictions.json

Each row runs what /api/analyze/ runs before choosing songs: the crisis check,
then `decide_after_crisis` with the real classifier. A row passes when:

- mix            -- the two detected emotions are the expected pair, in any order
- single/negated -- no pair is detected (the emotion itself is reported, not scored)
- mixed_unnamed  -- no pair is detected (the two emotions have no named mix)

This is the baseline (BERT + the sentence word rule) that a multi-label
classifier has to beat. --cache keeps the classifier's output per text in a
JSON file, so repeat runs do not reload BERT.
"""
from collections import defaultdict
import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand

from api.input_validation import decide_after_crisis
from api.safety import assess_crisis_severity
from ml.emotion_classifier import get_classifier

DEFAULT_CSV = Path(__file__).resolve().parents[4] / 'dataset' / 'mixed_emotion_eval.csv'
CATEGORY_ORDER = ('mix', 'mixed_unnamed', 'single', 'negated')


class Command(BaseCommand):
    help = 'Accuracy of two-emotion (named mix) detection on a labelled CSV.'

    def add_arguments(self, parser):
        parser.add_argument('--csv', default=str(DEFAULT_CSV))
        parser.add_argument('--split', choices=('dev', 'test', 'all'), default='all')
        parser.add_argument('--source', help='Only rows from this source (e.g. team, seed).')
        parser.add_argument('--cache', help='JSON file of classifier outputs keyed by text.')

    def handle(self, *args, **options):
        with open(options['csv'], encoding='utf-8', newline='') as handle:
            rows = list(csv.DictReader(handle))
        if options['split'] != 'all':
            rows = [row for row in rows if row['split'] == options['split']]
        if options['source']:
            rows = [row for row in rows if row['source'] == options['source']]
        cache_path = Path(options['cache']) if options['cache'] else None
        cache = (
            json.loads(cache_path.read_text(encoding='utf-8'))
            if cache_path and cache_path.exists()
            else {}
        )
        cached_count = len(cache)

        def predict(text):
            if text not in cache:
                cache[text] = get_classifier().predict(text)
            return cache[text]

        self._report(rows, predict)
        if cache_path and len(cache) != cached_count:
            cache_path.write_text(json.dumps(cache, indent=1, sort_keys=True), encoding='utf-8')

    def _report(self, rows, predict):
        per_category = defaultdict(lambda: [0, 0])
        per_pair = defaultdict(lambda: [0, 0])
        misses, crisis_rows = [], []
        for row in rows:
            text = row['text']
            if assess_crisis_severity(text):
                crisis_rows.append(row)
                continue
            decision = decide_after_crisis(text, predict)
            detected = (
                {decision.emotion, decision.second_emotion}
                if decision.second_emotion
                else None
            )
            if row['category'] == 'mix':
                ok = detected == set(row['expected_emotions'].split('|'))
                per_pair[row['expected_pair']][0] += int(ok)
                per_pair[row['expected_pair']][1] += 1
            else:
                ok = detected is None
            per_category[row['category']][0] += int(ok)
            per_category[row['category']][1] += 1
            if not ok:
                misses.append((row, decision))

        self.stdout.write(f'Two-emotion detection ({len(rows)} rows)\n')
        self.stdout.write(f"{'category':<16}{'correct':>9}{'total':>7}{'accuracy':>10}")
        correct_all = total_all = 0
        for category in CATEGORY_ORDER:
            if category not in per_category:
                continue
            correct, total = per_category[category]
            correct_all += correct
            total_all += total
            self.stdout.write(f'{category:<16}{correct:>9}{total:>7}{correct / total:>10.1%}')
        if total_all:
            self.stdout.write(
                f"{'overall':<16}{correct_all:>9}{total_all:>7}{correct_all / total_all:>10.1%}"
            )
        if per_pair:
            self.stdout.write('\nMix rows by expected pair:')
            for pair, (correct, total) in sorted(per_pair.items()):
                self.stdout.write(f'  {pair:<14}{correct:>3}/{total}')
        if crisis_rows:
            self.stdout.write(f'\nCaught by the crisis check first (not scored): {len(crisis_rows)}')
            for row in crisis_rows:
                self.stdout.write(f'  {row["text"]}')
        if misses:
            self.stdout.write('\nMisses (expected -> got, how):')
            for row, decision in misses:
                got = (
                    f'{decision.emotion} + {decision.second_emotion}'
                    if decision.second_emotion
                    else (decision.emotion or decision.status)
                )
                expected = row['expected_emotions'].replace('|', ' + ')
                self.stdout.write(
                    f"  [{row['category']}] {row['text']!r}: {expected} -> {got} ({decision.reason})"
                )
