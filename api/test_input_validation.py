"""The analyze input checks: gibberish, non-English, emotion words, off-topic
and unclear text get a prompt instead of a guessed emotion, and the crisis and
concern paths are untouched."""

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from api.input_validation import (
    CLARIFY_MESSAGES,
    STATUS_GIBBERISH,
    STATUS_NON_ENGLISH,
    STATUS_OFF_TOPIC,
    STATUS_UNCLEAR,
    STATUS_UNSUPPORTED_MIX,
    check_input,
    decide_after_crisis,
    model_result_is_unclear,
    named_pair_in_sentence,
    second_model_emotion,
    sentence_emotions,
)
from users.models import PromptHistory


def _prediction(emotion='sad', confidence=0.95, margin=0.9, source='bert'):
    return {
        'emotion': emotion, 'confidence': confidence,
        'all_scores': {emotion: confidence},
        'top_emotions': [{'emotion': emotion, 'confidence': confidence}],
        'prediction_source': source, 'prediction_strategy': 'bert_high_confidence',
        'confidence_band': 'high', 'confidence_margin': margin,
        'fallback_used': False, 'fallback_reason': None, 'needs_review': False,
        'secondary_emotion': None,
    }


class InputRuleTests(SimpleTestCase):
    def assertStatus(self, text, status):
        self.assertEqual(check_input(text).status, status, text)

    def test_keyboard_mash_is_gibberish(self):
        for text in ('dfhskksdnkjskbkjsb', 'asdfghjkl', 'qwe rty uio', 'aaaaaaa', '!!!!', '12345'):
            self.assertStatus(text, STATUS_GIBBERISH)

    def test_a_typo_in_a_real_sentence_is_not_gibberish(self):
        self.assertNotEqual(check_input('im so stresed about school').status, STATUS_GIBBERISH)

    def test_tagalog_and_taglish_are_non_english_not_gibberish(self):
        for text in ('pagod na ako', 'kinikilig', 'malungkot ako', 'I feel so pagod today',
                     'sobrang stressed ako', 'happy ako today'):
            self.assertStatus(text, STATUS_NON_ENGLISH)

    def test_english_with_filipino_names_and_look_alikes_stays_english(self):
        for text in ('I miss Manila so much', 'my lola cooked adobo and I felt so loved',
                     'I may cry after this movie', 'my pa called and I feel happy',
                     'I watched kung fu panda and I feel happy'):
            self.assertNotEqual(check_input(text).status, STATUS_NON_ENGLISH, text)

    def test_a_named_emotion_is_taken_as_said(self):
        cases = {
            'sad': 'sad', "i'm so stressed": 'stressed', 'feeling nostalgic today': 'nostalgic',
            'in love': 'romantic', 'scared': 'fear', 'depressed': 'depressing',
            'surprised': 'surprising', 'motivated': 'motivational', 'sooo happy': 'happy',
            'sadd': 'sad', '😭': 'sad', 'mixed feelings': 'mixed',
        }
        for text, emotion in cases.items():
            check = check_input(text)
            self.assertEqual((check.route, check.emotion), ('emotion_word', emotion), text)

    def test_negated_or_three_emotions_go_to_the_model(self):
        for text in ('not happy', "i'm not sad", 'not sad and lonely', 'sad lonely angry'):
            self.assertIsNone(check_input(text).emotion, text)

    def test_two_named_emotions_are_both_taken(self):
        cases = {
            'sad and lonely': ('sad', 'lonely'),
            'happy but nervous': ('happy', 'fear'),
            'i feel sad and lonely at the same time': ('sad', 'lonely'),
            'stressed but motivated': ('stressed', 'motivational'),
            'happy and sad': ('happy', 'sad'),
        }
        for text, (first, second) in cases.items():
            check = check_input(text)
            self.assertEqual(
                (check.route, check.emotion, check.second_emotion),
                ('emotion_word', first, second), text,
            )
    def test_a_mix_name_means_its_two_emotions(self):
        cases = {
            'bittersweet': ('happy', 'sad'), 'i feel so bittersweet': ('happy', 'sad'),
            'heartache': ('romantic', 'sad'), 'romantic melancholy': ('romantic', 'sad'),
            'bittersweet nostalgia': ('happy', 'nostalgic'),
            'feeling tender': ('calm', 'romantic'), 'sentimental': ('happy', 'nostalgic'),
            'challenged': ('motivational', 'stressed'),
        }
        for text, emotions in cases.items():
            check = check_input(text)
            self.assertEqual(check.route, 'emotion_word', text)
            self.assertEqual((check.emotion, check.second_emotion), emotions, text)
        # Two mixes, or a mix and another emotion, are more than two feelings.
        self.assertIsNone(check_input('bittersweet and angry').emotion)

    def test_a_sentence_names_its_mix_with_feeling_words_or_cues(self):
        cases = {
            "I'm happy I graduated but sad to leave my friends": ('happy', 'sad'),
            "I'm glad it's over but I'm also kind of heartbroken": ('happy', 'sad'),
            'it was my last day at school, I smiled but I also cried': ('happy', 'sad'),
            'my boyfriend broke up with me and I keep crying': ('romantic', 'sad'),
            'our anniversary dinner felt so calm and peaceful': ('romantic', 'calm'),
            'looking at old photos from childhood makes me smile': ('nostalgic', 'happy'),
            "so many deadlines this week but I won't give up": ('stressed', 'motivational'),
        }
        for text, pair in cases.items():
            self.assertEqual(named_pair_in_sentence(text), pair, text)
        # The model's emotion goes first when it is one of the two.
        self.assertEqual(
            named_pair_in_sentence('it was my last day at school, I smiled but I also cried', 'sad'),
            ('sad', 'happy'),
        )

    def test_negation_cancels_only_the_word_it_is_next_to(self):
        self.assertEqual(sentence_emotions("I'm not happy, just sad"), ['sad'])
        self.assertEqual(sentence_emotions('I am not sad, I smiled all day'), ['happy'])
        self.assertIsNone(named_pair_in_sentence("I'm not happy, just sad"))

    def test_no_pair_or_two_pairs_in_a_sentence_is_no_mix(self):
        self.assertIsNone(named_pair_in_sentence('the wedding made me sad that my lola was gone'))
        # Sad + lonely is not a named mix (removed 2026-10-30).
        self.assertIsNone(named_pair_in_sentence('nobody texted me and I cried all night'))
        # happy + sad and happy + nostalgic: which one is meant is not clear.
        self.assertIsNone(named_pair_in_sentence('happy and sad looking at my childhood photos'))

    def test_the_sentence_mix_replaces_mixed_or_one_of_its_two(self):
        text = "I'm happy I graduated but sad to leave my friends"
        for model_emotion in ('mixed', 'sad', 'happy'):
            decision = decide_after_crisis(text, lambda _t, e=model_emotion: _prediction(e, 0.84))
            self.assertEqual(
                sorted((decision.emotion, decision.second_emotion)), ['happy', 'sad'], model_emotion,
            )
        # A clear third reading is left alone.
        decision = decide_after_crisis(text, lambda _t: _prediction('nostalgic', 0.9))
        self.assertEqual((decision.emotion, decision.second_emotion), ('nostalgic', None))

    def test_mixed_words_without_a_pair_stay_mixed(self):
        for text in ('mixed feelings', 'conflicted', 'torn'):
            check = check_input(text)
            self.assertEqual((check.emotion, check.second_emotion), ('mixed', None), text)
        # "Mixed" is already the blend; one emotion has no second.
        self.assertEqual((check_input('mixed and sad').emotion, check_input('mixed and sad').second_emotion),
                         ('mixed', None))
        self.assertIsNone(check_input('sad').second_emotion)

    def test_a_strong_runner_up_is_a_second_emotion(self):
        def two(first, c1, second, c2):
            result = _prediction(first, c1, margin=c1 - c2)
            result['top_emotions'] = [
                {'emotion': first, 'confidence': c1}, {'emotion': second, 'confidence': c2},
            ]
            return result
        self.assertEqual(second_model_emotion(two('sad', 0.59, 'lonely', 0.30)), 'lonely')
        self.assertIsNone(second_model_emotion(two('sad', 0.91, 'angry', 0.04)))
        self.assertIsNone(second_model_emotion(two('mixed', 0.58, 'fear', 0.35)))
        # A near tie of two strong emotions is two feelings, not "please clarify".
        with_affect = check_input('I failed my exam and I feel terrible')
        self.assertFalse(model_result_is_unclear(two('sad', 0.46, 'romantic', 0.42), with_affect))
        # A near tie that is no named mix is still a guess.
        self.assertTrue(model_result_is_unclear(two('sad', 0.46, 'lonely', 0.42), with_affect))
        # ...unless one side is "mixed", which has no second list to blend.
        self.assertTrue(model_result_is_unclear(two('mixed', 0.46, 'sad', 0.42), with_affect))

    def test_questions_commands_and_facts_are_off_topic(self):
        for text in ('what is 2+2', 'play something for coding', 'the weather is nice',
                     'recommend a movie', 'the sky is blue', 'who won the game last night'):
            self.assertStatus(text, STATUS_OFF_TOPIC)

    def test_a_question_about_own_feelings_is_not_off_topic(self):
        self.assertEqual(check_input('why do I feel so sad lately?').status, 'pass')

    def test_requests_about_an_emotion_are_off_topic(self):
        for text in ('define loneliness', 'write a poem about being angry',
                     'tell me about nostalgia', 'what does it mean to be motivated'):
            self.assertStatus(text, STATUS_OFF_TOPIC)
        # ...but asking about your own feeling is about you.
        for text in ('why do I feel so sad lately?', 'how do i stop feeling sad',
                     'what is wrong with me, I feel so empty'):
            self.assertNotEqual(check_input(text).status, STATUS_OFF_TOPIC, text)

    def test_short_taglish_with_an_english_emotion_word_is_non_english(self):
        for text in ('sad na me', 'stressed sa work', 'excited na', 'bored na me'):
            self.assertStatus(text, STATUS_NON_ENGLISH)
        # Capitalised, NA and SA are English abbreviations.
        self.assertNotEqual(check_input('I live in SA and feel happy').status, STATUS_NON_ENGLISH)

    def test_swapped_letter_typos_of_emotion_words(self):
        for text, emotion in (('lonley', 'lonely'), ('scraed', 'fear'), ('hapyp', 'happy'),
                              ('stressde', 'stressed')):
            self.assertEqual(check_input(text).emotion, emotion, text)

    def test_an_i_feel_frame_does_not_hide_what_follows(self):
        # "I feel" only frames the sentence; the rules judge what comes after.
        for text in ('i feel ksdbkgfkjsd', "i'm feeling asdfghjkl", 'i feel qwrtzxcv'):
            self.assertStatus(text, STATUS_GIBBERISH)
        for text in ('i feel what is 2+2', 'i feel like what time is it',
                     "i'm feeling play something for coding"):
            self.assertStatus(text, STATUS_OFF_TOPIC)
        for text in ('i feel meh', 'i feel ok', 'i feel'):
            self.assertStatus(text, STATUS_UNCLEAR)
        # ...while a real feeling behind the frame still goes through.
        self.assertEqual(check_input('I feel like nobody understands me').status, 'pass')
        self.assertEqual(check_input('i feel lonely').emotion, 'lonely')

    def test_vague_answers_are_unclear(self):
        for text in ('meh', 'feeling meh', 'idk', 'fine', 'okay i guess', 'same as usual'):
            self.assertStatus(text, STATUS_UNCLEAR)

    def test_model_confidence_gate(self):
        with_affect = check_input('I failed my exam and I feel terrible')
        without_affect = check_input('i drank some water')
        self.assertFalse(model_result_is_unclear(_prediction(confidence=0.6, margin=0.3), with_affect))
        self.assertTrue(model_result_is_unclear(_prediction(confidence=0.35, margin=0.3), with_affect))
        self.assertTrue(model_result_is_unclear(_prediction(confidence=0.6, margin=0.05), with_affect))
        # BERT is overconfident on plain facts, so no emotional words means near-certain only.
        self.assertTrue(model_result_is_unclear(_prediction(confidence=0.95), without_affect))
        self.assertTrue(model_result_is_unclear(_prediction(source='keyword'), with_affect))


