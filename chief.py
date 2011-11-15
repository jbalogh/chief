import json
import os
import re
import subprocess

import redis as redislib
from flask import Flask, Response, abort, request, render_template

import settings
from forms import DeployForm


app = Flask(__name__)

os.environ['PYTHONUNBUFFERED'] = 'go time'


def do_update(app_name, app_settings, webapp_ref, who):
    deploy = app_settings['script']
    log_dir = os.path.join(settings.OUTPUT_DIR, app_name)
    if not os.path.isdir(log_dir):
        os.mkdir(log_dir)

    def run(task, output):
        subprocess.check_call(['commander', deploy, task],
                              stdout=output, stderr=output)

    def pub(event):
        redis = redislib.Redis(**settings.REDIS_BACKENDS['master'])
        d = {'event': event, 'ref': webapp_ref, 'who': who}
        redis.publish(app_settings['pubsub_channel'], json.dumps(d))

    try:
        pub('BEGIN')
        yield 'Updating! revision: %s\n' % webapp_ref

        log_file = os.path.join(log_dir,
                                re.sub('[^A-z0-9]', '.', webapp_ref))
        output = open(log_file, 'a')
        run('pre_update:%s' % webapp_ref, output)
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

    form = DeployForm(request.form)
    if request.method == 'POST' and form.validate():
        if form.password.data != app_settings['password']:
            abort(403)
        return Response(do_update(webapp, app_settings,
                                  form.ref.data, form.who.data),
                        direct_passthrough=True,
                        mimetype='text/plain')

    return render_template("index.html", app_name=webapp, form=form)
