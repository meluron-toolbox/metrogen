"""
Author: Ankit Anand
"""

#importing libraries
import streamlit as st
import librosa
import pandas as pd
import re
import sys
import time
import random
from audio_recorder_streamlit import audio_recorder

#adding custom paths to utility functions
sys.path.append("./utils/")
sys.path.append(".")
sys.path.append("..")
#from utils.generate_metronome import generate_metronome
from utils.generate_metronome_with_theka import generate_metronome
from utils.onset_detection import get_ticks_position
from utils.load_rhythm import get_rhythm_list, get_setting
from utils.audio_recorder import get_settings_from_clap
from utils.audio_effects import apply_equalizer, apply_compressor, add_reverb

#page configuration
st.set_page_config(
    page_title="Metronome Generator",
    page_icon="⏱",  # Optional, emoji or file path
    layout="wide",  # Makes the layout wider
    initial_sidebar_state="auto",  # Sidebar will be expanded by default, not collapsed
)

#global parameters
SR = 22050
SCALES = ["None", "A", "A#", "B", "C", "C#", "D", "D#", "E", "F", "F#", "G", "G#"]
RHYTHM_LIST = get_rhythm_list(rhythm_fp="https://raw.githubusercontent.com/meluron/assets/refs/heads/main/rhythm_db.csv")

#logo
st.markdown(
    """
        <style>
        img {
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 10%;
            margin-bottom: 10px;
        }
        </style>
        <a href="https://github.com/meluron" target="_blank">
            <img src="https://raw.githubusercontent.com/meluron/assets/refs/heads/main/mel_logo_circular.png">
        </a>
    """, unsafe_allow_html=True
)

st.markdown("<p style='text-align: center;'>where utility drives innovation</p>", unsafe_allow_html=True)

st.divider()

#initialize session state on page refresh
if "load_triggered" not in st.session_state: #this will run reloading the page
    st.session_state.load_triggered = False
    st.session_state.selected_rhythm = "Default"
    st.session_state.last_action = "preset"  #tracking the most recent action (preset or audio)
    st.session_state.audio_bytes = None  #track the recorded audio if any
    st.session_state.is_uploaded_file = False

#function to reset session state when a new preset is selected
def reset_session_state():
    st.session_state.last_action = "preset"  #mark that the last action was a preset change
    load_rhythm_settings()  #load the preset settings immediately
    
    
# Loading the page with default settings on first load
if not st.session_state.load_triggered:
#   st.info("Hi, I'm Ankit. I stopped sharing this app a few months ago, but if you're still using it, I would greatly appreciate your feedback to help further develop the product. Please let me know what you're using the app for [call me on 7357333796 or email me at ankit0.anand0@gmail.com. Thank you!")
    rhythm_name = random.choice(list(RHYTHM_LIST.keys()))
    default_rhythm_id = RHYTHM_LIST[rhythm_name]  # Default to first rhythm in the dictionary
    bpm, time_sign, strong_beats, suppress_beats, scale, duration, creator = get_setting(
        "https://raw.githubusercontent.com/meluron/assets/refs/heads/main/rhythm_db.csv", default_rhythm_id
    )
    
    # Store default settings in session state
    st.session_state.bpm = bpm
    st.session_state.time_sign = time_sign
    st.session_state.strong_beats = strong_beats
    st.session_state.suppress_beats = "" if suppress_beats == "None" else suppress_beats
    st.session_state.scale = scale
    st.session_state.duration = duration
    st.session_state.load_triggered = True  # Set flag to avoid reloading on subsequent reruns
    st.session_state.rhythm_name = rhythm_name

def load_setting_from_clap(audio):
    bpm, time_sign, strong_beats, suppress_beats = get_settings_from_clap(audio)
    st.session_state.bpm = bpm
    st.session_state.time_sign = time_sign
    st.session_state.strong_beats = strong_beats
    st.session_state.suppress_beats = "" if suppress_beats == "None" else suppress_beats
    st.session_state.scale = "C"
    st.session_state.duration = 3
    st.session_state.rhythm_name = "👏"
    st.session_state.last_action = "audio" 

