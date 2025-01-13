#!/usr/bin/env python3

from absl import app
from absl import flags
from absl import logging
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import json
import os
import requests
from io import BytesIO

FLAGS = flags.FLAGS
flags.DEFINE_string('name', '', 'Name filter (prefix)')
flags.DEFINE_string('id', '', 'Id filter (prefix)')
flags.DEFINE_bool('play', False, 'Play sample of first matching voice')


# Voice spec fields
# - name
# - id
# - settings
#   - stability (0..1)
#   - similarity (0..1)
#   - style (0..1)
def make_voice(name, id):
    settings = {'stability': 1.0, 'similarity': 1.0, 'style': 0.0}
    return {'name': name, 'id': id, 'settings': settings}


def load_voice(path):
    if not os.path.isfile(path):
        raise FileNotFoundError(f"The voice file '{path}' does not exist")
    with open(path, 'r') as f:
        return json.load(f)


def get_voices(name_filter, id_filter):
    # Install api key into environment first.
    client = ElevenLabs()
    response = client.voices.get_all()

    voices = []
    for voice in response.voices:
        if name_filter != "" and not voice.name.startswith(name_filter):
            continue
        if id_filter != "" and not voice.voice_id.startswith(id_filter):
            continue
        voices.append(voice)
    return voices


def main(argv):
    voices = get_voices(FLAGS.name, FLAGS.id)
    for voice in voices:
        print(json.dumps(make_voice(voice.name, voice.voice_id)))

    if FLAGS.play and len(voices) > 0:
        print(f"Playing {voices[0].name}")
        first_preview_url = voices[0].preview_url
        print(f"URL: {first_preview_url}")
        response = requests.get(first_preview_url)
        audio_data = BytesIO(response.content)
        play(audio_data)


if __name__ == '__main__':
    logging.set_verbosity(logging.WARNING)
    app.run(main)
