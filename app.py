"""
Adaptive Interview Coach with Real-Time Stress Recovery
By Satendra Singh Meena — SAGE University Indore
Patent Pending | B.Tech (AI/ML) Micro Project
"""

import streamlit as st
import time
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import random

from modules.question_bank import get_question, get_next_difficulty, QUESTIONS
from modules.audio_processor import extract_features, compute_stress_score, get_stress_level, get_recovery_prompt
from modules.analytics import generate_session_data, compute_answer_quality

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Adaptive Interview Coach",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
        color: white;
    }
    .main-header h1 { font-size: 2rem; margin: 0; }
    .main-header p  { opacity: 0.8; margin: 0.5rem 0 0 0; }
    
    .question-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 12px;
        margin: 1rem 0;
        color: white;
    }
    .question-card .diff-badge {
        background: rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 2px 12px;
        font-size: 0.8rem;
        display: inline-block;
        margin-bottom: 0.8rem;
    }
    .question-card h3 { margin: 0; font-size: 1.1rem; line-height: 1.5; }

    .stress-card {
        padding: 1.2rem;
        border-radius: 12px;
        text-align: center;
        margin: 0.5rem 0;
    }
    .stress-calm     { background: #d4edda; border: 2px solid #28a745; }
    .stress-moderate { background: #fff3cd; border: 2px solid #ffc107; }
    .stress-elevated { background: #fde8d8; border: 2px solid #fd7e14; }
    .stress-high     { background: #f8d7da; border: 2px solid #dc3545; }

    .recovery-prompt {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        font-size: 1.05rem;
        font-weight: 600;
        text-align: center;
        animation: pulse 2s infinite;
        margin: 0.8rem 0;
    }
    @keyframes pulse {
        0%   { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0.4); }
        70%  { box-shadow: 0 0 0 10px rgba(245, 87, 108, 0); }
        100% { box-shadow: 0 0 0 0 rgba(245, 87, 108, 0); }
    }

    .metric-box {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
        border: 1px solid #e9ecef;
    }
    .metric-box .value { font-size: 2rem; font-weight: 700; color: #0f3460; }
    .metric-box .label { font-size: 0.85rem; color: #6c757d; }

    .stProgress > div > div > div { height: 12px; border-radius: 6px; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ── Session State Init ────────────────────────────────────────────────────────
def init_state():
    defaults = {
        "started": False,
        "finished": False,
        "question_num": 0,
        "current_question": None,
        "current_difficulty": "Medium",
        "category": "Mixed",
        "session_log": [],
        "used_indices": [],
        "stress_scores": [],
        "last_stress": 50.0,
        "total_questions": 8,
        "user_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()


# ── Helpers ───────────────────────────────────────────────────────────────────
def reset_session():
    keys = ["started", "finished", "question_num", "current_question",
            "current_difficulty", "session_log", "used_indices",
            "stress_scores", "last_stress"]
    for k in keys:
        if k in st.session_state:
            del st.session_state[k]
    init_state()


def load_next_question():
    q = get_question(
        st.session_state.category,
        st.session_state.current_difficulty,
        st.session_state.used_indices,
    )
    st.session_state.current_question = q
    st.session_state.used_indices.append(q["index"])


def render_stress_gauge(score):
    level, color, emoji = get_stress_level(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"suffix": "", "font": {"size": 36}},
        title={"text": f"{emoji} {level}", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "tickwidth": 1},
            "bar": {"color": color},
            "steps": [
                {"range": [0, 30],  "color": "#d4edda"},
                {"range": [30, 55], "color": "#fff3cd"},
                {"range": [55, 75], "color": "#fde8d8"},
                {"range": [75, 100],"color": "#f8d7da"},
            ],
            "threshold": {
                "line": {"color": "black", "width": 3},
                "thickness": 0.8,
                "value": score,
            },
        },
    ))
    fig.update_layout(
        height=220,
        margin=dict(l=20, r=20, t=40, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Session Settings")

    if not st.session_state.started:
        st.session_state.user_name = st.text_input("👤 Your Name", placeholder="Satendra Singh Meena")
        st.session_state.category = st.selectbox(
            "📚 Interview Type",
            ["Mixed", "HR", "Technical"],
            index=0,
        )
        st.session_state.total_questions = st.slider(
            "❓ Number of Questions", 5, 15, 8
        )
        st.session_state.current_difficulty = st.select_slider(
            "🎯 Starting Difficulty",
            options=["Easy", "Medium", "Hard"],
            value="Medium",
        )
    else:
        st.markdown(f"**👤 Candidate:** {st.session_state.user_name or 'Anonymous'}")
        st.markdown(f"**📚 Type:** {st.session_state.category}")
        qn = st.session_state.question_num
        total = st.session_state.total_questions
        st.markdown(f"**❓ Progress:** {qn}/{total}")
        st.progress(qn / total if total > 0 else 0)
        st.markdown(f"**🎯 Difficulty:** {st.session_state.current_difficulty}")
        if st.session_state.stress_scores:
            avg = sum(st.session_state.stress_scores) / len(st.session_state.stress_scores)
            _, color, emoji = get_stress_level(avg)
            st.markdown(f"**💓 Avg Stress:** {emoji} {avg:.1f}/100")

    st.markdown("---")
    st.markdown("### 📖 How It Works")
    st.markdown("""
    1. **Record** your answer via audio
    2. **AI analyzes** voice stress signals
    3. **Get coaching** prompts in real-time
    4. **Questions adapt** to your stress level
    5. **Review** detailed analytics after
    """)
    st.markdown("---")
    st.caption("🎓 SAGE University Indore  \nPatent Pending — Satendra Singh Meena")


# ── Main Content ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🎯 Adaptive Interview Coach</h1>
    <p>Real-Time Stress Detection & Recovery — AI-Powered Mock Interview</p>
</div>
""", unsafe_allow_html=True)


# ── START SCREEN ──────────────────────────────────────────────────────────────
if not st.session_state.started and not st.session_state.finished:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### 🚀 Ready to Begin Your Interview?")
        st.markdown("""
        This AI coach will:
        - 🎙️ Analyze your voice for stress signals (pitch, energy, speech rate)
        - 🧠 Adapt question difficulty based on your performance
        - 💬 Give you real-time recovery prompts when needed
        - 📊 Generate a detailed post-session analytics report
        """)
        st.info("💡 **Tip:** Speak clearly and answer in complete sentences for best analysis.")

        if st.button("▶️ Start Interview Session", type="primary", use_container_width=True):
            if not st.session_state.user_name:
                st.session_state.user_name = "Candidate"
            load_next_question()
            st.session_state.started = True
            st.rerun()


# ── INTERVIEW SESSION ─────────────────────────────────────────────────────────
elif st.session_state.started and not st.session_state.finished:
    qn = st.session_state.question_num
    total = st.session_state.total_questions

    # Progress bar
    st.progress((qn) / total, text=f"Question {qn + 1} of {total}")

    q = st.session_state.current_question
    diff_colors = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}

    # Question Card
    st.markdown(f"""
    <div class="question-card">
        <div class="diff-badge">{diff_colors.get(q['difficulty'], '⚪')} {q['difficulty']} · {q['category']}</div>
        <h3>Q{qn + 1}. {q['text']}</h3>
    </div>
    """, unsafe_allow_html=True)

    col_left, col_right = st.columns([3, 2])

    with col_left:
        st.markdown("#### 🎙️ Record Your Answer")
        st.caption("Click the mic button to start recording, then stop when done.")

        audio_value = st.audio_input("Record your answer here 👇", key=f"audio_{qn}")

        answer_text = st.text_area(
            "📝 Or type your answer (if audio not available):",
            key=f"text_{qn}",
            placeholder="Type your answer here...",
            height=100,
        )

        submit_col, skip_col = st.columns(2)
        submit_btn = submit_col.button("✅ Submit Answer", type="primary", use_container_width=True)
        skip_btn = skip_col.button("⏭️ Skip Question", use_container_width=True)

    with col_right:
        st.markdown("#### 📊 Live Stress Monitor")
        stress_placeholder = st.empty()
        prompt_placeholder = st.empty()

        # Show current stress gauge
        last_score = st.session_state.last_stress
        stress_placeholder.plotly_chart(
            render_stress_gauge(last_score),
            use_container_width=True,
            config={"displayModeBar": False},
        )

        # Show session stress trend (mini chart)
        if len(st.session_state.stress_scores) > 1:
            mini_df = pd.DataFrame({
                "Q": [f"Q{i+1}" for i in range(len(st.session_state.stress_scores))],
                "Stress": st.session_state.stress_scores,
            })
            mini_fig = px.line(
                mini_df, x="Q", y="Stress",
                title="Stress Trend This Session",
                markers=True,
                color_discrete_sequence=["#764ba2"],
            )
            mini_fig.update_layout(
                height=160, margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                yaxis=dict(range=[0, 100]),
            )
            st.plotly_chart(mini_fig, use_container_width=True, config={"displayModeBar": False})

    # ── Handle Submit ─────────────────────────────────────────────────────────
    if submit_btn or skip_btn:
        stress_score = 50.0  # Default

        if submit_btn and audio_value is not None:
            # Process audio
            with st.spinner("🔍 Analyzing voice stress signals..."):
                audio_bytes = audio_value.read()
                features = extract_features(audio_bytes)
                if features:
                    stress_score = compute_stress_score(features)
                else:
                    # Fallback: simulate based on text length
                    text_len = len(answer_text.split()) if answer_text else 5
                    stress_score = max(20, 75 - text_len * 1.5 + random.uniform(-10, 10))

        elif submit_btn and answer_text.strip():
            # No audio — estimate stress from text patterns (heuristic fallback)
            text = answer_text.lower()
            fillers = ["um", "uh", "like", "basically", "you know"]
            filler_count = sum(text.count(f) for f in fillers)
            word_count = len(text.split())
            stress_score = max(15, min(85, 55 - word_count * 0.5 + filler_count * 8 + random.uniform(-8, 8)))

        elif skip_btn:
            stress_score = 60.0  # Assume moderate stress for skip

        # Answer quality
        answer_text_final = answer_text if answer_text.strip() else "(No text answer provided)"
        quality = compute_answer_quality(answer_text_final, q["text"])

        # Update state
        st.session_state.last_stress = stress_score
        st.session_state.stress_scores.append(stress_score)

        # Log this question
        st.session_state.session_log.append({
            "question_num": qn + 1,
            "question": q["text"],
            "category": q["category"],
            "difficulty": q["difficulty"],
            "stress_score": stress_score,
            "answer_quality": quality,
            "answer": answer_text_final,
            "timestamp": datetime.now().isoformat(),
        })

        # Show recovery prompt if needed
        prompt = get_recovery_prompt(stress_score)
        if prompt:
            prompt_placeholder.markdown(
                f'<div class="recovery-prompt">{prompt}</div>',
                unsafe_allow_html=True,
            )
            time.sleep(2)

        # Adapt difficulty
        next_diff = get_next_difficulty(q["difficulty"], stress_score, quality)
        st.session_state.current_difficulty = next_diff

        # Next question or finish
        st.session_state.question_num += 1
        if st.session_state.question_num >= st.session_state.total_questions:
            st.session_state.finished = True
        else:
            load_next_question()

        st.rerun()


# ── POST-SESSION ANALYTICS ───────────────────────────────────────────────────
elif st.session_state.finished:
    log = st.session_state.session_log
    analytics = generate_session_data(log)

    name = st.session_state.user_name or "Candidate"
    st.markdown(f"## 📊 Session Report — {name}")
    st.success("✅ Interview session complete! Here's your detailed performance analysis.")

    # ── Summary Metrics ────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    _, color_avg, emoji_avg = get_stress_level(analytics["avg_stress"])

    with c1:
        st.markdown(f"""<div class="metric-box">
            <div class="value">{analytics["total_questions"]}</div>
            <div class="label">Questions Answered</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-box">
            <div class="value" style="color:{color_avg}">{analytics["avg_stress"]}</div>
            <div class="label">{emoji_avg} Avg Stress Score</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-box">
            <div class="value">{analytics["avg_quality"]}</div>
            <div class="label">📝 Avg Answer Quality</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        trend = "📈 Improved" if analytics["stress_improved"] else "📉 Needs Work"
        st.markdown(f"""<div class="metric-box">
            <div class="value" style="font-size:1.4rem">{trend}</div>
            <div class="label">Stress Trend</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        df = pd.DataFrame(log)
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(
            x=df["question_num"], y=df["stress_score"],
            mode="lines+markers",
            name="Stress Score",
            line=dict(color="#f5576c", width=3),
            marker=dict(size=10),
            fill="tozeroy",
            fillcolor="rgba(245,87,108,0.1)",
        ))
        fig1.add_hline(y=55, line_dash="dash", line_color="#fd7e14",
                       annotation_text="Elevated Threshold")
        fig1.add_hline(y=75, line_dash="dash", line_color="#dc3545",
                       annotation_text="High Stress Threshold")
        fig1.update_layout(
            title="📈 Stress Score per Question",
            xaxis_title="Question Number",
            yaxis_title="Stress Score (0-100)",
            yaxis=dict(range=[0, 100]),
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig1, use_container_width=True)

    with col_chart2:
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=df["question_num"], y=df["answer_quality"],
            name="Answer Quality",
            marker_color="#667eea",
        ))
        fig2.add_trace(go.Scatter(
            x=df["question_num"], y=df["stress_score"],
            mode="lines+markers",
            name="Stress Score",
            line=dict(color="#f5576c", width=2),
            yaxis="y",
        ))
        fig2.update_layout(
            title="📊 Answer Quality vs Stress",
            xaxis_title="Question Number",
            yaxis_title="Score (0-100)",
            height=320,
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.2),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Difficulty Progression ─────────────────────────────────────────────────
    diff_map = {"Easy": 1, "Medium": 2, "Hard": 3}
    df["difficulty_num"] = df["difficulty"].map(diff_map)
    fig3 = go.Figure()
    fig3.add_trace(go.Scatter(
        x=df["question_num"], y=df["difficulty_num"],
        mode="lines+markers",
        name="Difficulty",
        line=dict(color="#28a745", width=2),
        marker=dict(size=10),
    ))
    fig3.update_layout(
        title="🎯 Adaptive Difficulty Progression",
        xaxis_title="Question Number",
        yaxis=dict(
            tickvals=[1, 2, 3],
            ticktext=["Easy", "Medium", "Hard"],
            title="Difficulty Level",
        ),
        height=250,
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig3, use_container_width=True)

    # ── Question-by-Question Breakdown ─────────────────────────────────────────
    st.markdown("### 📋 Question-by-Question Breakdown")
    for entry in log:
        _, s_color, s_emoji = get_stress_level(entry["stress_score"])
        with st.expander(
            f"Q{entry['question_num']}: {entry['question'][:60]}... "
            f"| {s_emoji} Stress: {entry['stress_score']:.0f} "
            f"| 📝 Quality: {entry['answer_quality']:.0f}"
        ):
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Stress Score", f"{entry['stress_score']:.1f}/100")
            col_b.metric("Answer Quality", f"{entry['answer_quality']:.1f}/100")
            col_c.metric("Difficulty", entry["difficulty"])
            st.markdown(f"**Question:** {entry['question']}")
            st.markdown(f"**Your Answer:** {entry['answer'][:200]}{'...' if len(entry['answer']) > 200 else ''}")

    # ── Personalized Recommendations ──────────────────────────────────────────
    st.markdown("### 💡 Personalized Improvement Tips")
    avg_stress = analytics["avg_stress"]
    avg_quality = analytics["avg_quality"]

    tips = []
    if avg_stress > 65:
        tips.append("🌬️ **Practice breathing exercises** before interviews. Deep breathing reduces cortisol and lowers voice pitch instability.")
    if avg_stress > 50:
        tips.append("🐢 **Slow your speech rate.** Rushed speaking is a major stress indicator — practice pacing with a metronome app.")
    if avg_quality < 55:
        tips.append("📚 **Structure your answers** using the STAR method (Situation, Task, Action, Result) for HR questions.")
    if not analytics["stress_improved"]:
        tips.append("📈 **Your stress increased over the session.** Try shorter sessions (5 questions) to build stamina gradually.")
    else:
        tips.append("🎉 **Great improvement!** Your stress decreased as the session progressed — you are building resilience!")
    if avg_quality > 70:
        tips.append("💪 **Strong answer quality!** Focus now on reducing stress signals to match your content quality.")

    if not tips:
        tips.append("✨ **Excellent performance!** Keep practicing to maintain this level of confidence and quality.")

    for tip in tips:
        st.markdown(f"- {tip}")

    st.markdown("---")

    # ── New Session Button ─────────────────────────────────────────────────────
    col_r1, col_r2 = st.columns(2)
    if col_r1.button("🔄 Start New Session", type="primary", use_container_width=True):
        reset_session()
        st.rerun()
    col_r2.caption("📁 Screenshot this page to save your report.")

    st.markdown("---")
    st.caption("🎓 Adaptive Interview Coach · Patent Pending · Satendra Singh Meena · SAGE University Indore")
