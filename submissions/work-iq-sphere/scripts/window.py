#!/usr/bin/env python3
"""Work out the windows of a Work IQ sphere (versions 1.7 and 1.8), so nobody does date arithmetic by hand.

Usage (one of the choices, plus today's date in UTC):
  python window.py --today 2026-10-21 --views        (version 1.8: the three views every sphere has, in one JSON line)
  python window.py --today 2026-10-21 --window week|month|quarter
  python window.py --today 2026-10-21 --last-weeks 6
  python window.py --today 2026-10-21 --since 2026-09-01
  python window.py --today 2026-10-21 --choice <a saved meta.choices.window value>

Prints one JSON line:
  choice        the value to save as meta.choices.window ("week", "month", "quarter", "last-6-weeks", "since-2026-09-01")
  unit          "day" (the week, shown day by day) or "week"
  start, end    the first day and the day after the last one (end is exclusive)
  columns       7 days, or the number of weekly columns (this partial week included)
  queryEnd      end of the calendar query: for the week it runs to the end of this week, so discover.py can list
                the meetings later this week for "prep me for" questions (they are never counted)
  label         the window label the build writes, for example "15 Oct to 21 Oct 2026"
  flags         the exact window flags for discover.py and count_signals.py (steps 6 and 8)
  files         the window args for the files recipe (step 5)
  period, partial, columnLabels   wording helpers: "the last 7 days", "today, Wed 21 Oct", the column labels
With --views it prints {"status": "ok", "today", "order": ["week", "month", "quarter"], "views": {<name>: the fields above}}:
the data is collected once for the quarter (its start, end and queryEnd hold the week and the month), then discover.py and
count_signals.py run once per view with that view's flags (the week and month runs add --view-of, see SKILL.md).
"""
import argparse, datetime as dt, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wiq_data as W

PERIOD = {'week': 'the last 7 days', 'month': 'the last month', 'quarter': 'three months'}


def describe(choice, today):
    win = W.choice_window(choice, today)
    if win is None:
        return None
    s, e, n = win['start'], win['end'], win['columns']
    if win['unit'] == 'day':
        flags = '--start %s --unit day --columns %d' % (s.isoformat(), n)
        partial = 'today, %s' % W.column_labels(win)[-1]
    else:
        flags = '--start %s --weeks %d' % (s.isoformat(), n)
        last = s + dt.timedelta(days=7 * (n - 1))
        partial = 'the week of %d %s' % (last.day, W.MONTH_NAMES[last.month - 1]) if e > today + dt.timedelta(days=1) else ''
    if choice in PERIOD:
        period = PERIOD[choice]
    elif choice.startswith('last-'):
        period = 'the last %s weeks' % choice.split('-')[1]
    else:
        d = dt.date.fromisoformat(choice[6:])
        period = 'since %d %s' % (d.day, W.MONTH_NAMES[d.month - 1])
    return {'status': 'ok', 'choice': choice, 'unit': win['unit'], 'start': s.isoformat(), 'end': e.isoformat(), 'columns': n,
            'queryEnd': W.ahead_end(win, today).isoformat(), 'label': W.window_label(win, today), 'flags': flags,
            'files': {'start': s.isoformat(), 'end': e.isoformat()}, 'period': period, 'partial': partial,
            'columnLabels': W.column_labels(win)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--today', required=True, help='today in UTC, YYYY-MM-DD')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--window', choices=W.PRESETS)
    g.add_argument('--last-weeks', type=int, help='the last N full weeks plus this partial week')
    g.add_argument('--since', help='from the Monday on or before this date (YYYY-MM-DD)')
    g.add_argument('--choice', help='a saved meta.choices.window value')
    g.add_argument('--views', action='store_true', help='version 1.8: the week, month and quarter views at once')
    a = ap.parse_args()
    try:
        today = dt.date.fromisoformat(a.today)
    except ValueError:
        print('ERROR: --today must be a date like 2026-10-21'); sys.exit(2)
    if a.views:
        print(json.dumps({'status': 'ok', 'today': today.isoformat(), 'order': list(W.VIEWS),
                          'views': {v: describe(v, today) for v in W.VIEWS}}))
        return
    choice = a.window or a.choice or ('last-%d-weeks' % a.last_weeks if a.last_weeks is not None else 'since-%s' % a.since)
    out = describe(choice, today)
    if out is None:
        print('ERROR: "%s" is not a window this skill knows: use week, month, quarter, the last 1 to 52 weeks, or since a '
              'date that is not after today' % choice)
        sys.exit(2)
    print(json.dumps(out))


if __name__ == '__main__':
    main()
