#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   autotaskDemo.py    
@Contact :   57343939@qq.com
@License :   (C)Copyright 2019-2020,Dekun Hu,cdu.edu.cn
支持同项目多医嘱、多次执行和多设备支持的排班
康复科自动排班/异常排班
1.问题说明：
    (1)排班要素
        患者、设备、治疗师，时间段，治疗项目
    (2)目标：
        只完成当日自动排班，自动排班会自动继承前一日的有效排班任务。
        自动排班结果可以手动调整。
    (3)相关约束说明
        a.排班设备（仅限于现代治疗区设备）的治疗项目定义为排班项目。
        b.患者同一时间段只能做一个排班治疗项目；
        c.设备同一时间段只能做一个排班治疗项目；
        d.同一治疗项目二次执行间需要的最小时间间隔；
        e.次日继承排班规则：同一患者同一治疗任务优先安排同一治疗师同一时段同一设备，
          新增的任务按照规则加入排班；
        f.自动排班完成后临时新增的治疗任务，通过手动添加分配。
    (4)异常排班：
        a.人员请假：治疗师因异常情况当天未完成的治疗任务需要重新分配给其它治疗师；
        b.设备故障：设备故障报修后当天未完成的治疗任务需要重新分配给其它设备或取消。
    (5)术语：
       治疗项目：来自HIS的医嘱项目

2.算法说明
算法：基于时间片优先级排班
原理：贪心算法
输入：患者，治疗任务，设备，康复师
属性定义：
(1)Devices—所有设备编号，数据类型列表: ['devices000', 'devices001', 'devices002', 'devices003', 'devices004', 'devices005', 'devices006', 'devices007', 'devices008', 'devices009', 'devices010', 'devices011', 'devices012', 'devices013', 'devices014']
(2)Patients—当日有治疗任务的所有患者信息，数据类型列表: [['P000000', 'Name0000'], ['P000001', 'Name0001'], ['P000002', 'Name0002'], ['P000037', 'Name0037'], ['P000038', 'Name0038'], ['P000039', 'Name0039']]
(3)Projects—康复治疗项目列表，数据类型列表: ['Project000', 'Project001', 'Project002', 'Project003', 'Project004', 'Project005', 'Project006']
(4)Therapist—所有的康复师列表，数据示例: ['Therapist000', 'Therapist001', 'Therapist002', 'Therapist003', 'Therapist004', 'Therapist005']，注：如果有优先级，优先级高的治疗师排前面可以有限安排治疗项目
(5)TimeSlice—时间段的开始时间列表，数据示例： ['08:10', '08:50', '09:30', '10：10', '10:50', '11:30', '14:00', '14:40', '15:20', '16:00', '16:40', '17:20']，每个时间端40分钟
(6)TheProject—治疗师项目资质，二维列表，TheProject[i][j]=1表示第i个治疗师可以执行第j类治疗任务（i表示Therapist列表中索引i的治疗师，j表示项目Project列表中索引为j的项目）；为=表示不能执行
(7)ProjectOnDeviceType—项目执行所依赖的设备类型，二维列表ProjectionDeviceType[i][j]=1表示项目i执行需要设备类型j，i是项目在Project列表中的索引，j是设备Devices中的索引，（目前支持一个项目最多两个不同类型设备同时使用）
(8)ProjectIntervalSlice--同一项目两次执行之间的最小间隔数
(9)PatientsTasks—待执行的医嘱项目，类型列表，元素为字典，示例数据：[{'patient': ['P000001', 'Name0001'], 'project': 'Project004', 'advice': [['20200601002', 2], ['20200601003', 2]], 'times': 4}]
(10)PatientSchedule—患者排班标，用于快速检测患者排班冲突,数据类型pandas dataframe
(11)DeviceSchedule—设备排班表，用于快速检测设备排班冲突，数据类型pandas dataframe
(12)TodaySchedule——当日排班总表，用于排班总览,数据类型pandas dataframe，数据类型pandas dataframe，含请假信息。
(13)YesterdaySchedule—前一日排班表，用于排班继承，数据类型pandas dataframe
(14)DeviceType--设备类型列表['DType001','DType002','DType003','DType004','DType005']
(15)TypeOfDevice--设备所属类型 TypeOfDevice[i][j]=1,表示第i个设备属于类型j。i,j为设备和类型列表的索引。
(16)maxDeviceNum--单个项目执行所需要的最大设备数目
(17)unArrangementTask--自动排班结束后剩余的未排任务
输出：
（1）排班总表TodaySchedule
（2）患者排班表PatientSchedule
（3）设备排班表DeviceSchedule
 (4)未排任务 unArrangementTask （由于设备，人员和患者约束，无法安排的任务，可以手动排班安排）

