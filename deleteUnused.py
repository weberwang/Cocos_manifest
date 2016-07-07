# coding: utf-8
import os

projectDir = os.getcwd()


def deleteImage():
    with open(projectDir + "/unused.txt") as unused:
        imgPath = unused.readline()
        while imgPath:
            imgPath = imgPath.strip('\n')
            filePath = resDir + imgPath
            print filePath
            if os.path.isfile(filePath):
                print u"文件存在"
                os.remove(filePath)
            imgPath = unused.readline()


if __name__ == "__main__":
    resDir = projectDir + "/res"
    if os.path.isdir(resDir):
        deleteImage()
