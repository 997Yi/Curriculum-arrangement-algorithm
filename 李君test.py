import pandas as pd
import numpy as np


############################### 数据结构定义 ###############################

# 定义一个教师类 存放着教师基本信息
class Teacher:
    def __init__(self, name):
        self._name = name
    
    def __str__(self):
        return self._name
    
    def getName(self):
        return self._name

# 定义一个班级类
#   由于此处测试数据全为两个班级绑定，因此这个类代指两个班级
class Class:
    def __init__(self, className1, studentNum1, className2, studentNum2):
        self._className = [className1, className2]
        self._studentNum = studentNum1 + studentNum2

    def __str__(self):
        return '%s and %s  人数 %d' %(self._className[0], self._className[1], self._studentNum)


    def getName(self):
        return self._className[0]

    def getStudentNum(self):
        return self._studentNum

# 定义一个教室类
#   储存教室的位置和容纳人数信息
class Classroom:
    def __init__(self, name, contains):
        self._name = name
        self._contains = contains
    
    def __str__(self):
        return '教室位置:%s  容纳人数:%d' %(self._name, self._contains)
    
    def getName(self):
        return self._name

    def getContains(self):
        return self._contains

# 定义一个课程类
#   储存课程的基本信息
class Course:
    def __init__(self, id, name, peerweek, total):
        self._id = id
        self._name = name
        self._peerweek = peerweek
        self._total = total
    
    def __str__(self):
        return '课程代码:%s  课程名称:%s  周学时:%d  总学时:%d' %(self._id, self._name, self._peerweek, self._total)

    def getName(self):
        return self._name

    def getContinue(self):
        return self._total // self._peerweek

    def getPeerWeek(self):
        return self._peerweek

# 课程计划
class CoursePlan:
    # 初始化时没有教室信息
    def __init__(self, courseInfo, classInfo, teacherInfo):
        self._courseInfo = courseInfo
        self._classInfo = classInfo
        self._teacherInfo = teacherInfo
        self._week = [0, courseInfo.getContinue()]
    
    def setClassroomInfo(self, classroomInfo):
        self._classroomInfo = classroomInfo
    
    # 判断当前课程计划是安排妥当
    def isDone(self):
        return hasattr(self, "_classroomInfo")

    def __str__(self):
        return "%s\n%s\n%s\n%s" %(self._classInfo.__str__(),self._courseInfo.__str__(),self._teacherInfo.__str__(), self._classroomInfo.__str__())

    def isContain(self, obj):
        mark = False
        if self.isDone():
            mark = id(self._classroomInfo) == id(obj)
        
        return id(self._classInfo) == id(obj) or \
                id(self._teacherInfo) == id(obj) or \
                    mark
            
    def getCourse(self):
        return self._courseInfo
    
    def getTeacher(self):
        return self._teacherInfo
    
    def getClass(self):
        return self._classInfo

    def getClassroom(self):
        if self.isDone():
            return self._classroomInfo



############################### excel读取函数定义 ###############################


# 定义一个从文件中读出教师的方法
#   传入excel的dataframe对象
def readTeacherInfo(dataframe):
    # 获取教师列信息 和 教师列内容定义信息（去重）
    teacherNames = dataframe.教师姓名
    declear = teacherNames.duplicated()

    teachers = []
    for i in range(len(teacherNames)):
        if declear[i] == False and type(teacherNames[i]) == str:
            teachers.append(Teacher(teacherNames[i]))
    
    return teachers

