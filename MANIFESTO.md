# Hearth

*Private AI that lives in your house and never leaves it.*

I want to explain why I built this, because the reasoning matters more than the software.

Most of the AI you can use right now runs on someone else's computer. You send your words to a company, the company runs a model, and it sends an answer back. That arrangement has two costs people tend to overlook. The first is that your data goes to the company — every question, every draft, every thing you were thinking. The second is that you pay by the use, indefinitely, the way you pay for water. You never own anything. You rent the ability to think with a machine, and the meter never stops.

I find both of those costs unacceptable, and I no longer think they're necessary. Models small enough to run on an ordinary laptop have gotten good enough to be genuinely useful for a lot of real tasks. Not everything — they are not going to replace the large systems at the frontier — but for a surprising number of the things people actually want, a model running privately on your own machine is not a compromise. It is the better arrangement, because nothing leaves and nothing is metered.

So I built software that does exactly that, and I am giving it away.

A note on "giving it away," since the phrase is usually softer than people mean it. I am not open-sourcing this in the ordinary sense, where you may use the work as long as you credit me or pass along the same license. I am putting it in the public domain. You owe nothing — not money, not attribution, not agreement with anything I think. Take it and do what you want. I hold the view, which I'm in the process of defending elsewhere at greater length, that functional code shouldn't be subject to copyright in the first place. This is that argument made concrete rather than asserted.

## What it does

This is a small and growing set of focused tools, each meant to do one thing honestly rather than to be a single assistant that claims to do everything.

The first is a reflective companion. I am wary of the chatbots that present themselves as friends, that say "I understand how you feel" and "I'm here for you," because they understand nothing and are nowhere. This one is built deliberately not to do that. It does not pretend to be a person. What it does is listen to what you say and reflect it back to you — name the pattern, ask the sharper question — so that you can hear your own thinking more clearly. The value was never in the machine's warmth. It was in giving you a private surface to think against. (Joseph Weizenbaum, who wrote the first program of this kind sixty years ago, spent the rest of his life worried that people would mistake the program for a mind. This is an attempt to build the honest version of what he made.)

The second is a guided-imagination tool. You tell it what you'd like to imagine; it composes a calm, paced session and reads it back to you in your own voice while you close your eyes and do the imagining. The work happens in your head, where it should. The software only shapes the silence around it.

The third reads your own files. You point it at your notes or documents and ask questions; it answers from what is actually written there, tells you plainly when the answer isn't in your files rather than inventing one, and sends none of it anywhere. This is the kind of thing you would never paste into a public chatbot, which is precisely why it belongs on your own machine.

There will be more — reflective journaling, rehearsal for hard conversations, ways of making sense of your own record over time. The point is the shape: small, private, honest tools you own, not a single system you rent.

## Building your own

The last part matters most to me. The same machinery that makes these tools can be handed to you directly. You describe the instrument you want, point it at your own writing or files, and keep it — a companion shaped like a character you love, a voice that settles you, an assistant that knows your work. If you want it to learn a particular voice, you can let it train on your own material overnight, on your own hardware. It will not be one of the large frontier systems, and it will be honest with you about that. But it will be yours, it will be free, and it will never leave your computer.

You don't need me, and you don't need them. You need a machine you already own.

— Sonali Maitra

---

*Status, honestly:* this is real, working software, still under active development — a beta. The tools above run locally today, and installing is now download → unzip → double-click (Apple Silicon Mac; macOS asks you to right-click → Open the first time, because the app isn't notarized yet — that polish is still coming). Everything here is in the public domain ([CC0](LICENSE)).
