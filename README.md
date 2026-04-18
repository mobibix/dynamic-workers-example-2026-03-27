# Face & Name Trainer

A Streamlit app for learning the faces and names of everyone in your organisation.
Feed it your PowerPoint staff directory, and it quizzes you in two modes:

- **Face → Name** — see a photo, type or select the correct name
- **Name → Face** — see a name, click the correct photo from four options

The app tracks your score per person and surfaces who you consistently struggle with.

---

## Quick start

### 1. Install dependencies

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Extract data from your PowerPoint

Each slide should have **one photo** and the person's **name as visible text**.

```bash
python extract_pptx.py staff_directory.pptx
```

You can pass multiple files:

```bash
python extract_pptx.py dept1.pptx dept2.pptx
```

This creates:
```
data/
  people.json          ← index of names + image paths
  images/              ← extracted photos
```

### 3. Run the app

```bash
streamlit run app.py
```

---

## Test without a PowerPoint

Generate 20 synthetic colour-swatch portraits to try the app immediately:

```bash
python generate_sample_data.py
streamlit run app.py
```

---

## Deploying to Streamlit Cloud

1. **Extract your data locally** and commit the `data/` folder to your repo.
2. Push to GitHub.
3. Go to [share.streamlit.io](https://share.streamlit.io), connect your repo, and set the main file to `app.py`.

> **Note:** Streamlit Cloud has a read-only filesystem, so score history resets between browser sessions. Run locally if you need persistent scores.

---

## PowerPoint format assumptions

| Requirement | Detail |
|---|---|
| One person per slide | Each slide = one name + one photo |
| Name as text | Any text frame on the slide; the first non-trivial text block is used |
| Photo as image | The largest picture shape on the slide is extracted |
| File format | `.pptx` (PowerPoint 2007+) |

If a slide has no text or no picture it is silently skipped and reported in the terminal output.

---

## Project structure

```
app.py                  ← Streamlit quiz app
extract_pptx.py         ← PPTX → data/ extraction script
generate_sample_data.py ← synthetic test data generator
requirements.txt
data/
  people.json
  images/
```
