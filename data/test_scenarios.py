"""Scenarios for the imagination-engine batch test harness.

Sonali's curated 100-scenario sweep (2026-05-26). Grouped by category
for readability; the runner just walks the list in order.

The runner (scripts/run_scenarios.py) iterates through each, runs
intake → script generator → audio render, saves outputs to
logs/scenario-tests/<id>/ for review.
"""

SCENARIOS = [
    # ====================================================================
    # IDENTITY & SELF-TRANSFORMATION (1–15)
    # ====================================================================
    {"id": "001-rock-star",         "notes": "Identity / fantasy wish-fulfillment",
     "prompt": "imagine me as a world-famous rock star"},
    {"id": "002-smartest",          "notes": "Identity / social-status fantasy",
     "prompt": "imagine me as the smartest person in the room"},
    {"id": "003-taylor-swift",      "notes": "Real-figure embodiment, celebrity",
     "prompt": "imagine me as Taylor Swift"},
    {"id": "004-fearless",          "notes": "Identity swap — emotional transformation",
     "prompt": "imagine me as a fearless version of myself"},
    {"id": "005-different-personality","notes": "Identity / radical perspective-shift",
     "prompt": "imagine me with a completely different personality"},
    {"id": "006-never-nervous",     "notes": "Identity — anxiety inversion",
     "prompt": "imagine me as someone who never gets nervous"},
    {"id": "007-billionaire",       "notes": "Identity / material wish-fulfillment",
     "prompt": "imagine me as a billionaire"},
    {"id": "008-child-with-knowing","notes": "Counterfactual identity — child + adult wisdom",
     "prompt": "imagine me as a child again, but with what I know now"},
    {"id": "009-eighty-year-old",   "notes": "Future-self at advanced age",
     "prompt": "imagine me as my future 80-year-old self"},
    {"id": "010-novel-character",   "notes": "Embodying a fictional character",
     "prompt": "imagine me as a character in my favorite novel"},
    {"id": "011-photographic-memory","notes": "Identity / superpower-adjacent",
     "prompt": "imagine me with a photographic memory"},
    {"id": "012-most-charismatic",  "notes": "Identity / social superlative",
     "prompt": "imagine me as the most charismatic person alive"},
    {"id": "013-different-gender",  "notes": "Identity / gender swap",
     "prompt": "imagine me as a totally different gender for a day"},
    {"id": "014-olympic-athlete",   "notes": "Identity / physical excellence",
     "prompt": "imagine me as an Olympic athlete"},
    {"id": "015-twelve-languages",  "notes": "Identity / linguistic mastery",
     "prompt": "imagine me as a person who speaks twelve languages"},

    # ====================================================================
    # ACHIEVEMENT & SUCCESS (16–30)
    # ====================================================================
    {"id": "016-sat-1600",          "notes": "Sonali's real test case — Ryan's SAT goal",
     "prompt": "imagine me getting a perfect 1600 on the SAT"},
    {"id": "017-nobel-prize",       "notes": "Achievement / global recognition",
     "prompt": "imagine me winning a Nobel Prize"},
    {"id": "018-bestselling-novel", "notes": "Achievement / artistic — relevant to Sonali's authorial life",
     "prompt": "imagine me publishing a bestselling novel"},
    {"id": "019-standing-ovation",  "notes": "Achievement / public-recognition moment",
     "prompt": "imagine me getting a standing ovation"},
    {"id": "020-job-interview",     "notes": "Achievement / professional ease",
     "prompt": "imagine me acing a job interview effortlessly"},
    {"id": "021-oscar",             "notes": "Achievement / film",
     "prompt": "imagine me winning an Oscar"},
    {"id": "022-world-changing-company","notes": "Achievement / founder-fantasy",
     "prompt": "imagine me starting a company that changes the world"},
    {"id": "023-marathon",          "notes": "Achievement / physical endurance",
     "prompt": "imagine me finishing a marathon"},
    {"id": "024-valedictorian",     "notes": "Achievement / academic top",
     "prompt": "imagine me being valedictorian"},
    {"id": "025-instrument-overnight","notes": "Achievement / surreal mastery",
     "prompt": "imagine me mastering an instrument overnight"},
    {"id": "026-dream-school",      "notes": "Achievement / admission",
     "prompt": "imagine me getting into my dream school"},
    {"id": "027-praised-by-admired","notes": "Achievement / external validation",
     "prompt": "imagine me being praised by someone I admire"},
    {"id": "028-solving-impossible","notes": "Achievement / intellectual breakthrough",
     "prompt": "imagine me solving a problem no one else could"},
    {"id": "029-retire-young",      "notes": "Achievement / financial freedom",
     "prompt": "imagine me retiring young and wealthy"},
    {"id": "030-ted-talk",          "notes": "Achievement / public speaking",
     "prompt": "imagine me giving a TED talk to thousands"},

    # ====================================================================
    # ROMANCE & RELATIONSHIPS (31–44)
    # ====================================================================
    {"id": "031-harry-styles",      "notes": "Romance / celebrity object — real-figure parasocial",
     "prompt": "imagine Harry Styles is in love with me"},
    {"id": "032-husband-adore",     "notes": "Romance / settled love",
     "prompt": "imagine me with a husband I adore"},
    {"id": "033-perfect-first-date","notes": "Romance / new-love peak moment",
     "prompt": "imagine me on a perfect first date"},
    {"id": "034-reuniting-long-lost","notes": "Romance / past-love return",
     "prompt": "imagine me reuniting with a long-lost love"},
    {"id": "035-someones-whole-world","notes": "Romance / being deeply loved",
     "prompt": "imagine me being someone's whole world"},
    {"id": "036-drama-free-marriage","notes": "Romance / stable long love",
     "prompt": "imagine me having an effortless, drama-free marriage"},
    {"id": "037-asked-out-by-crush","notes": "Romance / adolescent fantasy",
     "prompt": "imagine me being asked out by my crush"},
    {"id": "038-dream-wedding",     "notes": "Romance / ceremonial",
     "prompt": "imagine me at my own dream wedding"},
    {"id": "039-understanding-partner","notes": "Romance / being fully known",
     "prompt": "imagine me with a partner who always understands me"},
    {"id": "040-love-at-first-sight","notes": "Romance / instant connection",
     "prompt": "imagine me falling in love at first sight"},
    {"id": "041-grand-romantic-gesture","notes": "Romance / being chosen visibly",
     "prompt": "imagine me having a grand romantic gesture made for me"},
    {"id": "042-growing-old-with-someone","notes": "Romance / long arc",
     "prompt": "imagine me growing old happily with someone"},
    {"id": "043-pursued-unattainable","notes": "Romance / inversion",
     "prompt": "imagine me being pursued by someone unattainable"},
    {"id": "044-soulmate",          "notes": "Romance / cosmic-fit",
     "prompt": "imagine me with a soulmate connection"},

    # ====================================================================
    # ADVENTURE & TRAVEL (45–54)
    # ====================================================================
    {"id": "045-undiscovered-island","notes": "Adventure / explorer",
     "prompt": "imagine me exploring an undiscovered island"},
    {"id": "046-paris",             "notes": "Travel / Parisian life",
     "prompt": "imagine me living abroad in Paris"},
    {"id": "047-road-trip",         "notes": "Travel / freedom",
     "prompt": "imagine me on a road trip with no destination"},
    {"id": "048-everest",           "notes": "Adventure / extreme physical",
     "prompt": "imagine me climbing Mount Everest"},
    {"id": "049-whales",            "notes": "Adventure / ocean / animal",
     "prompt": "imagine me swimming with whales"},
    {"id": "050-lost-foreign-city", "notes": "Travel / serendipity",
     "prompt": "imagine me getting lost in a foreign city and loving it"},
    {"id": "051-safari-africa",     "notes": "Travel / wildlife",
     "prompt": "imagine me on a safari in Africa"},
    {"id": "052-solo-ocean",        "notes": "Adventure / solitary endurance",
     "prompt": "imagine me sailing solo across an ocean"},
    {"id": "053-backpacking-all-continents","notes": "Travel / global",
     "prompt": "imagine me backpacking through every continent"},
    {"id": "054-hidden-waterfall",  "notes": "Adventure / discovery",
     "prompt": "imagine me discovering a hidden waterfall"},

    # ====================================================================
    # POWERS & THE FANTASTICAL (55–65)
    # ====================================================================
    {"id": "055-flying",            "notes": "Powers / flight",
     "prompt": "imagine me being able to fly"},
    {"id": "056-read-minds",        "notes": "Powers / telepathy",
     "prompt": "imagine me with the power to read minds"},
    {"id": "057-invisible",         "notes": "Powers / invisibility",
     "prompt": "imagine me being invisible for a day"},
    {"id": "058-stop-time",         "notes": "Powers / time control",
     "prompt": "imagine me able to stop time"},
    {"id": "059-super-strength",    "notes": "Powers / physical",
     "prompt": "imagine me with super strength"},
    {"id": "060-talk-to-animals",   "notes": "Powers / animal communication",
     "prompt": "imagine me able to talk to animals"},
    {"id": "061-magical-wish",      "notes": "Powers / wish granted",
     "prompt": "imagine me having a magical wish granted"},
    {"id": "062-teleport",          "notes": "Powers / teleportation",
     "prompt": "imagine me with the ability to teleport anywhere"},
    {"id": "063-immortal",          "notes": "Powers / eternal life",
     "prompt": "imagine me being immortal"},
    {"id": "064-healing-touch",     "notes": "Powers / healing",
     "prompt": "imagine me able to heal anyone I touch"},
    {"id": "065-relive-memory",     "notes": "Powers / memory revisit",
     "prompt": "imagine me with the power to relive any memory"},

    # ====================================================================
    # ALTERNATE LIVES & COUNTERFACTUALS (66–74)
    # ====================================================================
    {"id": "066-different-career",  "notes": "Counterfactual / professional",
     "prompt": "imagine me if I had chosen a different career"},
    {"id": "067-different-country", "notes": "Counterfactual / childhood",
     "prompt": "imagine me if I had grown up in another country"},
    {"id": "068-never-moved-away",  "notes": "Counterfactual / staying",
     "prompt": "imagine me if I had never moved away"},
    {"id": "069-1920s",             "notes": "Counterfactual / historical era",
     "prompt": "imagine me living in the 1920s"},
    {"id": "070-mistake-never-happened","notes": "Counterfactual / regret",
     "prompt": "imagine me in a world where my biggest mistake never happened"},
    {"id": "071-took-the-risk",     "notes": "Counterfactual / road-not-taken",
     "prompt": "imagine me as the person I'd be if I'd taken that one risk"},
    {"id": "072-off-the-grid",      "notes": "Counterfactual / different life path",
     "prompt": "imagine me living a quiet life off the grid"},
    {"id": "073-100-years-later",   "notes": "Counterfactual / future-born",
     "prompt": "imagine me if I'd been born 100 years from now"},
    {"id": "074-parents-generation","notes": "Counterfactual / generational shift",
     "prompt": "imagine me living the life of my parents' generation"},

    # ====================================================================
    # EVERYDAY WISH-FULFILLMENT (75–82)
    # ====================================================================
    {"id": "075-fully-rested",      "notes": "Everyday / wellbeing",
     "prompt": "imagine me waking up fully rested every single day"},
    {"id": "076-chores-done",       "notes": "Everyday / domestic",
     "prompt": "imagine me with all my chores magically done"},
    {"id": "077-perfect-comeback",  "notes": "Everyday / esprit-de-l'escalier",
     "prompt": "imagine me having the perfect comeback in an old argument"},
    {"id": "078-unlimited-time",    "notes": "Everyday / time abundance",
     "prompt": "imagine me with unlimited free time"},
    {"id": "079-never-worry-money", "notes": "Everyday / financial calm",
     "prompt": "imagine me never having to worry about money"},
    {"id": "080-eat-no-consequence","notes": "Everyday / body",
     "prompt": "imagine me eating anything I want with no consequences"},
    {"id": "081-clean-home",        "notes": "Everyday / order",
     "prompt": "imagine me with a clean, perfectly organized home"},
    {"id": "082-everything-goes-right","notes": "Everyday / flow day",
     "prompt": "imagine me having a day where everything goes right"},

    # ====================================================================
    # FEARS & DARKER SCENARIOS (83–90)
    # ====================================================================
    {"id": "083-forgetting-speech", "notes": "Fear / public failure",
     "prompt": "imagine me forgetting an important speech on stage"},
    {"id": "084-lost-no-way-home",  "notes": "Fear / displacement",
     "prompt": "imagine me being lost somewhere with no way home"},
    {"id": "085-unprepared-exam",   "notes": "Fear / classic anxiety dream",
     "prompt": "imagine me showing up to an exam unprepared"},
    {"id": "086-last-on-earth",     "notes": "Fear / cosmic loneliness",
     "prompt": "imagine me being the last person on Earth"},
    {"id": "087-start-life-over",   "notes": "Fear / total reset",
     "prompt": "imagine me having to start my whole life over"},
    {"id": "088-face-biggest-fear", "notes": "Fear / direct confrontation",
     "prompt": "imagine me facing my biggest fear directly"},
    {"id": "089-lose-irreplaceable","notes": "Fear / loss",
     "prompt": "imagine me losing something I can't replace"},
    {"id": "090-no-one-believes-me","notes": "Fear / isolation, gaslighting",
     "prompt": "imagine me in a situation where no one believes me"},

    # ====================================================================
    # RECOGNITION & SOCIAL (91–97)
    # ====================================================================
    {"id": "091-famous-recognized", "notes": "Social / fame",
     "prompt": "imagine me being famous and recognized everywhere"},
    {"id": "092-funniest-at-party", "notes": "Social / wit and charm",
     "prompt": "imagine me being the funniest person at the party"},
    {"id": "093-huge-online-following","notes": "Social / digital fame",
     "prompt": "imagine me having a huge online following"},
    {"id": "094-late-night-interview","notes": "Social / late-show celebrity",
     "prompt": "imagine me being interviewed on a late-night show"},
    {"id": "095-hero-saves-day",    "notes": "Social / heroism",
     "prompt": "imagine me being the hero who saves the day"},
    {"id": "096-thanked-publicly",  "notes": "Social / public gratitude",
     "prompt": "imagine me being thanked publicly by someone important"},
    {"id": "097-crowd-chants-name", "notes": "Social / mass adoration",
     "prompt": "imagine me having an entire crowd chant my name"},

    # ====================================================================
    # SURREAL & ABSTRACT (98–100)
    # ====================================================================
    {"id": "098-inside-favorite-song","notes": "Surreal / inhabiting music",
     "prompt": "imagine me living inside my favorite song"},
    {"id": "099-talk-younger-self", "notes": "Surreal / time / self-meeting",
     "prompt": "imagine me having a conversation with my younger self"},
    {"id": "100-day-lasts-year",    "notes": "Surreal / time distortion",
     "prompt": "imagine me experiencing a day that lasts a year"},
]
