from typing import Optional, Tuple
import re
from urllib import request as urllib_request
import unicodedata
import json


class CleanerUtils(object):
    """Utils for cleaning up responses from large language models."""

    tla_regex = re.compile("([A-Z])\\w+ ([A-Z])\\w+ ([A-Z])\\w+ \\(([A-Z]{3})\\)")
    note_regex = re.compile(r"\n\s*\**\s*Note.*\Z")
    key_compliance_notes_regex = re.compile(
        r"\*\*Key Compliance Notes\*\*.*\Z", re.DOTALL
    )
    why_this_works_regex = re.compile(r"### \*\*Why This Works\*\*.*\Z", re.DOTALL)

    @classmethod
    def tla_fixer(cls, result: Optional[str]) -> Optional[str]:
        """Fix incorrectly identified TLAs (Three Letter Acronyms) in text."""
        if result is None:
            return None

        # Look for three letter acronyms
        matches = cls.tla_regex.finditer(result)
        for m in matches:
            tla = m.group(1) + m.group(2) + m.group(3)
            if tla != m.group(4):
                # Swap the bad TLA.
                result = re.sub(f"(?<=[\\.\\( ]){m.group(4)}", tla, result)
        return result

    @classmethod
    def note_remover(cls, result: Optional[str]) -> Optional[str]:
        """Remove the last line note because we'll put similar content up earlier anyways"""
        if result is None:
            return None
        result = cls.note_regex.sub("", result)
        result = cls.key_compliance_notes_remover(result)
        result = cls.why_this_works_remover(result)
        return result

    @classmethod
    def key_compliance_notes_remover(cls, result: Optional[str]) -> Optional[str]:
        """Remove anything after '**Key Compliance Notes**:'"""
        if result is None:
            return None
        return cls.key_compliance_notes_regex.sub("", result)

    @classmethod
    def why_this_works_remover(cls, result: Optional[str]) -> Optional[str]:
        """Remove anything after '### **Why This Works**'"""
        if result is None:
            return None
        return cls.why_this_works_regex.sub("", result)

    @classmethod
    def reject_appeals_with_45_cfr(cls, result: Optional[str]) -> Optional[str]:
        """Reject appeals mentioning '45 CFR §146.136' but not containing 'mental health'"""
        if result is None:
            return None
        if "45 CFR §146.136" in result and "mental health" not in result:
            return None
        return result

    @classmethod
    def reject_doctor_appeals_with_45_cfr(cls, result: Optional[str]) -> Optional[str]:
        """Reject doctor appeals mentioning '45 CFR §146.136' but not containing 'mental health'"""
        if result is None:
            return None
        if "45 CFR §146.136" in result and "mental health" not in result:
            return None
        return result

    # Different swaps for different types of responses.
    swaps: dict[str, list[Tuple[str, str]]] = {
        "general": [
            (
                "Note that the information is inferred based on the reviewer's findings, but the language used is general rather than directly referencing the reviewer's findings.",
                "",
            ),
            (
                "Based on the information provided, the following factors from the patient's history appear to have been relevant in the determination of",
                "",
            ),
            ("Based on the information provided, ", ""),
            (
                "and the reviewer's clinical experience and expertise in treating such cases",
                "",
            ),
            (
                "Please note: This letter is a hypothetical response and does not reflect the actual policies or decisions of any specific insurance company. It is intended for illustrative purposes only.",
                "",
            ),
            (
                "Please note: This letter is a hypothetical response and does not reflect the actual policies or decisions of any specific insurance company. It is intended for informational purposes only and should not be used as a substitute for professional legal or medical advice.",
                "",
            ),
            ("Facial Feminization Surgery (FGS)", "Facial Feminization Surgery (FFS)"),
            ("Facial Feminization Surgery (FMS)", "Facial Feminization Surgery (FFS)"),
            (
                "Facial Masculinization Surgery (FFS)",
                "Facial Masculinization Surgery (FMS)",
            ),
            (
                "Facial Masculinization Surgery (FGS)",
                "Facial Masculinization Surgery (FMS)",
            ),
        ],
        "patient_history": [
            (
                "There is no information provided about the patient's demographic details.",
                "",
            ),
            (
                "In summary, the relevant factors of the patient's history include symptoms or findings suggestive of ",
                "",
            ),
            ("In summary, the relevant factors of the patient's history include", ""),
            ("The relevant factors of the patient's history include:", ""),
            (
                "Based on this information, it can be inferred that the patient's relevant history include",
                "",
            ),
        ],
        "diagnosis": [
            ("The diagnosis is ", ""),
            ("The diagnosis was ", ""),
            ("The diagnosis in this case is ", ""),
            ("the enrollees ", ""),
            (r"^\s*(her|his|their) ", ""),
            ("  ", " "),
        ],
        "treatment": [
            (
                "The treatment that was denied and being requested is the authorization and coverage for ",
                "",
            ),
            ("The treatment that was denied and being requested is ", ""),
            (r"\s*The treatment denied was an ", ""),
            (r"\s*The treatment denied is ", ""),
            (r"\s*the enrollees ", ""),
            (r"\s*The treatment denied in this case is ", ""),
            (r"\s*The treatment denied in this case was ", ""),
            (r"\s*The treatment in this case is ", ""),
            (r"\s*The treatment in this case was ", ""),
            (r"\s*The treatment was ", ""),
            (r"\s*The treatment is ", ""),
            (r"^\s*(her|his|their) ", ""),
            (r"\s*The treatment denied was authorization and coverage for ", ""),
            (r"\s*The treatment denied was ", ""),
            ("  ", " "),
        ],
        "denial": [
            ("Esteemed Members of the Review Board", "$insurancecompany"),
            (
                "The Health Plans denial was overturned due to the reviewers determining that the requested services were likely to be more beneficial for treatment of the enrollees medical condition than any available standard therapy.",
                "",
            ),
            (
                "independent medical review findings were nature of statutory criteria/case summary:",
                "",
            ),
            ("will be overturned.*", ""),
            ("the independent medical reviewer", "we"),
            ("The physician reviewer", "we"),
            ("We always say no to surgeries.", ""),
            ("The reason was originally denied was", "Your request is denied because"),
            ("Therefore, the Health Plans denial should be overturned.", ""),
            ("We thank the reviewer for their assessment of this case.", ""),
            ("The reviewers determined that", "We do not believe that"),
            ("should be overturned", "should stand."),
            (
                "that denying coverage for this treatment would be inappropriate",
                "we have chosen to deny coverage",
            ),
            ("it is not possible to deny or approve", "we must deny"),
            ("should be granted coverage", "will not be granted coverage"),
            ("patient's condition warrants", "patient's condition does not warrant"),
            ("deny the denial", "deny the "),
            ("  ", " "),
            ("As an AI language model", ""),
            (r"\.\.\.", "."),
            (r"\.\.", "."),
            ("by our independent medical representative", "by us"),
            ("is medically necessary", "is not medically necessary"),
            ("Review findings: The", ""),
            ("Review findings:", ""),
            ("The physician reviewer found that", "We determined that"),
            ("independent medical review has determined", "we have determined"),
            ("was indicated for this patient", "was not indicated for this patient"),
            (
                "the requested .* is appropriate for this patient",
                "the request has been denied for this patient",
            ),
            ("Final Result: The reviewers determined that.*", ""),
            ("reviewers determined that.*", ""),
            ("findings: .* physician reviewers.*", ""),
            ("Thank you for providing me with this information.", ""),
            ("Consequently, the Health Plan's denial should be overturned.", ""),
            ("According to recent medical literature,", ""),
            ("I hope this letter finds you in good health and high spirits.", ""),
        ],
        "appeal": [
            ("Dear Independent Medical Reviewers", "Dear [Insurance Company];"),
            ("coverage has been approved.", "coverage should be approved."),
            ("The final determination was that ", ""),
            ("We reviewed the medical records of patients", "In patients"),
            ("We conducted a retrospective cohort", "In a"),
            ("< / FREETEXT > < / ABSTRACT > ▃", ""),
            ("< / FREETEXT >", ""),
            ("< / ABSTRACT >", ""),
            ("  ", " "),
            (r"\.\.", "."),
            (
                "trans men have well-developed jawlines",
                "trans women have well-developed jawlines",
            ),
            ("The provided denial was overturned", "The denial should be overturned"),
            (
                "Therefore, the provided denial should be upheld.",
                "Therefore, the denial should be overturned.",
            ),
            (
                "who is seeking authorization and coverage of",
                "I am seeking authorization and coverage of",
            ),
            (
                "Therefore, it may not be covered by insurance",
                "Regardless, it should be covered",
            ),
            (r"Dear \[Medical Necessity\]", "Dear [Insurance Company],"),
            ("to the independent medical review findings", "to your decision"),
            ("Thank you for providing me with this information.", ""),
            ("The independent medical review findings of.*?:", ""),
            ("According to the independent medical review, ", ""),
            ("Hence,  concluded", ""),
        ],
    }

    @classmethod
    def remove_control_characters(cls, s):
        """Remove control characters from the given string, except for newlines."""
        return "".join(
            ch for ch in s if unicodedata.category(ch)[0] != "C" or ch == "\n"
        )

    @classmethod
    def json_fix_missing_quotes(cls, json_string):
        """Fix missing quotes around JSON keys and unquoted values."""
        # Find all JSON keys without quotes (no spaces allowed in keys)
        pattern_keys = r"([{,])\s*([a-zA-Z_]\w*)\s*:"
        fixed_json = re.sub(pattern_keys, r' \1"\2":', json_string)

        # Find all JSON values without quotes (including null) and spaces allowed in values
        pattern_values = r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:\s*([^,"}\]]+|null)'
        fixed_json = re.sub(pattern_values, r' "\1": \2', fixed_json)

        return fixed_json

    @classmethod
    def json_fix_missing_colons(cls, json_string):
        """Fix missing colons in JSON strings."""
        # Find all places where a colon is missing between keys and values
        pattern = r'([{,])\s*([a-zA-Z_]\w*)\s+([^",}\]]+)'
        fixed_json = re.sub(pattern, r' \1"\2": \3', json_string)
        return fixed_json

    @classmethod
    def cleanup_json(cls, data):
        """
        Load a json *ish* record. The LLM seems to not end the JSON records very often (e.g. missing }
        and trailing ,s instead. This is kind of janky but YOLO.
        """

        # Some models get None and null mixed up in their JSON output
        data = data.replace("None", "null")
        data = cls.remove_control_characters(data)

        # Try and clean up the endings
        if data.endswith(","):
            data = data.rstrip(",")
        data = data.replace(",}", "}")

        # Handle some missing quotes if needed.
        try:
            return json.loads(data)
        except:
            data = cls.fix_missing_quotes(data)

        try:
            return json.loads(data)
        except:
            pass
        try:
            return json.loads(data + "}")
        except:
            pass

        try:
            return json.loads(data + '"}')
        except:
            pass

        return None

    @classmethod
    def cleanup_lt(cls, lt: str, data: Optional[str]) -> Optional[str]:
        if "appeal" in lt:
            data = cls.reject_appeals_with_45_cfr(data)
            data = cls.reject_doctor_appeals_with_45_cfr(data)
        if data is None:
            return None
        # json handled seperately
        if lt == "json":
            return cls.cleanup_json(data)
        # Use the gernal swap and then add any return type specific swaps
        my_swaps: dict[str, str] = dict(cls.swaps["general"])
        if lt in cls.swaps:
            my_swaps.update(cls.swaps[lt])

        # Since a swap may result in another swap keep swapping until we stop changing.
        old_data = ""
        while old_data != data:
            old_data = data
            for o, r in my_swaps.items():
                data = re.sub(o, r, data, flags=re.IGNORECASE)

        return data

    # Find all JSON keys without quotes (no spaces allowed in keys)
    json_pattern_keys = re.compile(r"([{,])\s*([a-zA-Z_]\w*)\s*:")
    # Find all JSON values without quotes (including null) and spaces allowed in values
    json_pattern_values = re.compile(
        r'(?<=[{,])\s*([a-zA-Z_]\w*)\s*:\s*([^,"}\]]+|null)'
    )

    @classmethod
    def fix_missing_quotes(cls, json_string: str) -> str:
        fixed_json = cls.json_pattern_keys.sub(r' \1"\2":', json_string)
        fixed_json = cls.json_pattern_values.sub(r' "\1": \2', fixed_json)

        return fixed_json

    json_missing_colon_pattern = re.compile(r'([{,])\s*([a-zA-Z_]\w*)\s+([^",}\]]+)')

    @classmethod
    def fix_missing_colons(cls, json_string: str) -> str:
        # Find all places where a colon is missing between keys and values
        fixed_json = cls.json_missing_colon_pattern.sub(r' \1"\2": \3', json_string)
        return fixed_json

    maybe_bad_url_endings = re.compile(r"^(.*)[\.\:\;\,\?\>\)\]]+$")

    # Some people return 200 when they should return 404
    common_bad_result_regex = re.compile(
        "The page you are trying to reach is not available. Please check the URL and try again.|"
        + "The requested article is not currently available on this site.",
        re.IGNORECASE,
    )

    url_pattern = "https?:\\/\\/(?:www\\.)?[-a-zA-Z0-9@:%._\\+~#=]{1,256}\\.[a-zA-Z0-9()]{1,6}\\b(?:[-a-zA-Z0-9@:%_\\+.~#?&\\/=]*)"
    url_re = re.compile(url_pattern, re.IGNORECASE)

    @classmethod
    def url_fixer(cls, result: Optional[str]) -> Optional[str]:
        """LLMs like to hallucinate URLs drop them if they are not valid"""
        if result is None:
            return None

        urls = cls.url_re.findall(result)
        for u in urls:
            print(f"{u}")
            if not cls.is_valid_url(u):
                print(f"Removing invalud url {u}")
                result = result.replace(u, "")
        return result

    @classmethod
    def is_valid_url(cls, url):
        try:
            # Some folks don't like the default urllib UA.
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
            }
            request = urllib_request.Request(url, headers=headers)
            result = urllib_request.urlopen(request)
            if ".pdf" not in url:
                result_text = result.read().decode("utf-8").lower()
                if cls.common_bad_result_regex.match(result_text):
                    raise Exception("Got a 200 but it sounds like we cant find it")
                return True
        except Exception as e:
            groups = cls.maybe_bad_url_endings.search(url)
            if groups is not None:
                return cls.is_valid_url(groups.group(1))
            else:
                print(f"Bad url {url} e {e} with no bad to strip")
                return False
