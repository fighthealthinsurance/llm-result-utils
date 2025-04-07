from typing import Optional, Union
import re
import chardet


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

    @classmethod
    def is_valid_text(cls, data: Union[str, bytes, None]) -> bool:
        """
        Check if the data is valid text.

        Args:
            data: Data to check, can be bytes or string

        Returns:
            True if the data is valid text, False otherwise
        """
        # If data is already a string, it's valid text
        if isinstance(data, str):
            return True

        # If it's bytes, try to decode it as UTF-8
        if isinstance(data, bytes):
            try:
                # Try to decode as UTF-8
                data.decode("utf-8")
                return True
            except UnicodeDecodeError:
                # Try to detect encoding and decode
                detection = chardet.detect(data)
                if detection["confidence"] > 0.7:  # Reasonable confidence threshold
                    try:
                        if "encoding" in detection and detection["encoding"]:
                            data.decode(detection["encoding"])
                            return True
                    except (UnicodeDecodeError, LookupError):
                        pass
                return False

        # Not a string or bytes
        return False

    @classmethod
    def is_well_formatted_for_reasoning(cls, result: str) -> bool:
        """
        Check if the result is well-formatted with properly structured thinking tags.
        This function supports nested thinking tags in either <thinking></thinking> or <think></think> format.

        Returns:
            True if the result has proper thinking/reasoning structure, False otherwise
        """
        if result is None:
            return False
        # Use regex to handle nested thinking tags properly
        # First try to find all top-level thinking/think tags
        thinking_pattern = re.compile(
            r"<thinking>(?:[^<]|<(?!/?thinking>)|(?:<thinking>.*?</thinking>))*</thinking>",
            re.DOTALL,
        )
        think_pattern = re.compile(
            r"<think>(?:[^<]|<(?!/?think>)|(?:<think>.*?</think>))*</think>", re.DOTALL
        )

        # Find all matches
        thinking_matches = thinking_pattern.findall(result)
        think_matches = think_pattern.findall(result)

        # Count opening and closing tags - they should be balanced
        num_thinking_open = result.count("<thinking>")
        num_thinking_close = result.count("</thinking>")
        num_think_open = result.count("<think>")
        num_think_close = result.count("</think>")

        # Check for mismatched tags
        if (num_thinking_open != num_thinking_close) or (
            num_think_open != num_think_close
        ):
            return False

        # Ensure there's text after the last closing tag of the top-level thinking section
        last_thinking_close = -1
        last_think_close = -1

        if thinking_matches:
            last_thinking_close = result.find(thinking_matches[0]) + len(
                thinking_matches[0]
            )

        if think_matches:
            last_think_close = result.find(think_matches[0]) + len(think_matches[0])

        last_closing_tag = max(last_thinking_close, last_think_close)

        # Check if there's meaningful text after the closing tag
        if last_closing_tag == -1 or last_closing_tag + 10 >= len(result):
            return False

        return True

    @classmethod
    def extract_reasoning_and_answer(
        cls, result: str
    ) -> tuple[Optional[str], Optional[str]]:
        """
        Extract the reasoning and answer portions of a response.
        This function handles nested thinking tags and extracts both reasoning and answer.

        Args:
            result: The full response text that may contain thinking tags
        """
        if not result:
            return None, None

        # Use regex to handle nested thinking tags properly
        # First try to find all top-level thinking/think tags
        thinking_pattern = re.compile(
            r"(?:[^<]|<(?!/?thinking>)|(?:<thinking>.*?</thinking>))*.*</thinking>",
            re.DOTALL,
        )
        think_pattern = re.compile(
            r"(?:[^<]|<(?!/?think>)|(?:<think>.*?</think>))*.*</think>",
            re.DOTALL,
        )

        # Find all matches
        thinking_matches = thinking_pattern.findall(result)
        think_matches = think_pattern.findall(result)

        reasoning: Optional[str] = None
        answer: Optional[str] = None

        # If no thinking tags were found, return the original text
        if not thinking_matches and not think_matches:
            print(f"No thinking match returning raw answer")
            answer = result
        else:
            # Get the positions of all closing tags
            thinking_end_positions = [
                m.end() for m in thinking_pattern.finditer(result)
            ]
            think_end_positions = [m.end() for m in think_pattern.finditer(result)]

            # Find the last closing tag position
            all_positions = thinking_end_positions + think_end_positions
            if not all_positions:
                answer = result
            else:
                last_position = max(all_positions)
                # Extract everything after the last closing tag
                answer = result[last_position:].strip()
                reasoning = result[:last_position].strip()

        # Remove any answer tags if present
        if answer:
            answer = re.sub(r"<answer>|</answer>", "", answer)
            answer = answer.strip()
        if reasoning:
            reasoning = re.sub(
                r"<think>|</think>|</thinking>|<thinking>", "", reasoning
            )
            reasoning = reasoning.strip()

        return reasoning, answer
