import os
import subprocess
import urlparse

import settings

deploy = os.path.join(settings.ZAMBONI_DIR, 'scripts/deploy.py')


def run(task, output):
    proc = subprocess.Popen('commander %s %s' % (deploy, task),
                            shell=True, stdout=output, stderr=output)
    proc.communicate()


def do_update(zamboni_tag, vendor_tag):
    yield 'Updating! zamboni: %s -- vendor: %s<br>' % (zamboni_tag, vendor_tag)
    output = open(os.path.join(settings.OUTPUT_DIR, zamboni_tag), 'a')
    run('start_update:%s,%s' % (zamboni_tag, vendor_tag), output)
    yield 'We have the new code!<br>'
    run('update_amo', output)
    yield 'All done!'


def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    if env['REQUEST_METHOD'] == 'POST':
        post = dict(urlparse.parse_qsl(env['wsgi.input'].read()))
        assert sorted(post.keys()) == ['password', 'vendor', 'zamboni']
        assert post['password'] == settings.PASSWORD
        return do_update(post['zamboni'], post['vendor'])

    return html


# So fancy.
html = """
<form method="post" action="">
  <input name="zamboni" placeholder="zamboni tag">
  <input name="vendor" placeholder="vendor tag">
  <input name="password" type="password" placeholder="secret">
  <button>ONWARD AND UPWARD</button>
</form>
"""
