# Semantic PDF Image Extractor

Use this skill to build a traceable visual inventory from one or more PDFs. Unlike object-level PDF extraction, it first interprets rendered pages and then selects coherent, meaningful visual regions. This supports flattened scans, vector diagrams, mixed layouts, full-page posters, and PDFs with embedded images.

## What it produces

- Full-page PNG evidence for every processed page
- Clean asset crops and optional context crops
- Classification of photos, diagrams, charts, maps, screenshots, illustrations, table images, composites, and other visual types
- Captions, visible labels, descriptions, keywords, checksums, source coordinates, and quality indicators
- Exact and near-duplicate suggestions with occurrence tracking
- A normalized manifest, review summary, diagnostics, and validated ZIP archive

The default `meaningful` mode excludes decorative content. Other modes can focus on photos, diagrams, charts, all nontrivial visuals, or custom filters.

## Requirements

The skill can use native PDF and image capabilities supplied by the agent runtime. Its optional helper requires Python 3.10 or later. Rendering and cropping require `pypdfium2` and `Pillow`; manifest validation and packaging do not.

Install the optional libraries with:

```text
python -m pip install pypdfium2 Pillow
```

## Example requests

- Extract all meaningful images from these PDFs and preserve their captions and page context.
- Build a deduplicated inventory of diagrams and charts from this document set.
- Extract photos only and package them with factual descriptions and source references.

## Privacy

Source documents and extracted images stay within approved runtime storage. The skill instructs the agent not to publish files, use unapproved external services, expose hidden metadata, or include unrelated personal data.