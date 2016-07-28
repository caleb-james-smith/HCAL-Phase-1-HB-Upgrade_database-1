from django.shortcuts import render
from django.views import generic
import datetime
from os import listdir, path
import json
from sets import Set

from .models import QieCard, Tester, Test, Attempt, Location
import custom.filters as filters

# Create your views here.

from django.utils import timezone
from django.http import HttpResponse, Http404
from card_db.settings import MEDIA_ROOT, CACHE_DATA 


class CatalogView(generic.ListView):
    """ This displays a list of all QIE cards """
    
    template_name = 'qie_cards/catalog.html'
    context_object_name = 'barcode_list'
    def get_queryset(self):
        return QieCard.objects.all().order_by('barcode')


def summary(request):
    """ This displays a summary of the cards """
    if CACHE_DATA:
        cache = path.join(MEDIA_ROOT, "cached_data/summary.json")
        print "opening JSON"
        infile = open(cache, "r")
        print "opened JSON"
        print "Loading JSON"
        cardStat = json.load(infile)
        print "JSON Loaded"
    else:
        print "Loading Cards"
        cards = list(QieCard.objects.all().order_by('barcode'))
        print "Loaded Cards"
        print "Loading Tests"
        tests = list(Test.objects.all())
        print "Loaded Tests"
        print "Loading Attempts"
        attempts = list(Attempt.objects.all())
        print "Loaded Attempts"
        print "Getting States!"
        cardStat = filters.getCardTestStates(cards, tests, attempts)
        print "Got 'em!"
    
    return render(request, 'qie_cards/summary.html', {'cards': cardStat})

class TestersView(generic.ListView):
    """ This displays the users and email addresses """
    
    template_name = 'qie_cards/testers.html'
    context_object_name = 'tester_list'
    def get_queryset(self):
        return Tester.objects.all().order_by('username')


class TestDetailsView(generic.ListView):
    """ This displays the tests and their descriptions """

    template_name = 'qie_cards/test-details.html'
    context_object_name = 'test_list'
    def get_queryset(self):
        return Test.objects.all().order_by('name')


def stats(request):
    """ This displays a summary of the cards """
   
    # Get required attempts and tests
    if CACHE_DATA:
        cache = path.join(MEDIA_ROOT, "cached_data/stats.json")
        infile = open(cache, "r")
        statistics = json.load(infile)
    else:
        attempts = []
        tests = list(Test.objects.filter(required=True))
        
        for test in tests:
            attempts.extend(list(test.attempt_set.all())) 
                
        cards = list(QieCard.objects.all().order_by("barcode"))

        testFailedStats = filters.getFailedCardStats(cards, tests, attempts)
        testPassedStats = filters.getPassedCardStats(cards, tests, attempts)
        testRemStats = filters.getRemCardStates(cards, tests, attempts)
        statistics = {'passed': testPassedStats,
                      'failed': testFailedStats,
                      'remaining': testRemStats,
                     }

    return render(request, 'qie_cards/stats.html', statistics)
 
def detail(request, card):
    """ This displays details about tests on a card """
    try:
        p = QieCard.objects.get(barcode__endswith=card)
    except QieCard.DoesNotExist:
        raise Http404("QIE card with barcode " + str(card) + " does not exist")

    tests = Test.objects.all()
    locations = Location.objects.filter(card=p)
    attempts = []
    status = {}    

    status["total"] = len(tests.filter(required=True))
    status["passed"] = 0
    failedAny = False
    forcedAny = False

    for test in tests:
        attemptList = Attempt.objects.filter(card=p.pk, test_type=test.pk).order_by("attempt_number")
        if attemptList:
            last = attemptList[len(attemptList)-1]
            if not last.revoked and test.required:
                if last.overwrite_pass:
                    status["passed"] += 1
                    forcedAny = True
                elif last.passed_all():
                    status["passed"] += 1
                else:
                    failedAny = True
            attempts.append({"attempt":last, "valid": True, "required": test.required})
        else:
            attempts.append({"attempt":test.name, "valid": False, "required": test.required})
 
    if status["total"] == status["passed"]:
        if forcedAny:
            status["banner"] = "GOOD (FORCED)"
            status["css"] = "forced"
        else:
            status["banner"] = "GOOD"
            status["css"] = "okay"
    elif failedAny:
        status["banner"] = "FAILED"
        status["css"] = "bad"
    else:
        status["banner"] = "INCOMPLETE"
        status["css"] = "warn"

    if(request.POST.get('comment_add')):
        comment = ""
        if not p.comments == "":
            comment += "\n"
        comment += str(timezone.now().date()) + " " + str(timezone.now().hour) + "." + str(timezone.now().minute) + ": " + request.POST.get('comment')
        p.comments += comment
        p.save()

    if(request.POST.get('location_add')):
        if len(Location.objects.filter(card=p)) < 10:
            Location.objects.create(geo_loc=request.POST.get("location"), card=p)

    return render(request, 'qie_cards/detail.html', {'card': p,
                                                     'attempts':attempts,
                                                     'locations':locations,
                                                     'status':status,
                                                    })


