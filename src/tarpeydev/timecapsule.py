# import native Python packages
from enum import Enum

# import third party packages
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


# router and templates
tc_views = APIRouter(prefix="/timecapsule")
tcd_views = APIRouter(prefix="/timecapsuledeep")
templates = Jinja2Templates(directory='templates')


class TemplateID(str, Enum):
    APARGUMENT = "apargument"
    APARGUMENTSCAN = "apargumentscan"
    APENGLISH12 = "apenglish12"
    APPS = "apps"
    APSCHOLARD = "apscholard"
    BLUEBIRD = "Bluebird"
    BOWLINGPIC = "bowlingpic"
    CALCULUS = "calculus"
    CARPAYMENT = "CarPayment"
    DIPLOMA = "diploma"
    DOYOUKNOWME = "DoYouKnowMe"
    ECSP = "ecsp"
    ENGLISH10 = "english10"
    ENTER = "enter"
    FIRSTAPPLET = "FirstApplet"
    GPA = "gpa"
    INDEX = "index"
    JAVAPROJECTS = "javaprojects"
    JGS = "jgs"
    MATHANALYSIS = "mathanalysis"
    MOMANDDAD = "momanddad"
    MTGP = "mtgp"
    MTHS = "mths"
    MYINDEX = "myindex"
    OOPS = "oops"
    PHYSICS = "physics"
    PORTFOLIO07 = "portfolio07"
    PORTFOLIO09 = "portfolio09"
    PORTFOLIO10 = "portfolio10"
    PRESIDENTGOLD = "presidentgold"
    PROJECTS = "projects"
    UCONNDIPLOMA = "uconndiploma"
    VAPILOT = "vapilot"
    VAPILOT2 = "vapilot2"
    VAPILOT3 = "vapilot3"
    WRITINGGOALS = "writinggoals"


class DeepTemplateID(str, Enum):
    CAREERENTRY = "3careerentry"
    CAREERHOME = "3careerhome"
    CP = "cp"
    DA = "da"
    DDR = "ddr"
    DDRLINKS = "ddrlinks"
    DDRPICS = "ddrpics"
    DDRVIDEOS = "ddrvideos"
    ENTER = "enter"
    INSANITY = "insanity"
    NSA = "nsa"
    OTHERHOME = "otherhome"
    REVIEWSFAQS = "reviewsfaqs"
    SCHOOLPROJECTS = "schoolprojects"
    STEPMANIA = "stepmania"


@tc_views.get('/{template_id}', tags=["enumerated_path_view"])
def timecapsule(request: Request, template_id: TemplateID):
    template_url = f'timecapsule/{template_id}.html'
    return templates.TemplateResponse(
        template_url,
        context={'request': request},
    )


@tcd_views.get('/{template_id}', tags=["enumerated_path_view"])
def timecapsuledeep(request: Request, template_id: DeepTemplateID):
    template_url = f'timecapsuledeep/{template_id}.html'
    return templates.TemplateResponse(
        template_url,
        context={'request': request},
    )
