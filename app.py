import pandas as pd
import streamlit as st
from pinForge import generate_stream, build_plan, DEFAULT_URL, DEFAULT_MODEL

st.set_page_config(page_title="PinPilot", page_icon="📌", layout="wide")
st.title("📌 PinForge")
st.caption("Your personal Pinterest marketing assistant, powered by an open-weight model.")
with st.sidebar:
    st.header("Server")
    base_url = st.text_input("Ollama address", DEFAULT_URL)
    st.caption("Use http://localhost:11434 on your laptop, or a server address later.")

# ---------- Inputs ----------
left, right = st.columns([3, 2])
with left:
    name = st.text_input("Product name", "Study Planner Printable")
    details = st.text_area(
        "Product details",
        "Printable PDF, pastel theme, daily and weekly study layouts, instant download",
    )
    audience = st.text_input("Target audience", "students who want to stay organized and focused")
    tone = st.selectbox(
        "Tone", ["Friendly and encouraging", "Motivational", "Practical", "Aesthetic and cozy"]
    )
with right:
    image = st.file_uploader("Product image (optional)", type=["png", "jpg", "jpeg"])
    if image:
        st.image(image, use_container_width=True)
    mode = st.radio("Mode", ["Quick", "Full"], horizontal=True)
    model = st.selectbox("Model", [DEFAULT_MODEL, "gemma3:1b", "gemma3:12b"])
    pins_per_week = st.slider("Pins per week", 3, 21, 7)

TAB_NAMES = ["Titles", "Descriptions", "Keywords", "Angles", "Overlays", "Weekly plan"]
TAB_INDEX = {"titles": 0, "descriptions": 1, "keywords": 2, "angles": 3, "overlays": 4}


# ---------- Rendering helpers ----------
def render(section, data, container):
    """Draw one finished section inside its tab."""
    with container:
        if section == "titles":
            for t in data:
                st.write(f"• {t['title']}  `{len(t['title'])} chars`  *{t['angle']}*")
        elif section == "descriptions":
            for i, d in enumerate(data):
                st.text_area(f"Description {i + 1}", d, height=140, key=f"desc{i}")
        elif section == "keywords":
            st.code(", ".join(data))
        elif section == "angles":
            for a in data:
                st.markdown(
                    f"**{a.get('name')}**: {a.get('hook')}  \n*{a.get('why_it_works')}*"
                )
        elif section == "overlays":
            st.table(data)


def render_plan(result, container):
    """Build and draw the weekly plan from whatever has been generated."""
    with container:
        plan = build_plan(result, pins_per_week)
        if plan:
            df = pd.DataFrame(plan)
            st.dataframe(df, use_container_width=True)
            st.download_button(
                "Download plan as CSV",
                df.to_csv(index=False),
                "pinpilot_weekly_plan.csv",
                "text/csv",
            )
        else:
            st.info("Generate content first.")

clicked = st.button("Generate plan", type="primary")

if clicked:
    result = {}
    st.session_state["result"] = result
    tabs = st.tabs(TAB_NAMES)
    progress = st.progress(0.0, text="Starting...")
    total = 5
    count = 0
    try:
        image_bytes = image.getvalue() if image else None
        for section, data in generate_stream(
            name, details, audience, tone, image_bytes,
            mode=mode, model=model, base_url=base_url,
        ):
            if section in TAB_INDEX:
                result[section] = data
                render(section, data, tabs[TAB_INDEX[section]])
                count += 1
                progress.progress(count / total, text=f"Finished {section} ({count}/{total})")
            elif section == "look":
                st.info(f"📷 What the model sees in your image: {data}")
            elif section == "_stats":
                result["_stats"] = data
        render_plan(result, tabs[5])
        progress.empty()
    except Exception as e:
        progress.empty()
        st.error(f"{e}\n\nIs Ollama running, and is the address in the sidebar correct?")
        render_plan(result, tabs[5])  # keep whatever was finished

elif st.session_state.get("result"):
    # Page reran (for example you moved the slider): redraw saved results.
    result = st.session_state["result"]
    tabs = st.tabs(TAB_NAMES)
    for section, idx in TAB_INDEX.items():
        if section in result:
            render(section, result[section], tabs[idx])
    render_plan(result, tabs[5])

stats = (st.session_state.get("result") or {}).get("_stats")
if stats:
    st.caption(
        f"⏱ {stats['seconds']}s of generation · {stats['tokens']} tokens · "
        f"{stats['tokens_per_sec']} tok/s · {stats['model']} ({stats['mode']})"
    )