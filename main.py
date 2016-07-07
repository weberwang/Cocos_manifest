# coding: utf-8
import os
import hashlib
import json
import shutil
import zipfile
import sys
import lxml.objectify as objectify

# 需要更新的最小svn版本号
if len(sys.argv) > 1:
    svnVersion = sys.argv[1]
else:
    svnVersion = 200

modules = ['lobby', 'bmw']  # 已有模块常量
# modules = sys.argv[2:]  # 需要更新的模块
#
# if len(modules) == 0:
#     modules = ['lobby']


# projectPath = os.getcwd()
projectPath = os.path.abspath(os.path.join(os.getcwd(), os.pardir))
os.chdir(projectPath)
relativeurl = None
svnCommand = 'svn log {0} -r{1}:"HEAD" -v -q --xml'
updatedir = os.path.join(projectPath, "updateCocos")
deleteFiles = set()
mainfestAddData = {}  # 更新添加的字段


def svnInfo():
    svnInfoStr = os.popen("svn info --xml").read()
    svnInfoXml = objectify.fromstring(svnInfoStr.encode("utf-8"))
    global relativeurl
    relativeurl = svnInfoXml.entry.find("relative-url").text
    relativeurl = relativeurl.replace("^", "")
    pass


def packageFiles():
    mainfiles = findGreaterFiles('main.js')
    srcfiles = findGreaterFiles('src/')
    resfiles = findGreaterFiles('res/')
    allfiles = mainfiles.union(srcfiles).union(resfiles)
    copyallfiles(allfiles)
    compilejs(allfiles)
    pass


def findGreaterFiles(path):
    filesSet = set()
    logStr = os.popen(svnCommand.format(path, svnVersion)).read()
    logXml = objectify.fromstring(logStr.encode('utf-8'))
    logs = logXml.getchildren()
    for log in logs:
        paths = log.findall('paths')
        for path in paths:
            path = path.findall('path')
            for pathEl in path:
                filePath = pathEl.text.replace(relativeurl + "/", '')
                if filePath.find('cocosstudio') >= 0:
                    continue
                if pathEl.get('action') != 'D':
                    filesSet.add(filePath)
                else:
                    deleteFiles.add(filePath)

    return filesSet
    pass


def copyallfiles(files):
    if os.path.exists(updatedir):
        shutil.rmtree(updatedir)
    os.mkdir(updatedir)
    for filePath in files:
        targetPath = os.path.join(updatedir, filePath)
        sourcePath = os.path.join(projectPath, filePath)
        fileName = os.path.basename(sourcePath)
        mkdirs(targetPath.replace(fileName, ""))
        shutil.copyfile(sourcePath, targetPath)
    pass


def compilejs(files):
    os.system("cocos jscompile -s " + updatedir + " -d " + updatedir)
    for filePath in files:
        # filePath = filePath #os.path.join(updatedir, filePath)
        fileextendName = filePath[filePath.rfind("."):]
        if fileextendName == '.js':
            os.remove(os.path.join(updatedir, filePath))
        checkFileModule(filePath)

    for module in modules:
        manifestFile = None
        if module == 'lobby':
            manifestFile = os.path.join(updatedir, 'res', 'project.manifest')
            pass
        else:
            manifestFile = os.path.join(updatedir, 'res', module, 'project.manifest')
            pass
        if not os.path.exists(manifestFile):
            shutil.copyfile(os.path.join(projectPath, 'manifest', 'version.manifest'),
                            manifestFile.replace('project.manifest', 'version.manifest'))
            shutil.copyfile(os.path.join(projectPath, 'manifest', 'project.manifest'), manifestFile)
        with open(manifestFile, "r+") as manifest:
            manifestData = manifest.read()
            asset = '"assets" : '
            assetIndex = manifestData.find(asset)
            seek = assetIndex + len(asset)
            manifest.seek(seek)
            manifest.write(json.dumps(mainfestAddData[module]) + '}')
            pass
    zip = zipfile.ZipFile(updatedir + '.zip', 'w', zipfile.ZIP_DEFLATED)
    for root, dirs, files in os.walk(updatedir):
        for f in files:
            zip.write(os.path.join(root, f), os.path.join(root, f).replace(updatedir + os.sep, ''))
    zip.close()

    pass


# 检查文件所属模块
def checkFileModule(filePath):
    fileextendName = filePath[filePath.rfind("."):]
    if fileextendName == '.manifest':
        return
    if fileextendName == '.js':
        filePath = filePath.replace('.js', '.jsc')
    with open(os.path.join(updatedir, filePath), "rb") as updateFile:
        m2 = hashlib.md5()
        m2.update(updateFile.read())
        newFileData = {"md5": m2.hexdigest()}
        if fileextendName == '.zip':
            newFileData["compressed"] = True

    for module in modules:
        if mainfestAddData.get(module) == None:
            mainfestAddData[module] = {}
        if fileextendName == '.js':
            # 代码文件
            if filePath.find('src/game/' + module) >= 0:
                mainfestAddData[module][filePath] = (newFileData)
            else:
                mainfestAddData['lobby'][filePath] = (newFileData)
        else:
            # 资源文件
            if filePath.find('res/' + module) >= 0:
                mainfestAddData[module][filePath] = (newFileData)
    pass


def mkdirs(path):
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
        return True
    else:
        # 如果目录存在则不创建，并提示目录已存在
        return False


if __name__ == '__main__':
    svnInfo()
    packageFiles()
