from BeautifulSoup import BeautifulSoup
import urllib2
import re
import socket
from urlparse import urlparse
from collections import Counter
from datetime import datetime
import os.path
from fake_useragent import UserAgent
from time import sleep
from sys import exit
import httplib
import time


def get_api_file(user_api_key):
    global debug
    ids = list()
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', ua.random)]

    if user_api_key:
        url = 'http://data.phishtank.com/data/' + user_api_key + '/online-valid.csv'

    else:
        url = 'http://data.phishtank.com/data/online-valid.csv'

    file_name = url.split('/')[-1]

    try:
        downloader = opener.open(url)
        print "Downloading file.."
        with open(file_name, "wb") as code:
            code.write(downloader.read())

        print "Download complete"
        return file_name

    except urllib2.URLError:
        print("Error: Do you have internets?")
        # TODO create a return to just wait
        exit(0)


def extract_links(csv_file_location):
    phish_link_from_file = list()
    with open(csv_file_location) as f:
        f.readline() # skip first line
        for line in f:
            phishing_url = line.split(',')[1]
            phish_link_from_file.append(phishing_url)

    return phish_link_from_file


def get_form_elements(phish_inks):

    global count
    global debug
    final_forms = list()

    opener = urllib2.build_opener()

    sid_and_links = list()

    if os.path.isfile('SID to link.txt'):
        sid_link_exists = True
        with open('SID to link.txt', 'r') as fp:
            for line in fp:
                sid_and_links.append(line)
        fp.close()

    else:
        sid_link_exists = False

    for link in phish_inks:
        opener.addheaders = [('User-agent', ua.random)]

        if sid_link_exists:
            if any(link in s for s in sid_and_links):
                # skip the link
                print("link already exits in the database")
                continue

        if not link.startswith("https:"):
            if debug:
                print 'wgetting ' + link

            try:
                response = opener.open(link, timeout=7) #download URL. Timeout after 10 seconds
                final_url = response.geturl()

                if debug:
                    print "Final URL is: " + final_url

            except urllib2.HTTPError as e:
                if e.code == 403:
                    print("Page 403ed: Forbidden. Skipping..")
                    continue
                if e.code == 404:
                    print("Page 404ed. Skipping..")
                    continue
                if e.code == 503:
                    print("503 Service Unavailable. Skipping..")
                    continue
                else:
                    print("Error occured." + str(e.code) + " Skipping.")
                    continue

            except urllib2.URLError:
                print("Entire domain is down.")
                continue
            except socket.timeout:
                print("URL timeout. Skipping..")
                continue
            except socket.error:
                print "socket error. Skipping.."
                continue
            except urllib2.URLError:
                print("There was a url error. Possible timeout.")
                continue

            #except ValueError:
                #print "Your url could not be opened. We added http://"
                #response = opener.open("http://" + link)
                #final_url = response.geturl()

                #if (debug):
                    #print "Final URL is: " + final_url
            except Exception as e:
                print "General exception caught, skipping URL"
                print e.__doc__
                print e.message
                continue
            except:
                print "Unknown error caught, skipping URL"
                continue

            #html = response.read()
            #print "Your html is: \n" + html

            try:
                #print "putting in beautiful soup"  #todo if debug
                try:
                    soup = BeautifulSoup(unicode(response.read(), errors='ignore'))
                except socket.error as e:
                    print "Caught socket error propigation in beautiful soup"
                    continue
                except socket.timeout as e:
                    print "Caught socket timeout propigation in beautiful soup"
                    continue
                except MemoryError as m:
                    continue
                except ValueError:
                    soup = BeautifulSoup(unicode(response.read(), errors='ignore'))
                except httplib.IncompleteRead, e:
                    soup = BeautifulSoup(unicode(e.partial, errors='ignore'))
                except:
                    print "\nBeautifulSoup parsing error ocurred. Skipping link: "
                    print link + "\n"

                #print "beautiful soup success"
            except TypeError: # protect against chineese characters
                soup = BeautifulSoup(unicode(response.read().decode('unicode-escape'), errors='ignore'))

            pretty_html = soup.prettify()  # prettify the html
            soup2 = BeautifulSoup(pretty_html)
            #sleep(.1)


            #if ("unescape(" in str(soup2)): #test to find javascript encoded pages.
                #print "Found encoded element.#ttest123"




            #For each form on the page
            #See text

            post_action = ""

            try:
                for form in soup2.findAll('form', attrs={'method':re.compile("^post", re.I)}):
                    formelements_conc = ""
                    first = True # first value in the set of elements in the form
                    # for item in form.findAll("input", name=True)["name"]:
                        # print "found item " + item.
                    #print "pre if call post_action is: " + post_action
                    try:
                        post_action = form['action'].replace('\n', '').replace('\r', '')

                        if post_action.startswith("https"):
                            continue

                    except KeyError:
                        post_action = ""
                    if not post_action or post_action == "" or post_action is "" or post_action is "#" or post_action == "#":
                        if (debug):
                            print "has # or is blank"
                        if ".php" in final_url:
                            print "final url is: " + final_url

                            post_action = final_url.split('/')[-1].rsplit('?', 1)[0]
                            if not post_action.endswith(".php"):
                                post_action = final_url.split('/')
                                for slash in post_action:
                                    if ".php" in slash:
                                        post_action = slash
                                if not post_action.endswith(".php"):
                                    post_action = final_url.split('?')[0]

                            if "/" in post_action:
                                post_action = post_action.split('/')[-1]

                        else:
                            if "/" in final_url:
                                final_split = final_url.split('/')
                                if final_split[-1] == "" or final_split[-1] is "":
                                    post_action = "/" + final_split[-2]
                                else:
                                    post_action = "/" + final_split[-1]

                    else:
                        try:
                            post_action = form['action'].replace('\n', '').replace('\r', '')
                            if ((not post_action.endswith(".php")) or (not post_action.endswith(".html")) or (not post_action.endswith(".htm")) or post_action.startswith("http")):
                                print "in parsing form statement"
                                post_split = post_action.split('/')
                                hit_on_extension = False
                                for slash in post_split:
                                    if ".php" in slash or ".html" in slash or ".htm" in slash or ".pl" in slash or ".jsp" in slash:
                                        hit_on_extension = True
                                        if post_split[-1] == "" or post_split[-1] is "":
                                            post_action = "/" + post_split[-2]
                                        else:
                                            post_action = "/" + post_split[-1]
                                        if not post_action.endswith(".php") or not post_action.endswith(".html") or not post_action.endswith(".htm"):
                                            post_action = post_action.split('?')[0]

                                if not hit_on_extension:
                                    if post_split[-1] == "" or post_split[-1] is "":
                                        post_action = "/" + post_split[-2]
                                    else:
                                        post_action = "/" + post_split[-1]

                        except KeyError:
                            final_split = final_url.split('/')
                            if final_split[-1] == "" or final_split[-1] is "":
                                post_action = final_split[-2]
                            else:
                                post_action = final_split[-1]



                    # TODO can be optimized here
                    # if you have a self targeting phish... ignore url
                    #elif post_action is "#":
                        #post_action = ""
                        #post_action = final_url.split('.com')[-1]


                    if (debug):
                        print "Form action is: "
                        print post_action

                    test_checkbox = ""
                    for element in form.findAll('input', attrs={'name': True}):
                        try:

                            test_checkbox = element['type'].lower()
                            #print "type element for input is" + test_checkbox
                            print element['name']

                            if test_checkbox != "checkbox" and test_checkbox != "radio":

                                if first:
                                    formelements_conc = formelements_conc + "," + element['name']
                                    first = False
                                else:
                                    formelements_conc = formelements_conc + ",&" + element['name']

                        except KeyError:

                                if (debug):
                                    print element['name']
                                if first:
                                    formelements_conc = formelements_conc + "," + element['name']
                                    first = False
                                else:
                                    formelements_conc = formelements_conc + ",&" + element['name']

                    try:
                        formelements_conc.decode('ascii')
                    except UnicodeDecodeError:
                        print "it was not a ascii-encoded unicode element. Skipping"
                        continue
                    except UnicodeEncodeError:
                        print "problem encoding element. Skipping"
                        continue



                    '''
                    print form.find("input", name=True)["name"]
                    for names in form.findAll("input", name=True)["name"]:
                        print(names.text)
                        #for attrs in names.findAll("input")["name"]:

                            #print(attrs.text)
                            #exit(0)
                    '''
                    try:
                        final_forms.append(link + "," + post_action + formelements_conc)
                    except UnicodeDecodeError: # catch crap like fancy A's
                        final_forms.append(re.sub(r'[^\x00-\x7f]',r'', link) + "," + post_action + formelements_conc)
            # TODO catch escaped javascript pages

            except IOError:
                print 'IO error'

    return final_forms