def load_user_settings(file):
    if file is not None:
        content = file.read().decode('utf-8').strip().split('\n')
        if len(content) >= 6:
            try:
                st.session_state.bpm = int(content[0])
                st.session_state.time_sign = content[1]
                st.session_state.strong_beats = content[2]
                st.session_state.suppress_beats = content[3]
                st.session_state.scale = content[4]
                st.session_state.duration = int(content[5])
                st.session_state.rhythm_name = "Custom" #f"{file.name.split(".")[0]}" #name of the rhythm
                st.session_state.last_action = "user_setting" 
                st.session_state.is_uploaded_file = True
            except Exception as e:
                st.error(f"Error loading settings")
        else:
            st.error("Invalid settings file format.")



# Initialize session state variables if they don't exist
if 'previous_file' not in st.session_state:
    st.session_state.previous_file = None
if 'is_uploaded_file' not in st.session_state:
    st.session_state.is_uploaded_file = False
    
# File uploader in the sidebar
st.sidebar.markdown("### Import Rhythm Settings")
uploaded_file = st.sidebar.file_uploader(label="load", type=["txt", "mg"], label_visibility="collapsed")

#Check if a file is uploaded and if it’s a new file (compared to the previous upload)
if uploaded_file is not None and uploaded_file != st.session_state.previous_file:
    # Trigger the file uploader and load settings
    with st.spinner("loading..."):
        load_user_settings(uploaded_file)  # Assuming this function processes the file
        st.session_state.previous_file = uploaded_file  # Store the uploaded file
        st.session_state.is_uploaded_file = True
        st.sidebar.success("Settings loaded successfully!")


st.sidebar.divider()

# Rhythm variations
st.sidebar.markdown("### Improvisation Control")

# Create a slider for Rhythm Variation Control (improvisation factor)
improvisation_factor = st.sidebar.slider(
    label="Improvisation Factor",
    min_value=0.0, 
    max_value=1.0, 
    value=0.0,  # Default value
    step=0.01,  # Increment step for slider
    help="Adjust this slider to control how much variation is added to the rhythm. Higher values introduce more improvisation."
)

# Sliders for equalizer controls in the sidebar
st.sidebar.markdown("### Equalizer Controls")

# Low frequencies slider
low_gain = st.sidebar.slider(
    "Lows",
    min_value=-20.0, max_value=20.0, value=0.0, step=0.1,
    key="low_gain",
    help="Adjust the low frequencies (bass)"
)

# Mid frequencies slider
mid_gain = st.sidebar.slider(
    "Mids",
    min_value=-20.0, max_value=20.0, value=-3.70, step=0.1,
    key="mid_gain",
    help="Adjust the mid frequencies"
)

# High frequencies slider
high_gain = st.sidebar.slider(
    "Highs",
    min_value=-20.0, max_value=20.0, value=0.0, step=0.1,
    key="high_gain",
    help="Adjust the high frequencies (treble)"
)
        

# Layout for rhythm template selection
recorder_cols = st.columns(3)

with recorder_cols[0]:
    st.markdown("""
        <h4 style='text-align: left;'>
            RECORD CLAP <a href="https://www.linkedin.com/feed/update/urn:li:activity:7248643815907971072/" target="_blank" style="text-decoration: none;">👏</a>
        </h4>
    """, unsafe_allow_html=True)
with recorder_cols[1]:
        audio_bytes = audio_recorder(
        pause_threshold=1.0,
        sample_rate=16000,
        text="",
        recording_color="#ff0000",
        neutral_color="#174987",
        icon_size="3x",
    )


