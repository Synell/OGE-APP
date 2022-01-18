from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from data.lib import *
from sys import exit
import json
from pyautogui import *



class loginData:
    username = ''
    password = ''



class SaveData:
    path = './data/save.dat'
    def __init__(self):
        self.username = ''
        self.language = 'english'
        self.theme = 'winRounded'
        self.themeVariant = 'dark'

        self.load()

    def save(self):
        with open(self.path, 'w', encoding = 'utf-8') as outfile:
            json.dump({'username': self.username, 'language': self.language, 'theme': self.theme, 'themeVariant': self.themeVariant}, outfile, indent = 4, sort_keys = True, ensure_ascii = False)

    def load(self):
        if not os.path.exists(self.path): self.save()
        with open(self.path, 'r', encoding = 'utf-8') as infile:
            data = json.load(infile)
        self.username = data['username']
        self.language = data['language']
        self.theme = data['theme']
        self.themeVariant = data['themeVariant']
        self.loadLanguageData()
        self.loadThemeData()

    def loadLanguageData(self):
        with open(f'./data/lang/{self.language}.json', 'r', encoding = 'utf-8') as infile:
            self.languageData = json.load(infile)['data']

    def loadThemeData(self):
        self.themeData = ''
        with open(f'./data/themes/{self.theme}.json', 'r', encoding = 'utf-8') as infile:
            data = json.load(infile)['qss']
            path = data[self.themeVariant]['filename']
            if 'qUtils' in list(data[self.themeVariant].keys()): loadQUtils = True
            else: loadQUtils = False

        if loadQUtils:
            varPath = data[self.themeVariant]['qUtils']
            with open(f'./data/lib/qtUtils/themes/{varPath}', 'r', encoding = 'utf-8') as infile:
                self.themeData += infile.read() + '\n'

        with open(f'./data/themes/{self.theme}/{path}', 'r', encoding = 'utf-8') as infile:
            self.themeData += infile.read()



