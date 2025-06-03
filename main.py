from api import VtAPI

def initAPI(api):
    global pythonPath, QtWidgets, QtCore, vtApi, os, sys, subprocess
    vtApi = api # type: VtAPI ;  Secure typing
    pythonPath = ""
    QtWidgets = vtApi.importModule("PySide6.QtWidgets")
    QtCore =    vtApi.importModule("PySide6.QtCore")
    subprocess= vtApi.importModule("subprocess")
    sys =       vtApi.importModule("sys")
    os =        vtApi.importModule("os")

    window = vtApi.activeWindow # type: VtAPI.Window ; Secure typing

    window.registerCommandClass({"command": GetPythonCommand})
    window.registerCommandClass({"command": RunPyFileCommand})
    window.registerCommandClass({"command": ShowPPthDlgCommand})

    window.signals.windowStateSaving.connect(onStateSaving)
    window.signals.windowStateRestoring.connect(onStateRestore)

def onStateRestore():
    global pythonPath
    pythonPath = vtApi.findKey("state.plugins.PythonIDE.pythonPath", vtApi.activeWindow.state())
    if not pythonPath:
        vtApi.activeWindow.runCommand({"command": "GetPythonCommand", "kwargs": {"path": "state.plugins.PythonIDE.pythonPath"}})
        pythonPath = vtApi.findKey("state.plugins.PythonIDE.pythonPath", vtApi.activeWindow.state())

def onStateSaving():
    global pythonPath
    vtApi.addKey("state.plugins.PythonIDE.pythonPath", pythonPath, vtApi.CLOSINGSTATEFILE)
    if not pythonPath:
        vtApi.activeWindow.runCommand({"command": "GetPythonCommand", "kwargs": {"path": "state.plugins.PythonIDE.pythonPath"}})
        pythonPath = vtApi.findKey("state.plugins.PythonIDE.pythonPath", vtApi.activeWindow.state())

class GetPythonCommand(VtAPI.Plugin.ApplicationCommand):
    def run(self, path=None):
        self.api: VtAPI
        self.path = path
        system_type = self.api.platform()
        if system_type == "Windows": return self.find_python_windows()
        elif system_type in ("Linux", "Darwin"): return self.find_python_unix()
        else: return "", ""

    def find_python_windows(self):
        paths = os.environ["PATH"].split(os.pathsep)
        for path in paths:
            python_exe = self.api.Path.joinPath(path, "python.exe")
            if self.api.Path(python_exe).exists():
                try:
                    self.api.addKey(self.path, python_exe, vtApi.activeWindow.state())
                except subprocess.SubprocessError:
                    continue

    def find_python_unix(self):
        try:
            python_path = subprocess.check_output(["which", "python3"]).decode().strip()
            if python_path:
                self.api.addKey(self.path, python_path, vtApi.activeWindow.state())
        except subprocess.CalledProcessError:
            pass

        try:
            python_path = subprocess.check_output(["which", "python"]).decode().strip()
            if python_path:
                version = subprocess.check_output([python_path, "--version"]).decode().strip()
                self.api.addKey(self.path, python_path, vtApi.activeWindow.state())
        except subprocess.CalledProcessError:
            pass
        return "", ""

class ShowPPthDlgCommand(VtAPI.Plugin.WindowCommand):
    def run(self):
        mLayout = self.setupUi()
        self.window.showDialog(content=mLayout, width=400, height=141)
    def setupUi(self):
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.frame = QtWidgets.QFrame()
        self.frame.setFrameShape(QtWidgets.QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QtWidgets.QFrame.Shadow.Raised)
        self.frame.setObjectName("frame")
        self.verticalLayout_2 = QtWidgets.QVBoxLayout(self.frame)
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.label = QtWidgets.QLabel(parent=self.frame)
        self.label.setObjectName("label")
        self.verticalLayout_2.addWidget(self.label)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.lineEdit = QtWidgets.QLineEdit(parent=self.frame)
        self.lineEdit.setObjectName("comboBox")
        self.lineEdit.insert(pythonPath)
        self.horizontalLayout.addWidget(self.lineEdit)
        self.pushButton = QtWidgets.QPushButton(parent=self.frame)
        self.pushButton.setMaximumSize(QtCore.QSize(50, 16777215))
        self.pushButton.clicked.connect(self.customPythonPath)
        self.pushButton.setObjectName("pushButton")
        self.horizontalLayout.addWidget(self.pushButton)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.pushButton_2 = QtWidgets.QPushButton(parent=self.frame)
        self.pushButton_2.clicked.connect(self.savePath)
        self.pushButton_2.setObjectName("pushButton_2")
        self.verticalLayout_2.addWidget(self.pushButton_2)
        self.verticalLayout.addWidget(self.frame)

        self.retranslateUi()
        return self.verticalLayout

    def retranslateUi(self):
        _translate = QtCore.QCoreApplication.translate
        self.label.setText(_translate("self", "Choose Python path"))
        self.pushButton.setText(_translate("self", "Add"))
        self.pushButton_2.setText(_translate("self", "Save"))

    def customPythonPath(self):
        path = self.api.Dialogs.openFileDialog()
        if path[0]:
            self.lineEdit.clear()
            self.lineEdit.insert(path[0][0])

    def savePath(self):
        global pythonPath
        t = self.lineEdit.text()
        if t:
            pythonPath = t
        vtApi.Dialogs.infoMessage(string=vtApi.activeWindow.translate("Saved Python path"))

class RunPyFileCommand(VtAPI.Plugin.TextCommand):
    def run(self):
        if self.api.activeWindow.activeView:
            process = self.api.Widgets.Process()
            script_path = self.view.getFile()
            sys.path.insert(0, pythonPath)

            if os.name == 'nt':  #  Windows
                cmd_command = f"start cmd.exe /k python {script_path} & timeout /t -1"
                process.start("cmd.exe", ["/c", cmd_command])
            else:  #  Linux   
                bash_command = f"bash -c \"python3 {script_path}; read -p 'Press Enter to continue...'\""
                process.start("x-terminal-emulator", ["-e", bash_command])

            process.waitForFinished()

