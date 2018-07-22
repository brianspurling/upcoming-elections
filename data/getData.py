import sys
import requests
import csv
import json
from datetime import datetime
from dateutil.relativedelta import relativedelta
from flask import Flask

REFRESH = False
DATA_FILENAME = 'upcoming_elections.json'
ALL_ELECTIONS = False

app = Flask(__name__)


@app.route("/upcoming")
def webHook_upcoming():
    global REFRESH
    REFRESH = True
    execute()
    return 'data written to file'


@app.route("/ge2017")
def webHook_ge2017():
    global REFRESH
    global ALL_ELECTIONS
    global DATA_FILENAME
    
    REFRESH = True
    ALL_ELECTIONS = False
    DATA_FILENAME = 'ALL_ELECTIONS.json'

    execute()
    return 'data written to file'


def processArgs(args):

    global REFRESH
    global ALL_ELECTIONS
    global DATA_FILENAME

    helpText = 'Use the `refresh` argument to refresh the election data '
    helpText += 'and `getall` to get historic elections'
    isUnrecognisedArg = False
    argNotRecognised = ("Argument(s) {arg} not recognised. Try 'help'")
    unrecognisedArgs = []

    if len(args) > 0 and args[0] == 'getData.py':
        del args[0]

    for arg in args:
        if arg == 'help':
            print(helpText)
            sys.exit()
        elif arg == 'refresh':
            REFRESH = True
        elif arg == 'getall':
            ALL_ELECTIONS = True
            DATA_FILENAME = 'ALL_ELECTIONS.json'

    if isUnrecognisedArg:
        print(argNotRecognised.format(arg=str(unrecognisedArgs)))
        sys.exit()


def getElectionTypesData():
    url_et = 'http://elections.democracyclub.org.uk/api/election_types/'
    r_et = requests.get(url_et)
    data_et = r_et.json()

    electionTypes = {}

    for electionTypeDict in data_et['results']:
        electionTypes[electionTypeDict['election_type']] = \
            electionTypeDict['name']

    return electionTypes


def getOrganisationsData():
    url_o = 'https://elections.democracyclub.org.uk/api/organisations'
    organisations = {}

    while url_o:
        r_o = requests.get(url_o)
        data_o = r_o.json()
        for orgDict in data_o['results']:
            organisations[orgDict['slug']] = orgDict
        url_o = data_o['next']

    return organisations


def getFutureElectionsData():

    url_ee = \
        'https://elections.democracyclub.org.uk/api/elections.json'
    if not ALL_ELECTIONS:
        url_ee += '?future=1'

    elections = {}

    while url_ee:
        print(url_ee)
        res_ee = requests.get(url_ee)
        res_ee.raise_for_status()
        data_ee = res_ee.json()
        for elecDict in data_ee['results']:
            elections[elecDict['election_id']] = elecDict
        url_ee = data_ee['next']
    print('Pulled ' + str(len(elections)) +
          ' elections from the Every Election API')

    return elections


def constructBallotsDataset(electionsData):

    ballots = {}

    for electionId in electionsData:

        # Heiarchy of election data:
        #    Election type > [Election subtype] > [Organisation] > [Division] >
        #    [By-election] > Date polls open

        # We want to create a nested dictionary that follows this hierarchy.
        # I.e. a dictionary of election types,  each containing a dictionary of
        # organisations, each containing a dictionary of ballots
        # (division.date_poll_opens).

        # Later on we will add a dictionary of candidates for each ballot.

        # In the election object we pulled from elections.dc, if group_type is
        # none then we are at the bottom of the hiearchy, so we know this is a
        # ballot (and the election_id is therefore our ballot_id)

        elec = electionsData[electionId]

        elecDatetime = datetime.strptime(elec['poll_open_date'], '%Y-%m-%d')
        threshold_date = datetime.now() + relativedelta(months=1)

        if elec['group_type'] is None and elecDatetime <= threshold_date:

            # Election Type
            electionTypeId = elec['election_type']['election_type']
            if electionTypeId not in ballots:
                ballots[electionTypeId] = {}

            # Organisation
            organisationId = elec['group']
            if organisationId not in ballots[electionTypeId]:
                ballots[electionTypeId][organisationId] = {
                    # We need the slug to lookup to our master list of orgs
                    'org_slug': elec['organisation']['slug'],
                    # We need the org-level poll date, so we have a date for
                    # this org's election (rather than a date for every ballot)
                    # This requires looking up the parent record in the
                    # electionsData, which is in the group attribute
                    'poll_open_date': electionsData[elec['group']]['poll_open_date'],
                    'ballots': {}
                }

            # Ballots
            ballotId = elec['election_id']

            divisionName = None
            divisionId = None
            if elec['division'] is not None:
                divisionName = elec['division']['name']
                divisionId = elec['division']['official_identifier']

            ballots[electionTypeId][organisationId]['ballots'][ballotId] = {
                'ballot_id': ballotId,
                'ynr_election_id': organisationId,
                'election_title': elec['election_title'],
                'election_type_id': electionTypeId,
                'election_type_name': elec['election_type']['name'],
                'elected_role': elec['elected_role'],
                'division_name': divisionName,
                'division_id': divisionId,
                'seats_contested': elec['seats_contested'],
                'organisation_name': elec['organisation']['common_name'],
                'organisation_type': elec['organisation']['organisation_type'],
                'organisation_subtype':
                    elec['organisation']['organisation_subtype'],
                'poll_open_date': elec['poll_open_date']
            }

    return ballots


