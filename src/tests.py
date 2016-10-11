import logging

from django.core.exceptions import ValidationError
from django.test import TestCase

from . import entrance as e


class Flow(TestCase):

    def setUp(self):
        logging.disable(logging.ERROR)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def testFull(self):
        self.assertTupleEqual((['Okay, let\'s get started. Send "start over" any time.', "I'll ask five questions. Please give simple answers.", "What's your full name?"], False), e.receive("9234567890", "help", "en"))

        resp, fin = e.receive("9234567890", "Joe")
        self.assertIn("Try again?", resp[0])
        self.assertIn("What's your full name?", resp)
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "Joe!!!!!!!!!!!!!!!!!!!")
        self.assertIn("Try again?", resp[0])
        self.assertIn("What's your full name?", resp)
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "Joe Smith")
        self.assertIn("What kind of tree would you like? Pick a number.", resp[0])
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "12")
        self.assertIn("Try again?", resp[0])
        self.assertIn("What kind of tree would you like? Pick a number.", resp[1])
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "3")
        self.assertEqual('What number and street is your house at? It has to be inside Orlando. ex, "123 Maple Ave"', resp[0])
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "3 Al S")
        self.assertIn("Try again?", resp[0])
        self.assertEqual('What number and street is your house at? It has to be inside Orlando. ex, "123 Maple Ave"', resp[1])
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "3 Al St")
        self.assertEqual(['What postal code?'], resp)
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "SE3 4W3")
        self.assertIn("Try again?", resp[0])
        self.assertEqual('What postal code?', resp[1])
        self.assertFalse(fin)

        resp, fin = e.receive("9234567890", "   32806-2234  ")
        self.assertEqual(["What's your email address?"], resp)
        self.assertFalse(fin)

        class Delivery:
            def __init__(self): self.is_run = False
            def send(self, *args): self.is_run = True; self.args = args

        delivery = Delivery()
        resp, fin = e.receive("9234567890", "  32806   ", False, delivery)
        self.assertTrue(fin)
        self.assertIn("Done", resp[0])
        self.assertTrue(delivery.is_run)
        url, data = delivery.args
        self.assertIn("Orlando", data.values())
        self.assertIn("FL", data.values())
        self.assertIn("United States", data.values())