def get_ids(ua_input):

    global debug
    ids = list()
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', ua_input)]
    try:
        #response = opener.open('https://www.phishtank.com/phish_search.php?page=1&active=y&valid=y&Search=Search')
        response = opener.open('https://www.phishtank.com/phish_search.php?valid=y&active=y&Search=Search')
    except urllib2.URLError:
        print("Error: Do you have internets?")
        #TODO create a return to just wait
        exit(0)
    #print("Response:" + response.read())

    soup = BeautifulSoup(response)
    prettyHTML=soup.prettify()  #prettify the html
    soup2 = BeautifulSoup(prettyHTML)

    try:
        for table in soup2.findAll('table', attrs={'class': 'data'}):
            for cell in table.findAll('td'):
                #print cell

                for id in cell.findAll('a'):
                    if "phish_id" in str(id):
                        #if debug:
                        #print str(id.text)
                        ids.append(id.text)


        #table = soup2.findAll('table', attrs={'class': 'data'})

        if (debug):
            print len(ids)

        if (debug):
            for item in ids:
                print item
    except IOError:
        print 'IO error'
    return ids

    '''  for div in soup2.findAll("div", attrs={'class': 'thread'}):
            ids.append(div['id'])
    '''


def get_phish_links(ua_input, ids):

    global debug
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', ua_input)]

    PhishLinks = list()


    for id in ids:
        if (debug):
            print "Downloading ID page " + id

        try:
            response = opener.open('https://www.phishtank.com/phish_detail.php?phish_id=' + id )
        except urllib2.URLError:
            print("Error: Do you have internets?")
            #TODO create a return to just wait
            exit(0)
        #print("Response:" + response.read())

        soup = BeautifulSoup(response)
        prettyHTML=soup.prettify()  #prettify the html
        soup2 = BeautifulSoup(prettyHTML)

        try:
            for div1 in soup2.findAll('div', attrs={'id': 'widecol'}):
                for div2 in div1.findAll('div', attrs={'class': 'padded'}):
                    for div3 in div2.findAll('div'):
                        if "http" in str(div3):
                            #if(debug):
                            print str(div3.text)
                            PhishLinks.append(div3.text)

        except IOError:
            print 'IO error'

    # remove duplicates
    PhishLink_douped = list(set(PhishLinks))
    return PhishLink_douped


