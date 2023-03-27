
import openai
import os
import sounddevice as sd
import soundfile as sf
import numpy as np
import time
from pydub import AudioSegment
import re

time.sleep(1)

openai.api_key = "<OPEN AI KEY HERE>"

total_messages = [ 
          {"role": "system", "content": 'Keep your messages short and snappy 200 characters max this is vital for the system to function. We have connected GPT 3.5 and setup speech synthesis and voice recognition. The user is talking to you in real time.'},
]

def get_time():
    return time.time()

speech_off = 0
recording = False

filename = "tmp_audio_in/" + str(get_time()) + "-speech.wav"
samplerate = 44100
channels = 1

_filename = ""
_filename_mp3 = ""

sf_obj = sf.SoundFile(filename, 'w', samplerate=samplerate, channels=channels)

def split_sentences(sentence):

    max_length = 240
    sentences = []
    current_sentence = ""
    for word in sentence.split():
        if len(current_sentence) + len(word) + 1 <= max_length:
            current_sentence += word + " "
        else:
            sentences.append(current_sentence.strip())
            current_sentence = word + " "
    if current_sentence:
        sentences.append(current_sentence.strip())

    return sentences

def print_sound(indata, outdata, frames, time, status):

    global sf_obj
    global speech_off
    global recording

    global _filename
    global _filename_mp3

    speech_volume = np.linalg.norm(indata)*10

    if(speech_volume > 40):

        speech_off = 0

        if(recording != True):

            print("> Start Recording")

            _filename = "tmp_audio_in/" + str(get_time()) + "-speech.wav"
            _filename_mp3 = "tmp_audio_in/" + str(get_time()) + "-speech.mp3"
            sf_obj = sf.SoundFile(_filename, 'w', samplerate=samplerate, channels=channels)

        recording = True

    else:

        if recording:

            if speech_off > 30:

                print("> Message sent to ChatGPT")

                sf_obj.close()

                AudioSegment.from_wav(_filename).export(_filename_mp3, format="mp3", codec="libmp3lame")

                audio_file= open(_filename_mp3, "rb")
                transcript = openai.Audio.translate("whisper-1", audio_file)

                print("Text Recognized: " + str(transcript["text"]))

                sd.sleep(100)

                total_messages.append({"role": "user", "content": transcript["text"]})

                response = openai.ChatCompletion.create(

                    model="gpt-3.5-turbo",
                    messages=total_messages
                    
                )
                
                s = re.sub(r'\W+', ' ', response['choices'][0]['message']['content'].replace("\"", "").replace("'", ""))

                _sentences = split_sentences(s)

                for _sen in _sentences:

                    # change this line for anything other than MacOS suport
                    
                    os.system("say " + s)

                sd.sleep(1000)

                # stop recording
                speech_off = 0
                recording = False
                
            else:
                speech_off += 1
                # keep recording
        else:
            speech_off += 1
            # keep recording

    if(recording):
        sf_obj.write(indata)



with sd.Stream(callback=print_sound, samplerate=44100, channels=channels, blocksize=4096):
    sd.sleep(1000000)





