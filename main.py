#!/usr/local/bin/python
# coding: utf-8
import wx
import os
import sys
import hashlib
import json
import shutil
import zipfile


class Main(wx.App):
    HGap = 20
    VGap = 20

    def OnInit(self):
        frame = wx.Frame(parent=None, title="cocos2d manifest")
        self.frame = frame

        frame.SetSize((500, 400))
        self.winSize = frame.GetSize()
        frame.Show()
        self.InitViews()
        return True

    def InitViews(self):
        projectPathLbl = wx.StaticText(self.frame)
        projectPathLbl.SetLabel("manifest:")
        projectPathLbl.SetPosition((self.VGap, self.HGap))
        pathLblSize = projectPathLbl.GetSize()

        selectProject = wx.Button(self.frame)
        selectProject.SetLabel("选择")
        selectProject.Bind(wx.EVT_BUTTON, self.selectProjectDir)
        btnSize = selectProject.GetSize()
        selectProject.SetPosition((self.winSize.width - btnSize.width - self.HGap, self.HGap))

        projectPathTxt = wx.TextCtrl(self.frame)
        projectPathTxt.SetPosition((pathLblSize.width + projectPathLbl.GetPosition().x + 5, self.VGap))
        projectPathTxt.SetSizeWH(self.winSize.width - btnSize.width - pathLblSize.width - self.HGap * 2 - 10, -1)
        self.projectPathTxt = projectPathTxt
        manifestDt = ManifestDropTarget(projectPathTxt)
        projectPathTxt.SetDropTarget(manifestDt)

        filesPathList = wx.ListBox(self.frame)
        self.filesPathList = filesPathList
        filesPathList.SetPosition(
            (projectPathLbl.GetPosition().x, projectPathLbl.GetPosition().y + pathLblSize.height + 16))
        filesPathList.SetSizeWH(self.winSize.width - self.HGap * 2, self.winSize.height - 2 * self.HGap - 100)

        createBtn = wx.Button(self.frame)
        createBtn.SetLabel("生成")
        createSize = createBtn.GetSize()
        createBtn.SetPosition(
            (
                self.winSize.width - self.HGap - createSize.width,
                self.winSize.height - createSize.height * 2 - self.VGap))
        createBtn.Bind(wx.EVT_BUTTON, self.createManifest)

        versiontxt = wx.TextCtrl(self.frame)
        self.versiontxt = versiontxt
        versiontxt.SetSizeWH(60, -1)
        versiontxt.SetPosition((createBtn.GetPosition().x - 60 - 10, createBtn.GetPosition().y))

        versionLbl = wx.StaticText(self.frame)
        versionLbl.SetLabel("版本:")
        versionLbl.SetPosition(
            (versiontxt.GetPosition().y - versionLbl.GetSize().width - 15, versiontxt.GetPosition().y))

        dt = JsFileDropTarget(self.filesPathList, self.projectPathTxt)
        self.dt = dt
        self.filesPathList.SetDropTarget(dt)

    def selectProjectDir(self, event):
        fileDlg = wx.FileDialog(self.frame, message="选择project.manifest", style=wx.CHANGE_DIR | wx.OPEN)
        fileDlg.SetWildcard("*.manifest")
        if fileDlg.ShowModal() == wx.ID_OK:
            filePath = fileDlg.GetPath()
            fileName = os.path.basename(filePath)
            if fileName == "project.manifest" or fileName == "version.manifest":
                self.projectPathTxt.SetValue(filePath)
                self.projectPathTxt.SetInsertionPointEnd()
            fileDlg.Destroy()

    def createManifest(self, event):
        if self.versiontxt.GetValue() == "":
            wx.MessageBox("版本号不能为空", caption="错误", style=wx.ICON_ERROR)
            return
        projectPath = self.projectPathTxt.GetValue()
        projectRoot = projectPath[:projectPath.index("res/")]
        updateDir = projectRoot + "updatecocos"

        if os.path.basename(projectPath) == "version.manifest":
            projectPath = os.path.dirname(projectPath) + "/project.manifest"
        if not os.path.exists(projectPath):
            wx.MessageBox("该工程目录不存在", caption="错误", style=wx.ICON_ERROR)
            return
        if os.path.exists(updateDir):
            shutil.rmtree(updateDir)
        os.mkdir(updateDir)
        try:
            fileJSONData = None
            with open(projectPath, "r+") as manifestFile:
                manifestData = manifestFile.read()
                fileJSONData = json.loads(manifestData)
                fileJSONData["version"] = self.versiontxt.GetValue()

                files = self.dt.getAllFiles()
                updateFiles = []
                for fileDic in files:
                    for key in fileDic:
                        filePath = fileDic[key]
                        fileName = os.path.basename(filePath)
                        targetPath = updateDir+"/"+key
                        self.mkdirs(targetPath.replace(fileName, ""))
                        if os.path.exists(targetPath):
                            os.remove(targetPath)

                        shutil.copy(filePath, targetPath)
                        updateFiles.append(targetPath)
                os.system("cocos jscompile -s " + updateDir + " -d " + updateDir)
                for targetFile in updateFiles:
                    if not os.path.exists(targetFile):
                        wx.MessageBox(targetFile + u"不存在", caption="错误", style=wx.ICON_ERROR)
                        return
                    extendName = targetFile[targetFile.rfind('.'):]
                    mFile = targetFile
                    if extendName == "js":
                        mFile = mFile.replace("js", "jsc")
                    with open(mFile, "rb") as updateFile:
                        m2 = hashlib.md5()
                        m2.update(updateFile.read())
                        newFile = {"md5": m2.hexdigest()}
                        if filePath[filePath.rfind('.'):] == ".zip":
                            newFile["compressed"] = True
                        fileJSONData["assets"][key] = newFile
                    if(targetFile[targetFile.rfind('.'):] == ".js") :
                        os.remove(targetFile)
                manifestFile.seek(0)
                manifestFile.write(json.dumps(fileJSONData))

            targetPath = updateDir + "/" + projectPath.replace(projectRoot, "")
            self.mkdirs(targetPath.replace(os.path.basename(projectPath), ""))
            if os.path.exists(targetPath):
                os.remove(targetPath)
            targetVersionPath = targetPath.replace("project", "version")
            if os.path.exists(targetVersionPath):
                os.remove(targetVersionPath)

            shutil.copy(os.path.dirname(projectPath) + "/version.manifest", targetVersionPath)
            shutil.copy(projectPath, targetPath)
            zip = zipfile.ZipFile(updateDir + '.zip', 'w', zipfile.ZIP_DEFLATED)
            for root, dirs, files in os.walk(updateDir):
                for f in files:
                    zip.write(os.path.join(root, f), os.path.join(root, f).replace(updateDir + os.sep, ''))
            zip.close()
        except Exception as e:
            print e.message

    def mkdirs(self, path):
        # 去除首位空格
        path = path.strip()
        # 去除尾部 \ 符号
        path = path.rstrip("\\")

        # 判断路径是否存在
        # 存在     True
        # 不存在   False
        isExists = os.path.exists(path)

        # 判断结果
        if not isExists:
            # 创建目录操作函数
            os.makedirs(path)
            # 如果不存在则创建目录
            print path + u' 创建成功'
            return True
        else:
            # 如果目录存在则不创建，并提示目录已存在
            print path + u' 目录已存在'
            return False


