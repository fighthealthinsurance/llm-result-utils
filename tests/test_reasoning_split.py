"""LLMResponseUtils.extract_reasoning_and_answer: the split at the last closing tag.

The split used to be done with two regular expressions that took time cubic
in the length of the text. They are kept here as the reference the linear
implementation has to agree with.
"""

import itertools
import re
import time
from typing import Optional, Tuple

import pytest

from llm_result_utils.llm_utils import LLMResponseUtils


def reference(result: str) -> Tuple[Optional[str], Optional[str]]:
    """extract_reasoning_and_answer as it was, regular expressions and all."""
    if not result:
        return (None, None)
    thinking_pattern = re.compile(
        r"(?:[^<]|<(?!/?thinking>)|(?:<thinking>.*?</thinking>))*.*</thinking>",
        re.DOTALL,
    )
    think_pattern = re.compile(
        r"(?:[^<]|<(?!/?think>)|(?:<think>.*?</think>))*.*</think>",
        re.DOTALL,
    )
    thinking_matches = thinking_pattern.findall(result)
    think_matches = think_pattern.findall(result)
    reasoning: Optional[str] = None
    answer: Optional[str] = None
    if not thinking_matches and not think_matches:
        answer = result
    else:
        thinking_end_positions = [m.end() for m in thinking_pattern.finditer(result)]
        think_end_positions = [m.end() for m in think_pattern.finditer(result)]
        all_positions = thinking_end_positions + think_end_positions
        if not all_positions:
            answer = result
        else:
            last_position = max(all_positions)
            answer = result[last_position:].strip()
            reasoning = result[:last_position].strip()
    if answer:
        answer = re.sub(r"<answer>|</answer>", "", answer)
        answer = answer.strip()
    if reasoning:
        reasoning = re.sub(r"<think>|</think>|</thinking>|<thinking>", "", reasoning)
        reasoning = reasoning.strip()
    return reasoning, answer


CASES = [
    # (text, reasoning, answer)
    ("<think>why</think>the answer", "why", "the answer"),
    ("<thinking>why</thinking>\nthe answer\n", "why", "the answer"),
    (
        "<think>\n- one\n- two\n</think>\n\nA letter.\n\nSincerely",
        "- one\n- two",
        "A letter.\n\nSincerely",
    ),
    # No tags: all of it is the answer.
    ("just an answer", None, "just an answer"),
    ("  padded  ", None, "padded"),
    # Nested and repeated blocks: everything up to the last closing tag is reasoning.
    ("<think>a<think>b</think>c</think>d", "abc", "d"),
    ("<think>a</think>mid<think>b</think>end", "amidb", "end"),
    ("<think>a</think>mid<thinking>b</thinking>end", "amidb", "end"),
    ("<thinking>a</thinking>mid<think>b</think>end", "amidb", "end"),
    # Text before the block (leaked reasoning) goes with the reasoning.
    ("leaked. <think>why</think>answer", "leaked. why", "answer"),
    # A closing tag alone still splits; an opening tag alone does not.
    ("why</think>answer", "why", "answer"),
    ("<think>never closed", None, "<think>never closed"),
    # Nothing after the block, or nothing in it.
    ("<think>why</think>", "why", ""),
    ("<think></think>answer", "", "answer"),
    ("</think>", "", ""),
    # <answer> tags come off the answer, and only the answer.
    ("<think>why</think><answer>yes</answer>", "why", "yes"),
    ("<answer>yes</answer>", None, "yes"),
    ("<think><answer>x</answer></think>y", "<answer>x</answer>", "y"),
    # Near misses are not tags.
    ("<think>why</think >answer", None, "<think>why</think >answer"),
    ("<Think>why</Think>answer", None, "<Think>why</Think>answer"),
    ("a </thinking b </think", None, "a </thinking b </think"),
]


@pytest.mark.parametrize("text,reasoning,answer", CASES)
def test_split(text, reasoning, answer):
    assert LLMResponseUtils.extract_reasoning_and_answer(text) == (reasoning, answer)
    assert reference(text) == (reasoning, answer)
    assert LLMResponseUtils.extract_answer(text) == answer


@pytest.mark.parametrize("empty", [None, ""])
def test_nothing_in_nothing_out(empty):
    assert LLMResponseUtils.extract_reasoning_and_answer(empty) == (None, None)
    assert LLMResponseUtils.extract_answer(empty) is None


#: Whole tags, pieces of tags and ordinary text, to build every short reply from.
TOKENS = [
    "<think>",
    "</think>",
    "<thinking>",
    "</thinking>",
    "<answer>",
    "</answer>",
    "<",
    ">",
    "</",
    "think",
    "ing>",
    "a",
    " ",
    "\n",
]


def test_agrees_with_the_regular_expressions_on_every_short_reply():
    """Every sequence of up to four tokens (41,371 texts), tags broken and whole."""
    checked = 0
    for length in range(0, 5):
        for parts in itertools.product(TOKENS, repeat=length):
            text = "".join(parts)
            assert LLMResponseUtils.extract_reasoning_and_answer(text) == reference(
                text
            ), repr(text)
            checked += 1
    assert checked == sum(len(TOKENS) ** n for n in range(0, 5))


def test_agrees_with_the_regular_expressions_on_longer_replies():
    """Longer texts from a fixed pseudo-random walk over the same tokens."""
    state = 20261111
    for _ in range(4000):
        parts = []
        for _ in range(5 + state % 21):
            state = (state * 1103515245 + 12345) % 2**31
            parts.append(TOKENS[(state >> 8) % len(TOKENS)])
        text = "".join(parts)
        assert LLMResponseUtils.extract_reasoning_and_answer(text) == reference(
            text
        ), repr(text)


def test_a_long_letter_takes_no_time():
    """The regular expressions took about 30 seconds on a 4,500-character answer."""
    sentence = "The plan's own criteria list this as the next step after conservative therapy. "
    letter = sentence * 2500  # about 200,000 characters
    for tag in ("think", "thinking"):
        text = f"<{tag}>\n- read the denial\n- answer it\n</{tag}>\n{letter}"
        start = time.perf_counter()
        reasoning, answer = LLMResponseUtils.extract_reasoning_and_answer(text)
        assert time.perf_counter() - start < 2.0
        assert reasoning == "- read the denial\n- answer it"
        assert answer == letter.strip()
    # And with no tags at all, which was quick before and still is.
    start = time.perf_counter()
    assert LLMResponseUtils.extract_reasoning_and_answer(letter) == (
        None,
        letter.strip(),
    )
    assert time.perf_counter() - start < 2.0
