# QR Code Builder

Point it at a link and you get a scannable QR code. Add a logo, a caption, a
frame, or your brand colors if you want one that looks like it belongs on your
flyer. It also handles QR code variations: Wi-Fi network, contact card
(vCard), email, SMS, phone number, map pin, and calendar event.

## What you get

- PNG, SVG, PDF, JPG, and/or WEBP files of the QR code.
- A readability estimate so you can catch problems before you print, plus a real
  decode test when a QR reader is available in your environment.
- Optional QR code style selection of: 8 body shapes, 5 corner-eye styles,
  5 corner-eye centers, 4 outer frames, brand color, logo in the middle,
  and a caption underneath.
- Batch mode: upload a CSV (or an Excel file, when your environment can read one)
  and get one QR code per row.

## How it works

Only one thing is required: the web address (or the details for whichever
non-link type you asked for).

If you want to customize the QR code, you get a small style guide with
numbered samples, so you can point at the one you like instead of
describing it.

## Try it

- "Make a QR code for contoso.com"
- "QR code with our logo, navy body, and a 'Scan me' banner"
- "Wi-Fi QR code for the guest network"
- "Contact card QR code for me"
- "One QR code per row from this CSV"

## What it won't do

- Read or decode an existing QR code (this only makes them).
- Other barcode types like Code 128, EAN, Data Matrix, or PDF417.
- Build a whole flyer, poster, or slide with a QR code on it. It makes the
  QR code; drop it into your document from there.
- Re-skin a whole presentation in brand colors. "Brand color" here means the
  color of the QR code only.

## Under the hood

Runs the bundled `scripts/make_qr.py` engine. Needs Pillow plus one QR
encoder (ReportLab, `qrcode`, or `segno`) in the host environment. If a
scan verifier is available (OpenCV, zxing-cpp, or pyzbar) it also test-decodes
the finished code and reports whether it read cleanly.
