# coding: utf-8
import os
import json

imageFiles = []
usedFiles = []


def searchImage(dir):
    imageExtendNames = ['.jpg', '.png']
    resFiles = os.listdir(dir)
    for file in resFiles:
        if file.find('.') == 0:
            continue
        file = dir + "/" + file
        if os.path.isdir(file):
            searchImage(file)
        else:

            fileExtendName = file[file.rfind('.'):]
            if fileExtendName == '.json':
                # json中是否用到资源
                with open(file, 'rb') as jsonFile:
                    resourceJson = json.loads(jsonFile.read().decode('utf-8'))
                    usedResources = resourceJson["Content"]["Content"]["UsedResources"]
                    for resource in usedResources:
                        resImagPath = subParStr(resource, dir)
                        if not resImagPath in usedFiles:
                            usedFiles.append(resImagPath)
            else:
                if fileExtendName in (imageExtendNames):
                    resImagPath = os.path.abspath(file)
                    if not resImagPath in imageFiles:
                        imageFiles.append(resImagPath)


def subParStr(imagePath, currentDir):
    index = imagePath.find('../')
    if index > -1:
        currentDir = os.path.abspath(os.path.join(currentDir, os.pardir))
        imagePath = imagePath[index + 3:]
        return subParStr(imagePath, currentDir)
    else:
        return (currentDir + "/" + imagePath)


def findUnused():
    projectRootDir = os.getcwd()
    resDir = projectRootDir + '/res'
    if not os.path.isdir(resDir):
        print('没有找到res文件夹')
        return
    searchImage(resDir)

    with open("unused.txt", 'w') as unused:
        for img in imageFiles:
            if not img in usedFiles:
                relPath = img.replace(resDir, "")
                print(relPath)
                unused.write(relPath+"\n")


if __name__ == '__main__':
    findUnused()
