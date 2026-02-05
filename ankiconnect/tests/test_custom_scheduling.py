# -*- coding: utf-8 -*-
import time
from unittest import TestCase
from util import callAnkiConnectEndpoint


class TestCustomScheduling(TestCase):
    def _create_basic_note(self):
        response = callAnkiConnectEndpoint(
            {
                "action": "addNote",
                "params": {
                    "note": {
                        "deckName": "Default",
                        "modelName": "Basic",
                        "fields": {"Front": "kw-test-front", "Back": "kw-test-back"},
                        "tags": ["kw_test"],
                    }
                },
            }
        )
        return response

    def _get_note_cards(self, note_id):
        notes_info = callAnkiConnectEndpoint(
            {"action": "notesInfo", "params": {"notes": [note_id]}}
        )
        self.assertTrue(isinstance(notes_info, list))
        self.assertEqual(1, len(notes_info))
        self.assertTrue("cards" in notes_info[0])
        return notes_info[0]["cards"]

    def test_cardsSchedulingInfo_returns_expected_shape(self):
        note_id = self._create_basic_note()
        self.assertTrue(note_id is not None)
        cards = self._get_note_cards(note_id)
        self.assertTrue(len(cards) >= 1)

        info = callAnkiConnectEndpoint(
            {"action": "cardsSchedulingInfo", "params": {"cards": cards}}
        )
        self.assertTrue(isinstance(info, list))
        self.assertEqual(len(cards), len(info))
        self.assertTrue("cardId" in info[0])
        self.assertTrue("noteId" in info[0])
        self.assertTrue("queue" in info[0])
        self.assertTrue("type" in info[0])
        self.assertTrue("interval" in info[0])
        self.assertTrue("isDue" in info[0])

    def test_setCardDueAt_forces_learning_due_now(self):
        note_id = self._create_basic_note()
        cards = self._get_note_cards(note_id)
        now = int(time.time())

        updated = callAnkiConnectEndpoint(
            {
                "action": "setCardDueAt",
                "params": {"cards": cards, "dueAt": now - 5},
            }
        )
        self.assertTrue(updated)

        info = callAnkiConnectEndpoint(
            {"action": "cardsSchedulingInfo", "params": {"cards": cards}}
        )
        self.assertEqual(True, info[0]["isLearning"])
        self.assertEqual(True, info[0]["isDue"])
        self.assertTrue(info[0]["dueAt"] is not None)

    def test_setCardInterval_sets_review_interval(self):
        note_id = self._create_basic_note()
        cards = self._get_note_cards(note_id)

        updated = callAnkiConnectEndpoint(
            {
                "action": "setCardInterval",
                "params": {"cards": cards, "intervalDays": 3},
            }
        )
        self.assertTrue(updated)

        info = callAnkiConnectEndpoint(
            {"action": "cardsInfo", "params": {"cards": cards}}
        )
        self.assertEqual(3, info[0]["interval"])

