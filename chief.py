import json
import os
import re
import subprocess

import redis as redislib
from flask import Flask, Response, abort, request, render_template

import settings


app = Flask(__name__)

os.environ['PYTHONUNBUFFERED'] = 'go time'


def do_update(app_name, app_settings, webapp_tag, who):
    deploy = os.path.join(app_settings['dir'], 'scripts/update/update.py')
    log_dir = os.path.join(settings.OUTPUT_DIR, app_name)
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    def run(task, output):
        subprocess.check_call('commander %s %s' % (deploy, task),
                              shell=True, stdout=output, stderr=output)

    def pub(event):
        redis = redislib.Redis(**settings.REDIS_BACKENDS['master'])
        d = {'event': event, 'zamboni': webapp_tag, 'who': who}
        redis.publish(app_settings['pubsub_channel'], json.dumps(d))

    try:
        pub('BEGIN')
        yield 'Updating! zamboni: %s\n' % webapp_tag

        log_file = os.path.join(log_dir,
                                re.sub('[^A-z0-9]', '.', webapp_tag))
        output = open(log_file, 'a')
        run('pre_update:%s' % webapp_tag, output)
        pub('PUSH')
        yield 'We have the new code!\n'

        run('update', output)
        pub('UPDATE')
        yield "Code has been updated locally!\n"

        run('deploy', output)
        pub('DONE')
        yield 'All done!'
    except:
        pub('FAIL')
        raise


@app.route("/<webapp>", methods=['GET', 'POST'])
def index(webapp):
    if webapp not in settings.WEBAPPS.keys():
        abort(404)
    else:
        app_settings = settings.WEBAPPS[webapp]

    if request.method == 'POST':
        post = request.form
        assert sorted(post.keys()) == ['password', 'who', 'tag']
        assert post['password'] == app_settings['password']
        return Response(do_update(webapp, app_settings,
                                  post['tag'], post['who']),
                        direct_passthrough=True,
                        mimetype='text/plain')

    return render_template("index.html")