# GET CANDIDATE DATA FOR THE ORGANISATIONS OF ALL BALLOTS
def getCandidatesData(ballotsData):

    # We pull candidate data from YourNextRepresentative (YNR,
    # candidates.democracyclub.org.uk), which identifies elections with the
    # organisation ID (not the ballot ID) and a post ID, so we need to call the
    # candidates API using the organisation_id. Of course, we will have
    # multiple ballots for each organisation. So to avoid hitting the API every
    # time, we'll build up a standalone list of candidates and thus only
    # access the API for new orgIds

    candidates = {}

    for electionTypeId in ballotsData:
        for orgId in ballotsData[electionTypeId]:
            for ballotId in ballotsData[electionTypeId][orgId]['ballots']:

                if orgId not in candidates:

                    candidates[orgId] = {}

                    url_ynr = ('https://candidates.democracyclub.org.uk/' +
                               'media/candidates-%s.csv' % (orgId))
                    print(url_ynr)

                    try:
                        res_ynr = requests.get(url_ynr)
                        res_ynr.raise_for_status()
                        decoded_data_ynr = res_ynr.content.decode('utf-8')
                        data_ynr = list(
                            csv.DictReader(
                                decoded_data_ynr.splitlines(), delimiter=','))
                        print('Pulled ' + str(len(data_ynr)) +
                              ' candidates for ' + orgId)
                        for candidate_ynr in data_ynr:
                            candidates[orgId][candidate_ynr['id']] = \
                                dict(candidate_ynr)
                    except requests.exceptions.HTTPError:
                        print('Pulled 0 candidates for ' + orgId)

    return candidates


def linkCandidatesToBallots(ballotsData, candidatesData):

    for electionTypeId in ballotsData:
        for orgId in ballotsData[electionTypeId]:
            for ballotId in ballotsData[electionTypeId][orgId]['ballots']:
                ballot = \
                    ballotsData[electionTypeId][orgId]['ballots'][ballotId]
                ballot['candidates'] = {}
                orgCan = candidatesData[orgId]
                for canId in orgCan:
                    if ballot['division_name'] == orgCan[canId]['post_label']:
                        ballot['candidates'][canId] = orgCan[canId]

    return ballotsData