def check_uniq(elements):

    global debug
    minimum_histogram_count = 5
    final_new_elements = list()

    if not os.path.isfile("current_sid.txt"):
        current_sid_file = open('current_sid.txt', 'w')
        current_sid_file.write('6000000')
        current_sid_file.close()

    current_sid_file = open('current_sid.txt', 'r+')
    current_sid = int(current_sid_file.read())
    current_sid_file.close()

    # create the file if does not exist
    if not os.path.isfile("elementdatabase.txt"):
        element_database_file = open('elementdatabase.txt', 'w')
        element_database_file.write('')
        element_database_file.close()

    element_count = list()
    element_sid = list()
    element_from_database = list()

    sid_and_link_database = list()

    if os.path.isfile('SID to link.txt'):
        with open('SID to link.txt', 'r') as fp:
            for line in fp:
                sid_and_link_database.append(line)
        fp.close()

    print "Reading the entire file into a list."

    #element_database_file = open('elementdatabase.txt', 'r')
    #element_database = element_database_file.readlines() # take the entire file as a list.. might not be good for ram usage :p
    #element_database_file.close()

    with open('elementdatabase.txt', 'r') as fp:
        for line in fp:
            temp = (line.rstrip()).split(" ", 2)
            element_count.append(temp[0])
            element_sid.append(temp[1])
            element_from_database.append(temp[2])

    if (debug):
        print "Current database is: "
        x = 0
        for test in element_from_database:
            print element_count[x] + " " + element_sid[x] + " " + test
            x += 1

    print len(element_from_database)

    for element in elements:

        element_split = element.split(",")

        if len(element_split) > 3:

            #link = element_split[0] # save the phishing link
            link = element_split.pop(0) # get rid of the first element (the phishing url)
            element_minus_first = ",".join(element_split)
            #print hashlib.md5(element_minus_first).hexdigest()

            #print "element splitted and poped: " + element_minus_first
            #print "element splitted and poped and rsplited: " + element_minus_first.rstrip()+"\n"

            if element_minus_first not in element_from_database:
                print element_minus_first + " is not in the file, adding it. "
                #final_new_elements.append(element) # moved to add only when > 1
                element_count.append(1)
                element_sid.append(current_sid)

                sid_and_link_database.append(str(current_sid) + "\n" + link + "\n")

                current_sid += 1
                element_from_database.append(element_minus_first)
            else:
                location = element_from_database.index(element_minus_first)
                #tempsplit = element_database_from_file.split(" ", 1) # Make only one split (in case the input elements might be split with a space)
                element_count[location] = str(int(element_count[location])+1)

                element_sid_for_link = element_sid[location]

                count1 = 0
                for x in sid_and_link_database:
                    if x.startswith(str(element_sid_for_link)):
                        temp1 = (x.rstrip()).split(" ", 1)
                        sid_and_link_database[count1] = sid_and_link_database[count1] + link + "\n"
                    else:
                        count1 += 1



                        #todo check if link is in this file of sid + links, if it is skip it.

                #element_database_from_file[location] = tempsplit[0] + " " + tempsplit[1]


    # soon (TM)
    #uniq_from_dic = dict(Counter(new_element_database_entries))
    #for uniq in uniq_from_dic.items():
    #    print uniq

    print "Length of element database " + str(len(element_from_database))
    print "Length of element count " + str(len(element_count))
    for item in element_count:
        print "Element count is: " + str(item)

    for item2 in element_from_database:
        print "Element database is: " + item2

    # todo write element_count + element_from_database to file!
    z = 0
    for y in element_from_database:
        print "element data is: " + str(element_count[z]) + " " + element_from_database[z]
        z += 1


    element_database_file = open('elementdatabase.txt', 'w')

    if len(element_from_database) > 0:
        index = 0
        for item in element_from_database:
            element_database_file.write(str(element_count[index]) + " " + str(element_sid[index]) +" " + element_from_database[index]+"\n")
            index += 1

    element_database_file.close()

    element_count_as_int = map(int, element_count) # convert str to ints

    element_database_zipped = zip(element_count_as_int, element_sid, element_from_database)

    print "Zipped the two lists: "
    for x in element_database_zipped:
        print x

    element_database_zipped = sorted(element_database_zipped, key=lambda element_database_zipped: element_database_zipped[0], reverse=True)

    print "Sorted the Zipped lists: "
    for x in element_database_zipped:
        print x

    element_count_as_int_sorted, element_sid_sorted, element_from_database_sorted = zip(*element_database_zipped)

    #element_element_sorted = [x for y, x in element_database_zipped]


    print "\nSorted element element is: "

    for t in element_from_database_sorted:
        print t



    element_count_sorted = [int(i[0]) for i in element_database_zipped]

    print "\nSorted element count is: "

    for count in element_count_sorted:
        print count

    element_database_histogram_file = open('elementdatabase_histogram.txt', 'w')

    print "\nLength of element_count_sorted is: " + str(len(element_count_sorted))

    if len(element_count_sorted) > 0:
        index = 0
        for item in element_from_database_sorted:

            if element_count_sorted[index] >= minimum_histogram_count:
                #print "writing to hist file!-----------------------"
                final_new_elements.append(element_from_database_sorted[index])
                element_database_histogram_file.write(str(element_count_sorted[index]) + " " + str(element_sid_sorted[index]) + " " + element_from_database_sorted[index]+"\n")
            index += 1

    element_database_histogram_file.close()


    #element_database_file = open('elementdatabase.txt', 'a')
    #for line in new_element_database_entries:
    #    element_database_file.write(line+"\n")
    #element_database_file.close()

    current_sid_file = open('current_sid.txt', 'w')
    current_sid_file.write(str(current_sid))
    current_sid_file.close()




    #write sid + link list
    current_sid_link_file = open('SID to link.txt', 'w')
    for y in sid_and_link_database:
        current_sid_link_file.write(y)
    current_sid_file.close()

    return final_new_elements