class ManifestDropTarget(wx.FileDropTarget):
    def __init__(self, source):
        wx.FileDropTarget.__init__(self)
        self.source = source

    def OnDropFiles(self, *args, **kwargs):
        self.source.SetValue(args[2][0])


class JsFileDropTarget(wx.FileDropTarget):
    def __init__(self, source, preDir):
        wx.FileDropTarget.__init__(self)
        self.source = source
        self.preDir = preDir
        self.files = []

    def getAllFiles(self):
        return self.files

    def deleteFileWithIndex(self, index):
        self.files.remove(index)

    def OnDropFiles(self, *args, **kwargs):
        manifestpath = self.preDir.GetValue()
        if not os.path.exists(manifestpath):
            wx.MessageBox("该文件不存在", caption="错误", style=wx.ICON_ERROR)
            return
        dirpath = manifestpath[:manifestpath.index("res/")]
        if isinstance(self.source, wx.ListBox):
            files = args[2]
            filepath = files[0]
            index = filepath.index(dirpath)
            if index < 0:
                wx.MessageBox("该文件不在同一工程目录下", caption="错误", style=wx.ICON_ERROR)
                return

            result = filepath.replace(dirpath, "")
            self.files.append({result: filepath})
            self.source.Append(result)


if __name__ == "__main__":
    app = Main()
    app.MainLoop()
