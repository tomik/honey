
from __future__ import with_statement
import fabric.api as fab
from fabric.contrib.console import confirm

def run():
    """Run the development server."""
    from honey import app
    app.debug = True
    app.run()

def compile():
    """Compile .less and .coffee files and make sure that links are up to date."""
    fab.local("lessc -c bootstrap/less/bootstrap.less > bootstrap/less/bootstrap.css")
    for coffee in ["honey", "hex", "go"]:
        fab.local("coffee -c honey/static/js/%s.coffee > honey/static/js/%s.js" % (coffee, coffee))
    # setup links
    fab.local("cd honey/static/css && ln -fs ../../../bootstrap/less/bootstrap.css")
    fab.local("cd honey/static/img && ln -fs ../../../bootstrap/img/glyphicons-halflings.png")
    fab.local("cd honey/static/img && ln -fs ../../../bootstrap/img/glyphicons-halflings-white.png")
    fab.local("cd honey/static/js && ln -fs ../../../bootstrap/js/bootstrap-button.js")

fab.env.hosts = ['tomik@zene.sk:2222']

def pack():
    # create a new source distribution as tarball
    fab.local("python setup.py sdist --formats=gztar", capture=False)

def deploy():
    DEPLOY_DIR = "~/public/www/senseicrowd"
    TMP_DIR = "~/tmp/honey-deploy"
    # prepare tmp dir
    fab.run("rm -rf %s 2>/dev/null" % TMP_DIR)
    fab.run("mkdir %s" % TMP_DIR)
    # upload
    dist = fab.local("python setup.py --fullname", capture=True).strip()
    fab.put("dist/%s.tar.gz" % dist, "%s/honey.tar.gz" % TMP_DIR)
    # backup current deploy
    fab.run("if [ ! -d %s.bak ]; then mv %s %s/senseicrowd.bak; fi" % (DEPLOY_DIR, DEPLOY_DIR, TMP_DIR))
    fab.run("rm -rf %s 2>/dev/null" % DEPLOY_DIR)
    fab.run("mkdir %s" % DEPLOY_DIR)
    # apache needs to write log files
    fab.run("chmod o+w %s" % DEPLOY_DIR)
    # copy the virtual env
    fab.run("cp -r %s/senseicrowd.bak/env %s" % (TMP_DIR, DEPLOY_DIR))
    # install the package
    with fab.cd(DEPLOY_DIR):
        fab.run("tar xzf %s/honey.tar.gz" % TMP_DIR)
        with fab.cd(dist):
            fab.run("%s/env/bin/python setup.py develop" % DEPLOY_DIR)
    # update apache stuff
    fab.local("tar -czf deploy.tgz deploy")
    fab.put("deploy.tgz", "%s/deploy.tgz" % TMP_DIR)
    with fab.cd(TMP_DIR):
        fab.run("tar xzf deploy.tgz")
        with fab.cd("deploy"):
            # update_fcgi works with .htaccess
            fab.run("mv htaccess .htaccess")
            fab.run("python update_fcgi.py")
            fab.run("mv .htaccess %s" % DEPLOY_DIR)
            fab.run("mv *fcgi* %s" % DEPLOY_DIR)

def clear_db():
    """
    Creates vanilla db setup.

    This includes:
    - no games
    - no comments
    - users admin, tomik and slpwnd
    """

    from honey import db
    from honey.core import app

    db.reset()
    # setup users
    tp_hash = 'sha1$Pq4yk8OM$3081feca50438e33cfd3bacef83cb47bdb6cbb93'
    db.create_user("admin", "admin@senseicrowd.com", tp_hash)
    db.create_user("tomik", "tomas.kozelek@gmail.com", tp_hash)
    db.create_user("slpwnd", "tomas.kozelek@gmail.com", tp_hash)

def setup_fixtures():
    """
    Setup simple fixtures.

    Creates couple of games, users, comments and variants for manual testing.
    Requires db server to be running.
    """
    import urllib
    import socket
    import random

    from werkzeug import generate_password_hash

    from honey import db
    from honey.core import app

    # what if lg is down
    socket.setdefaulttimeout(5)
    # clear the database
    db.reset()
    # setup users
    users = ["user1", "user2", "user3"]
    for user in users:
        db.create_user(user, "%s@gmail.com" % user, generate_password_hash(user))
    # setup lg games
    #hex_lg_games = ["1401966", "1401967", "1401968", "1401969", "1401970", "1401971", "1401972", "1401973", "1401974", "1401975", "1401976", "1401977", "1401978", "1401979", "1401980", "1401981", "1401982", "1401983", "1401984", "1401985", "1401986", "1401987", "1401988", "1401989", "1401990", "1401991", "1401992", "1401993", "1401994", "1401995", "1401996", "1401997", "1401998", "1401999", "1402000", "1402001"][:3]
    go_lg_games = ["1384554", "1384555", "1384556", "1384557", "1384558", "1384559", "1384560", "1384561", "1384562", "1384563", "1384564", "1384565", "1384566", "1384567", "1384568", "1384569", "1384570", "1384571", "1384572", "1384573", "1384574", "1384575", "1384576", "1384577", "1384578", "1384579", "1384580", "1384581", "1384582", "1384583", "1384584", "1384585", "1384586", "1384587", "1384588", "1384567"]
    #for id in hex_lg_games:
        #print("Creating lg game %s" % id)
        #sgf = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.hsgf" % id).read()
        #user_id = random.choice(list(db.get_users()))["_id"]
        #game, err = db.create_game(user_id, sgf)
    for id in go_lg_games:
        print("Creating lg game %s" % id)
        sgf = urllib.urlopen("http://www.littlegolem.net/servlet/sgf/%s/game.sgf" % id).read()
        user_id = random.choice(list(db.get_users()))["_id"]
        game, err = db.create_game(user_id, sgf)

