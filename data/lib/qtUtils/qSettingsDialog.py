#----------------------------------------------------------------------

    # Libraries
from PyQt6.QtWidgets import QDialog, QTabWidget, QLabel, QComboBox, QDialogButtonBox, QGridLayout
from PyQt6.QtCore import Qt
from .qScrollableGridWidget import QScrollableGridWidget
import json

from inspect import getsourcefile
import os.path as path, sys
current_dir = path.dirname(path.abspath(getsourcefile(lambda:0)))
sys.path.insert(0, current_dir[:current_dir.rfind(path.sep)])
from customOS import *
sys.path.pop(0)

#----------------------------------------------------------------------

    # Class
class QSettingsResponse:
    def __init__(self, lang = '', theme = '', themeVariant = ''):
        self.lang = lang
        self.theme = theme
        self.themeVariant = themeVariant


class __QData__:
    class __QLang__:
        def __init__(self, langFolder = '', langPath = ''):
            with open(f'{langFolder}/{langPath}', encoding = 'utf-8') as infile:
                data = json.load(infile)
                self.displayName = data['info']['name']
                self.version = data['info']['version']
                self.desc = data['info']['description']
                self.filename = '.'.join(langPath.split('.')[:-1])


    class __QTheme__:
        def __init__(self, themesFolder = '', themePath = ''):
            with open(f'{themesFolder}/{themePath}', encoding = 'utf-8') as infile:
                data = json.load(infile)
                self.displayName = data['info']['name']
                self.version = data['info']['version']
                self.desc = data['info']['description']
                self.filename = '.'.join(themePath.split('.')[:-1])
                self.variants = data['qss']


    def __init__(self, langFolder = '', themesFolder = ''):
        self.lang = []
        for file in get.files.extensions(langFolder, ['.json'], False, True):
            self.lang.append(self.__QLang__(langFolder, file))

        self.themes = []
        for file in get.files.extensions(themesFolder, ['.json'], False, True):
            self.themes.append(self.__QTheme__(themesFolder, file))


class QSettingsDialog(QDialog):
    def __init__(self, parent = None, settingsData = {}, langFolder = '', themesFolder = '', currentLang = '', currentTheme = '', currentThemeVariant = ''):
        super().__init__(parent)

        self.layout = QGridLayout()

        QBtn = QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setWindowTitle(settingsData['title'])

        self.tabs = QTabWidget()
        self.__data__ = __QData__(langFolder, themesFolder)
        self.langTab = self.__langTabWidget__(settingsData['langTab'], currentLang)
        self.tabs.addTab(self.langTab, 'Tab 1')
        self.tabs.setTabText(1, settingsData['langTab']['title'])
        self.themesTab = self.__themesTabWidget__(settingsData['themesTab'], currentTheme, currentThemeVariant)
        self.tabs.addTab(self.themesTab, 'Tab 2')
        self.tabs.setTabText(2, settingsData['themesTab']['title'])

        self.layout.addWidget(self.tabs, 0, 0)

        self.layout.addWidget(self.buttonBox, 1, 0)

        self.setLayout(self.layout)

    def __langTabWidget__(self, langData = {}, currentLang = ''):
        widget = QScrollableGridWidget()
        label = QLabel(langData['QLabel']['lang'])
        widget.scrollLayout.addWidget(label, 0, 0)

        self.langDropdown = QComboBox()
        self.langDropdown.addItems(list(lang.displayName for lang in self.__data__.lang))
        i = 0
        for langId in range(len(self.__data__.lang)):
            if self.__data__.lang[langId].filename == currentLang: i = langId
        self.langDropdown.setCurrentIndex(i)
        widget.scrollLayout.addWidget(self.langDropdown, 0, 1)

        return widget

    def __themesTabWidget__(self, themesData = {}, currentTheme = '', currentThemeVariant = ''):
        widget = QScrollableGridWidget()
        label = QLabel(themesData['QLabel']['themes'])
        widget.scrollLayout.addWidget(label, 0, 0)

        self.themesDropdown = QComboBox()
        self.themesDropdown.addItems(list(theme.displayName for theme in self.__data__.themes))
        i = 0
        for themeId in range(len(self.__data__.themes)):
            if self.__data__.themes[themeId].filename == currentTheme: i = themeId
        self.themesDropdown.setCurrentIndex(i)
        self.themesDropdown.currentIndexChanged.connect(self.__loadThemeVariants__)
        widget.scrollLayout.addWidget(self.themesDropdown, 0, 1)

        label = QLabel(themesData['QLabel']['themeVariants'])
        widget.scrollLayout.addWidget(label, 1, 0)

        self.themeVariantsDropdown = QComboBox()
        self.__loadThemeVariants__(i)
        self.themeVariantsDropdown.setCurrentIndex(list(self.__data__.themes[i].variants.keys()).index(currentThemeVariant))
        widget.scrollLayout.addWidget(self.themeVariantsDropdown, 1, 1)

        return widget

    def __loadThemeVariants__(self, index):
        self.themeVariantsDropdown.clear()
        self.themeVariantsDropdown.addItems(list(self.__data__.themes[index].variants[variant]['displayName'] for variant in self.__data__.themes[index].variants.keys()))
        self.themeVariantsDropdown.setCurrentIndex(0)

    def get(self):
        if self.exec():
            return QSettingsResponse(
                self.__data__.lang[self.langDropdown.currentIndex()].filename,
                self.__data__.themes[self.themesDropdown.currentIndex()].filename,
                list(self.__data__.themes[self.themesDropdown.currentIndex()].variants.keys())[self.themeVariantsDropdown.currentIndex()]
            )
        return None
#----------------------------------------------------------------------
