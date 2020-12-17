# import native Python packages

# import third party packages
from flask import Blueprint, render_template


timecapsule_bp = Blueprint('timecapsule', __name__, url_prefix='')


@timecapsule_bp.route('/timecapsule')
def timecapsule():
    return render_template('timecapsule/timecapsule.html')


@timecapsule_bp.route('/timecapsule/index')
def index():
    return render_template('timecapsule/index.html')


@timecapsule_bp.route('/timecapsule/apargument')
def apargument():
    return render_template('timecapsule/apargument.html')


@timecapsule_bp.route('/timecapsule/apargumentscan')
def apargumentscan():
    return render_template('timecapsule/apargumentscan.html')


@timecapsule_bp.route('/timecapsule/apenglish12')
def apenglish12():
    return render_template('timecapsule/apenglish12.html')


@timecapsule_bp.route('/timecapsule/apps')
def apps():
    return render_template('timecapsule/apps.html')


@timecapsule_bp.route('/timecapsule/apscholard')
def apscholard():
    return render_template('timecapsule/apscholard.html')


@timecapsule_bp.route('/timecapsule/bowlingpic')
def bowlingpic():
    return render_template('timecapsule/bowlingpic.html')


@timecapsule_bp.route('/timecapsule/calculus')
def calculus():
    return render_template('timecapsule/calculus.html')


@timecapsule_bp.route('/timecapsule/diploma')
def diploma():
    return render_template('timecapsule/diploma.html')


@timecapsule_bp.route('/timecapsule/ecsp')
def ecsp():
    return render_template('timecapsule/ecsp.html')


@timecapsule_bp.route('/timecapsule/english10')
def english10():
    return render_template('timecapsule/english10.html')


@timecapsule_bp.route('/timecapsule/gpa')
def gpa():
    return render_template('timecapsule/gpa.html')


@timecapsule_bp.route('/timecapsule/javaprojects')
def javaprojects():
    return render_template('timecapsule/javaprojects.html')


@timecapsule_bp.route('/timecapsule/jgs')
def jgs():
    return render_template('timecapsule/jgs.html')


@timecapsule_bp.route('/timecapsule/mathanalysis')
def mathanalysis():
    return render_template('timecapsule/mathanalysis.html')


@timecapsule_bp.route('/timecapsule/mtgp')
def mtgp():
    return render_template('timecapsule/michaeltarpeygraduationportal.html')


@timecapsule_bp.route('/timecapsule/mths')
def mths():
    return render_template('timecapsule/michaeltarpeyhs.html')


@timecapsule_bp.route('/timecapsule/momanddad')
def momanddad():
    return render_template('timecapsule/momanddad.html')


@timecapsule_bp.route('/timecapsule/myindex')
def myindex():
    return render_template('timecapsule/myindex.html')


@timecapsule_bp.route('/timecapsule/oops')
def oops():
    return render_template('timecapsule/oops.html')


@timecapsule_bp.route('/timecapsule/physics')
def physics():
    return render_template('timecapsule/physics.html')


@timecapsule_bp.route('/timecapsule/portfolio07')
def portfolio07():
    return render_template('timecapsule/portfolio07.html')


@timecapsule_bp.route('/timecapsule/portfolio09')
def portfolio09():
    return render_template('timecapsule/portfolio09.html')


@timecapsule_bp.route('/timecapsule/portfolio10')
def portfolio10():
    return render_template('timecapsule/portfolio10.html')


@timecapsule_bp.route('/timecapsule/presidentgold')
def presidentgold():
    return render_template('timecapsule/presidentgold.html')


@timecapsule_bp.route('/timecapsule/projects')
def projects():
    return render_template('timecapsule/projects.html')


@timecapsule_bp.route('/timecapsule/uconndiploma')
def uconndiploma():
    return render_template('timecapsule/uconndiploma.html')


@timecapsule_bp.route('/timecapsule/vapilot')
def vapilot():
    return render_template('timecapsule/vapilot.html')


@timecapsule_bp.route('/timecapsule/vapilot2')
def vapilot2():
    return render_template('timecapsule/vapilot2.html')


@timecapsule_bp.route('/timecapsule/vapilot3')
def vapilot3():
    return render_template('timecapsule/vapilot3.html')


@timecapsule_bp.route('/timecapsule/writinggoals')
def writinggoals():
    return render_template('timecapsule/writinggoals.html')


@timecapsule_bp.route('/timecapsule/firstapplet')
def firstapplet():
    return render_template('timecapsule/FirstApplet.html')


@timecapsule_bp.route('/timecapsule/bluebird')
def bluebird():
    return render_template('timecapsule/Bluebird.html')


@timecapsule_bp.route('/timecapsule/carpayment')
def carpayment():
    return render_template('timecapsule/CarPayment.html')


@timecapsule_bp.route('/timecapsule/doyouknowme')
def doyouknowme():
    return render_template('timecapsule/DoYouKnowMe.html')