# 定义一个从文件中读出班级信息的方法
#   传入excel的dataframe对象
def readClassInfo(dataframe):
    # 获取班级人数和名称
    classNames = dataframe.班级名称
    studentNums = dataframe.班级人数

    declear = classNames.duplicated()

    classes = []
    for i in range(len(classNames)//2):
        if declear[2 * i] == False:
            classes.append(Class(classNames[2 * i], studentNums[2 * i], classNames[2 * i + 1], studentNums[2 * i] + 1))
    
    return classes

# 定义一个从文件中读出教室信息的方法
#   传入excel的dataframe对象
def readClassroomInfo(dataframe):
    # 获取班级人数和名称
    classroomNames = dataframe.教室编号
    contains = dataframe.座位数
    
    classrooms = []
    for i in range(len(classroomNames)):
        classrooms.append(Classroom(classroomNames[i], contains[i]))

    return classrooms

# 定义一个从文件中读出教室信息的方法
#   传入excel的dataframe对象
def readCourseInfo(dataframe):

    # 获取课程基本信息 和 定义信息（去重）
    courseIds = dataframe.课程代码
    courseNames = dataframe.课程名称
    peerweeks = dataframe.周学时
    totals = dataframe.总学时

    declear = courseIds.duplicated()

    courses = []
    for i in range(len(courseIds)):
        if declear[i] == False:
            for j in range(peerweeks[i] // 2):
                courses.append(Course(courseIds[i], courseNames[i], peerweeks[i], totals[i]))
    
    return courses

# 读出所有的教学计划
def readCoursePlanInfo(dataframe, teachers, classes, courses):
    coursePlans = []

    for i in range(len(dataframe)//2):
        course = findByName(courses, dataframe.课程名称[i * 2])
        teacher = findByName(teachers, dataframe.教师姓名[i * 2])
        classInfo = findByName(classes, dataframe.班级名称[i * 2])

        for j in range(course.getPeerWeek() // 2):
            coursePlans.append(CoursePlan(course, classInfo, teacher))

    return coursePlans


############################### 条件判断工具方法 ###############################


# 判断这个班今天是否已经上过两次这个课了
def alreadyHave(timeTable, courseInfo, classInfo):
    num = 0

    for i in range(len(timeTable)):
        for j in range(len(timeTable[i])):
            if timeTable[i][j].isContain(classInfo) and timeTable[i][j].isContain(courseInfo):
                num += 1
    
    return num != 2

# 判断这个时间段里该（老师、课程、教室）是否被占用了 没有被占用则为True
def isFree(coursePlanList, obj):
    for i in range(len(coursePlanList)):
        if coursePlanList[i].isContain(obj):
            return False
    return True


############################### 属性获取工具方法 ###############################


# 通过传入的类型（teacher、class）获取他们今天上的课的个数
def getCourseNum(timeTable, obj):
    num = 0

    for i in range(len(timeTable)):
        for j in range(len(timeTable[i])):
            if timeTable[i][j].isContain(obj):
                num += 1
    
    return num


# 传入Teacher、Class、ClassRoom、Course等列表
#   能够通过getName方法获取其中元素
def findByName(arr, name):
    for i in range(len(arr)):
        if arr[i].getName() == name:
            return arr[i]

# 获取一个空课表 dataframe
def getEmptyTimeTable():
    dataframe = pd.DataFrame(columns=("  ", "周一", "周二", "周三", "周四", "周五"))
    dataframe = dataframe.append(pd.DataFrame({"  ": ["第一节","第二节","第三节","第四节","第五节"], \
        "周一": [[], [], [], [], []], \
            "周二": [[], [], [], [], []], \
                "周三": [[], [], [], [], []], \
                    "周四": [[], [], [], [], []], \
                        "周五": [[], [], [], [], []]
        }))

    return dataframe


############################### 核心方法 ###############################


# 传入一个课程表、教室表和教学计划，为这个教学计划安排一个合适的时间和教室
def divide(timeTable, classrooms, coursePlan):
    weekdays = ["周一","周二","周三","周四","周五"]

    # 先为课程安排一个星期几 
    for weekday in range(5):


        # 此时先剪枝，将不满足一下条件的剔除
        # (5)一个教师每天不能超过6节课
        # (6)每个学生班级每天不能超过8节课
        # (7)每个教学班同一门课程每天不能超过2节课
        dayTable = timeTable[weekdays[weekday]]

        if alreadyHave(dayTable, coursePlan.getCourse(), coursePlan.getClass()) and \
            getCourseNum(dayTable, coursePlan.getClass()) < 4 and \
                getCourseNum(dayTable, coursePlan.getTeacher()) < 3:


            # 再为课程安排一个第几节课
            for time in range(5):

                # 获取安排在这个日期的课程的列表（dataframe中存的是列表）
                coursePlanList = dayTable[time]


                # 此时对以下条件剪枝
                # (1)同一个任课教师在一个教学时间段只能进行一门课程教学
                # (2)同一个班级在一个教学时间段只能进行一门课程教学
                if isFree(coursePlanList, coursePlan.getTeacher()) and \
                    isFree(coursePlanList, coursePlan.getClass()):


                    # 最后为课程计划分配一个教室即可
                    for classroom in range(len(classrooms)):
                        
                        # 确定教室是否能够容纳和教室此时是否为空
                        if classrooms[classroom].getContains() >= coursePlan.getClass().getStudentNum() \
                            and isFree(coursePlanList, classrooms[classroom]):

                            
                            # 至此，确定所有要求都满足了
                            
                            # 为当前授课计划设置教室
                            coursePlan.setClassroomInfo(classrooms[classroom])
                            # 将这个计划添加到课表中
                            coursePlanList.append(coursePlan)

                            return
                            
# 读取excel并且排得课表并返回
def readAndGet():
    try:
        excelPage1 = pd.read_excel("/Users/xxx_/Desktop/IT新技术/实验三排课系统/test.xlsx", 0)
        excelPage2 = pd.read_excel("/Users/xxx_/Desktop/IT新技术/实验三排课系统/test.xlsx", 1)

    except:
        print("读取测试文件失败，请检查路径是否正确!")
    
    # 读取老师信息
    teachers = readTeacherInfo(excelPage1)
    # 读取班级信息
    classes = readClassInfo(excelPage1)
    # 读取课程信息
    courses = readCourseInfo(excelPage1)
    # 通过前三个数据获取授课信息
    coursePlans = readCoursePlanInfo(excelPage1, teachers, classes, courses)

    # 读取教室信息
    classrooms = readClassroomInfo(excelPage2)

    # 获取一个空课表
    timeTable = getEmptyTimeTable()

    weekdays = ["周一","周二","周三","周四","周五"]

    # 开始排课
    for coursePlan in range(len(coursePlans)):
        # 对每一个课程计划进行排课
        divide(timeTable, classrooms, coursePlans[coursePlan])

    return teachers, classes, timeTable

# 根据传入的（班级/老师）获取他的课表
def getTimeTable(timeTable, obj):
    res = getEmptyTimeTable()

    for weekday in ["周一","周二","周三","周四","周五"]:
        for time in range(5):
            coursePlanList = timeTable[weekday][time]

            for i in range(len(coursePlanList)):
                if coursePlanList[i].isContain(obj):
                    res[weekday][time].append(coursePlanList[i])
                    # 由于同一时间只会有一节课，则直接break即可
                    break
    
    return res

# 将timeTable中的内容格式化：typeInfo为类型信息
#    如果是老师，则课表信息中需要有： 教室信息 班级信息 课程信息
#    如果是学生，则课表信息中需要有： 教室信息 老师信息 课程信息
def toString(timeTable, typeInfo):
    mark = typeInfo == Teacher
    
    for weekday in ["周一","周二","周三","周四","周五"]:
        for time in range(5):
            coursePlan = timeTable[weekday][time]
            targetStr = ""

            if len(coursePlan) != 0:
                coursePlan = coursePlan[0]

                targetStr = "%s%s%s%s%s"%(coursePlan.getClassroom().__str__(), chr(10), \
                    coursePlan.getCourse().__str__(), chr(10), \
                        coursePlan.getClass().__str__() if mark else coursePlan.getTeacher().__str__())
            
            timeTable[weekday][time] = targetStr
    
    return timeTable
            





def main():
    teachers, classes, timeTable = readAndGet()

    # timeTable.to_excel("/Users/xxx_/Desktop/IT新技术/实验三排课系统/out.xlsx")

    targetTimeTable = getTimeTable(timeTable, findByName(classes, "软件(本)18-3"))

    targetTimeTable = toString(targetTimeTable, Class)

    print(targetTimeTable)

    targetTimeTable.to_excel("/Users/xxx_/Desktop/IT新技术/实验三排课系统/out.xlsx")



main()