#----------------------------------------------------------------------

    # Libraries
from bs4.element import Tag, NavigableString
from re import findall
from requests import session
import re
from bs4 import BeautifulSoup as BS
import os
import json
import colorama
#----------------------------------------------------------------------

    # Init
colorama.init()
#----------------------------------------------------------------------

    # Class
class OGE:
    __rawData__ = None
    strInDepth = False
    __data__ = None
    __semestreCount__ = 0
    __currentSemester__ = None



    def __new__(cls):
        return None



    def __removeEndSpaces__(s):
        while len(s) > 1 and s[-1] == ' ':
            s = s[:-1]
        if s == ' ': s = ''
        return s



    def __getKey__(url, session):
        print(colorama.Fore.LIGHTBLACK_EX + '[INFO]' + colorama.Fore.RESET + ' Trying to get a key...')
        try:
            keyResults = re.findall(r'name=\"execution\" value=\"(.*?)\"/>', session.get(url).text)
        except Exception as err:
            raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + ' Unable to get a key!', err)

        if(len(keyResults) == 0):
            raise Exception(colorama.Fore.LIGHTBLACK_EX + '[ERROR]' + colorama.Fore.RESET + ' Couldn\'t find a key!')
        else:
            print(colorama.Fore.GREEN + '[SUCCESS]' + colorama.Fore.RESET + ' Key obtained successfully!')
            return keyResults[0]


    def __getViewState__(session_, url):
        print(colorama.Fore.LIGHTBLACK_EX + '[INFO]' + colorama.Fore.RESET + ' Getting viewState key...')
        try:
            r = session_.get(url)
            id = re.findall(r'<li class=\"ui-tabmenuitem(?:.*?)onclick=\"PrimeFaces\.ab\({s:&quot;(.*?)&quot;,f:(?:.*?)</li>', r.text)
            viewState = re.findall(r'id=\"javax\.faces\.ViewState\" value=\"(.*?)\" />', r.text)
        except Exception as e:
            raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Unable to get a viewState key!\n{e}')

        if(len(id)==0 or len(viewState)==0):
            raise Exception()
        else:
            print(colorama.Fore.GREEN + '[SUCCESS]' + colorama.Fore.RESET + ' Key obtained successfully!')
            return id[0], viewState[0]


    def __getHtml__(username = '', password = '', semestre = 1):
        session_ = session()

        URL_SITE = 'http://casiut21.u-bourgogne.fr/login?service=https%3A%2F%2Fiutdijon.u-bourgogne.fr%2Foge%2F'
        URL_NOTE = 'https://iutdijon.u-bourgogne.fr/oge/stylesheets/etu/bilanEtu.xhtml'

        data = {'username': username, 'password': password, 'execution': OGE.__getKey__(URL_SITE, session_), '_eventId': 'submit', 'geolocation' : ''}

        print(colorama.Fore.LIGHTBLACK_EX + '[INFO]' + colorama.Fore.RESET + ' Creating a new session...')

        request = session_.post(URL_SITE, data, {'referer': URL_SITE})
        if request.status_code == 200:
            print(colorama.Fore.GREEN + '[SUCCESS]' + colorama.Fore.RESET + f' Session successfully created! (Status Code: {request.status_code})')
        else:
            return print(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' A connection error has occurred! (Status Code {request.status_code})')

        print(colorama.Fore.LIGHTBLACK_EX + '[INFO]' + colorama.Fore.RESET + ' Waiting for GET request...')

        """code = session_.get(URL_NOTE, headers = {'referer': URL_NOTE})
        code = BS(BS(code.text, 'html.parser').prettify(), 'html.parser')

        print(colorama.Fore.GREEN + '[SUCCESS]' + colorama.Fore.RESET + f' Server response successfully obtained!')"""

        data = {
            'javax.faces.partial.ajax': 'true',
            'javax.faces.source': 'mainBilanForm:j_id_1t',
            'javax.faces.partial.execute': 'mainBilanForm:j_id_1t',
            'javax.faces.partial.render': 'mainBilanForm',
            'mainBilanForm:j_id_1t': 'mainBilanForm:j_id_1t',
            'i': str(semestre - 1),
            'mainBilanForm:j_id_1t_menuid': str(semestre - 1),
            'mainBilanForm_SUBMIT': '1',
            'javax.faces.ViewState': OGE.__getViewState__(session_, URL_NOTE)[1]
        }

        code = session_.post(URL_NOTE, data, headers = {'referer': URL_NOTE})

        session_.close()

        code = BS(code.text, 'lxml')

        semestreCount = len(code.find_all('a', attrs={'class': 'ui-menuitem-link ui-corner-all'}))

        return code, semestreCount



    def __generateList__(lst, length, valueToAppend):
        if len(lst) == length:
            return lst
        lst = list(lst)
        for i in range(length - len(lst)):
            lst.append(valueToAppend)
        return tuple(lst)



    def __filterData__(code = ''):
        print(colorama.Fore.LIGHTBLACK_EX + '[INFO]' + colorama.Fore.RESET + ' Filtering OGE Data...')

        data = {}
        for moyUE in code.find_all('div', attrs={'class': 'moy_UE'}):
            tags = []
            navigables = []

            for ue in moyUE.children:
                if isinstance(ue, Tag):
                    tags.append(ue)
                elif isinstance(ue, NavigableString):
                    navigables.append(ue)
                else:
                    Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + ' Couldn\'t find valid children in source code!')

            ueName, ueCoeff = OGE.__generateList__(findall('^[\w\s\.]+|\([0-9]+\.[0-9]+\)$', tags[0].text.strip()), 2, '(1.0)')
            ueName = OGE.__removeEndSpaces__(ueName)
            data[ueName] = {'coeff': float(ueCoeff.replace('(', '').replace(')', '')), 'pole': {}}


            for tag in tags[1:]:
                poleName = tag.find('thead').tr.th.attrs['aria-label']

                poleName, poleNameCoeff = OGE.__generateList__(findall('^[\w\s]+|\([0-9]+\.[0-9]+\)$', poleName), 2, '(1.0)')
                poleName = OGE.__removeEndSpaces__(poleName)

                data[ueName]['pole'][poleName] = {'matieres': [], 'coeff': float(poleNameCoeff.replace('(', '').replace(')', ''))}
                
                linesTab = [x for x in tag.find('tbody') if isinstance(x, Tag)]

                for lineTab in linesTab:
                    dataTab = [x for x in lineTab.find_all('td') if isinstance(x, Tag)]
                    lineName = OGE.__removeEndSpaces__(dataTab[0].text.strip())

                    try:
                        lineCoeff = float(dataTab[1].text.strip())
                    except:
                        lineCoeff = 1.0
                    matiere = {lineName: {'coeff': lineCoeff, 'notes': []}}

                    try:
                        noteS = repr(dataTab[2]).split('<br/>')
                    except:
                        noteS = []
                    

                    for note in noteS:
                        code = BS('<span>'+note, 'html.parser')
                        line = ' '.join(code.text.split())
                        titreNoteMatLst = findall('^[\w\s\-\,\.\;\:\!\?\/\\\\\(\)]+|\[.*\]|\([0-9]+\.[0-9]+\)$', line)
                        if titreNoteMatLst:
                            titre, notes, coeff = titreNoteMatLst
                            titre = OGE.__removeEndSpaces__(titre)
                            noteData = {titre: {'notes': [], 'coeff': float(coeff.replace('(', '').replace(')', ''))}}

                            noteLst = findall('([0-9]+\.[0-9]+)',notes)
                            for index in range(0, len(noteLst), 3):
                                note = float(noteLst[index])
                                max = float(noteLst[index + 1])
                                coeff = float(noteLst[index + 2])
                                noteData[titre]['notes'].append({'note': note, 'max': max, 'coeff': coeff})

                            matiere[lineName]['notes'].append(noteData)

                    data[ueName]['pole'][poleName]['matieres'].append(matiere)

        if data == {}: return print(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + ' An error occurred while retrieving information!\nThis error can occur with an incorrect username or an incorrect password.')
        print(colorama.Fore.GREEN + '[SUCCESS]' + colorama.Fore.RESET + ' Successfully got filtered information from OGE source code.')
        return data



    def connect(username = '', password = '', semestre = 1):
        html, OGE.__semestreCount__ = OGE.__getHtml__(username, password, semestre)
        OGE.__rawData__ = OGE.__filterData__(html)
        OGE.__currentSemester__ = semestre
        if OGE.__currentSemester__ > OGE.getSemestreCount(): OGE.__currentSemester__ = OGE.getSemestreCount()
        if OGE.__currentSemester__ < 1: OGE.__currentSemester__ = 1
        return OGE.__generateAll__()



    def __connectWarning__():
        return print(colorama.Fore.YELLOW + '[WARNING]' + colorama.Fore.RESET + ' You need to login to OGE to get data! Syntax: \'OGE.connect(username, password, semestre)\'.')



    def getSemestreCount():
        return OGE.__semestreCount__



    def getCurrentSemester():
        return OGE.__currentSemester__




    def getRawData():
        if OGE.__rawData__ == None:
            return OGE.__connectWarning__()
        return OGE.__rawData__



    def getData():
        if OGE.__rawData__ == None:
            return OGE.__connectWarning__()
        return OGE.__data__



    class __UE__:
        class __Pole__:
            class __Matiere__:
                class __GroupeNote__:
                    class __Note__:
                        def __init__(self, note = None, max = None, coeff = None) -> None:
                            self.note = note
                            self.max = max
                            self.coeff = coeff

                        def getStr(self) -> str:
                            return f'{self.note}/{self.max} ({self.coeff})'

                        def __str__(self) -> str:
                            return '{\n  ' + (f'note: {self.note},\nmax: {self.max},\ncoeff: {self.coeff}').replace('\n', '\n  ') + '\n}'


                    def __init__(self, nom = None, coeff = None, notes = None) -> None:
                        self.nom = nom
                        self.coeff = coeff
                        self.notes = []
                        for note in notes:
                            self.notes.append(self.__Note__(note['note'], note['max'], note['coeff']))

                    def getStr(self) -> str:
                        return f'[{self.nom}]\n' + ''.join(list(note.getStr() + '\n' for note in self.notes)) + '\n'

                    def __str__(self) -> str:
                        if OGE.strInDepth:
                            return '{\n' + (f'  nom: \'{self.nom}\',\n  coeff: \'{self.coeff}\',\n  notes: ' + ('[\n    ' + (''.join(list((str(note) + ',\n').replace('\n', '\n    ') for note in self.notes)))[:-6] + '\n  ]')) + '\n}'
                        return '{\n' + f'  nom: \'{self.nom}\',\n  notes: [List of Objects]' + '\n}'

                    def moyenne(self, max: float = 20.0, roundNote = True):
                        total, totalDiv = 0, 0
                        for note in self.notes:
                            if note.coeff == None: continue
                            total += note.note * note.coeff
                            totalDiv += note.max * note.coeff
                        if totalDiv == 0: return self.__Note__(0, 0, 0)
                        if roundNote:
                            return self.__Note__(round(total / totalDiv * max, 2), max, self.coeff)
                        return self.__Note__(total / totalDiv * max, max, self.coeff)

                    def note(self, noteId):
                        if (noteId - 1) not in list(range(len(self.notes))):
                            raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid Note ID! (Must be between 1 and {len(self.notes)})')

                        return self.notes[noteId - 1]

                    def findNoteByNom(self, noteName):
                        for note in self.notes:
                            if note.nom.lower() == noteName.lower(): return note
                        return None

                    def getNoteCount(self):
                        return len(self.notes)


                def __init__(self, nom = None, coeff = None, notes = None) -> None:
                    self.nom = nom
                    self.coeff = coeff
                    self.notes = []
                    for note in notes:
                        noteName = list(note.keys())[0]
                        self.notes.append(self.__GroupeNote__(noteName, note[noteName]['coeff'], note[noteName]['notes']))

                def getStr(self) -> str:
                    return f'{self.nom} ({self.coeff})\n\t' + ''.join(list(gNote.getStr().replace('\n', '\n\t') for gNote in self.notes)) + '\n'

                def __str__(self) -> str:
                    if OGE.strInDepth:
                        return '{\n' + (f'  nom: \'{self.nom}\',\n  coeff: {self.coeff},\n  notes: ' + ('[\n    ' + (''.join(list((str(note) + ',\n').replace('\n', '\n    ') for note in self.notes)))[:-6] + '\n  ]')) + '\n}'
                    return '{\n' + f'  nom: \'{self.nom}\',\n  coeff: \'{self.coeff}\',\n  notes: [List of Objects]' + '\n}'

                def moyenne(self, max: float = 20.0, roundNote = True):
                    total, totalDiv = 0, 0
                    for note in self.notes:
                        if note.coeff == None: continue
                        moy = note.moyenne(roundNote = False)
                        total += moy.note * moy.coeff
                        totalDiv += moy.max * moy.coeff
                    if totalDiv == 0: return self.__GroupeNote__.__Note__(0, 0, 0)
                    if roundNote:
                        return self.__GroupeNote__.__Note__(round(total / totalDiv * max, 2), max, self.coeff)
                    return self.__GroupeNote__.__Note__(total / totalDiv * max, max, self.coeff)

                def note(self, noteId):
                    if (noteId - 1) not in list(range(len(self.notes))):
                        raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid Note ID! (Must be between 1 and {len(self.notes)})')

                    return self.notes[noteId - 1]

                def findNoteByNom(self, noteName):
                    for note in self.notes:
                        if note.nom.lower() == noteName.lower(): return note
                    return None

                def getNoteCount(self):
                    return len(self.notes)



            def __init__(self, nom = None, coeff = None, matieres = None) -> None:
                self.nom = nom
                self.coeff = coeff
                self.matieres = []
                for matiere in matieres:
                    matiereName = list(matiere.keys())[0]
                    self.matieres.append(self.__Matiere__(matiereName, matiere[matiereName]['coeff'], matiere[matiereName]['notes']))

            def getStr(self) -> str:
                return f'{self.nom} ({self.coeff})\n\t' + ''.join(list(matiere.getStr() for matiere in self.matieres)).replace('\n', '\n\t') + '\n'

            def __str__(self) -> str:
                if OGE.strInDepth:
                    return '{\n' + (f'  nom: \'{self.nom}\',\n  coeff: {self.coeff},\n  matieres: ' + ('[\n    ' + (''.join(list((str(matiere) + ',\n').replace('\n', '\n    ') for matiere in self.matieres)))[:-6] + '\n  ]')) + '\n}'
                return '{\n' + f'  nom: \'{self.nom}\',\n  coeff: \'{self.coeff}\',\n  matieres: [List of Objects]' + '\n}'

            def moyenne(self, max: float = 20.0, roundNote = True):
                total, totalDiv = 0, 0
                for matiere in self.matieres:
                    if matiere.coeff == None: continue
                    moy = matiere.moyenne(roundNote = False)
                    total += moy.note * moy.coeff
                    totalDiv += moy.max * moy.coeff
                if totalDiv == 0: return self.__Matiere__.__GroupeNote__.__Note__(0, 0, 0)
                if roundNote:
                    return self.__Matiere__.__GroupeNote__.__Note__(round(total / totalDiv * max, 2), max, self.coeff)
                return self.__Matiere__.__GroupeNote__.__Note__(total / totalDiv * max, max, self.coeff)

            def matiere(self, matiereId):
                if (matiereId - 1) not in list(range(len(self.matieres))):
                    raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid Matiere ID! (Must be between 1 and {len(self.matieres)})')

                return self.matieres[matiereId - 1]

            def findMatiereByNom(self, matiereName):
                for matiere in self.matieres:
                    if matiere.nom.lower() == matiereName.lower(): return matiere
                return None

            def getMatiereCount(self):
                return len(self.matieres)


        def __init__(self, nom = None, coeff = None, poles = None) -> None:
            self.nom = nom
            self.coeff = coeff
            self.poles = []
            for pole in list(poles.keys()):
                self.poles.append(self.__Pole__(pole, poles[pole]['coeff'], poles[pole]['matieres']))

        def getStr(self) -> str:
            return f'{self.nom} ({self.coeff})\n\t' + ''.join(list(pole.getStr() for pole in self.poles)).replace('\n', '\n\t') + '\n'

        def __str__(self) -> str:
            if OGE.strInDepth:
                return '{\n' + (f'  nom: \'{self.nom}\',\n  coeff: \'{self.coeff}\',\n  poles: ' + ('[\n    ' + (''.join(list((str(pole) + ',\n').replace('\n', '\n    ') for pole in self.poles)))[:-6] + '\n  ]')) + '\n}'
            return '{\n' + f'  nom: \'{self.nom}\',\n  coeff: \'{self.coeff}\',\n  poles: [List of Objects]' + '\n}'

        def moyenne(self, max: float = 20.0, roundNote = True):
            total, totalDiv = 0, 0
            for pole in self.poles:
                if pole.coeff == None: continue
                moy = pole.moyenne(roundNote = False)
                total += moy.note * moy.coeff
                totalDiv += moy.max * moy.coeff
            if totalDiv == 0: return self.__Pole__.__Matiere__.__GroupeNote__.__Note__(0, 0, 0)
            if roundNote:
                return self.__Pole__.__Matiere__.__GroupeNote__.__Note__(round(total / totalDiv * max, 2), max, self.coeff)
            return self.__Pole__.__Matiere__.__GroupeNote__.__Note__(total / totalDiv * max, max, self.coeff)
        
        def pole(self, poleId):
            if (poleId - 1) not in list(range(len(self.poles))):
                raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid Pole ID! (Must be between 1 and {len(self.poles)})')

            return self.poles[poleId - 1]

        def findPoleByNom(self, poleName):
            for pole in self.poles:
                if pole.nom.lower() == poleName.lower(): return pole
            return None

        def getPoleCount(self):
            return len(self.poles)



    def moyenne(max: float = 20.0, roundNote = True):
        if OGE.__rawData__ == None:
            return OGE.__connectWarning__()
        total, totalDiv = 0, 0
        for ue in OGE.__data__:
            if ue.coeff == None: continue
            moy = ue.moyenne(roundNote = False)
            total += moy.note * moy.coeff
            totalDiv += moy.max * moy.coeff
        if totalDiv == 0: return OGE.__UE__.__Pole__.__Matiere__.__GroupeNote__.__Note__(0, 0, 0)
        if roundNote:
            return OGE.__UE__.__Pole__.__Matiere__.__GroupeNote__.__Note__(round(total / totalDiv * max, 2), max, 1.0)
        return OGE.__UE__.__Pole__.__Matiere__.__GroupeNote__.__Note__(total / totalDiv * max, max, 1.0)

    def UE(ueId: int = 1):
        if OGE.__rawData__ == None:
            return OGE.__connectWarning__()
        if (ueId - 1) not in list(range(len(list(OGE.__rawData__.keys())))):
            raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid UE ID! (Must be between 1 and {len(list(OGE.__rawData__.keys()))})')

        return OGE.__data__[ueId - 1]

    def getUECount():
        return len(OGE.__data__)

    def findUEByNom(self, ueName):
        if OGE.__rawData__ == None:
            return OGE.__connectWarning__()
        for ue in OGE.__data__:
            if ue.nom.lower() == ueName.lower(): return ue
        return None



    def __generateAll__():
        def __generateUE__(ueId: int = 0):
            ueName = list(sorted(OGE.__rawData__.keys()))[ueId]
            return OGE.__UE__(ueName, OGE.__rawData__[ueName]['coeff'], OGE.__rawData__[ueName]['pole'])

        data = []
        for ueId in range(len(list(OGE.__rawData__.keys()))):
            data.append(__generateUE__(ueId))
        OGE.__data__ = data

        return data



    def saveData(path = None):
        if OGE.__rawData__ == None:
            return OGE.__connectWarning__()
        if path == None: raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid path!')
        with open(path, 'w', encoding = 'utf-8') as outfile:
            json.dump(OGE.__rawData__, outfile, indent = 4, sort_keys = True, ensure_ascii = False)



    def loadData(path = None):
        if path == None: raise Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' Invalid path!')
        if not os.path.exists(path): Exception(colorama.Fore.RED + '[ERROR]' + colorama.Fore.RESET + f' This path doesn\' exist!')
        with open(path, 'r', encoding = 'utf-8') as infile:
            OGE.__rawData__ = json.load(infile)
        return OGE.__generateAll__()



    def isData():
        return OGE.__data__ != None
#----------------------------------------------------------------------