with recorder_cols[2]:
    # Check if audio_bytes is present and if it's a new recording
    if audio_bytes and (audio_bytes != st.session_state.audio_bytes):  
        st.session_state.audio_bytes = audio_bytes  # Store the audio bytes
        with st.spinner("Loading..."):
            time.sleep(1)
            try:
                load_setting_from_clap(audio_bytes)  # Always load audio settings if audio is recorded
                st.audio(data=audio_bytes)
            except Exception as e:
                st.warning("Something went wrong while analyzing audio, please try again.")
                print(e)


# Settings form
with st.form("Inputs"):
#   rhythm name
    st.markdown(
        """
        <div style="text-align: left; vertical-align: bottom; height: 100%; color: red; font-family: 'Cabin Sketch', cursive; font-size: 18px;">
                Rhythm: {rhythm_name}
        </div>
        """.format(rhythm_name=st.session_state.rhythm_name),
        unsafe_allow_html=True
    )
    try:
        cols = st.columns(6)
        
        with cols[0]:
            bpm = st.number_input("BPM (Beats Per Minute)", min_value=20, max_value=3000, value=st.session_state.bpm)
    
        with cols[1]:
            time_sign = st.text_input("Time signature (4/4)", value=st.session_state.time_sign)
            if not re.match(r'^\d+/\d+$', st.session_state.time_sign):
                st.error("Invalid time signature format. Please use 'X/Y' format, where X and Y are numbers.")
                    
        with cols[2]:
            strong_beats = st.text_input("Strong Beats (1, 3)", value=st.session_state.strong_beats)
            strong_beats_list = [int(sb) for sb in strong_beats.split(",") if sb.isdigit()]
            for s in strong_beats_list:
                if s > int(time_sign.split("/")[0]):
                    st.error(f"Value cannot exceed {int(st.session_state.time_sign.split('/')[0])}")
                    
        with cols[3]:
            suppress_beats = st.text_input("Suppress Beats (1, 3)", value=st.session_state.suppress_beats)
            suppress_beats_list = [int(sb) for sb in suppress_beats.split(",") if sb.isdigit()]
            for s in suppress_beats_list:
                if s in strong_beats_list:
                    st.error(f"Strong and suppress beats cannot overlap")
                if s > int(time_sign.split("/")[0]):
                    st.error(f"Value cannot exceed {int(st.session_state.time_sign.split('/')[0])}")
            suppress_beats_list = [s for s in suppress_beats_list if s <= int(time_sign.split("/")[0])]
                    
        with cols[4]:
            scale = st.selectbox("Scale", options=SCALES, index=SCALES.index(st.session_state.scale))
            
        with cols[5]:
            duration = st.number_input("Duration (in minutes)", min_value=1, max_value=30, value=st.session_state.duration)
            
                        

        generate_button = st.form_submit_button(label='Generate')
            

    except Exception as e:
        st.warning("Something went wrong while analyzing the audio, please try again.")

audio_cols = st.columns(2)

with audio_cols[0]:
    if generate_button:
        with st.spinner("Generating..."):
            time.sleep(1)
            audio_placeholder = st.empty()
            metro_audio, sr = generate_metronome(
                bpm=bpm,
                time_sign=time_sign,
                strong_beats=strong_beats_list,
                suppress_beats=suppress_beats_list,
                scale=scale,
                duration=duration,
                sr=SR,
                api_mode=True,
                temperature=improvisation_factor
            )
            onsets = get_ticks_position(metro_audio, sr, H=512)
            
            # applying effects
            metro_audio = apply_equalizer(metro_audio, sr, low_gain*10, mid_gain*10, high_gain*10)

            # Play audio
            audio_placeholder.audio(data=metro_audio, sample_rate=sr, start_time=0, autoplay=True)


st.sidebar.divider()
settings = f"""{bpm}\n{time_sign}\n{strong_beats}\n{suppress_beats}\n{scale}\n{duration}"""

# Display the download button after form submission
st.sidebar.download_button(
    label="Export Rhythm Settings",
    data=settings,
    file_name="custom_rhythm.mg",
#   mime="text/plain"
)
    

# Add a toggle button for language selection
if 'spanish_inst' not in st.session_state:
    st.session_state.spanish_inst = False
