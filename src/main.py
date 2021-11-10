"""A web-based YouTube Downloader built using Flask"""

import io
import os
import flask
import pytube
import requests
import humanize

app = flask.Flask(__name__) # pylint: disable=invalid-name

def generate_name(title):
    """Generates a filename for a YouTube video title."""
    title = title.replace('ä', 'ae').replace('ü', 'ue').replace('ö', 'oe')
    name = ''

    for char in title:
        if char in ' -()[]{}§$%&`´#~,;/\\<>:"|?*@.!?':
            name += '_'
        else:
            name += char

    return name.lower()

@app.route('/', methods=['GET'])
def index():
    """Main page"""
    if not flask.request.args.get('v'):
        return flask.render_template('index.html')

    video_id = flask.request.args.get('v')
    video_url = f'https://www.youtube.com/watch?v={video_id}'
    try:
        video = pytube.YouTube(video_url)
    except:
        return flask.render_template('index.html', message='There was an error while trying to load the video, sorry.')

    if flask.request.args.get('cc'):
        return video.captions.get_by_language_code(flask.request.args.get('cc')).xml_captions

    avaiable_streams = video.streams.filter(file_extension='mp4')
    filtered_streams = sorted(avaiable_streams, key=lambda s: s.filesize_approx, reverse=True)

    if flask.request.args.get('dl'):
        best_video = video.streams.get_by_itag(int(flask.request.args.get('dl')))
        video_data = io.BytesIO(requests.get(best_video.url).content)

        def generate():
            for row in video_data:
                yield row

        resp = flask.Response(generate(), mimetype='video/mp4', direct_passthrough=True)
        resp.headers['Content-Disposition'] = 'attachment'
        return resp


    streams = []

    for count, stream in enumerate(filtered_streams):
        audio_only = not 'video' in stream.mime_type

        if not stream.includes_audio_track and count: # no audio AND not highest resolution
            continue

        emoji = ''

        if not stream.includes_audio_track:
            emoji = ' 🔇'

        streams.append({
            'url': stream.url,
            'quality': stream.abr if audio_only else (stream.resolution + str(stream.fps)),
            'ext': stream.mime_type.split('/')[1],
            'size': humanize.naturalsize(stream.filesize_approx),
            'type': '🎵' if audio_only else '🎞️',
            'emoji': emoji,
            'itag': stream.itag
        })

    return flask.render_template(
        'download.html',
        url=video_url,
        title=video.title,
        author=video.author,
        views=humanize.intword(video.views),
        image=video.thumbnail_url,
        streams=streams
    )

@app.route('/pro')
def pro():
    """Pro Version Info-Page"""
    return flask.render_template('pro.html')

@app.route('/source')
def source():
    """Source code of the project"""
    files = os.listdir(os.path.dirname(__file__))
    file_list = []

    for f in files:
        f = os.path.join(os.path.dirname(__file__), f)
        if os.path.isfile(f):
            file_list.append({
                'name': f.split('src/')[1],
                'code': open(f).read().replace('\n', '\n\n')
            })
    
    print(file_list)

    return flask.render_template('source.html', code=open(__file__).read(), files=file_list)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7171, debug=True)
