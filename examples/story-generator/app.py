import streamlit as st

# Import functions from your new modules
from functions.get_realtime_info import get_realtime_info
from functions.get_video_transcription import generate_video_transcription

# Streamlit page setup
st.set_page_config(
    page_title="StoryForge Agent",
    page_icon="🌐",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- Custom modern CSS theme ---
st.markdown("""
    <style>
        .stApp {
            background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
            color: #f5f5f5;
        }
        h1, h2, h3 {
            text-align: center;
            color: #F9FAFB !important;
        }
        .stTextInput>div>div>input {
            border: 1px solid #6EE7B7 !important;
            border-radius: 10px;
            padding: 12px;
            background-color: #111827;
            color: white !important;
        }
        div.stButton > button {
            background: linear-gradient(90deg, #06b6d4, #3b82f6);
            color: white;
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            border: none;
            transition: 0.3s ease-in-out;
        }
        div.stButton > button:hover {
            transform: scale(1.05);
            background: linear-gradient(90deg, #2563eb, #06b6d4);
        }
        .card {
            background-color: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3);
            margin-top: 20px;
        }
        .stRadio > div {
            justify-content: center;
        }
        footer, .stCaption {
            text-align: center;
            color: #9CA3AF;
        }
    </style>
""", unsafe_allow_html=True)


def main():
    st.markdown("<h1>🌐StoryForge Agent</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p style='text-align:center; color:#D1D5DB;'>"
        "Search any topic — from world news to research trends — and get AI-powered insights & video scripts instantly 🚀"
        "</p>",
        unsafe_allow_html=True
    )

    query = st.text_input("🔎 Enter your topic or question:")

    if query:
        with st.spinner('🌍 Gathering latest information...'):
            try:
                info_result = get_realtime_info(query)
            except Exception as e:
                st.error(f"❌ Error fetching info: {e}")
                info_result = None

        if info_result:
            st.markdown("<div class='card'>", unsafe_allow_html=True)
            st.subheader("📚 AI-Generated Summary")
            st.write(info_result)
            st.markdown("</div>", unsafe_allow_html=True)

            generate_script = st.radio(
                "🎬 Generate a short video script?",
                ("No", "Yes"),
                index=0,
                horizontal=True
            )

            if generate_script == "Yes":
                with st.spinner('🎥 Crafting your video script...'):
                    try:
                        script = generate_video_transcription(info_result)
                    except Exception as e:
                        st.error(f"❌ Error generating video script: {e}")
                        script = None

                if script:
                    st.markdown("<div class='card'>", unsafe_allow_html=True)
                    st.subheader("🎥 Video Script")
                    st.write(script)
                    st.download_button(
                        label="📥 Download Script",
                        data=script,
                        file_name="video_script.txt",
                        mime="text/plain"
                    )
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.warning("⚠️ Could not generate transcription.")
        else:
            st.warning("⚠️ No valid information found. Please try another query.")

    st.markdown("<hr>", unsafe_allow_html=True)
    st.caption("Made with 💖")


if __name__ == "__main__":
    main()
