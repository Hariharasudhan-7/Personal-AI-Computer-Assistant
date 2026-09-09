from datetime import datetime
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

import streamlit as st
import streamlit.components.v1 as components

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from backend.main_ai.runtime import build_runtime_main_ai

VOICE_INPUT_PATH = Path(__file__).parent / "voice_input"

voice_input = components.declare_component(
    "voice_input",
    path=str(VOICE_INPUT_PATH),
)


st.set_page_config(
    page_title="LEO",
    page_icon="◉",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def add_log(user_text: str, leo_text: str) -> None:
    st.session_state.activity.extend([("You", user_text), ("SYS", leo_text)])
    st.session_state.activity = st.session_state.activity[-8:]


def get_main_ai():
    if "main_ai" not in st.session_state:
        st.session_state.main_ai = build_runtime_main_ai()
    return st.session_state.main_ai


def get_active_attachment_ids(main_ai) -> list[str]:
    upload_dir = WORKSPACE_ROOT / "automation_workspace" / "uploads"
    attachment_ids = list(st.session_state.active_attachment_ids)
    if not attachment_ids:
        pdf_files = sorted(
            upload_dir.glob("*.pdf"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        if pdf_files:
            attachment_ids = [pdf_files[0].relative_to(upload_dir.parent).as_posix()]

    for attachment_id in attachment_ids:
        file_path = upload_dir.parent / attachment_id
        if file_path.exists() and main_ai.attachment_rag.retriever_for_attachment(attachment_id) is None:
            main_ai.attachment_rag.register(attachment_id, file_path)

    if attachment_ids:
        st.session_state.active_attachment_ids = attachment_ids
    return attachment_ids


if "activity" not in st.session_state:
    st.session_state.activity = [("SYS", "LEO online."), ("You", "hey leo")]

if "voice_reply" not in st.session_state:
    st.session_state.voice_reply = ""

if "last_voice_command" not in st.session_state:
    st.session_state.last_voice_command = ""

if "attachment_reset" not in st.session_state:
    st.session_state.attachment_reset = 0

if "active_attachment_ids" not in st.session_state:
    st.session_state.active_attachment_ids = []

if "voice_draft" not in st.session_state:
    st.session_state.voice_draft = ""

if "stop_voice_token" not in st.session_state:
    st.session_state.stop_voice_token = 0

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid4())

if "user_id" not in st.session_state:
    st.session_state.user_id = os.getenv("USER_ID", "local-user")


st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');
    :root { --ink:#02070b; --cyan:#11d8f5; --cyan-dim:#087a94; --line:rgba(20,207,239,.28); --muted:#4e8999; --amber:#f27d20; }
    html,body,[data-testid="stAppViewContainer"] { background:var(--ink); color:var(--cyan); font-family:'Share Tech Mono','Courier New',monospace; }
    [data-testid="stAppViewContainer"],.main { overflow:visible; }
    [data-testid="stHeader"] { display:none; }
    .block-container { max-width:none; min-height:100vh; height:auto; padding:0 1.25rem .5rem; overflow:visible; }
    .console-header { height:4.1rem; border-bottom:1px solid var(--line); position:relative; display:flex; align-items:center; justify-content:center; background:linear-gradient(180deg,#04131a,#02070b); }
    .brand { text-align:center; letter-spacing:.5rem; font-weight:700; font-size:1.55rem; color:#eaffff; text-shadow:0 0 4px #fff,0 0 12px var(--cyan),0 0 28px rgba(17,216,245,.8); }
    .clock { position:absolute; right:0; top:.45rem; text-align:right; }
    .clock strong { display:block; font-size:1.15rem; letter-spacing:.08rem; }
    .clock span { color:var(--muted); font-size:.55rem; }
    .online-status { display:block; color:#63ef9b; font-size:.65rem; letter-spacing:.08rem; margin-top:.2rem; text-shadow:0 0 8px rgba(99,239,155,.55); }
    .section-label { color:#6ba5b2; border-bottom:1px solid var(--line); padding:.3rem 0 .45rem; font-size:.64rem; letter-spacing:.06rem; }
    .side-panel { border-left:1px solid var(--line); padding-left:.65rem; min-height:calc(100vh - 5rem); height:auto; display:flex; flex-direction:column; }
    .activity-box { flex:1 1 auto; min-height:10rem; border:1px solid rgba(24,150,173,.35); border-radius:3px; padding:.7rem; margin-top:.5rem; background:rgba(2,12,17,.72); overflow-y:auto; }
    .log-line { font-size:.71rem; line-height:1.55; color:#a1dbe4; }
    .log-line.user,.log-line.sys { color:#f0db7d; }
    .radar-wrap { height:calc(100vh - 5rem); display:grid; place-items:center; position:relative; overflow:hidden; }
    .radar { width:min(calc(100% - 2rem),46rem,calc(100vh - 7rem)); aspect-ratio:1; position:relative; border-radius:50%; background:repeating-radial-gradient(circle,transparent 0 4.2rem,rgba(8,106,133,.15) 4.25rem 4.35rem),radial-gradient(circle,#061b2b 0 14%,#0a3050 14.2% 27%,#082843 27.2% 35%,transparent 35.2%); box-shadow:0 0 0 1px rgba(5,94,119,.45),0 0 2rem rgba(0,180,232,.22),inset 0 0 5rem rgba(1,81,121,.16); }
    .radar.speaking { animation:voicePulse .55s ease-in-out infinite alternate; }
    .radar::before,.radar::after { content:''; position:absolute; inset:0; border-radius:50%; pointer-events:none; }
    .radar::before,.radar::after { background:none; }
    .orbit-lines { position:absolute; inset:0; width:100%; height:100%; overflow:visible; animation:spin 34s linear infinite; }
    .orbit-lines circle { fill:none; stroke:#0eb5d1; stroke-width:.38; opacity:.78; }
    .orbit-lines circle:nth-child(2n) { stroke:#08728d; opacity:.55; }
    .orbit-lines circle:nth-child(3n) { stroke:#16d7ee; opacity:.85; }
    .orbit-points { transform-origin:50px 50px; animation:spin 11s linear infinite reverse; }
    .light-dot { fill:#b9fbff; stroke:#14dff7; stroke-width:.7; filter:drop-shadow(0 0 2px #11d8f5); animation:twinkle 1.2s ease-in-out infinite alternate; }
    .light-dot:nth-child(2n) { animation-delay:-.6s; }
    .crosshair { position:absolute; inset:15%; background:linear-gradient(90deg,transparent 49.9%,rgba(17,216,245,.18) 50%,transparent 50.1%),linear-gradient(0deg,transparent 49.9%,rgba(17,216,245,.18) 50%,transparent 50.1%); }
    .core { position:absolute; inset:34%; border-radius:50%; background:radial-gradient(circle at 50% 42%,#0b3a5d,#061c31 67%,#03111c); border:1px solid rgba(29,181,219,.45); display:grid; place-items:center; box-shadow:0 0 2rem rgba(0,112,170,.3); animation:coreBlink 1.8s ease-in-out infinite; }
    .core-label { letter-spacing:.36rem; font-size:1.05rem; color:#eaffff; font-weight:700; text-shadow:0 0 4px #fff,0 0 10px var(--cyan),0 0 22px rgba(17,216,245,.8); }
    .corner { position:absolute; width:2rem; height:2rem; border-color:var(--cyan); opacity:.85; }
    .corner.tl { top:0; left:0; border-top:2px solid; border-left:2px solid; } .corner.tr { top:0; right:0; border-top:2px solid; border-right:2px solid; } .corner.bl { bottom:0; left:0; border-bottom:2px solid; border-left:2px solid; } .corner.br { bottom:0; right:0; border-bottom:2px solid; border-right:2px solid; }
    .state { position:absolute; bottom:1.1rem; left:50%; transform:translateX(-50%); color:var(--amber); font-size:.84rem; letter-spacing:.04rem; }
    .state::before { content:'●'; margin-right:.8rem; }
    .bars { position:absolute; bottom:-1rem; left:50%; transform:translateX(-50%); display:flex; align-items:end; gap:3px; height:1.4rem; }
    .bars i { display:block; width:6px; height:calc(8px + (var(--i) * 3px)); background:var(--cyan); }
    .radar.speaking .bars i { animation:equalize .3s ease-in-out infinite alternate; animation-delay:calc(var(--i) * -80ms); }
    .command-row [data-testid="stColumn"] { display:flex; align-items:center; }
    [data-testid="stForm"] { margin-top:.5rem; padding:.35rem; border:1px solid rgba(17,216,245,.22); border-radius:8px; background:rgba(2,12,17,.72); }
    .command-row [data-testid="stColumn"] > div { width:100%; }
    .stPopover button { background:rgba(3,18,25,.94) !important; color:#b9fbff !important; border:1px solid rgba(17,216,245,.42) !important; border-radius:999px !important; min-width:3.2rem; height:3.2rem; font-size:1.2rem !important; box-shadow:0 0 12px rgba(0,153,190,.08), inset 0 0 12px rgba(17,216,245,.04); transition:all .2s ease; }
    .stPopover button:hover { border-color:var(--cyan) !important; color:white !important; box-shadow:0 0 18px rgba(17,216,245,.28), inset 0 0 12px rgba(17,216,245,.08); transform:translateY(-1px); }
    [data-testid="stPopoverBody"] { background:#04151c; border:1px solid rgba(17,216,245,.55); border-radius:10px; box-shadow:0 12px 35px rgba(0,0,0,.5),0 0 20px rgba(0,180,232,.12); padding:.7rem; }
    [data-testid="stPopoverBody"] > div { gap:.3rem !important; }
    [data-testid="stPopoverBody"] [data-testid="stFileUploader"] { margin:.08rem 0; }
    [data-testid="stPopoverBody"] [data-testid="stFileUploader"] + div { margin-top:-.25rem; }
    [data-testid="stPopoverBody"] label { color:#9feaf4; font-size:.65rem; margin-bottom:0 !important; }
    .stTextInput input { background:#f5f3ef !important; color:#26323a !important; border:0 !important; border-radius:2rem !important; font-family:inherit !important; height:3.2rem !important; font-size:1rem !important; padding:0 1.15rem !important; box-shadow:0 0 0 1px rgba(17,216,245,.28),0 0 14px rgba(0,180,232,.06) !important; }
    .stTextInput input::placeholder { color:#64727a !important; }
    .stButton button { background:rgba(3,18,25,.94); color:var(--cyan); border:1px solid rgba(17,216,245,.42); border-radius:999px; height:3.2rem; min-width:3.2rem; font-size:1.2rem; box-shadow:0 0 12px rgba(0,153,190,.08); transition:all .2s ease; }
    [data-testid="stFileUploader"] { margin:0; }
    [data-testid="stFileUploader"] section { height:3.4rem; min-height:3.4rem; padding:.25rem .1rem; border:0; background:transparent; border-radius:3px; }
    [data-testid="stFileUploader"] section small,[data-testid="stFileUploader"] section button,[data-testid="stFileUploaderDropzoneInstructions"] { display:none; }
    [data-testid="stFileUploader"] section > div { padding:0; }
    [data-testid="stForm"] [data-testid="stColumn"]:nth-child(3) [data-testid="stFileUploader"] section { height:3.2rem; min-height:3.2rem; border:1px solid rgba(17,216,245,.42); border-radius:999px; background:rgba(3,18,25,.94); box-shadow:0 0 12px rgba(0,153,190,.08); cursor:pointer; transition:all .2s ease; }
    [data-testid="stForm"] [data-testid="stColumn"]:nth-child(3) [data-testid="stFileUploader"] section:hover { border-color:var(--cyan); box-shadow:0 0 18px rgba(17,216,245,.3); }
    [data-testid="stForm"] [data-testid="stColumn"]:nth-child(3) [data-testid="stFileUploader"] section::before { content:'📷'; display:block; color:#b9fbff; font-size:1.2rem; line-height:2.6rem; text-align:center; }
    .command-row .stButton button:hover { border-color:var(--cyan); color:white; box-shadow:0 0 18px rgba(17,216,245,.3); transform:translateY(-1px); }
    .selected-file { display:flex; align-items:center; justify-content:space-between; gap:.6rem; margin-top:.35rem; padding:.4rem .65rem; border:1px solid rgba(17,216,245,.28); border-radius:7px; background:rgba(8,38,50,.8); color:#b9fbff; font-size:.66rem; }
    .selected-file-name { overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    @keyframes spin { to { transform:rotate(360deg); } } @keyframes equalize { to { height:1.35rem; } } @keyframes twinkle { from { opacity:.35; r:1; } to { opacity:1; r:2; } } @keyframes voicePulse { from { transform:scale(1); box-shadow:0 0 0 1px rgba(5,94,119,.45),0 0 2rem rgba(0,180,232,.22),inset 0 0 5rem rgba(1,81,121,.16); } to { transform:scale(1.025); box-shadow:0 0 0 5px rgba(17,216,245,.22),0 0 4rem rgba(0,209,255,.7),inset 0 0 7rem rgba(1,133,171,.45); } } @keyframes radarBlink { 0%,100% { opacity:.9; } 50% { opacity:1; } } @keyframes coreBlink { 0%,100% { box-shadow:0 0 2rem rgba(0,112,170,.3); } 50% { box-shadow:0 0 4rem rgba(0,209,255,.65); } }
    @media (max-width:900px) { .block-container { height:auto; overflow:visible; } .side-panel { min-height:0; height:auto; border-left:0; padding-left:0; } .radar-wrap { height:72vw; } .radar { width:min(calc(100% - 2rem),calc(100vh - 7rem)); } .activity-box { flex:none; height:15rem; } .clock { right:.5rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


now = datetime.now()
st.markdown(f"<div class='console-header'><div class='brand'>L.E.O.</div><div class='clock'><strong>{now:%H:%M:%S}</strong><span>{now:%a %d %b %Y}</span><b class='online-status'>● ONLINE</b></div></div>", unsafe_allow_html=True)

main_col, side_col = st.columns([2.85, 1.65], gap="small")

with main_col:
    radar_class = "radar speaking" if st.session_state.voice_reply else "radar"
    st.markdown(f"""
        <div class='radar-wrap'><div class='{radar_class}'><div class='crosshair'></div><svg class='orbit-lines' viewBox='0 0 100 100' aria-hidden='true'><circle cx='50' cy='50' r='20' stroke-dasharray='32 9 5 18 12 20'></circle><circle cx='50' cy='50' r='28' stroke-dasharray='5 17 25 12 9 28'></circle><circle cx='50' cy='50' r='36' stroke-dasharray='44 10 7 17 19 13'></circle><circle cx='50' cy='50' r='43' stroke-dasharray='8 22 33 11 5 18'></circle><circle cx='50' cy='50' r='48' stroke-dasharray='52 13 5 24 15 17'></circle><g class='orbit-points'><circle class='light-dot' cx='50' cy='13' r='1.4'></circle><circle class='light-dot' cx='80' cy='31' r='1.2'></circle><circle class='light-dot' cx='87' cy='64' r='1.5'></circle><circle class='light-dot' cx='35' cy='86' r='1.1'></circle><circle class='light-dot' cx='14' cy='48' r='1.3'></circle></g></svg><div class='core'><div class='core-label'>L.E.O.</div></div><div class='corner tl'></div><div class='corner tr'></div><div class='corner bl'></div><div class='corner br'></div><div class='bars'><i style='--i:1'></i><i style='--i:3'></i><i style='--i:5'></i><i style='--i:2'></i><i style='--i:7'></i><i style='--i:4'></i><i style='--i:6'></i><i style='--i:3'></i><i style='--i:8'></i><i style='--i:5'></i><i style='--i:2'></i></div></div></div>
        """, unsafe_allow_html=True)

with side_col:
    st.markdown("<div class='side-panel'>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>▸ ACTIVITY LOG</div>", unsafe_allow_html=True)
    lines = []
    for speaker, message in st.session_state.activity:
        kind = "sys" if speaker == "SYS" else "user" if speaker == "You" else ""
        lines.append(f"<div class='log-line {kind}'>{speaker}: {message}</div>")
    st.markdown(f"<div class='activity-box'>{''.join(lines)}</div>", unsafe_allow_html=True)
    st.markdown("<div class='section-label' style='margin-top:.6rem'>▸ COMMAND INPUT</div>", unsafe_allow_html=True)
    with st.form("command_form", clear_on_submit=True):
        command_col, mic_col, photo_col, send_col = st.columns([7.1, 1.25, 1.25, 1.4], gap="small")
        with command_col:
            command = st.text_input("Command", placeholder="Type a command or use the mic...", label_visibility="collapsed")
        with mic_col:
            voice_command = voice_input(stop_listening=st.session_state.stop_voice_token, key="voice_command")
        with photo_col:
            attached_files = st.file_uploader(
                "Camera / add files",
                type=["png", "jpg", "jpeg", "webp", "gif", "pdf"],
                accept_multiple_files=True,
                key=f"camera_photos_{st.session_state.attachment_reset}",
                label_visibility="collapsed",
            )
            if attached_files:
                for attached_file in attached_files:
                    st.markdown(f"<div class='selected-file'><span class='selected-file-name'>📄 {attached_file.name}</span></div>", unsafe_allow_html=True)
                remove_attachments = st.form_submit_button("REMOVE SELECTED", use_container_width=True)
            else:
                remove_attachments = False
        with send_col:
            submitted = st.form_submit_button("SEND ➤", type="primary")
    if remove_attachments:
        st.session_state.active_attachment_ids = []
        st.session_state.attachment_reset += 1
        st.rerun()
    if isinstance(voice_command, str) and voice_command and voice_command != st.session_state.last_voice_command:
        st.session_state.last_voice_command = voice_command
        st.session_state.voice_draft = voice_command
        st.rerun()
    if submitted:
        message = command.strip() or st.session_state.voice_draft.strip()
        if message:
            try:
                uploaded_pdf_paths = []
                if attached_files:
                    upload_dir = WORKSPACE_ROOT / "automation_workspace" / "uploads"
                    upload_dir.mkdir(parents=True, exist_ok=True)
                    main_ai = get_main_ai()
                    for attached_file in attached_files:
                        if attached_file.name.lower().endswith(".pdf"):
                            safe_name = Path(attached_file.name).name
                            upload_path = upload_dir / safe_name
                            upload_path.write_bytes(attached_file.getvalue())
                            attachment_id = upload_path.relative_to(upload_dir.parent).as_posix()
                            main_ai.attachment_rag.register(attachment_id, upload_path)
                            uploaded_pdf_paths.append(attachment_id)
                if uploaded_pdf_paths:
                    message = f"{message}\n\nThe uploaded PDF is ready in the RAG agent. Answer only from its contents."
                else:
                    main_ai = get_main_ai()
                if uploaded_pdf_paths:
                    st.session_state.active_attachment_ids = uploaded_pdf_paths
                attachment_ids = uploaded_pdf_paths or get_active_attachment_ids(main_ai)
                response = main_ai.handle_message(
                    user_id=st.session_state.user_id,
                    conversation_id=st.session_state.conversation_id,
                    content=message,
                    attachment_ids=attachment_ids,
                )
                reply = response.message
                if response.error:
                    reply = f"{reply} ({response.error})"
            except Exception as error:
                reply = f"Request failed: {error}"
            add_log(message, reply)
            st.session_state.voice_reply = reply
            st.session_state.voice_draft = ""
            st.session_state.stop_voice_token += 1
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.voice_reply:
    components.html(
        f"""<script>
                const text = {json.dumps(st.session_state.voice_reply)};
        if ('speechSynthesis' in window && text) {{
          window.speechSynthesis.cancel();
          const utterance = new SpeechSynthesisUtterance(text);
          utterance.rate = 0.92;
          utterance.pitch = 0.9;
          window.speechSynthesis.speak(utterance);
        }}
                if (navigator.vibrate) navigator.vibrate([100, 50, 100]);
        </script>""",
        height=0,
    )
    st.session_state.voice_reply = ""