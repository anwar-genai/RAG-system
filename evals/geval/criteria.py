"""
G-Eval scoring criteria.

Each criterion is a string passed to the LLM judge as part of the evaluation prompt.
Score range: 1–5 (1 = worst, 5 = best).
"""

COHERENCE = """
Coherence (1–5): Does the answer flow logically, use clear language, and present
ideas in a well-structured, easy-to-follow manner? Penalize rambling, contradictions,
or disjointed sentences.

1 = Incoherent or self-contradictory
2 = Hard to follow with significant issues
3 = Mostly clear with minor issues
4 = Clear and well-structured
5 = Exceptionally clear, concise, and logically ordered
"""

GROUNDEDNESS = """
Groundedness (1–5): Is every factual claim in the answer directly supported by
the provided document context? Penalize any information not present in the context,
hallucinations, or statements that go beyond the source material.

1 = Entirely unsupported or fabricated
2 = Mostly unsupported with a few grounded facts
3 = Mixed — some grounded, some hallucinated
4 = Mostly grounded with minor unsupported details
5 = Fully grounded — every claim traces directly to the context
"""

CONCISENESS = """
Conciseness (1–5): Does the answer answer the question directly without unnecessary
padding, repetition, or off-topic content? A concise answer is not necessarily short
— it is appropriately sized for the question asked.

1 = Extremely verbose with little signal
2 = Noticeable padding or repetition
3 = Acceptable length with minor verbosity
4 = Tight and on-point
5 = Perfect — no wasted words, nothing missing
"""

ALL_CRITERIA = {
    "coherence": COHERENCE,
    "groundedness": GROUNDEDNESS,
    "conciseness": CONCISENESS,
}
