# Canvas Apps — Accessibility

Canvas apps give pixel-level control, which means accessibility is **largely on
you**. The studio provides an **Accessibility checker** — use it continuously,
but it doesn't catch everything. Apply `wcag-checklist.md` plus these
canvas-specific properties and patterns.

## Per-control accessibility properties (set these)
- **AccessibleLabel** — the screen-reader name for every meaningful control
  (buttons, icons, images, inputs, galleries). Required for icon/image buttons
  (1.1.1, 4.1.2). Leave decorative images without a label and consider
  `TabIndex = -1`.
- **TabIndex** — use **0** to include in keyboard order, **-1** to remove
  decorative/duplicate controls. **Never use positive TabIndex values** — they
  break logical order (2.4.3). Order primarily by control position; only override
  when needed.
- **Tooltip** — supplementary help/format hints (supports 3.3.2) but is **not** a
  substitute for AccessibleLabel.
- **Focused border** (FocusedBorderColor / FocusedBorderThickness) — keep a
  visible, ≥3:1 focus indicator (2.4.7). Don't set thickness to 0.
- **Live (for labels)** — set to *Polite* or *Assertive* so dynamic text (status,
  results, errors) is announced (4.1.3). Use Assertive only for errors.
- **Role** (Screen/containers and the HTML text control) — use heading roles to
  create structure (1.3.1, 2.4.6).

## Structure & headings (1.3.1, 2.4.6)
- Build a heading hierarchy using label **Role = Heading 1/2/3** (don't skip
  levels). Canvas has no DOM headings otherwise.
- Group related controls in containers; use them to create logical reading and
  tab order.

## Keyboard (2.1.1, 2.1.2, 2.4.3)
- Confirm every interactive control is reachable and operable by keyboard. Custom
  composite controls built from shapes/icons need explicit TabIndex and
  OnSelect that also fires via keyboard.
- Enable the **Simplified tab index** app setting (Settings → General/Display) —
  Microsoft recommends it for predictable Tab order.
- Test focus order matches reading order; fix with TabIndex and container
  grouping. Ensure no traps (especially custom modals/overlays built with
  containers + visibility).

## Colour & contrast (1.4.1, 1.4.3, 1.4.11)
- Check text 4.5:1 / large 3:1 and control borders/states 3:1 against the screen
  Fill. The Accessibility checker flags some contrast issues — verify manually
  too, including any theme variants.
- Don't signal required/error/status by colour fill alone — add an icon + text.

## Reflow, sizing, orientation (1.3.4, 1.4.4, 1.4.10)
- Turn on **Scale to fit = Off** + **responsive layout** (containers with
  Fill/Width formulas, or `Parent.Width`-based sizing) so the app reflows and
  doesn't lock orientation. Avoid absolute fixed positions that clip on small
  screens.
- Ensure text isn't truncated when scaled; set `AutoHeight` where appropriate.

## Forms & errors (3.3.1, 3.3.2, 3.3.3)
- Give each input a visible label control (not just placeholder) and an
  AccessibleLabel. On validation failure, show an error **label** with `Live =
  Assertive` and text describing the problem and the fix; don't rely on red
  border alone.

## Media & motion (1.2.x, 2.2.2, 2.3.x)
- **Video** captions: supply a WebVTT file via the Video control's
  **ClosedCaptionsUrl** property. Provide a transcript for any audio recordings.
- Avoid auto-playing audio; provide pause. Avoid flashing > 3×/s. Offer a way to
  reduce motion for any timer/animation-driven UI.
- **Timer** caveat: with a screen reader on, the Timer announces *elapsed time*
  (not its button text), and these announcements **can't be turned off** even
  when the timer is hidden via low opacity. Don't leave stray running timers on a
  screen, as they'll interrupt the screen-reader experience.

## Signatures — PenInput (2.1.1, 1.1.1)
- A **PenInput** signature control isn't keyboard/screen-reader operable on its
  own. Provide an alternative: a **TextInput** where the user can type their name,
  placed to the right of or immediately below the pen control. Put the signing
  instructions in the TextInput's **AccessibleLabel**.

## Unsupported patterns
- Some designs can't be made accessible in canvas — check Microsoft's
  **accessibility limitations** list before committing to a pattern, and pick a
  supported alternative.

## App-level
- Set a meaningful **App name / screen names** (2.4.2). Keep navigation
  consistent across screens (3.2.3). Avoid auto-navigation on focus/input without
  warning (3.2.1/3.2.2).

## Verify
- **Accessibility checker** in the studio (right-hand pane) — resolve every item.
- Keyboard-only run-through in Play mode (Tab/Enter/Space; arrow keys in
  galleries).
- Screen reader pass confirming labels, headings, and live announcements, using a
  **Microsoft-verified pairing**: JAWS or Narrator on Edge; NVDA on Chrome or
  Firefox; VoiceOver on Safari / Power Apps mobile; TalkBack on Chrome / Power
  Apps mobile. Testing in an unverified browser can give false failures.
- Contrast + High Contrast theme; responsive check at narrow widths / 200% OS
  scaling.
