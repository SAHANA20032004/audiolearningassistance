import os
import threading
import queue
import PyPDF2
import pyttsx3
import speech_recognition as sr
from fpdf import FPDF
import streamlit as st
import tempfile

# Initialize text-to-speech engine
speak = pyttsx3.init()
speak_queue = queue.Queue()
stop_reading_flag = threading.Event()
resume_reading_flag = threading.Event()


# Function to transcribe voice input to text
def listen_and_transcribe():
    recognizer = sr.Recognizer()
    sentences = []
    st.write("Start speaking. Say 'stop' to finish.")

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            st.write("Listening for input...")
            try:
                audio = recognizer.listen(source)
                command = recognizer.recognize_google(audio).lower()
                st.write(f"Recognized: {command}")

                if "stop" in command:
                    st.write("Stop command received.")
                    break

                sentences.append(command)
            except sr.UnknownValueError:
                st.write("Could not understand. Please try again.")
            except sr.RequestError as e:
                st.write(f"Speech recognition error: {e}")
                break

    return sentences


# Function to save sentences to PDF
def save_to_pdf(sentences, pdf_filename):
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for sentence in sentences:
            pdf.multi_cell(0, 10, sentence)

        pdf.output(pdf_filename)
        st.write(f"PDF saved as {pdf_filename}")
    except Exception as e:
        st.write(f"Error saving PDF: {e}")


# Function to process voice commands (stop or resume)
def handle_voice_commands():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                st.write("Listening for commands: say 'stop' or 'resume'.")
                audio = recognizer.listen(source)
                command = recognizer.recognize_google(audio).lower()

                if "stop" in command:
                    st.write("Pausing reading...")
                    stop_reading_flag.set()
                elif "resume" in command:
                    st.write("Resuming reading...")
                    stop_reading_flag.clear()
                    resume_reading_flag.set()

            except sr.UnknownValueError:
                st.write("Could not understand command. Please try again.")
            except sr.RequestError as e:
                st.write(f"Speech recognition error: {e}")
                break


# Function to read a PDF aloud with pause and resume functionality
def read_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as pdf_file:
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            sentences = []

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    sentences.extend(text.split('. '))

        def read_text():
            for idx, sentence in enumerate(sentences):
                if stop_reading_flag.is_set():
                    resume_reading_flag.wait()  # Wait until resume is triggered
                st.write(f"Reading: {sentence.strip()}")
                speak.say(sentence)
                speak.runAndWait()

        # Start the text-to-speech in a separate thread
        tts_thread = threading.Thread(target=read_text)
        tts_thread.start()

        # Start listening for commands in a separate thread
        command_thread = threading.Thread(target=handle_voice_commands)
        command_thread.start()

        tts_thread.join()
        command_thread.join()

    except FileNotFoundError:
        st.write("The specified PDF file was not found.")
    except Exception as e:
        st.write(f"Error reading PDF: {e}")


# Streamlit app
def main():
    st.title("AI Learning Assistant for Visually Impaired")

    st.sidebar.title("Menu")
    choice = st.sidebar.radio("Choose an option:", ["Convert Voice to PDF", "Read Existing PDF", "Exit"])

    if choice == "Convert Voice to PDF":
        st.header("Convert Voice to PDF")
        pdf_name = st.text_input("Enter the name for the PDF file (e.g., output.pdf):", "output.pdf")

        if st.button("Start Voice Input"):
            sentences = listen_and_transcribe()
            if sentences:
                save_to_pdf(sentences, pdf_name)

                st.write("Do you want to read the PDF now?")
                if st.button("Read PDF"):
                    read_pdf(pdf_name)

    elif choice == "Read Existing PDF":
        st.header("Read Existing PDF")
        uploaded_file = st.file_uploader("Upload a PDF file:", type="pdf")

        if uploaded_file:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                temp_file.write(uploaded_file.read())
                temp_pdf_path = temp_file.name

            if st.button("Read PDF"):
                read_pdf(temp_pdf_path)

    elif choice == "Exit":
        st.write("Thank you for using the AI Learning Assistant!")


if __name__ == "__main__":
    main()
