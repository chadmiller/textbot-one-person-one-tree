from django.core.exceptions import ValidationError
from django.db import models

import re
from collections import OrderedDict

TREE_KINDS = OrderedDict((str(k+1), v) for k, v in enumerate("Live Oak/Nuttall Oak/Magnolia/Winged Elm/Tabebuia Ipe (Pink Trumpet Tree)/Eagleson Holly/Yauppon Holly/Crape Myrtle/Yellow Tabebuia (Trumpet Tree)/Elaeocarpus (Japanese Blueberry)".split("/")))

class TreeRequestState(models.Model):
    caller_number = models.CharField(max_length=30)
    started_at = models.DateTimeField(auto_now=True)
    finished_at = models.DateTimeField(null=True)
    name = models.CharField(max_length=255, help_text="What's your full name?")
    tree_choice = models.IntegerField(choices=TREE_KINDS.items(), help_text="What kind of tree would you like? Pick a number.\n" + "\n".join("{}:{}".format(k, v) for k,v in TREE_KINDS.items()), null=True)
    street_address = models.CharField(max_length=255, help_text="What number and street is your house at? It has to be inside Orlando. ex, \"123 Maple Ave\"")
    postal_code = models.CharField(max_length=255, help_text="What postal code?")
    email_address = models.EmailField(help_text="What's your email address?", null=True)

    def __str__(self):
        return "TreeReq {}: needs {!r}".format(self.caller_number, self.next_needed_field())

    def next_needed_field(self):
        if not self.name: return "name"
        if not self.tree_choice: return "tree_choice"
        if not self.street_address: return "street_address"
        if not self.postal_code: return "postal_code"
        if not self.email_address: return "email_address"
        return None

    def form_data(self, caller):
        caller = caller.replace("+", "").replace("-", "").lstrip("1")
        assert len(caller) == 10, caller
        ph1, ph2, ph3 = caller[:3], caller[3:6], caller[6:]
        return "https://cityoforlando.wufoo.com/forms/tree-planting-program-online-application/", {
            "Field2": "Right-of-way Trees (individual request)",
            "Field6": TREE_KINDS[str(self.tree_choice)],
            "Field8": self.name,
            "Field15": self.street_address,
            "Field17": "Orlando",
            "Field18": "FL",
            "Field19": self.postal_code,
            "Field20": "United States",
            "Field21": ph1,
            "Field21-1": ph2,
            "Field21-2": ph3,
            "Field22": self.email_address,
            }

    def clean(self):
        if self.tree_choice:
            if str(self.tree_choice) not in TREE_KINDS:
                raise ValidationError("tree choice must be in range.")

        if self.postal_code:
            if not re.match(r"\d{5}(?:-\d\d\d\d)?$", self.postal_code):
                raise ValidationError("nonnumeric zip")
            short_form = self.postal_code[:5]
            if short_form not in ['32801', '32802', '32803', '32804', '32805', '32806', '32807', '32808', '32809', '32810', '32811', '32812', '32814', '32815', '32816', '32817', '32818', '32819', '32820', '32821', '32822', '32824', '32825', '32826', '32827', '32828', '32829', '32830', '32831', '32832', '32833', '32834', '32835', '32836', '32837', '32839', '32853', '32854', '32855', '32856', '32857', '32858', '32859', '32860', '32861', '32862', '32867', '32868', '32869', '32872', '32877', '32878', '32885', '32886', '32887', '32891', '32896', '32897', '32899']:
                raise ValidationError("zip %r not in known Orlando list" % (short_form,))

        if self.street_address:
            if not re.match(r"\d\S* \S{2,} \S{2,}", self.street_address):
                raise ValidationError("weird street address")

        if self.name and len(re.sub(r"\W", "", self.name)) < 5:
                raise ValidationError("name too short")
