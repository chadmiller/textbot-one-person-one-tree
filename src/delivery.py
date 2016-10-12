"""How we send the collected user answers to the City of Orlando. We use a
terrible web form."""

class FailedToSend(Exception): pass

import logging as logging_mod

logger = logging_mod.getLogger(__name__)


def patch_form_input(self, data):
    exceptions = {}
    for (name, value) in data.items():
        node = self.form.find("input", {"name": name})
        if node:
            node["value"] = value
        else:
            parent = self.form.find("select", {"name": name})
            assert parent
            if parent:
                # clear old
                for option in parent.findAll("option"):
                    if "selected" in option.attrs:
                        del option.attrs["selected"]
                # set new
                text_node = parent.find(text=value)
                assert text_node, (data, name, value)
                if text_node:
                    parent = text_node.parent
                    if not parent:
                        exceptions[name] = "%r not found as an option" % (value,)
                    while parent.name != "option": parent = parent.parent
                    parent["selected"] = "selected"
            else:
                exceptions[name] = "%r not found" % (value,)
    if exceptions:
        raise ValueError(exceptions)

import mechanicalsoup
mechanicalsoup.form.Form.input = patch_form_input


def send(url, form_source):

    br = mechanicalsoup.Browser()
    page = br.get(url)

    form_ = page.soup.select_one("form")

    del form_.find("input", { "name": "Field24" })["checked"]

    form = mechanicalsoup.Form(form_)

    form.input(form_source)
    if "@example." in form_source["Field22"]:
        logger.warn("Redirecting opot req to black hole instead of real site.")
        form_["action"] = "http://httpbin.org/status/200"

    result = br.submit(form_)

    if result.status_code != 200:
        logger.error("failed to deliver message. HTTP status %s", result.status_code)
        logger.error("%r", result.content)
        raise FailedToSend(result.status_code)


if __name__ == "__main__":
    url = "https://cityoforlando.wufoo.com/forms/tree-planting-program-online-application/"
    record = { "Field2": "Right-of-way Trees (individual request)", "Field6": "Live Oak", "Field8": "Chad", "Field15": "3010 PC", "Field17": "Orlando", "Field18": "FL", "Field19": "32801", "Field20": "United States", "Field21": "321", "Field21-1": "321", "Field21-2": "3210", "Field22": "test@example.com", }
    send(url, record)