class PlotView(generic.ListView):
    """ This displays various plots of data """
    
    template_name = 'qie_cards/plots.html'
    context_object_name= 'tests'
    def get_queryset(self):
        return list(Test.objects.all())

def testDetail(request, card, test):
    try:
        qieCard = QieCard.objects.get(barcode__endswith=card)
    except QieCard.DoesNotExist:
        raise Http404("QIE card does not exist")
    try:
        curTest = Test.objects.get(name=test)
    except QieCard.DoesNotExist:
        raise Http404("QIE card does not exist")
    
    if(request.POST.get('overwrite_pass')):
        if(request.POST.get('secret') == "pseudo" or request.POST.get('secret') == "pseudopod"):
            attempt = Attempt.objects.get(pk=request.POST.get('overwrite_pass'))
            attempt.overwrite_pass = not attempt.overwrite_pass
            attempt.save()
    
    attemptList = list(Attempt.objects.filter(card=qieCard, test_type=curTest).order_by("attempt_number").reverse())
    attemptData = []
    for attempt in attemptList:
        data = ""
        if not str(attempt.hidden_log_file) == "default.png":
            inFile = open(path.join(MEDIA_ROOT, str(attempt.hidden_log_file)), "r")
            tempDict = json.load(inFile)
            if attempt.test_type.abbreviation == "overall pedestal": 
                data = tempDict["TestOutputs"]["pedResults"]
            elif attempt.test_type.abbreviation == "overall charge injection": 
                data = tempDict["TestOutputs"]["ciResults"]
            elif attempt.test_type.abbreviation == "overall phase scan":
                data = tempDict["TestOutputs"]["phaseResults"]
            elif attempt.test_type.abbreviation == "overall shunt scan":
                data = tempDict["TestOutputs"]["shuntResults"]
            elif "ResultStrings" in tempDict:
                if attempt.test_type.abbreviation in tempDict["ResultStrings"]:
                    data = tempDict["ResultStrings"][attempt.test_type.abbreviation]
        attemptData.append((attempt, data))

    firstTest = []

    return render(request, 'qie_cards/testDetail.html', {'card': qieCard,
                                                         'test': curTest,
                                                         'attempts': attemptData
                                                         })


def fieldView(request):
    """ This displays details about tests on a card """ 
    options = ["barcode",
               "uid",
               "bridge_major_ver",
               "bridge_minor_ver",
               "bridge_other_ver",
               "igloo_major_ver",
               "igloo_minor_ver",
               "comments",
               "last location"]
    
    fields = []
    for i in range(5):
        if(request.POST.get('field' + str(i+1))):
            field = request.POST.get('field' + str(i+1))
            if field in options:
                fields.append(field)


    cards = list(QieCard.objects.all())
    items = []
    
    for card in cards:
        item = {}
        item["id"] = card.pk
        item["fields"] = []
        for field in fields:
            if field == "last location":
                item["fields"].append(card.location_set.all().order_by("date_received").reverse()[0].geo_loc)
            else:
                item["fields"].append(getattr(card, field))

        items.append(item)

    return render(request, 'qie_cards/fieldView.html', {'fields': fields, "items": items, "options": options})