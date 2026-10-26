# Ember

Ember is a small animated desktop companion for Linux, with a pixel-art
character, responsive movement, voice and text questions, and a Gemini-powered
conversation window built with PySide6.

On Wayland, Ember prefers Qt's XWayland backend when an X display is available.
This keeps the transparent companion movable and allows its chat and question
windows to use rounded corners; an explicitly selected Qt platform is respected.

## Development setup

On Ubuntu, install the venv module if it is missing:

```bash
sudo apt install python3-venv
```

For system keyring support, install the Secret Service backend:

```bash
sudo apt install libsecret-1-0 gnome-keyring
```

The Arabic settings interface bundles the AlMotLaQ V2.5 Regular and Bold
fonts under the user's confirmed permission. Font information is available at
<https://www.arfonts.net/almotlaq-bold-info>.

```bash
python3 -m venv --system-site-packages .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
```

On Ubuntu, install Qt's platform libraries if the window cannot start:

```bash
sudo apt install libxcb-cursor0 libxkbcommon-x11-0
```

## Run

```bash
ember
```

To add Ember to your applications menu with its pixel-art icon, install the
desktop entry and icon for your user:

```bash
install -Dm644 packaging/ember.desktop \
  "$HOME/.local/share/applications/ember.desktop"
install -Dm644 packaging/ember.svg \
  "$HOME/.local/share/icons/hicolor/scalable/apps/ember.svg"
```

The overlay draws on a 380 by 250 logical canvas, starts near the bottom center
of the current work area, and follows the pointer with its eyes. Right-click
Ember to open the question bubble; hold right-click to record and release to
send the recording. A submitted text or recording opens the conversation
window, where Ember walks to the upper edge, sits, and looks toward the replies.
Click Ember or press Escape to close the conversation and have Ember return.
Text and replies follow the language of the question, with AlMotLaQ used for
Arabic. Gemini uses the model and API key from Settings; the key stays in the
system keyring. Ctrl+right-click opens settings.

When Ember has been left alone for five minutes, it sleeps upside down from a
random spot at the top of the screen, with the full sprite kept clear of the
top panel. Ember now arcs and rotates into its upside-down sleeping pose; its
closed eyes, gentle sway, and floating Zs animate while it rests. Moving the
pointer near Ember wakes it; it remains hanging there until dragged. Automatic
sleep is silent; interaction sounds play for direct actions, while the sleep
chime is reserved for choosing “sleep now.” Left-click and hold for a moment
before dragging to move Ember,
then release to throw it or perch it above a window. When Ember sits beside a
conversation, dragging it keeps the conversation open; it follows the window
where it is released when the window system exposes that window. Wayland may
limit tracking windows from other applications. The “stand on windows” behavior
can be disabled in Behavior settings. A brief landing pose settles into a subtle
perching animation, and Ember follows the window while it moves. Its size is adjustable from
35% to 150% in Settings and updates while it is sitting beside the
conversation. It rebounds from the work-area edges, catches a wall when its
momentum fades, and lands with a squash-and-dust effect. A short click pets
Ember and releases pixel hearts. Motion sounds are 20 distinct cues synthesized
and cached by the app; the supplied sleep, wake, and reply chirps remain in use.
The settings window provides Gemini, voice, behavior, permissions, memory, and
shortcuts sections.

Local wake-word listening is enabled by default and is indicated on Ember.
Say “Ember” to open voice recording; standby audio is processed locally and
isn't saved or sent online. The spoken question is sent to Gemini after you
finish speaking. Turn off “التنبيه الصوتي” in Settings or from Ember's menu to
stop standby listening.

In conversation, Gemini can open installed apps and HTTP(S) links, adjust
volume, repair a muted or silent microphone input, open supported system
settings pages, and turn Bluetooth on or off when requested. Microphone repair
checks available hardware inputs, selects a non-monitor source, unmutes it, and
restores its level only when it is zero. The operating system's privacy
permissions cannot be bypassed, and Ember does not claim that audio capture
works without testing it. When explicitly requested, Ember can open a visible
terminal and run one installed command with its supplied arguments; commands
that commonly modify the system or delete files are blocked. Other terminal
requests are limited to a fixed read-only allowlist and run in a worker thread.
Ember can close only terminal windows that it opened itself and confirms that
process ended. A close shortcut sent to another active window is reported as
unverified. When `wmctrl` is available, Ember can list window titles exposed to
the X11 window manager and close one uniquely matching title, then verify that
the window disappeared; ambiguous titles are left untouched. Native Wayland
windows may not be exposed to this interface. Desktop input and screenshots
use the system's desktop portals.

Conversation messages have copy and editable-forward actions, and users can
attach up to five images, PDFs, or text files (10 MiB each, 20 MiB total).
Attachments are sent to Gemini only after the user selects them. Screen watch
is off by default and requires both the camera button and a confirmation; while
active, it sends a screenshot to Gemini every 10 seconds, shows the latest
description, and stops when disabled, the conversation is closed, or Ember
exits. Facts are stored locally only when explicitly requested and can be
reviewed or deleted from the Memory settings page.

## Test

```bash
pytest
```
