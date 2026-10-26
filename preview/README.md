# Ember settings preview

This is a standalone, browser-based concept preview. It does not replace or
modify Ember's PySide desktop settings window.

From the repository root, run:

```bash
python3 -m http.server 4173 --directory preview
```

Then open <http://localhost:4173>.

The page defaults to English; use the language menu in the top bar to switch to
Arabic. Click a part of Ember or one of the surrounding labels to explore its
settings. The small Ember in a settings page returns to the character screen
with a jump-and-grow transition.

Arabic interface text uses the supplied AlMotLaQ V2.5 Regular and Bold fonts
under the user's confirmed permission. The designer and font information are
listed at <https://www.arfonts.net/almotlaq-bold-info>.

Settings are only saved in this browser's local storage when **Save changes** is
pressed. The API-key field is never persisted, and the connection/voice preview
buttons do not contact Google or produce audio. No settings are applied to the
desktop app.
