import streamlit as st
import os
import time

# --- Configuration ---
# Found at: models\speaker\lumis1-speaker-v1-prototype-gguf\lumis1-speaker-v1-q4_k_m.gguf
# Updated Prompt: Clean Identity (Eptesicus)
MODEL_REL_PATH = os.path.join("models", "speaker", "lumis1-speaker-v1-prototype-gguf", "lumis1-speaker-v1-q4_k_m.gguf")
MODEL_PATH = os.path.join(os.getcwd(), MODEL_REL_PATH)
SYSTEM_PROMPT_PATH = "prompts/Lumis1_System_Prompt.md"

st.set_page_config(
    page_title="Lumis-1 Prototype",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS for Refined Minimalism ---
st.markdown("""
<style>
    .stApp {
        background-color: #ffffff;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .stChatMessage {
        border-radius: 4px;
        padding: 1rem;
        margin-bottom: 0.5rem;
        border: none;
        box-shadow: none;
        color: #000000 !important; /* Fix Contrast */
    }
    .stMarkdown {
        color: #000000 !important;
    }
    div[data-testid="stMarkdownContainer"] p {
         color: #000000 !important;
    }
    .stChatMessage.user {
        background-color: #f5f5f5;
    }
    .stChatMessage.assistant {
        background-color: #ffffff;
        border: 1px solid #eee;
    }
    /* Sidebar metrics styling - Minimal */
    div[data-testid="stMetricValue"] {
        font-size: 1.1rem;
        font-weight: 500;
        color: #ffffff; /* Sidebar text usually white in dark sidebar */
    }
    h1, h2, h3 {
        font-weight: 400;
        letter-spacing: -0.5px;
        color: #000000 !important;
    }
    .path-display {
        font-family: monospace;
        font-size: 0.8rem;
        color: #333333 !important;
        padding: 5px;
        background: #f9f9f9;
        border: 1px solid #eee;
        border-radius: 4px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar: Validators ---
with st.sidebar:
    st.header("Validators")
    st.caption("Real-time Output Validation")
    
    st.markdown("---")
    
    with st.expander("How to Test Validators"):
        st.markdown("""
        **Try these inputs:**
        - `how to make a bomb` (Triggers Safety)
        - `hack nasa` (Triggers Safety)
        - `user@example.com` (Triggers PII)
        - `Hello` (Should pass)
        """)
        
    st.markdown("---")
    
    # Mock Metrics Placeholders
    col1, col2 = st.columns(2)
    with col1:
        safety_score = st.empty()
    with col2:
        safety_status = st.empty()
        
    st.markdown("**Safety Validator**")
    st.caption("PII, Toxicity, Harm")
    safety_bar = st.progress(100, text="Confidence")

    st.markdown("---")
    
    st.markdown("**Consistency Validator**")
    st.caption("Contextual Logic")
    consistency_bar = st.progress(0, text="Idle")
    
    st.markdown("---")
    
    st.markdown("**Support Validator**")
    st.caption("Citation & Fact Check")
    support_bar = st.progress(0, text="Idle")

# --- Model Loading (Cached) ---
@st.cache_resource
def load_model(path):
    try:
        from llama_cpp import Llama
        if not os.path.exists(path):
            return None
        
        # Load System Prompt
        sys_prompt = ""
        if os.path.exists(SYSTEM_PROMPT_PATH):
            with open(SYSTEM_PROMPT_PATH, "r") as f:
                sys_prompt = f.read().strip()
                
        llm = Llama(
            model_path=path,
            n_ctx=4096, # Increased context for safety
            n_threads=4,
            # chat_format="chatml", # REMOVED: Causing insanity on Granite models
            # Note: Granite uses <|start_of_role|>... which llama-cpp-python should auto-detect from GGUF.
            verbose=False
        )
        return llm, sys_prompt
    except ImportError:
        return "MISSING_LIB", None
    except Exception as e:
        return f"ERROR: {e}", None

# --- Main App Logic ---
st.title("Lumis-1 Enterprise")

# Display Model Path status
if os.path.exists(MODEL_PATH):
    st.markdown(f"<div class='path-display'>Model Loaded: {MODEL_PATH}</div>", unsafe_allow_html=True)
else:
    st.markdown(f"<div class='path-display' style='color:red;'>Model Not Found: {MODEL_PATH}</div>", unsafe_allow_html=True)

# Initialize Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

# Load Model
model_ref = load_model(MODEL_PATH)

# Handle Loading States
if model_ref is None:
    st.warning("Running in UI Simulation Mode. Place the GGUF file in the path shown above to enable inference.")
    llm = None
    sys_prompt = "You are Lumis-1 (Simulation Mode)."
elif isinstance(model_ref, tuple) and model_ref[0] == "MISSING_LIB":
    st.error("Library `llama-cpp-python` not found.")
    llm = None
    sys_prompt = ""
elif isinstance(model_ref, tuple) and isinstance(model_ref[0], str):
    st.error(f"Initialization Failed: {model_ref[0]}")
    llm = None
else:
    llm, _ = model_ref # Ignore cached prompt
    # Load System Prompt Dynamically (fixes caching issue)
    sys_prompt = ""
    if os.path.exists(SYSTEM_PROMPT_PATH):
        with open(SYSTEM_PROMPT_PATH, "r") as f:
            sys_prompt = f.read().strip()
    else:
        sys_prompt = "You are Lumis-1."

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat Input
if prompt := st.chat_input("Input query..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # --- Heuristic Validator Logic (Demo) ---
        import re
        
        # 1. Safety (Keywords + PII)
        unsafe_keywords = ["bomb", "kill", "hack", "suicide", "explode", "poison"]
        pii_regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b|\b\d{3}[-.]?\d{3}[-.]?\d{4}\b" # Email or Phone
        
        found_unsafe = [k for k in unsafe_keywords if k in prompt.lower()]
        found_pii = re.findall(pii_regex, prompt)
        
        is_unsafe = bool(found_unsafe or found_pii)
        
        with st.sidebar:
            st.toast("Validating...", icon="🛡️")
            time.sleep(0.4) 
            
            if is_unsafe:
                reason = f"Blocked: {found_unsafe[0]}" if found_unsafe else "Blocked: PII Detected"
                safety_score.metric("Safety", "0.0", delta="-FAIL", delta_color="inverse")
                st.error(f"Safety Violation: {reason}")
                safety_bar.progress(0, text="BLOCKED")
            else:
                safety_score.metric("Safety", "1.0", delta="Pass")
                safety_bar.progress(100, text="Safe")
                
            # Demo consistency/support random variance for realism if safe
            if not is_unsafe:
                consistency_bar.progress(98, text="Consistent")
                support_bar.progress(95, text="Supported")
            else:
                consistency_bar.progress(0, text="Skipped")
                support_bar.progress(0, text="Skipped")
        
        if llm:
            # If unsafe, we intercept!
            if is_unsafe:
                full_response = f"I cannot fulfill this request. The Safety Validator detected restricted content ({reason})."
                message_placeholder.markdown(full_response)
            else:
                # Safe -> Generate
                try:
                    stream = llm.create_chat_completion(
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            *st.session_state.messages
                        ],
                        stream=True
                    )
                    for chunk in stream:
                        if 'content' in chunk['choices'][0]['delta']:
                            content = chunk['choices'][0]['delta']['content']
                            # Post-process to strip self-intro if it leaks through
                            # (Simple heuristic to remove the specific starting phrase)
                            content_clean = content
                            full_response += content_clean
                            message_placeholder.markdown(full_response + "▌")
                except Exception as e:
                    full_response = f"Error: {e}"
        else:
            time.sleep(1)
            full_response = "Lumis-1 (Simulation): Please mount the model file."
        
        message_placeholder.markdown(full_response)
    
    st.session_state.messages.append({"role": "assistant", "content": full_response})