# Use our electionTypes and organisation lookup tables to agument the
# ballotsAndCandidates data, and create a tidy hierachial dictionary with
# everything we need
def finaliseOutputData(ballotsAndCandidates,
                       electionTypesData,
                       orgData):
    op = {}

    for eTypeId in ballotsAndCandidates:

        op[eTypeId] = {
            'election_type_name': electionTypesData[eTypeId],
            'orgs': {}}

        for orgId in ballotsAndCandidates[eTypeId]:

            org = ballotsAndCandidates[eTypeId][orgId]

            # Our master list of organistions is keyed with the org slug, which
            # we have saved in our ballot record. So use this to lookup the
            # election name from the organisation master data

            op[eTypeId]['orgs'][orgId] = {
                'election_name': orgData[org['org_slug']]['election_name'],
                'organisation_name': orgData[org['org_slug']]['common_name'],
                'poll_open_date': org['poll_open_date'],
                'ballots': {}}

            for bId in org['ballots']:

                ballot = org['ballots'][bId]

                op[eTypeId]['orgs'][orgId]['ballots'][bId] = {
                    'id': bId,
                    'seats_contested': ballot['seats_contested'],
                    'elected_role': ballot['elected_role'],
                    'division_name': ballot['division_name'],
                    'poll_open_date': ballot['poll_open_date'],
                    'post_id': None,  # Stored on candidates, so populate below
                    'web_url': None,
                    'cans': {}}

                for canId in ballot['candidates']:

                    candidate = ballot['candidates'][canId]

                    # First, set the post_id on the level above (which is
                    # ballot/post). Do this for every candidate, even though
                    # all their posts SHOULD be the same, so we can raise an
                    # exception if they're not
                    currentPostId = \
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['post_id']

                    if currentPostId and currentPostId != candidate['post_id']:
                        raise ValueError('Post IDs differ between ' +
                                         'candidates. This was not expected!')

                    op[eTypeId]['orgs'][orgId]['ballots'][bId]['post_id'] = \
                        candidate['post_id']

                    # Now build up the candidate record
                    twitter = candidate['twitter_username']
                    if twitter != '':
                        twitter = '@' + twitter
                    canWebUrl = 'https://candidates.democracyclub.org.uk/'
                    canWebUrl += 'person/' + str(candidate['id'])
                    op[eTypeId]['orgs'][orgId]['ballots'][bId]['cans'][canId] \
                        = {'name': candidate['name'],
                           'gender': candidate['gender'].lower(),
                           'twitter': twitter,
                           'web_url': canWebUrl}

                # As far as I can tell, we need a post id to link directly to
                # the ballot's web page (on YNR (candidates.dc.org.uk). And
                # we can only get the post ID from the candidate dataset. #
                # So if we don't have any candidates, we have to link to the
                # organisation's web page instead (which will list all the
                # ballots with registered elections)
                # TODO: find a better way to look up post_ids from ballot_ids

                ballotWebUrl = 'https://candidates.democracyclub.org.uk/'
                ballotWebUrl += 'election/' + orgId + '/'
                if op[eTypeId]['orgs'][orgId]['ballots'][bId]['post_id'] is None:
                    ballotWebUrl += 'constituencies'
                else:
                    ballotWebUrl += 'post/'
                    ballotWebUrl += op[eTypeId]['orgs'][orgId]['ballots'][bId]['post_id']

                op[eTypeId]['orgs'][orgId]['ballots'][bId]['web_url'] = \
                    ballotWebUrl

    return op


