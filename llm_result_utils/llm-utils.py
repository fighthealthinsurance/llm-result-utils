from typing import Optional
import re


class LLMResponseUtils(object):
    tla_regex = re.compile("([A-Z])\\w+ ([A-Z])\\w+ ([A-Z])\\w+ \\(([A-Z]{3})\\)")
    note_regex = re.compile(r"\n\s*\**\s*Note.*\Z")

    @classmethod
    def tla_fixer(cls, result: Optional[str]) -> Optional[str]:
        """Fix incorrectly picked TLAs from the LLM."""
        if result is None:
            return None
        else:
            # Look for three letter acronyms
            matches = cls.tla_regex.finditer(result)
            for m in matches:
                tla = m.group(1) + m.group(2) + m.group(3)
                if tla != m.group(4):
                    return re.sub(f"(?<=[\\.\\( ]){m.group(4)}", tla, result)
            return result

    @classmethod
    def note_remover(cls, result: Optional[str]) -> Optional[str]:
        """Remove the last line note because we'll put similar content up earlier anyways"""
        if result is None:
            return None
        else:
            return cls.note_regex.sub("", result)