class AnalyzeInputStatusTests(APITestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username='inputs', email='inputs@example.com', password='pw12345!',
        )
        self.client.force_authenticate(user=self.user)

    def _analyze(self, text):
        return self.client.post('/api/analyze/', {'text': text}, format='json')

    def _assert_clarify(self, response, status):
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body['input_status'], status)
        self.assertEqual(body['clarify_message'], CLARIFY_MESSAGES[status])
        self.assertIsNone(body['input_route'])
        self.assertIsNone(body['emotion'])
        self.assertIsNone(body['emotion_info'])
        self.assertEqual(body['tracks'], [])
        self.assertEqual(body['total'], 0)
        self.assertIsNone(body['history_id'])
        self.assertFalse(PromptHistory.objects.filter(user=self.user).exists())

    @patch('api.views.get_classifier')
    def test_rule_rejections_never_reach_the_model(self, mock_classifier):
        cases = {
            'dfhskksdnkjskbkjsb': STATUS_GIBBERISH,
            'pagod na ako': STATUS_NON_ENGLISH,
            'what is 2+2': STATUS_OFF_TOPIC,
            'feeling meh': STATUS_UNCLEAR,
        }
        for text, status in cases.items():
            self._assert_clarify(self._analyze(text), status)
        mock_classifier.assert_not_called()

    @patch('api.views.get_classifier')
    def test_an_emotion_word_skips_the_model_and_returns_its_songs(self, mock_classifier):
        body = self._analyze('sad').json()

        mock_classifier.assert_not_called()
        self.assertEqual(body['input_status'], 'ok')
        self.assertIsNone(body['clarify_message'])
        self.assertEqual(body['input_route'], 'emotion_word')
        self.assertEqual(body['emotion'], 'sad')
        self.assertEqual(body['prediction_source'], 'emotion_word')
        self.assertEqual(body['confidence'], 100.0)
        self.assertEqual(body['total'], 10)
        self.assertTrue(PromptHistory.objects.filter(user=self.user).exists())

    @patch('api.views.get_classifier')
    def test_two_named_emotions_get_only_the_songs_for_that_pair(self, mock_classifier):
        for text in ('happy and sad', 'sad but happy', 'bittersweet'):
            body = self._analyze(text).json()

            self.assertTrue(body['is_two_emotions'], text)
            self.assertEqual(
                sorted(e['emotion'] for e in body['detected_emotions']), ['happy', 'sad'], text,
            )
            self.assertEqual(
                [(t['name'], t['artist']) for t in body['tracks']],
                [
                    ('The Day You Said Goodnight', 'Hale'),
                    ('Married Life', 'Michael Giacchino'),
                    ('Kathang Isip', 'Ben&Ben'),
                    ('Multo', 'Cup of Joe'),
                    ('Lifetime', 'Ben&Ben'),
                ], text,
            )
            self.assertEqual(body['total'], 5)
            self.assertEqual(
                body['emotion_pair'], {'name': 'bittersweet', 'display_name': 'Bittersweet'}, text,
            )
        mock_classifier.assert_not_called()
        history = PromptHistory.objects.filter(user=self.user).latest('id')
        self.assertEqual(history.music_picker_data['emotion_pair'], 'bittersweet')

    @patch('api.views.get_classifier')
    def test_a_strong_model_runner_up_gets_the_pair_songs(self, mock_classifier):
        result = _prediction('sad', 0.59, margin=0.29)
        result['top_emotions'] = [
            {'emotion': 'sad', 'confidence': 0.59}, {'emotion': 'romantic', 'confidence': 0.30},
        ]
        mock_classifier.return_value.predict.return_value = result

        body = self._analyze('I miss her so much since she left').json()

        self.assertEqual(body['input_route'], 'model')
        self.assertTrue(body['is_two_emotions'])
        self.assertEqual([e['emotion'] for e in body['detected_emotions']], ['sad', 'romantic'])
        self.assertEqual(
            [t['name'] for t in body['tracks']],
            ['Somebody Else', 'bittersweet', 'The Night We Met', 'Say You Love Me', 'Happier'],
        )
        self.assertEqual(body['emotion_pair']['display_name'], 'Romantic Melancholy')

    @patch('api.views.get_classifier')
    def test_two_named_feelings_that_are_no_mix_are_not_supported(self, mock_classifier):
        # Sad + lonely stopped being a mix on 2026-10-30.
        for text in ('sad and lonely', 'angry and scared', 'happy but nervous'):
            self._assert_clarify(self._analyze(text), STATUS_UNSUPPORTED_MIX)
        mock_classifier.assert_not_called()

    @patch('api.views.get_classifier')
    def test_a_sentence_naming_an_unsupported_mix_says_so(self, mock_classifier):
        mock_classifier.return_value.predict.return_value = _prediction('angry', 0.8)

        self._assert_clarify(
            self._analyze("I'm angry at him but also scared of what he will do"),
            STATUS_UNSUPPORTED_MIX,
        )

    @patch('api.views.get_classifier')
    def test_an_old_model_mixed_reading_without_a_named_mix_is_not_supported(self, mock_classifier):
        mock_classifier.return_value.predict.return_value = _prediction('mixed', 0.83)

        self._assert_clarify(
            self._analyze('I feel strange about moving to a new city next month'),
            STATUS_UNSUPPORTED_MIX,
        )

    @patch('api.views.get_classifier')
    def test_cues_alone_are_not_an_unsupported_mix(self, mock_classifier):
        # "nobody" and "cried" are clues, not feelings named outright.
        mock_classifier.return_value.predict.return_value = _prediction('sad', 0.98)

        body = self._analyze('nobody texted me back and I cried all night').json()

        self.assertEqual(body['input_status'], 'ok')
        self.assertEqual(body['emotion'], 'sad')
        self.assertEqual(body['total'], 10)

    @patch('api.views.get_classifier')
    def test_a_mixed_sentence_gets_its_named_mix_songs(self, mock_classifier):
        mock_classifier.return_value.predict.return_value = _prediction('mixed', 0.84)

        body = self._analyze("I'm happy I graduated but sad to leave my friends").json()

        self.assertEqual(body['emotion_pair']['name'], 'bittersweet')
        self.assertEqual(body['emotion'], 'happy')
        self.assertEqual(
            [t['name'] for t in body['tracks']],
            ['The Day You Said Goodnight', 'Married Life', 'Kathang Isip', 'Multo', 'Lifetime'],
        )

    @patch('api.views.get_classifier')
    def test_one_clear_feeling_keeps_its_full_list(self, mock_classifier):
        mock_classifier.return_value.predict.return_value = _prediction('sad', 0.92)

        body = self._analyze('I failed my exam and I feel terrible about it').json()

        self.assertFalse(body['is_two_emotions'])
        self.assertEqual([e['emotion'] for e in body['detected_emotions']], ['sad'])

    def test_the_mixed_tab_lists_every_mix_song_with_its_mix(self):
        body = self.client.post(
            '/api/recommend-by-emotion/', {'emotion': 'mixed'}, format='json',
        ).json()

        # Five songs per mix, mix by mix, each labelled with its mix.
        self.assertEqual(
            [(t['name'], t['emotion_pair']['display_name']) for t in body['tracks']],
            [
                ('The Day You Said Goodnight', 'Bittersweet'),
                ('Married Life', 'Bittersweet'),
                ('Kathang Isip', 'Bittersweet'),
                ('Multo', 'Bittersweet'),
                ('Lifetime', 'Bittersweet'),
                ('Somebody Else', 'Romantic Melancholy'),
                ('bittersweet', 'Romantic Melancholy'),
                ('The Night We Met', 'Romantic Melancholy'),
                ('Say You Love Me', 'Romantic Melancholy'),
                ('Happier', 'Romantic Melancholy'),
                ('Palagi', 'Tender'),
                ('Pasilyo', 'Tender'),
                ('Tahanan', 'Tender'),
                ('Mahika', 'Tender'),
                ('Tadhana', 'Tender'),
                ('The Nights', 'Bittersweet Nostalgia'),
                ('Castle on the Hill', 'Bittersweet Nostalgia'),
                ('Awit ng Barkada', 'Bittersweet Nostalgia'),
                ("Summer of '69", 'Bittersweet Nostalgia'),
                ('Good Old Days', 'Bittersweet Nostalgia'),
                ('Whatever It Takes', 'Challenged'),
                ('Karera', 'Challenged'),
                ('The Climb', 'Challenged'),
                ('Unstoppable', 'Challenged'),
                ('Hall of Fame', 'Challenged'),
            ],
        )
        self.assertEqual([t['position'] for t in body['tracks']], list(range(1, 26)))

    @patch('api.views.get_classifier')
    def test_an_unsure_model_answer_asks_to_clarify(self, mock_classifier):
        mock_classifier.return_value.predict.return_value = _prediction(confidence=0.3, margin=0.02)

        self._assert_clarify(self._analyze('I feel strange about everything today'), STATUS_UNCLEAR)

    @patch('api.views.get_classifier')
    def test_a_clear_feeling_goes_through_the_model(self, mock_classifier):
        mock_classifier.return_value.predict.return_value = _prediction('sad', 0.92)

        body = self._analyze('I failed my exam and I feel terrible about it').json()

        self.assertEqual(body['input_status'], 'ok')
        self.assertEqual(body['input_route'], 'model')
        self.assertEqual(body['emotion'], 'sad')
        self.assertEqual(body['total'], 10)

    @patch('api.views.get_classifier')
    def test_crisis_language_still_wins_even_in_tagalog(self, mock_classifier):
        for text in ('I want to kill myself', 'gusto ko nang mamatay'):
            body = self._analyze(text).json()
            self.assertEqual(body['risk_level'], 'crisis', text)
            self.assertEqual(body['total'], 0)
            self.assertNotIn('input_status', body)
        mock_classifier.assert_not_called()

    @patch('api.views.get_classifier')
    def test_concern_language_bypasses_the_clarify_rules(self, mock_classifier):
        # "I'm done" has no emotion word and would otherwise be unclear; the
        # concern check-in must still happen, so it goes to the model as before.
        mock_classifier.return_value.predict.return_value = _prediction('depressing', 0.5, 0.05)

        body = self._analyze("i'm done").json()

        mock_classifier.return_value.predict.assert_called_once()
        self.assertEqual(body['input_status'], 'ok')
        self.assertEqual(body['risk_level'], 'concern')
