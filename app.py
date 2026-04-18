"""
Face & Name Trainer — Streamlit app.

Reads data/people.json produced by extract_pptx.py and offers two quiz modes:
  • Face → Name : see a photo, type or pick the correct name
  • Name → Face : see a name, click the correct photo from four options
"""

import json
import random
from pathlib import Path

import streamlit as st
from PIL import Image

DATA_DIR = Path("data")
PEOPLE_FILE = DATA_DIR / "people.json"
SCORES_FILE = DATA_DIR / "scores.json"


# ── data helpers ─────────────────────────────────────────────────────────────

@st.cache_data
def load_people():
    if not PEOPLE_FILE.exists():
        return []
    with open(PEOPLE_FILE, encoding="utf-8") as f:
        return json.load(f)


def load_scores(names: list[str]) -> dict:
    scores: dict = {}
    if SCORES_FILE.exists():
        try:
            with open(SCORES_FILE, encoding="utf-8") as f:
                scores = json.load(f)
        except Exception:
            scores = {}
    for name in names:
        scores.setdefault(name, {"correct": 0, "total": 0})
    return scores


def save_scores(scores: dict) -> None:
    try:
        DATA_DIR.mkdir(exist_ok=True)
        with open(SCORES_FILE, "w", encoding="utf-8") as f:
            json.dump(scores, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # read-only filesystem on Streamlit Cloud — scores live in session only


def get_image(person: dict) -> Image.Image | None:
    path = DATA_DIR / person["image_path"]
    if path.exists():
        try:
            return Image.open(path)
        except Exception:
            return None
    return None


# ── quiz logic ────────────────────────────────────────────────────────────────

def weighted_pick(people: list, scores: dict, exclude_name: str | None = None) -> dict:
    """Pick a person weighted toward those with higher error rates."""
    candidates = [p for p in people if p["name"] != exclude_name]
    if not candidates:
        candidates = people

    weights = []
    for p in candidates:
        s = scores.get(p["name"], {"correct": 0, "total": 0})
        if s["total"] == 0:
            w = 2.0
        else:
            error_rate = 1.0 - s["correct"] / s["total"]
            w = max(0.1, error_rate + 0.2)
        weights.append(w)

    total = sum(weights)
    r = random.random() * total
    cumulative = 0.0
    for person, w in zip(candidates, weights):
        cumulative += w
        if r <= cumulative:
            return person
    return candidates[-1]


def make_choices(people: list, correct: dict, n: int = 4) -> list:
    """Return n shuffled choices including the correct person."""
    others = [p for p in people if p["name"] != correct["name"]]
    distractors = random.sample(others, min(n - 1, len(others)))
    choices = distractors + [correct]
    random.shuffle(choices)
    return choices


def advance_question() -> None:
    people = st.session_state.people
    scores = st.session_state.scores
    last = st.session_state.get("current_person")
    last_name = last["name"] if last else None

    person = weighted_pick(people, scores, exclude_name=last_name)
    st.session_state.current_person = person
    st.session_state.choices = make_choices(people, person)
    st.session_state.answered = False
    st.session_state.correct = None
    st.session_state.selected_idx = None


def record_answer(name: str, is_correct: bool) -> None:
    scores = st.session_state.scores
    scores[name]["total"] += 1
    if is_correct:
        scores[name]["correct"] += 1
    st.session_state.answered = True
    st.session_state.correct = is_correct
    save_scores(scores)


# ── UI sections ───────────────────────────────────────────────────────────────

def render_sidebar(people: list) -> None:
    with st.sidebar:
        st.title("Face & Name Trainer")

        mode = st.radio(
            "Training Mode",
            options=["face_to_name", "name_to_face"],
            format_func=lambda x: "🖼 Face → Name" if x == "face_to_name" else "🔤 Name → Face",
            key="mode",
        )
        # Reset question when mode changes
        if mode != st.session_state.get("_last_mode"):
            st.session_state._last_mode = mode
            st.session_state.current_person = None

        st.divider()
        st.subheader("Progress")

        scores = st.session_state.scores
        total_correct = sum(s["correct"] for s in scores.values())
        total_attempts = sum(s["total"] for s in scores.values())

        if total_attempts:
            pct = total_correct / total_attempts * 100
            st.metric("Accuracy", f"{pct:.1f}%", f"{total_correct}/{total_attempts}")
        else:
            st.write("No attempts yet — start quizzing!")

        st.divider()
        st.subheader("Needs Work")
        tested = [
            (name, s) for name, s in scores.items() if s["total"] >= 2
        ]
        if tested:
            tested.sort(key=lambda x: x[1]["correct"] / x[1]["total"])
            for name, s in tested[:6]:
                pct = s["correct"] / s["total"] * 100
                st.write(f"• {name} — {pct:.0f}% ({s['correct']}/{s['total']})")
        else:
            st.write("Answer at least 2 questions per person to see stats.")

        st.divider()
        if st.button("Reset all scores", use_container_width=True):
            st.session_state.scores = {
                p["name"]: {"correct": 0, "total": 0} for p in people
            }
            save_scores(st.session_state.scores)
            st.success("Scores cleared.")


def render_face_to_name(person: dict, people: list) -> None:
    st.markdown("### Who is this person?")

    col_img, col_quiz = st.columns([1, 1], gap="large")

    with col_img:
        img = get_image(person)
        if img:
            st.image(img, use_container_width=True)
        else:
            st.warning("Image file not found.")

    with col_quiz:
        if not st.session_state.answered:
            answer_mode = st.radio(
                "Answer method",
                ["Type the name", "Pick from list"],
                horizontal=True,
                key="answer_mode",
            )

            if answer_mode == "Type the name":
                with st.form("face_name_form", clear_on_submit=True):
                    typed = st.text_input("Name:", placeholder="First Last")
                    submitted = st.form_submit_button("Submit", type="primary")
                if submitted and typed.strip():
                    is_correct = typed.strip().lower() == person["name"].lower()
                    record_answer(person["name"], is_correct)
                    st.rerun()
            else:
                names = sorted(p["name"] for p in people)
                chosen = st.selectbox("Select the name:", ["— choose —"] + names)
                if st.button("Submit", type="primary") and chosen != "— choose —":
                    is_correct = chosen == person["name"]
                    record_answer(person["name"], is_correct)
                    st.rerun()
        else:
            if st.session_state.correct:
                st.success(f"Correct!  That's **{person['name']}**.")
            else:
                st.error(f"Not quite — this is **{person['name']}**.")

            if st.button("Next →", type="primary", use_container_width=True):
                advance_question()
                st.rerun()


def render_name_to_face(person: dict) -> None:
    st.markdown(f"### Find the photo of:  **{person['name']}**")

    choices: list = st.session_state.choices
    correct_idx = next(
        (i for i, c in enumerate(choices) if c["name"] == person["name"]), 0
    )

    cols = st.columns(len(choices), gap="small")

    for i, choice in enumerate(choices):
        with cols[i]:
            img = get_image(choice)
            if img:
                st.image(img, use_container_width=True)
            else:
                st.markdown("*(no image)*")

            if not st.session_state.answered:
                if st.button(f"Select", key=f"ntf_{i}", use_container_width=True):
                    st.session_state.selected_idx = i
                    record_answer(person["name"], i == correct_idx)
                    st.rerun()
            else:
                sel = st.session_state.selected_idx
                if i == correct_idx:
                    st.success(f"✓ {choice['name']}")
                elif i == sel:
                    st.error(f"✗ {choice['name']}")
                else:
                    st.caption(choice["name"])

    if st.session_state.answered:
        st.divider()
        if st.session_state.correct:
            st.success("Correct!")
        else:
            st.error(f"The correct answer was **{person['name']}**.")

        if st.button("Next →", type="primary"):
            advance_question()
            st.rerun()


# ── main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    st.set_page_config(
        page_title="Face & Name Trainer",
        page_icon="🧑",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    people = load_people()

    if not people:
        st.error("No data found.")
        st.info(
            "Run the extraction script first:\n\n"
            "```bash\npython extract_pptx.py your_staff.pptx\n```\n\n"
            "Then reload this page."
        )
        return

    if len(people) < 2:
        st.error("Need at least 2 people in the dataset.")
        return

    # ── session state initialisation ──────────────────────────────────────────
    if "mode" not in st.session_state:
        st.session_state.mode = "face_to_name"
    if "_last_mode" not in st.session_state:
        st.session_state._last_mode = st.session_state.mode
    if "people" not in st.session_state:
        st.session_state.people = people
    if "scores" not in st.session_state:
        st.session_state.scores = load_scores([p["name"] for p in people])
    if "answered" not in st.session_state:
        st.session_state.answered = False
    if "correct" not in st.session_state:
        st.session_state.correct = None
    if "selected_idx" not in st.session_state:
        st.session_state.selected_idx = None
    if "choices" not in st.session_state:
        st.session_state.choices = []
    if "current_person" not in st.session_state:
        st.session_state.current_person = None

    render_sidebar(people)

    if st.session_state.current_person is None:
        advance_question()

    person = st.session_state.current_person
    mode = st.session_state.mode

    if mode == "face_to_name":
        render_face_to_name(person, people)
    else:
        if len(people) < 4:
            st.warning(
                "Name → Face mode works best with at least 4 people. "
                "Add more slides or switch to Face → Name mode."
            )
        render_name_to_face(person)


if __name__ == "__main__":
    main()
