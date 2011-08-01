import json
import os
import subprocess

import redis as redislib
from flask import Flask, Response, request, render_template

import settings


app = Flask(__name__)
deploy = os.path.join(settings.ZAMBONI_DIR, 'scripts/update/update.py')

os.environ['PYTHONUNBUFFERED'] = 'go time'


def run(task, output):
    proc = subprocess.Popen('commander %s %s' % (deploy, task),
                            shell=True, stdout=output, stderr=output)
    proc.communicate()


def do_update(zamboni_tag, vendor_tag, who):
    def pub(event):
        redis = redislib.Redis(**settings.REDIS_BACKENDS['master'])
        d = {'event': event, 'zamboni': zamboni_tag, 'vendor': vendor_tag,
             'who': who}
        redis.publish('deploy.amo', json.dumps(d))

    pub('BEGIN')
    yield 'Updating! zamboni: %s -- vendor: %s<br>' % (zamboni_tag, vendor_tag)

    output = open(os.path.join(settings.OUTPUT_DIR, zamboni_tag), 'a')
    run('pre_update:%s,%s' % (zamboni_tag, vendor_tag), output)
    pub('PUSH')
    yield 'We have the new code!<br>'

    run('update', output)
    pub('UPDATE')
    yield "Code has been updated locally!<br>"

    run('deploy', output)
    pub('DONE')
    yield 'All done!'


@app.route("/")
def index():
    if request.method == 'POST':
        post = request.form
        assert sorted(post.keys()) == ['password', 'vendor', 'who', 'zamboni']
        assert post['password'] == settings.PASSWORD
        return Response(
                do_update(post['zamboni'], post['vendor'], post['who']),
                direct_passthrough=True, mimetype='text/plain')

    return render_template("index.html")
