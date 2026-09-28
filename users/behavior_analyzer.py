BAD_WORDS = [

    "hate",
    "stupid",
    "idiot",
    "fool",
    "dumb",
    "loser",
    "ugly",
    "nonsense",
    "shut up",
    "trash",

    "abuse",
    "harass",
    "bully",
    "threat",
    "kill",
    "attack",
    "fight",
    "die",
    "hurt",

    "fraud",
    "cheat",
    "scam",
    "fake",
    "hack",
    "steal",
    "phishing",
    "illegal",

    "spam",
    "buy now",
    "click here",
    "subscribe now",
    "free money",
    "offer now",
    "lottery",

    "racist",
    "discriminate",
    "dirty",
    "worthless",

    "worst",
    "bad",
    "terrible",
    "angry",
    "annoying",
    "disgusting"
]


import re

from .models import UserBehavior


def analyze_behavior(user_id):

    # only the most recent 50 logs, so old behavior does not label a user forever
    logs = UserBehavior.objects.filter(
        user_id=user_id
    ).order_by("-timestamp")[:50]

    score = 0

    for log in logs:
        text = (log.description or "").lower()

        for bad in BAD_WORDS:
            # whole-word match, so "die" does not match "studied"
            if re.search(r"\b" + re.escape(bad) + r"\b", text):
                score += 1

    if score >= 3:
        return "Highly Negative"
    elif score >= 1:
        return "Negative"
    else:
        return "Positive"