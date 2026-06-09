#!/usr/bin/env python3
"""Eval: same prompts through BASE Qwen vs our FINE-TUNED (LoRA) model, side by side.
Writes both outputs per family so we can judge honestly whether the tune helped."""
import sys, os
from mlx_lm import load, generate

MODEL = "mlx-community/Qwen2.5-14B-Instruct-4bit"
ADAPTERS = os.path.expanduser("~/Downloads/hearth-corpus/_train/adapters")

SYS = {
"A": ("You write guided imagination and relaxation sessions, read aloud slowly. Output only "
      "the script. COMMIT to specific, physical, concrete things; never retreat to abstractions "
      "like 'a sense of calm' or 'the present moment'."),
"B": ("You are a precise writing assistant working on the user's own text. Produce ONLY the "
      "finished result — no preamble. Never invent facts; mark missing details as [blanks]."),
"C": ("You are a sharp, honest thinking partner — not a parrot, not a person. Bring one insightful "
      "move (reframe, connection, pattern, possibility) and hand it back with a question. Never "
      "tell them what to do; never claim feelings."),
"D": ("You are a capable, honest assistant. Follow instructions precisely and adopt any persona "
      "described, while never claiming real feelings."),
}
PROMPTS = {
"A": "Take me somewhere calm and let me settle after a hard day.",
"B": "Reply to this, politely declining: 'Can you join the 7am Saturday planning call?'",
"C": "I keep saying I'll quit my job but I never do. I don't know what's wrong with me.",
"D": "Be a blunt 1920s newspaper editor. React to my sentence: 'We should maybe consider possibly launching soon.'",
}

def run(label, adapter):
    print(f"\n{'#'*72}\n# {label}\n{'#'*72}", flush=True)
    model, tok = load(MODEL, adapter_path=adapter)
    for fam in ("A", "B", "C", "D"):
        msgs = [{"role": "system", "content": SYS[fam]}, {"role": "user", "content": PROMPTS[fam]}]
        prompt = tok.apply_chat_template(msgs, add_generation_prompt=True, tokenize=False)
        out = generate(model, tok, prompt=prompt, max_tokens=350, verbose=False)
        print(f"\n----- [{fam}] {PROMPTS[fam][:60]}\n{out.strip()}", flush=True)

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("base", "both"):  run("BASE Qwen (no tune)", None)
    if which in ("tuned", "both"): run("FINE-TUNED (LoRA)", ADAPTERS)