3.排班流程：step1:排班继承（继承后得到未排队列）-->step2:遍历患者{遍历治疗任务}--》step3 遍历时间片--》
           step4遍历治疗师--查询治疗师资质--step5 遍历设备时间
@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020-05-21 20:32   Dekun Hu      1.0         None

自动排班使用示例如下：
'''

# import lib

# 第三方库导入
import random
import pandas as pd
import numpy as np
import operator
import autotask
from datetime import datetime
import math

# import taskdistribute


# 将整数转为指定长度的字符串
def ss(x, m):
    s = str(x)
    while len(s) < m:
        s = "0" + s
    return s


# 产生排班所需要的模拟数据
def createdata():
    # 1.随机产生N个病人数据
    for i in range(0, N):
        templist = []
        tempid = ss(i, 4)  # 将病人编号转换为固定长度4位的编号
        pid = 'P00' + tempid
        name = 'Name' + tempid
        templist.append(pid)
        templist.append(name)
        Patients.append(templist)

    # 2.M种治疗项目 及同一项目连续两次治疗的间隔时间
    for i in range(0, M):
        Projects.append('Project' + ss(i, 3))
        #IntrevalType= random.randint(1, 3)*2 #第i个项目连续两次治疗治疗需要间隔的时间片段
        IntrevalType = random.randint(3, 6)   # 第i个项目连续两次治疗治疗需要间隔的时间片段
        ProjectIntervalSlice.append(IntrevalType)
    #         if i % 2 == 0:
    #             ProjectInternal.append(4)  # 每天2-3次的治疗任务
    #         else:
    #             ProjectInternal.append(24)  # 每天一次的治疗任务

    # 3.K个治疗师
    for i in range(0, K):
        Therapists.append('Therapist' + ss(i, 3))
    # 4.Q种设备
    for i in range(0, Q):
        typeid = 'Dtype' + ss(i, 3)
        DeviceType.append(typeid)

    #R个设备R
    for i in range(0,R):
        deviceid = 'device' + ss(i, 3)
        Devices.append(deviceid)

    #设备所属类型
    for i in range(0,Q):
        TypeOfDevice[i][i]=1
    for i in range(Q,R):
        j=random.randint(0, Q-1)
        TypeOfDevice[i][j]=1

    # 5 PatientsProjects 患者治疗项目
    for i in range(0, N):
        # 项目种类ProjectNumforpatientOneday
        taskcategory = random.randint(1, ProjectNumforpatientOneday)
        tasktemp = []
        for j in range(1, taskcategory + 1): #1个患者多个项目
            taskid = random.randint(0, M - 1)  # 项目编号下标/索引
            project='Project' + ss(taskid, 3)
            maxnum=math.floor(len(TimeSlices)/ProjectIntervalSlice[Projects.index(project)]) #计算项目执行的最大次数
            #医嘱编号
            advices=[]
            count=0
            advicenum=random.randint(1,maxAdviceNum)  #同一项目的医嘱出现的次数
            for k in range(0,advicenum): #同一项目多医嘱
                if maxnum-count>0:
                    strdate=datetime.now()
                    adviceID=strdate.strftime('%Y%m%d')+ss(i+j+k,3)
                    nums = random.randint(1, maxnum-count)  # 一天内项目的执行次数
                    advices.append([adviceID,nums])
                    count += nums
            if len(advices)>0:
                #PatientsTasks.append ([Patients[i], 'Project' + ss(taskid, 3), advices, count])
                PatientsTasks.append({'patient':Patients[i],'project':'Project' + ss(taskid, 3), 'advice':advices,'times':count})
    PatientsTasks.sort(key=operator.itemgetter('times'), reverse=True)

    # 6 治疗项目和设备关系：允许一个项目用多个设备,
      # 每个项目需要用到的最多设备数目
    for i in range(M):  # M个项目，Q个设备
        devicenums = random.randint(1, maxDeviceNum)  # 项目和devicenum个设备相关
        for j in range(devicenums):
            deviceno = random.randint(0, Q - 1)
            ProjectOnDeviceType[i][deviceno] = 1  # 具体相关设备

    # 7 治疗师资质：治疗师只能执行具备资质的任务
    for i in range(K - 5):  # 默认有15个治疗师可执行所有的项目
        for j in range(M):
            TheProject[i][j] = random.randint(0, 1)

    return True


def simulateleave(Therapist):
    '''
    模拟治疗师请假
    :return:
    '''
    # 模拟5个以内治疗师请半天假的情况，请假时段连续
    n = 5
    nums = random.randint(1, n)
    Therno = random.sample(range(0, len(Therapist)), nums)
    leavetime = {}
    for i in Therno:
        if random.randint(0, 1):  # 假设上午为1，下午为0
            leaveslice = [0, 1, 2, 3, 4, 5]
        else:
            leaveslice = [6, 7, 8, 9, 10, 11]
        leavetime[Therapist[i]] = leaveslice  # 存在索引越界bug
    return leavetime


def createSchedule(Therapist, TimeSlice, Devices, Patients):
    '''
    根据当日值班的治疗师M个和时间片（N个）生成N行M列的排班表，并初始化为空，格式为DataFrame
    :param Therapist:
    :param TimeSlice:
    :return: ScheduleDF
    '''
    # 排班总表
    datainit = np.zeros((len(TimeSlice), len(Therapist)))
    ScheduleDF = pd.DataFrame(data=datainit, index=TimeSlice, columns=Therapist)

    # 设备排班
    deviceinit = np.zeros((len(TimeSlice), len(Devices)))
    DeviceSchedule = pd.DataFrame(data=deviceinit, index=TimeSlice, columns=Devices)

    # 患者排班
    patientinit = np.zeros((len(TimeSlice), len(Patients)))
    PatientsID = [];
    for i in Patients:
        PatientsID.append(i[0])
    PatientSchedule = pd.DataFrame(data=patientinit, index=TimeSlice, columns=PatientsID)
    # 根据请假情况设置排班表
    # 产生请假数据，时间可以不连续，采用切片
    leavetime = simulateleave(Therapist)
    for key, value in leavetime.items():
        for i in value:
            ScheduleDF.iloc[i, Therapist.index(key)] = '请假'  # 治疗师对应时间片段置为请假
            # 排班记录格式[['患者编号p1','项目编号project001'，'设备编号device001'],...]
    return ScheduleDF, DeviceSchedule, PatientSchedule




if __name__ == "__main__":
    ######################基础参数，用于模拟数据生成#########################
    # 病人数量
    N =20
    # 治疗任务类型
    M = 30
    # P个治疗师
    K = 10
    # Q种设备类型
    Q = 15
    # R个设备
    R=22

    # 同一项目一天内医嘱的数量
    maxAdviceNum = 2
    #项目一日内2次治疗的间隔时间片数目
    InternalTime=6
    #单个项目所需要的设备类别
    maxDeviceNum=2
    #患者每天的设备项目类别
    ProjectNumforpatientOneday=2
    TimeSlices = ['08:10', '08:50', '09:30', '10：10', '10:50', '11:30', '14:00', '14:40', '15:20', '16:00', '16:40',
                 '17:20']
    # TimeSlice = [['8:10', '8:40'], ['8:50', '9:20'], ['9:30', '10:00'], ['10：10', '10:40'],\
    #                  ['10:50', '11:20'], ['11:30', '12:00'], ['14:00', '14:30'], ['14:40', '15:10'],
    #                  ['15:20', '15:50'], ['16:00', '16:30'], ['16:40', '17:10'], ['17:20', '17:50']]

    # 一天多次项目间隔时间段数目


    ##########################################################################
    ##########################################################################

    ##########################################################################
    ######################当日自动排班需要准备的数据#################################
    # 病人列表
    Patients = []
    # 病人医嘱，治疗任务

    PatientsTasks = []
    # 治疗项目
    Projects = []
    ProjectIntervalSlice=[]
    # 治疗项目所需要的设备
    ProjectOnDeviceType = [[0 for i in range(Q)] for i in range(M)]
    # 设备列表
    Devices = []
    # 治疗师列表
    Therapists = []
    # 治疗师可执行的治疗项目
    TheProject = [[1 for i in range(M)] for i in range(K)]  # 1表示具备该项目资质
    #设备类型列表
    DeviceType=[]
    TypeOfDevice=[[0 for i in range(Q)] for i in range(R)]
    # 当日排班总表

    TodaySchedule = pd.DataFrame()
    # 昨日排班表
    YesterdaySchedule = pd.DataFrame()
    # 当日设备排班表
    DeviceSchedule = pd.DataFrame()
    # 患者当日排班
    PatientSchedule = pd.DataFrame()
    # 未排任务列表
    unArrangementTask = []
    #生成模拟数据
    createdata()
    # 生成治疗任务：将可合并的治疗项目合并为可单独排班的治疗任务
    # PatientsTasks = getTask(PatientsProjects)
    # step1:建立初始化排班表
    TodaySchedule, DeviceSchedule, PatientSchedule = createSchedule(Therapists, TimeSlices, Devices, Patients)
    # TodaySchedule,DeviceSchedule,PatientSchedule = createSchedule();
    # 根据请假情况设置排班表
    # print(Schedule)
    #YesterdaySchedule = pd.read_csv('YdaySchedule.csv', encoding='utf-8')
    #开始排班
    print('task is starting')
    todaytask=autotask.autotask(DeviceType=DeviceType,
                                Devices=Devices,
                                TypeOfDevice=TypeOfDevice,
                                Patients=Patients,
                                Projects=Projects,
                                Therapists=Therapists,
                                TimeSlices=TimeSlices,
                                TheProject=TheProject,
                                ProjectOnDeviceType=ProjectOnDeviceType,
                                PatientsTasks=PatientsTasks,
                                PatientSchedule=PatientSchedule,
                                TodaySchedule= TodaySchedule,
                                YesterdaySchedule=YesterdaySchedule,
                                DeviceSchedule=DeviceSchedule,
                                ProjectIntervalSlice=ProjectIntervalSlice)

    # 应用一：常规排班

    todaytask.normaltaskdistribute();
    #获取排班结果
    Schedule=todaytask.getTodaySchedule()
    DeviceSchedule=todaytask.getDeviceSchedule()
    patientSchedule=todaytask.getPatientSchedule()
    unArrangementTask=todaytask.getUnarrangement()
    print('未排项目数：',len(unArrangementTask),unArrangementTask)


    # 应用二：异常排班--设备临时故障
    deviceID = 'device005'
    time = '14:20'
    print("设备异常重排！")
    todaytask.devicefaultRedistribute(deviceID, time)
    # 获取排班结果
    Schedule = todaytask.getTodaySchedule()
    DeviceSchedule = todaytask.getDeviceSchedule()
    patientSchedule = todaytask.getPatientSchedule()
    unArrangementTask = todaytask.getUnarrangement()
    print('未排项目数：', len(unArrangementTask), unArrangementTask)


    # # # 应用三：异常排班--治疗师临时请假
    therapistID = 'Therapist002'
    starttime = "14:30"
    endtime = "16:30"
    print('人员异常重排')
    todaytask.therapistLeaveRedistribute(therapistID, starttime, endtime)
    # 获取排班结果
    Schedule = todaytask.getTodaySchedule()
    DeviceSchedule = todaytask.getDeviceSchedule()
    patientSchedule = todaytask.getPatientSchedule()
    unArrangementTask = todaytask.getUnarrangement()
    print('未排项目数：', len(unArrangementTask), unArrangementTask)
    print("task is over")
    ########################排班结果存放##########################################
    ############################################################################