class Application(QBaseApplication):
    def __init__(self):
        super().__init__()

        self.saveData = SaveData()

        self.window.setWindowTitle(self.saveData.languageData['QMainWindow']['title'])

        self.setStyleSheet(self.saveData.themeData)

        self.currentSemesterIndex = None

        self.createWidgets()
        self.createMenuBar()


    def createMenuBar(self):
        menuBar = self.window.menuBar()
        fileMenu = menuBar.addMenu(self.saveData.languageData['QMainWindow']['QMenuBar']['file'])

        action = QAction(self.saveData.languageData['QMainWindow']['QMenuBar']['import'], self.window)
        action.triggered.connect(self.importMenu)
        fileMenu.addAction(action)

        action = QAction(self.saveData.languageData['QMainWindow']['QMenuBar']['export'], self.window)
        action.triggered.connect(self.exportMenu)
        fileMenu.addAction(action)

        fileMenu.addSeparator()

        action = QAction(self.saveData.languageData['QMainWindow']['QMenuBar']['connectOGE'], self.window)
        action.triggered.connect(self.connectToOGE)
        fileMenu.addAction(action)

        fileMenu.addSeparator()

        action = QAction(self.saveData.languageData['QMainWindow']['QMenuBar']['settings'], self.window)
        action.triggered.connect(self.settingsMenu)
        fileMenu.addAction(action)

        fileMenu.addSeparator()

        action = QAction(self.saveData.languageData['QMainWindow']['QMenuBar']['exit'], self.window)
        action.setShortcut('Ctrl+Q')
        action.triggered.connect(self.window.close)
        fileMenu.addAction(action)


    def createWidgets(self):
        self.window.widget = QScrollableGridWidget()

        self.window.showMaximized()

        self.window.setCentralWidget(self.window.widget)


    def clearWidget(self):
        layout = self.window.widget.scrollLayout
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


    def drawMainWindow(self, semesterId = None):
        self.clearWidget()

        if semesterId != False:
            self.semesterCombobox = QComboBox()
            for semester in range(OGE.getSemestreCount()):
                self.semesterCombobox.addItem(self.saveData.languageData['QMainWindow']['QComboBox']['semester'] + f' {semester + 1}')
            if semesterId == None: self.semesterCombobox.setCurrentIndex(OGE.getSemestreCount() - 1)
            else: self.semesterCombobox.setCurrentIndex(semesterId - 1)
            self.currentSemesterIndex = self.semesterCombobox.currentIndex()
            self.semesterCombobox.currentIndexChanged.connect(self.semesterChanged)
            self.window.widget.scrollLayout.addWidget(self.semesterCombobox, 0, 0)
            moy = OGE.moyenne()
            label = QLabel(self.saveData.languageData['QMainWindow']['overallAVG'] + f': {moy.note}/{moy.max} ({moy.coeff})')
            self.window.widget.scrollLayout.addWidget(label, 1, 0)

        for ue in range(len(OGE.getData())):
            ueWidget = self.generateUETable(OGE.UE(ue + 1))
            self.window.widget.scrollLayout.addWidget(ueWidget, ue + 2, 0)


    def semesterChanged(self, semester):
        return self.loadOGEData(loginData.username, loginData.password, semester + 1)



    def generateUETable(self, ue):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setObjectName('outline')

        moy = ue.moyenne()
        label = QLabel(f'{ue.nom} - {moy.note}/{moy.max} ({ue.coeff})')
        label.setObjectName('th')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, 0, 0)

        for pole in range(len(ue.poles)):
            item = self.generatePoleTable(ue.poles[pole])
            layout.addWidget(item, pole + 1, 0)
        return widget


    def generatePoleTable(self, pole):
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)

        titles = [pole.nom, 'Coeff', 'Notes', 'Moyenne']

        for titleId in range(len(titles)):
            label = QLabel(titles[titleId])
            label.setObjectName('th')
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if titleId == len(titles) - 1: layout.addWidget(label, 0, titleId, 1, 3)
            else: layout.addWidget(label, 0, titleId)

        y = 1
        itemClear = True

        for matiere in pole.matieres:
            # Titre de la Matière
            label = QLabel(matiere.nom)
            if itemClear: label.setObjectName('tr1')
            else: label.setObjectName('tr2')
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label, y, 0, len(matiere.notes), 1)

            # Coeff de la Matière
            label = QLabel(str(matiere.coeff))
            if itemClear: label.setObjectName('tr1')
            else: label.setObjectName('tr2')
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label, y, 1, len(matiere.notes), 1)

            # Notes de la Matière + Moyenne du Groupe de Notes
            for gNoteId, gNote in enumerate(matiere.notes):
                s = f'{gNote.nom} [ '
                for note in gNote.notes:
                    s += f'{note.note}/{note.max} ({note.coeff}) | '
                s = s[:-3] + f' ] ({gNote.coeff})'

                label = QLabel(s)
                if itemClear: label.setObjectName('tr1')
                else: label.setObjectName('tr2')
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                layout.addWidget(label, y + gNoteId, 2)

                moy = gNote.moyenne()
                label = QLabel(f'{moy.note}/{moy.max} ({moy.coeff})')
                if itemClear: label.setObjectName('tr1')
                else: label.setObjectName('tr2')
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label, y + gNoteId, 3)

            if len(matiere.notes) == 0:
                label = QLabel('')
                if itemClear: label.setObjectName('tr1')
                else: label.setObjectName('tr2')
                label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
                layout.addWidget(label, y, 2)

                label = QLabel('')
                if itemClear: label.setObjectName('tr1')
                else: label.setObjectName('tr2')
                label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(label, y, 3)

            # Moyenne de la Matière
            moy = matiere.moyenne()
            label = QLabel(f'{moy.note}/{moy.max} ({moy.coeff})')
            if itemClear: label.setObjectName('tr1')
            else: label.setObjectName('tr2')
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(label, y, 4, len(matiere.notes), 1)

            itemClear = not itemClear
            y += len(matiere.notes)

        # Moyenne du Pôle
        moy = pole.moyenne()
        label = QLabel(f'{moy.note}/{moy.max} ({moy.coeff})')
        label.setObjectName('tr1')
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label, 1, 5, y, 1)

        return widget


    def connectToOGE(self):
        response = QLoginDialog(self.window, langData = self.saveData.languageData['QLoginDialog'], username = self.saveData.username, rememberChecked = bool(self.saveData.username), rememberCheck = True).getText()
        if response:
            if response.rememberChecked:
                self.saveData.username = response.username
            else:
                self.saveData.username = ''
            loginData.username = response.username
            loginData.password = response.password
            self.saveData.save()
            self.loadOGEData(response.username, response.password, 99)


    def loadOGEData(self, username = '', password = '', semester = 99):
        self.window.setWindowTitle(self.saveData.languageData['QMainWindow']['loadDataOGE'])
        try:
            OGE.connect(username, password, semester)
            if OGE.isData():
                if semester == 99: self.drawMainWindow(None)
                else: self.drawMainWindow(semester)
            else:
                QMessageBox.critical(self.window,
                    self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantConnect']['title'],
                    self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantConnect']['message'],
                    QMessageBox.StandardButton.Ok
                )
        except:
            QMessageBox.critical(self.window,
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantConnect']['title'],
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantConnect']['message'],
                QMessageBox.StandardButton.Ok
            )
        self.window.setWindowTitle(self.saveData.languageData['QMainWindow']['title'])


    def importMenu(self):
        path = QFileDialog.getOpenFileName(self.window, self.saveData.languageData['QMainWindow']['QFileDialog']['import'], '', 'JSON Files (*.json)')
        if path[0] == '': return
        try:
            OGE.loadData(path[0])
            self.drawMainWindow(False)
        except:
            QMessageBox.critical(self.window,
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantLoadData']['title'],
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantLoadData']['message'],
                QMessageBox.StandardButton.Ok
            )


    def exportMenu(self):
        if not OGE.isData(): return QMessageBox.critical(self.window,
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['noData']['title'],
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['noData']['message'],
                QMessageBox.StandardButton.Ok
            )
        path = QFileDialog.getSaveFileName(self.window, self.saveData.languageData['QMainWindow']['QFileDialog']['export'], '', 'JSON Files (*.json)')
        if path[0] == '': return
        try:
            OGE.saveData(path[0])
        except:
            QMessageBox.critical(self.window,
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantSaveData']['title'],
                self.saveData.languageData['QLoginDialog']['QMessageBox']['critical']['cantSaveData']['message'],
                QMessageBox.StandardButton.Ok
            )

    def settingsMenu(self):
        response = QSettingsDialog(self.window, self.saveData.languageData['QSettingsDialog'], './data/lang/', './data/themes/',
            self.saveData.language, self.saveData.theme, self.saveData.themeVariant
        ).get()
        if response != None:
            self.saveData.language = response.lang
            self.saveData.theme = response.theme
            self.saveData.themeVariant = response.themeVariant
            self.saveData.save()
            self.saveData.load()
            self.setStyleSheet(self.saveData.themeData)
            QMessageBox.information(self.window,
                self.saveData.languageData['QLoginDialog']['QMessageBox']['information']['settingsReload']['title'],
                self.saveData.languageData['QLoginDialog']['QMessageBox']['information']['settingsReload']['message'],
                QMessageBox.StandardButton.Ok
            )





def except_hook(cls, exception, traceback):
    import sys
    sys.__excepthook__(cls, exception, traceback)

def main():
    import sys

    sys.excepthook = except_hook
    app = Application()
    app.window.show()

    exit(app.exec())



if __name__ == "__main__":
    main()


