# Privacy and safety

## Authorization

Only process meeting content the current user is authorized to access and use. Access to a
recording does not automatically mean the content may be republished in a library.

Before publishing, confirm:

- the meeting is in scope;
- the capture type is appropriate;
- recording and transcription consent requirements are met;
- customer or external-party content is permitted;
- sensitivity and retention requirements are understood; and
- the destination audience is allowed to receive the resulting files.

## Data minimization

The final library may contain:

- approved title and outcome;
- meeting/session title and date;
- verified presenter attribution;
- timestamp and duration;
- category;
- original recording URL; and
- approval status.

Do not include:

- full transcript text;
- hidden chain-of-thought;
- access tokens, cookies, credentials, or secrets;
- private calendar details unrelated to the moment;
- inferred presenter identities;
- customer data not required for the approved use; or
- a recording URL that was not automatically resolved through the user's authorized
  Microsoft 365 access.

## External meetings

Exclude external-customer meetings by default. Include them only when the user explicitly
confirms that the content may be captured and shared with the intended audience.

## Publication

Generating draft files is not authorization to upload or share them. Before any upload,
show the destination and filenames, warn that the output can contain names and recording
links, and obtain explicit confirmation.

## Source quality

When transcript timing is missing or unreliable, hold the candidate rather than inventing
a timestamp. When speaker attribution is missing, use `Unattributed`. When a recording
link is missing, keep the entry in draft or hold status.