if 'english_inst' not in st.session_state:
    st.session_state.english_inst = False
if 'faqs' not in st.session_state:
    st.session_state.faqs = False
    
with st.expander("**INSTRUCTIONS**"):
    cols = st.columns(7)
    
    with cols[0]:
        if st.button("🇪🇸 cómo usar"):
            st.session_state.spanish_inst = True
            st.session_state.english_inst = False
            st.session_state.faqs = False
    with cols[1]:
        if st.button("🇬🇧 How to Use?"):
            st.session_state.english_inst = True
            st.session_state.spanish_inst = False
            st.session_state.faqs = False
    with cols[2]:
        if st.button("FAQ(s)"):
            st.session_state.english_inst = False
            st.session_state.spanish_inst = False
            st.session_state.faqs = True
        
    # Display Spanish instructions if the button is clicked
    if st.session_state.spanish_inst:
        st.write("""

        1. **Grabación de palmadas para generar un metrónomo:**
            - Haz clic en el icono 🎙️ para empezar a grabar. El icono se volverá rojo durante la grabación.
            - Para detener la grabación:
                - Haz clic de nuevo en el icono 🎙️ para apagarlo manualmente, o bien se detendrá automáticamente tras 1 segundo de silencio.
            - Deberias tocar las palmas de un ciclo de ritmo y acabar con la primera palma del ciclo siguiente, [demo](https://www.linkedin.com/feed/update/urn:li:activity:7248643815907971072/).
                - Ejemplo 1: para 4/4, tocas como 1,2,3,4 y 1
                - Ejemplo 2: para 6/4, tocas como **1**,2,3,**4**,5,6 y **1**
                - En caso de que el ritmo generado no sea preciso, puedes tocar las palmas mas despacio, y ajustar los BPM luego.
            - Siéntete libre de utilizar palmadas fuertes y suaves para crear acentos rítmicos.  
            - *Nota:* Puede que necesites varios intentos para familiarizarte con la interfaz, pero pronto la dominarás.

        2. **Personalizar la configuración del metrónomo:**
            - Puedes ajustar la configuración del metrónomo según tus preferencias en cualquier momento.

        3. **¡Disfruta de tu práctica!**
            - Sigue explorando y ¡feliz aprendizaje!

        4. **Ponte en contacto**
            - Si necesitas ayuda, no dudes en escribirme a [LinkedIn](https://www.linkedin.com/in/ankit-anand-1893a21b5/)

        ---
        **Apoya Mi Trabajo:**

        Si encuentras útil esta herramienta y te gustaría apoyar futuras mejoras, considera invitarme un café.
        """)
        
        if st.button("☕ Invítame un Café"):
            st.info("**UPI**: ankit0.anand0@oksbi or [Buy me a coffee](https://buymeacoffee.com/ankitanand) \n\n ¡Gracias por tu apoyo! 😊 Tu amabilidad mantiene este proyecto en marcha.")
            
    # Display English instructions if the button is clicked
    elif st.session_state.english_inst:
        st.write("""

        1. **Recording Claps to Generate a Metronome:**
            - Click on the 🎙️ icon to start recording. The icon will turn red while recording.
            - To stop recording:
                - Either click the 🎙️ icon again to turn it off manually, or it will automatically stop after 1 second of silence.
            - Make sure that you clap 1 rhythm cycle along with the **first hit** of the next rhythm cycle, [demo](https://www.linkedin.com/feed/update/urn:li:activity:7248643815907971072/).
                - Example 1: for 4/4, you clap at 1,2,3,4 and **1**
                - Example 2: for 6/4, you clap at **1**,2,3,**4**,5,6 and **1**
            - In case the generated rhythm is not accurate, you can try clapping slow, then later on adjust BPM.
            - Feel free to use **loud** and **soft claps** to create rhythmic accents.
            - *Note:* It may take a few tries to get comfortable with the interface, but you’ll master it soon!

        2. **Customizing Metronome Settings:**
            - You can adjust the metronome settings to match your preferences at any time.

        3. **Enjoy your Practice!**
            - Keep exploring, and happy learning!

        4. **Get in touch**
            - For any assistance, feel free to ping me on [LinkedIn](https://www.linkedin.com/in/ankit-anand-1893a21b5/)

        ---
        **Support My Work:**

        If you find this tool helpful and would like to support future improvements, consider buying me a coffee!
        """)
        
        if st.button("☕ Buy Me a Coffee"):
            st.info("**UPI**: ankit0.anand0@oksbi or [Buy me a coffee](https://buymeacoffee.com/ankitanand) \n\n Thank you for your support! 😊 Your kindness keeps this project going strong.")
        
    elif st.session_state.faqs:
        st.markdown("""
            #### Frequently Asked Questions (FAQs)
            
            ---
            ##### Q. **How do I use this app?**
            1. Click on the "Instructions" at the bottom of the page.
            2. Select your preferred language (🇪🇸 or 🇬🇧).
            3. You can also check this [demo video](https://www.linkedin.com/feed/update/urn:li:activity:7248643815907971072/).

            ---
            ##### Q. **Is the app free to use?**
            Yes, this app is completely free to use with all its features available to everyone.

            ---
            ##### Q. **Can I use this app on mobile?**
            Yes, the app is fully responsive and works on both desktop and mobile devices.
        
            ---
            ##### Q. **I am unable to generate the correct rhythm with my clap.**
            1. After recording your clap, listen to the playback to check for any issues.
            2. If the first beat is missed in the recording, give a small break after pressing the record button.
            3. Try clapping at a slower BPM to ensure you are clapping in sync with the rhythm.
        
            ---
            ##### Q. **After I hit generate, the audio file loads but it says error.**
            It could be due to a slow internet connection. Try reducing the duration from 3 minutes to 1 minute.
        
            ---
            ##### Q. **How can I save my settings?**
            1. Click on the > icon on the top-left of the site to open the navigation bar.
            2. Scroll down and click on "Export Rhythm Settings".
            3. The settings will be downloaded as a file with a `.mg` extension.
        
            ---
            ##### Q. **How can I load my custom saved settings?**
            1. Click on the > icon on the top-left of the site to open the navigation bar.
            2. In the "Import Rhythm Settings" section, click on "Browse file".
            3. Select the `.mg` file you previously saved. The settings will be applied automatically, and you can then hit generate.
        
            ---
            ##### Q. **Can we change the sound of the metronome?**
            1. At the moment, you can only perform EQ adjustments. Access the EQ settings by clicking on the > icon on the top-left.

            ---
            ##### Q. **How can I support the developer?**
            If you find this app helpful, you can support the developer in the following ways:
            1. Share the app with friends and on social media to help spread the word.
            2. Provide feedback or suggestions through the [feedback form](https://forms.gle/pMCzaQUGfeGdFvK79).
            3. You can also consider donating via [GPAY](ankit0.anand0@oksbi) or [Buy Me a Coffee](https://buymeacoffee.com/ankitanand).

            ---
            ##### Q. **What if I encounter a problem?**
            1. You can submit issues or feedback via the [feedback form](https://forms.gle/pMCzaQUGfeGdFvK79) located in the footer of the website.
            2. Alternatively, you can reach us via email: themeluron@gmail.com
            
        """)
        
        


st.markdown(
    """
    <style>
    .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: transparent;
            color: #808080;
            text-align: center;
            font-size: medium;
            padding: 10px;
    }
    </style>
    <div class="footer">
            © 2024 Meluron | Made with ❤️ by <a href="https://www.linkedin.com/in/ankit-anand-1893a21b5/" target="_blank" style="color: #808080;">Ankit Anand</a> | <a href="https://forms.gle/pMCzaQUGfeGdFvK79" target="_blank" style="color: #808080;">Feedback Form</a>
    </div>""",
    unsafe_allow_html=True
)
