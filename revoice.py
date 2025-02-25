#!/usr/bin/env python3

from absl import app
from absl import flags
from absl import logging
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from elevenlabs import VoiceSettings
import json
import os
import pathlib
import requests
import subprocess
from io import BytesIO
import voices

FLAGS = flags.FLAGS
flags.DEFINE_string('i', '', 'Input directory or file')
flags.DEFINE_string('o', '', 'Output directory')
flags.DEFINE_integer('n', 1, 'Count (0 = all)')
flags.DEFINE_string('voice', '', 'Target voice config file')
flags.DEFINE_boolean('dryrun', True, "Don't revoice any files")
flags.DEFINE_boolean('curl', False,
                     "Use curl to call revoice service (instead of api)")

# Retrieve the API key
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
if not ELEVENLABS_API_KEY:
    raise ValueError("ELEVENLABS_API_KEY environment variable not found. "
                     "Please set the API key in your environment variables.")

client11 = ElevenLabs(api_key=ELEVENLABS_API_KEY)


# A curl-based version for when the api wasn't working.
def revoice_curl(input_file_path, output_file_path, voice):
    subprocess.run(
        f"./revoice.curl {voice['id']} {input_file_path} {output_file_path}",
        shell=True,
        check=True)


def revoice_api(input_file_path, output_file_path, voice):
    with open(input_file_path, "rb") as input_audio_file:
        response = client11.speech_to_speech.convert(
            audio=(input_file_path.name, input_audio_file.read(), 'audio/mp4'),
            voice_id=voice['id'],
            output_format="mp3_44100_192",
            model_id="eleven_english_sts_v2",
            # model_id="eleven_multilingual_sts_v2",
            voice_settings=VoiceSettings(
                stability=voice['settings']['stability'],
                similarity_boost=voice['settings']['similarity'],
                style=voice['settings']['style'],
                use_speaker_boost=False,
            ).json(),
        )

    if not response:
        print("Request failed or timed out")
        return

    with open(output_file_path, 'wb') as f:
        for chunk in response:
            if chunk:
                f.write(chunk)


def revoiceFile(input_file_path, output_file_path, voice):
    print(
        f"revoicing {input_file_path} to {output_file_path} with {voice['name']}"
    )

    if not os.path.isfile(input_file_path):
        raise FileNotFoundError(
            f"The input file does not exist: {input_file_path}")
    if input_file_path.suffix not in ['.m4a', '.mp3']:
        print(f"Skipping non-audio file {input_file_path}")
        return

    if FLAGS.dryrun:
        print('Dry run -- not revoicing')
        return

    if FLAGS.curl:
        revoice_curl(input_file_path, output_file_path, voice)
    else:
        revoice_api(input_file_path, output_file_path, voice)


def revoiceDirectory(input_dir, output_dir, voice):
    input_files = input_dir.glob('*')
    max_count = FLAGS.n
    if max_count == 0:
        max_count = 1000000
    count = 0
    for input_file in input_files:
        if count == max_count:
            print(f"Hit max revoicing count {count}. Stopping.")
            return
        stem = input_file.stem
        output_file = output_dir / f"{stem}.mp3"
        if output_file.exists():
            print(f'{input_file} already revoiced')
        else:
            revoiceFile(input_file, output_file, voice)
            count += 1


def main(argv):
    print('Input:', FLAGS.i)
    print('Output:', FLAGS.o)
    print('Voice:', FLAGS.voice)

    input_dir = pathlib.Path(FLAGS.i)
    output_dir = pathlib.Path(FLAGS.o)
    voice = voices.load_voice(FLAGS.voice)

    if os.path.isdir(input_dir):
        revoiceDirectory(input_dir, output_dir, voice)
    else:
        revoice(input_dir, output_dir, voice)


if __name__ == '__main__':
    logging.set_verbosity(logging.WARNING)
    app.run(main)
