"""Local output staging only; never overwrite supplied input evidence."""
from pathlib import Path
import os
import tempfile


def check_outputs(outputs, inputs=()):
    destinations = [Path(p).resolve() for p in outputs]
    sources = [Path(p).resolve() for p in inputs]
    for i, destination in enumerate(destinations):
        for other in sources + destinations[:i]:
            if destination == other or (destination.exists() and other.exists() and destination.samefile(other)):
                raise ValueError("Outputs must be separate files and must not overwrite source evidence")
        if destination.exists() and not destination.is_file():
            raise ValueError("Output must be a file: " + str(destination))
    return destinations


def write_outputs(outputs, inputs=()):
    destinations = check_outputs([p for p, _ in outputs], inputs)
    staged, backups, completed, cleanup = {}, {}, [], []
    try:
        for destination, (_, text) in zip(destinations, outputs):
            with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".draft-output-", delete=False) as handle:
                pending = Path(handle.name)
                cleanup.append(pending)
                handle.write(text.replace("\n", os.linesep).encode("utf-8"))
            staged[destination] = pending
            backups[destination] = None
            if destination.exists():
                with tempfile.NamedTemporaryFile(dir=destination.parent, prefix=".draft-backup-", delete=False) as handle:
                    backup = Path(handle.name)
                    cleanup.append(backup)
                    handle.write(destination.read_bytes())
                backups[destination] = backup
        try:
            for destination in destinations:
                staged[destination].replace(destination)
                completed.append(destination)
        except OSError:
            for destination in reversed(completed):
                if backups[destination] is None:
                    destination.unlink()
                else:
                    backups[destination].replace(destination)
            raise
    finally:
        for path in cleanup:
            path.unlink(missing_ok=True)