def generate_rules(database_file):

    finalrules = list()
    element_count = list()
    element_sid = list()
    element_from_database = list()

    with open(database_file, 'r') as fp:
        for line in fp:
            temp = (line.rstrip()).split(" ", 2)
            print "Items in temp list are:"
            for t in temp:
                print t
            element_count.append(temp[0])
            element_sid.append(temp[1])
            element_from_database.append(temp[2])

    index = 0

    for element in element_from_database:

        content = ""

        position = 1
        links_elements = element.split(",")

        if len(links_elements) > 2:
            action = links_elements[0]

            if action == "":
                uricontent = ""

            else:
                uricontent = "uricontent:\"" + action + "\"; "

            while position < len(links_elements):

                content += "content:\"" + links_elements[position] + "\"; nocase; "
                position += 1

            template = "alert tcp $HOME_NET any -> $EXTERNAL_NET any (sid:" + element_sid[index] + "; gid:1; flow:established,to_server; " + uricontent + "content:\"POST\"; http_method; " + content + "fast_pattern; metadata:service http; msg:\"Custom PhishRule " + element_sid[index] + "- PhishTank generated: phished victim POSTing data\"; classtype:attempted-recon; rev:1; )"

            finalrules.append(template)

            index += 1

        else:
            print "Too few elements, skipping:"
            print element
            continue

        if not os.path.isfile("SF_Phish_Rules.txt"):
            sf_file = open('SF_Phish_Rules.txt', 'w')
            sf_file.write('')
            sf_file.close()

        sf_file = open('SF_Phish_Rules.txt', 'w')
        sf_file.write("#Rules generated by Rakesh's script based on ~30k phishing links from PhishTank\n")
        for rule in finalrules:
            sf_file.write("#\n")
            sf_file.write(rule.encode("utf-8") + "\n")
            sf_file.write("\n")

        sf_file.close()

    return(finalrules)


