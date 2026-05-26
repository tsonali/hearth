# How to run the Imagination Engine on your Mac

A walkthrough for someone who hasn't opened Terminal before. Nothing here assumes prior coding experience.

---

## What you have, after Task 01

A working local app that runs on your machine and only your machine. The model (Llama 3.1 8B) is already downloaded — ~4.5 GB sitting in `~/.cache/huggingface/`. You won't need to download it again.

**Important expectation-setting:** Right now, the model has no idea it's supposed to be a guided-imagination engine. It's just generic Llama 3.1, responding to whatever you type. If you type *"I'm anxious about a hard conversation Sunday,"* it will respond like a generic AI assistant — not like a calm guide. **That's normal.** Turning it into the actual future-self engine is what Tasks 02 and 03 are for. What you're testing today is just that the wires are connected: you type → the model runs locally → the response appears.

---

## Step 1 — Open the Terminal app

Terminal is a built-in macOS app. You've never needed it before; today you do.

1. Press **⌘ Command + Space** on your keyboard. A search bar opens in the middle of your screen ("Spotlight").
2. Type **`Terminal`** and press **Return**.
3. A window opens with white or black text. It will look something like this:

   ```
   sonali@Scott-s-S20 ~ %
   ```

   The `%` is your **prompt**. That's where you type. After typing each command below, press **Return** to run it.

Leave that window open. You'll need it.

---

## Step 2 — Go to the project folder

Type this exactly, then press Return:

```
cd ~/Downloads/imagination-engine
```

What it does: `cd` means *change directory* (move Terminal's focus to a different folder). `~` is shorthand for your home folder (`/Users/sonali`). So this command tells Terminal: *work inside `Downloads/imagination-engine` from now on.*

**Success looks like:** Nothing visible happens. The prompt just comes back, but now with `imagination-engine` somewhere in it:

```
sonali@Scott-s-S20 imagination-engine %
```

If you see *"No such file or directory,"* the folder isn't where I think it is — let me know and I'll find it.

---

## Step 3 — Start the local server

Type this exactly, then press Return:

```
uv run imagination-engine serve
```

What it does: starts a small web server *on your own computer*. Nothing is exposed to the internet.

**Success looks like:** Several lines of text appear. The last useful line will read:

```
INFO:     Uvicorn running on http://127.0.0.1:8765 (Press CTRL+C to quit)
```

That's the server saying *"I'm ready."* **Leave this Terminal window open** — closing it stops the server.

(`127.0.0.1` literally means *"this computer."* You are connecting to a server running on your own machine. Nothing leaves it.)

---

## Step 4 — Open the app in your browser

1. Open any browser (Safari, Chrome, whichever you use).
2. Click in the URL bar at the top — the place where you'd normally type `nytimes.com`.
3. Type: **`127.0.0.1:8765`** and press Return.

You should see a page titled **Imagination Engine** with a text box and a Generate button.

---

## Step 5 — Talk to the model

1. Click into the text box.
2. Type literally anything — a question, a sentence, whatever you want to test.
3. Click **Generate** (or press **⌘ Cmd + Return** on your keyboard).
4. Watch the response stream into the gray box below.

The **first** response after starting the server will pause for ~3 seconds (the model loads from disk into memory). Every response after that will start instantly and stream at roughly human reading speed — about 14 words per second.

---

## Step 6 — Stop the server when you're done

1. Go back to the Terminal window where the server is running.
2. Press **Control + C** (hold the Control key, press C, release both).

The server stops. The prompt returns. You can close the Terminal window now if you want.

If you forget and just close the Terminal window — that also stops the server, just less gracefully. No harm done.

---

## Optional: prove to yourself that it's local

The whole point of this product is that nothing leaves your machine. You can verify with your own eyes:

1. Start the server (Steps 1–3 above) and open the page in your browser (Step 4).
2. Generate one response so the model is loaded into memory.
3. **Turn off your WiFi.** Click the WiFi icon in the top-right of your screen, click *Wi-Fi: On*, toggle it off.
4. Go back to the browser and try generating another response.
5. It works. Because there is no internet involved.
6. Turn WiFi back on.

---

## When something goes wrong

**The browser says "This site can't be reached."**
The server isn't running. Go back to Terminal, run `uv run imagination-engine serve` again, wait for the "Uvicorn running" message, then refresh the browser.

**The Terminal window shows an error in red text.**
Copy the whole error (select the text, ⌘ Cmd + C), open Claude Code, paste it. I'll read it and tell you what to do.

**The model says something weird or unhelpful.**
That's expected at this stage. It's vanilla Llama 3.1 with no system prompt. Personality and protocol come in Task 02 and Task 03.

**The fans on the Mac spin up while generating.**
Normal. The model uses the GPU through Apple's Metal framework while it generates. Idle when not generating.

**You see "Address already in use" when trying to start the server.**
A previous server is still running. Either find that Terminal window and press Ctrl+C in it, or close it. Then try again.

---

## What's next

When you're done playing with this and want to make the model actually behave like a future-self guide — that's Task 02 (the intake conversation) and Task 03 (the script generator). Both happen in your Claude Code session, not in Terminal — just tell me when you're ready.