def addGenderCounts(op):

    for eTypeId in op:
        eType = op[eTypeId]

        for orgId in eType['orgs']:
            org = eType['orgs'][orgId]

            op[eTypeId]['orgs'][orgId]['genderBD'] = {
                'totalMale': 0,
                'totalFemale': 0,
                'totalUnknown': 0,
                'totalCan': 0,
                'percentMale': 0,
                'percentFemale': 0,
                'percentUnknown': 0}

            for bId in org['ballots']:
                ballot = org['ballots'][bId]

                op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD'] = {
                    'totalMale': 0,
                    'totalFemale': 0,
                    'totalUnknown': 0,
                    'totalCan': 0,
                    'percentMale': 0,
                    'percentFemale': 0,
                    'percentUnknown': 0}

                for canId in ballot['cans']:
                    can = ballot['cans'][canId]

                    op[eTypeId]['orgs'][orgId]['genderBD']['totalCan'] += 1
                    op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalCan'] += 1

                    if can['gender'].lower() == 'male':
                        op[eTypeId]['orgs'][orgId]['genderBD']['totalMale'] += 1
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalMale'] += 1
                    elif can['gender'].lower() == 'female':
                        op[eTypeId]['orgs'][orgId]['genderBD']['totalFemale'] += 1
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalFemale'] += 1
                    else:
                        op[eTypeId]['orgs'][orgId]['genderBD']['totalUnknown'] += 1
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalUnknown'] += 1

                if op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalCan'] != 0:
                    op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['percentMale'] = round(
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalMale'] /
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalCan'] * 100)
                    op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['percentFemale'] = round(
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalFemale'] /
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalCan'] * 100)
                    op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['percentUnknown'] = round(
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalUnknown'] /
                        op[eTypeId]['orgs'][orgId]['ballots'][bId]['genderBD']['totalCan'] * 100)

            if op[eTypeId]['orgs'][orgId]['genderBD']['totalCan'] != 0:
                op[eTypeId]['orgs'][orgId]['genderBD']['percentMale'] = round(
                    op[eTypeId]['orgs'][orgId]['genderBD']['totalMale'] /
                    op[eTypeId]['orgs'][orgId]['genderBD']['totalCan'] * 100)
                op[eTypeId]['orgs'][orgId]['genderBD']['percentFemale'] = round(
                    op[eTypeId]['orgs'][orgId]['genderBD']['totalFemale'] /
                    op[eTypeId]['orgs'][orgId]['genderBD']['totalCan'] * 100)
                op[eTypeId]['orgs'][orgId]['genderBD']['percentUnknown'] = round(
                    op[eTypeId]['orgs'][orgId]['genderBD']['totalUnknown'] /
                    op[eTypeId]['orgs'][orgId]['genderBD']['totalCan'] * 100)


    return op


def writeDataToJsonFile(outputData):
    with open(DATA_FILENAME, 'w') as outfile:
        json.dump(outputData, outfile)


def writeDataToJsonConsole(outputData):
    for electionTypeId in outputData:

        elecType = outputData[electionTypeId]

        print('')
        print(elecType['election_type_name'])

        for orgId in outputData[electionTypeId]['orgs']:

            org = outputData[electionTypeId]['orgs'][orgId]

            # Our master list of organistions is keyed with the org slug, which
            # we have saved in our ballot record. So use this to lookup the
            # election name from the organisation master data
            print('')
            print(org['organisation_name'] + ' [' + org['poll_open_date'] + ']')

            for ballotId in org['ballots']:

                ballot = org['ballots'][ballotId]

                if ballot['seats_contested'] is None:
                    seatsCount = '[unknown number of]'
                    plural = 's'
                elif ballot['seats_contested'] == 1:
                    seatsCount = '1'
                    plural = ''
                elif int(ballot['seats_contested']) > 1:
                    seatsCount = str(ballot['seats_contested'])
                    plural = 's'

                print('  - ' +
                      elecType['election_type_name'] +
                      ' for ' +
                      seatsCount + ' ' +
                      ballot['elected_role'] + plural + ' in ' +
                      org['organisation_name'] + "'s " +
                      str(ballot['division_name']) + ' division, on ' +
                      str(ballot['poll_open_date']) +
                      ' ~ ' + ballot['web_url'])

                if len(ballot['cans']) == 0:
                    print('    - No candidates in data yet')
                else:
                    print('    - ' + str(len(ballot['cans'])) + ' candidates')

                for candidateId in ballot['cans']:

                    can = ballot['cans'][candidateId]
                    gender = 'UNKNOWN'

                    if can['gender'] is not None and can['gender'] != '':
                        gender = can['gender']

                    print('    - ' + can['name'] + ' | ' +
                          ' Gender: ' + gender + ' | ' +
                          can['twitter'] + ' ~ ' + can['web_url'])

                print('')


def execute():

    processArgs(sys.argv)

    if REFRESH:

        electionTypesData = getElectionTypesData()
        organisationsData = getOrganisationsData()
        futureElectionsData = getFutureElectionsData()

        # futureElectionsData is in DemoClub structure, so we need transform
        ballotsData = constructBallotsDataset(futureElectionsData)

        # Get the candidates for all these ballots
        candidatesData = getCandidatesData(ballotsData)

        # Candidates need joining into the ballots data
        ballotsAndCandidates = \
            linkCandidatesToBallots(ballotsData, candidatesData)

        outputData = finaliseOutputData(
            ballotsAndCandidates,
            electionTypesData,
            organisationsData)

        outputData = addGenderCounts(outputData)

        writeDataToJsonFile(outputData)

    else:
        with open(DATA_FILENAME, 'r') as f:
            outputData = json.load(f)

    writeDataToJsonConsole(outputData)