def check_if_int(int_from_user):
    try:
        input_int = int(int_from_user)
        return True
    except ValueError:
        print("That's not an int! Exiting")
        return False


# main
debug = True
ua = UserAgent()

program_start_input = raw_input('Generate rules via API download(1) or live(2)(live mode is in testing)? \n')
if len(program_start_input) > 1:
    print "Too many inputs."
    exit(0)

if not check_if_int(program_start_input):
    exit()


if int(program_start_input) is 1:
    start_time = time.time()

    input_api_question = raw_input('Do you have an API key? 1 for Yes, 2 for No \n')
    if len(input_api_question) > 1:
        print "Too many inputs."
        exit(0)

    if not check_if_int(input_api_question):
        exit()
    if input_api_question == 1:
        API_key = raw_input('Enter your API key: ')
        if len(API_key) is not 64:
            print "Improper API key entered"
            exit(0)
    else:
        API_key = False

    csv_file = get_api_file(API_key)
    #csv_file = "online-valid.csv"
    links_from_api = extract_links(csv_file)
    #print all urls in the csv file (about 30k)
    #print "URLs from csv are: "
    #for url in links_from_api:
    #print url

    Elements2 = get_form_elements(links_from_api)

    print "Element2 are: "
    for ele in Elements2:
        print ele

    UniqElements2 = check_uniq(Elements2)

    print "Uniq elements greater than 2:"
    for uniq_element in UniqElements2:
        print uniq_element

    if len(UniqElements2) != 0:
        SF_final_rules = generate_rules("elementdatabase_histogram.txt")


        print "\nFinal rules are: \n"

        for rule in SF_final_rules:
            print rule

    else:
        print "No new rules to add. Have a good day."

    end_time = time.time()
    print("Elapsed time was %g seconds" % (end_time - start_time))

elif program_start_input is 2:

    while True:
        count = 0

        # new UA every 10 minutes
        random_ua = ua.random
        #if(debug):
        print("Current UA: " + random_ua)

        # print start time
        now = datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
        print ("Running at time %s" % now)

        # Get the IDs for the valid phishs
        IDS = get_ids(random_ua)

        # Get the phishing links from within the ID pages
        Links = get_phish_links(random_ua, IDS)

        if (debug):
            print len(Links)

        '''
        if (debug):
            for link in Links:
                print link
        '''
        Elements = get_form_elements(random_ua, Links)

        for element in Elements:
            print element

        #check uniq
        UniqElements = check_uniq(Elements)

        print "Uniq elements are:"
        for uniq_element in UniqElements:
            print uniq_element
        if not os.path.isfile("SF_Rules.txt"):
            sf_file = open('SF_Rules.txt', 'w')
            sf_file.write('')
            sf_file.close()
        sf_file = open('SF_Rules.txt', 'a')

        if len(UniqElements) != 0:
            SF_final_rules = generate_rules(UniqElements)


            print "\nFinal rules are: \n"

            for rule in SF_final_rules:
                print rule
                sf_file.write(rule + "\n")

        else:
            print "No new rules to add. Have a good day."

        sf_file.close()
        #exit(0)
        print("Sleeping for 60 minutes")
        sleep(3600) # delays for 60 minutes


# elif Custom CSV with line separated phishing sites

else:
    print "Input not understood. Exiting.."
    exit(0)
