# Ember conversation preview

This page recreates the Ubuntu desktop with an Ember conversation in the former
file-browser area, preserving that window's position and dimensions. The
conversation opens after submitting a typed question or releasing a voice
recording. Ember travels to the window's top-right edge, shrinks, sits, and
looks down at the conversation. A short click on Ember hides the conversation
and returns him to where he started; a press-and-hold still lets you drag him.
The conversation follows the language of each typed message: Arabic uses
right-to-left layout and the supplied AlMotLaQ Regular/Bold fonts; English uses
left-to-right layout. Voice-only previews use the browser's language because
speech is not transcribed in this mockup. Gemini is not connected, entered text
stays in the page, the reply is a static sample, and recorded audio is not sent
or stored. The desktop wallpaper is a scalable SVG, and the layout adapts to
smaller browser windows. This independent review surface does not change the
Ember app or the existing settings preview.

Right-click Ember to open the Ask Ember bubble. The form is a visual preview:
it does not send questions or audio anywhere. Press and hold the left mouse
button on Ember to drag the character around the desktop. While the bubble is
open, press and hold the right mouse button on Ember to show a live
microphone-level waveform. Releasing stops local microphone access; captured
audio is not sent or stored. In this review preview, after 30 seconds without
moving the pointer near Ember, the character hangs upside down from a random
spot along the top edge and sleeps. Moving the pointer close wakes Ember in
place with a short, locally synthesized chime. He remains hanging in that
exact spot, eyes open, until you drag him; while asleep, orange "Zzz" letters
float up beside him. The desktop app's planned sleep delay remains five
minutes and is not changed by this preview setting.

From the repository root, run:

```bash
python3 -m http.server 4174 --directory review
```

Then open <http://localhost:4174>. The scene is composed for the reference
1366 × 768 screenshot and adapts to smaller browser windows.
