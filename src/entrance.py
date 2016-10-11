import re
from contextlib import suppress
import logging as loggingmod
from random import choice

from django.core.exceptions import ValidationError

from . import models
from . import delivery

logger = loggingmod.getLogger(__name__)

# required
def common_name(): return "tree"  # What short name should others know us as?

# required
def help():
    """Return a list of messages to tell the user about this module. Lead with
    the canonical keyword that would claim a conversation, and then dashes and
    a little pitch for using it. Phrase as: 
    "keyword" -- what I can do for you."""
    return [ '''"{0}" -- come plant a free sidewalk tree. You must be within Orlando's city limits!'''.format(common_name) ]

# required
def claims_conversation(message):
    """Returns whether the incoming message is sufficient to indicate that user
    wants to start a conversation. Should all future messages from this user be
    directed to this module's handlers? If return value is not falsey, this
    returned value is passed into the first receive() as the third param."""
    if len(message) > 10: return   # Too complicated for us to assume is ours
    if re.search(r"(?i)\btrees?\b", message): return "en"
    if re.search(r"(?i)\b[aá]rbols?\b", message): return "es"
    if "\U0001F332" in message: return "en"  #?  tree emoji isn't English!
    if "\U0001F333" in message: return "en"  #?  tree emoji isn't English!
    if "\U0001F334" in message: return "en"  #?  tree emoji isn't English!

# required
def abort(caller_number):
    """User signaled they want to abort all state. Returns nothing. This may be
    called even if a conversation has never started."""
    with suppress(models.TreeRequestState.DoesNotExist):
        models.TreeRequestState.objects.filter(caller_number=caller_number).delete()

# required
def receive(caller_number, incoming_message, initial_state_info=None, delivery=delivery):
    record, _ = models.TreeRequestState.objects.get_or_create(caller_number=caller_number, finished_at__isnull=True)
    outgoing_messages = []

    if initial_state_info or not incoming_message:
        logger.debug("new conversation!")
        outgoing_messages.append("Okay, let's get started. Send \"start over\" any time.")
        outgoing_messages.append("I'll ask five questions. Please give simple answers.")

    next_needed_name = record.next_needed_field()
    assert next_needed_name, "This incoming message has nowhere to go. That's a bug."

    # If a message has come in, then it's the answer to a question or the first
    # trigger. Two stages. Answer the obvious question. Then decide if that's
    # enough.
    if incoming_message and not initial_state_info:
        logger.info("Saving %s as an answer for %s in %s", incoming_message.strip(), next_needed_name, record)
        try:
            setattr(record, next_needed_name, incoming_message.strip())
            record.clean()
            record.save()
        except (ValueError, ValidationError):
            logger.exception("Response %r didn't fit.", incoming_message.strip())
            outgoing_messages.append(choice([
                "That doesn't look right to me. 😕  Try again? ",
                "That doesn't look right to me. 😕  Try again? ",
                "That doesn't look right to me. 😕  Try again? ",
                "That doesn't look right to me. 😕  Try again? ",
                "Hmm, no. Remember, I'm just a robot. 😕  Try again?",
                "Hmm, no. Remember, I'm just a robot. 😕  Try again?",
                "Beep boop. Robotbrain can't understand. 😕  Try again?",
                ]))
            outgoing_messages.append(record._meta.get_field(next_needed_name).help_text)
            return outgoing_messages, False
        next_needed_name = record.next_needed_field()

    conversation_ends_now = False
    if next_needed_name:
        logger.info("want %r in %s. getattr gives %s for %s", next_needed_name, record, record._meta.get_field(next_needed_name), record)
        outgoing_messages.append(record._meta.get_field(next_needed_name).help_text)
    else:
        url, data = record.form_data(caller_number)
        delivery.send(url, data)
        conversation_ends_now = True
        outgoing_messages.append("Done! Someone from the city should email/call. 🌲🐝  Enjoy your tree!")

        with suppress(models.TreeRequestState.DoesNotExist):
            models.TreeRequestState.objects.filter(caller_number=caller_number).delete()

    return outgoing_messages, conversation_ends_now

