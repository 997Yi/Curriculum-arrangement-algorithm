#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   autotask.py    
@Contact :   57343939@qq.com
@License :   (C)Copyright 2019-2020,Dekun Hu,buffalo-robot.com
自动排班任务类定义：
属性定义：
(1)Devices—所有设备编号，数据类型列表: ['devices000', 'devices001', 'devices002', 'devices003', 'devices004', 'devices005', 'devices006', 'devices007', 'devices008', 'devices009', 'devices010', 'devices011', 'devices012', 'devices013', 'devices014']
(2)Patients—当日有治疗任务的所有患者信息，数据类型列表: [['P000000', 'Name0000'], ['P000001', 'Name0001'], ['P000002', 'Name0002'], ['P000037', 'Name0037'], ['P000038', 'Name0038'], ['P000039', 'Name0039']]
(3)Projects—康复治疗项目列表，数据类型列表: ['Project000', 'Project001', 'Project002', 'Project003', 'Project004', 'Project005', 'Project006']
(4)Therapists—所有的康复师列表，数据示例: ['Therapist000', 'Therapist001', 'Therapist002', 'Therapist003', 'Therapist004', 'Therapist005']，注：如果有优先级，优先级高的治疗师排前面可以有限安排治疗项目
(5)TimeSlices—时间段的开始时间列表，数据示例： ['08:10', '08:50', '09:30', '10：10', '10:50', '11:30', '14:00', '14:40', '15:20', '16:00', '16:40', '17:20']，每个时间端40分钟
(6)TheProject—治疗师项目资质，二维列表，TheProject[i][j]=1表示第i个治疗师可以执行第j类治疗任务（i表示Therapist列表中索引i的治疗师，j表示项目Project列表中索引为j的项目）；为=表示不能执行
(7)ProjectOnDeviceType—项目执行所依赖的设备类型，二维列表ProjectionDeviceType[i][j]=1表示项目i执行需要设备类型j，i是项目在Project列表中的索引，j是设备Devices中的索引，（目前支持一个项目最多两个不同类型设备同时使用）
(8)ProjectIntervalSlice--项目两次执行之间的间隔时间段数目:[6, 6, 5, 4, 3, 6, 5, 6, 6, 5, 3, 6, 4, 4, 4, 5]
(9)PatientsTasks—待执行的医嘱项目，类型列表，元素为字典，示例数据：[{'patient': ['P000001', 'Name0001'], 'project': 'Project004', 'advice': [['20200601002', 2], ['20200601003', 2]], 'times': 4}]
(11)PatientSchedule—患者排班标，用于快速检测患者排班冲突,数据类型pandas dataframe
(10)DeviceSchedule—设备排班表，用于快速检测设备排班冲突，数据类型pandas dataframe
(12)TodaySchedule——当日排班总表，用于排班总览,数据类型pandas dataframe，数据类型pandas dataframe，含请假信息。
(13)YesterdaySchedule—前一日排班表，用于排班继承，数据类型pandas dataframe
(14)DeviceType--设备类型列表['DType001','DType002','DType003','DType004','DType005']
(15)TypeOfDevice--设备所属类型 TypeOfDevice[i][j]=1,表示第i个设备属于类型j。i,j为设备和类型列表的索引。
(16)unArrangementTask--自动排班结束后剩余的未排任务
@Modify Time      @Author    @Version    @Desciption
------------      -------    --------    -----------
2020-05-21 20:26   Dekun Hu      1.0         None
'''

# import lib
import random
import pandas as pd
import numpy as np
import operator
#自动排班类
class autotask():

    #初始化类的属性
    def __init__(self,**kwargs):
        self.DeviceType =  kwargs.get('DeviceType')
        self.Devices =  kwargs.get('Devices')
        self.TypeOfDevice = kwargs.get('TypeOfDevice')
        self.Patients =  kwargs.get('Patients')
        self.Projects =  kwargs.get('Projects')
        self.Therapists =  kwargs.get('Therapists')
        self.TimeSlices =  kwargs.get('TimeSlices')
        self.TheProject =  kwargs.get('TheProject')
        self.ProjectOnDeviceType =  kwargs.get('ProjectOnDeviceType')
        self.PatientsTasks =  kwargs.get('PatientsTasks')
        self.PatientSchedule =  kwargs.get('PatientSchedule')
        self.TodaySchedule =  kwargs.get('TodaySchedule')
        self.YesterdaySchedule = kwargs.get('YesterdaySchedule')
        self.DeviceSchedule =  kwargs.get('DeviceSchedule')
        self.ProjectIntervalSlice= kwargs.get('ProjectIntervalSlice')
        self.unArrangementTask = []


    # 治疗师排班总表获取
    def getTodaySchedule(self):
        return self.TodaySchedule

    # 设备排班总表获取
    def getDeviceSchedule(self):
        return self.DeviceSchedule

    # 患者排班总表获取
    def getPatientSchedule(self):
        return self.PatientSchedule

    #未能完成排班的任务
    def getUnarrangement(self):
        return self.unArrangementTask

    # 查找可用设备
    def searchDevices(self, deviceType, row):
        '''
        根据项目需要的设备类型返回可用的设备索引
        '''
        devices = []
        for each in deviceType:
            for j in range(len(self.Devices)):
                x=self.TypeOfDevice[j][each]
                #print('row:',row,'col:',j)
                y= self.DeviceSchedule.iloc[row, j]
                if x == 1 and y== 0:
                    #if self.TypeOfDevice[j][each] == 1 and self.DeviceSchedule.iloc[row, j] == 0:
                    devices.append(j)
                    break
        return devices


    #查找项目可用设备
    def searchDeviceType(self,task):
        '''
        task:治疗任务信息
        返回任务所需的设备类型
        '''
        DeviceType= []
        taskIndex = self.Projects.index(task)
        needDevices = self.ProjectOnDeviceType[taskIndex]
        for i in range(len(needDevices)):
            if needDevices[i] == 1:
                DeviceType.append(i)
        return DeviceType

    # 查询当前时间段项目所需设备是否空闲
    def freeDevicesQuery(self,row,task):
        # 查询排班次数
        deviceType = self.searchDeviceType(task['project'])  # 搜索关联设备：支持单任务多设备
        devices = self.searchDevices(deviceType,row)
        if len(devices)!=len(deviceType):
            return False,devices
        else:
            return True,devices


    def taskinherit(self):
        '''
        功能:排班继承,继承前一日相同的任务排班，以满足同一患者同一治疗任务尽量安排给同一治疗师和同一设备
        '''
        # 逐行逐列扫描排班表，如果有相同的患者和项目，则复制排班，已排班任务从任务队列删除
        for i in range(len(self.YesterdaySchedule)):
            for j in range(1,self.YesterdaySchedule.columns.size):
                Yitem = self.YesterdaySchedule.iloc[i, j]
                if (type(Yitem))!='str':
                    Yitem=str(Yitem)
                if len(Yitem)>4:
                    item=Yitem.split(' ')
                    YTpatientid = [item[0],item[1]]
                    YTtemptask = item[2]
                    # 格式为[项目，次数]
                    YTDevices = item[4:]

                    for k in range(len(self.PatientsTasks)):
                        # 比较是否同一个患者且任务相同
                        patientinfo=self.PatientsTasks[k]['patient'] #患者信息
                        task=self.PatientsTasks[k]['project']    #患者任务
                        advices=self.PatientsTasks[k]['advice']   #医嘱列表

                        if (( patientinfo == YTpatientid) and (YTtemptask==task)):
                            # 获取昨天的治疗师
                            theid = self.YesterdaySchedule.columns[j]
                            if (theid in self.TodaySchedule.columns) and (set(YTDevices).issubset(set(self.Devices))):  # 如果今天该治疗师也正常排班,设备正常
                                #判断设备是否空闲,判断治疗师是否请假
                                if self.TodaySchedule.ix[i, theid] == 0 and self.devicefreeQuery(YTDevices,i) and self.PatientSchedule.iloc[i, self.Patients.index(YTpatientid )]==0:
                                    self.TodaySchedule.ix[i, theid] = Yitem
                                    ##备排班写入
                                    devicestr=''
                                    for each in YTDevices:
                                        self.DeviceSchedule.iloc[i, self.Devices.index(each)] = patientinfo[0] + ' ' + \
                                            patientinfo[1] + ' ' + task+' '+advices[0][0]
                                        devicestr+=' +'+each
                                    #患者排班写入
                                    self.PatientSchedule.iloc[i, self.Patients.index(YTpatientid )] = task +' '+advices[0][0]+devicestr
                                    #已排班医嘱处理
                                    self.PatientsTasks[k]['advice'][0][1]=self.PatientsTasks[k]['advice'][0][1]-1 #已排班一次，减少医嘱次数
                                    if self.PatientsTasks[k]['advice'][0][1]<1:
                                        del self.PatientsTasks[k]['advice'][0]

                                    #任务总数减少，已排完班任务出队
                                    self.PatientsTasks[k]['times']=self.PatientsTasks[k]['times']-1# 任务次数
                                    if self.PatientsTasks[k]['times']<1:
                                        del self.PatientsTasks[k] #按继承任务排班后，删除任务
                                    break

    #排班负荷检查
    def overLoadcheck(self):
        '''
        检测当天需要完成的任务书是否超出最大排班负荷
        :param Schedule:排班表，包含已经请假不在岗的信息
        :param PatientsTasks:治疗总任务
        :return:True--超出最大排版负荷，False--未超出负荷
        '''
        # 当天任务数统计
        totaltask = 0
        for each in self.PatientsTasks:
            totaltask += each['times']

        print("总任务数:",totaltask)
        maxtasks =(self.TodaySchedule == 0).astype(int).sum(axis=1)
    #    for col in Schedule.columns:
    #        temp = Schedule.loc[:, col]
        maxtask = maxtasks.sum()
        if totaltask > maxtask:
            return True
        else:
            return False

    # 正常排班
    def normaltaskdistribute(self):
        '''
        根据当天的治疗任务进行排班
        排班原则：顺序如下
        (1)任务均衡：
        (2)治疗师优先--将治疗师按优先级从高到低组织为列表
        (3)设备优先--将同类型设备优先级从高到低组织为列表
        (4)治疗项目优先--同一天执行次数多的项目优先，同次数优先级高的项目优先
        (5)患者优先--同一项目，优先级高的患者优先级从高到低组织为列表
        算法：贪心算法，目标-最短任务完成时间
        方法：按时间片空闲优先搜索
        starttime:开始排班时间，默认为当前时间
        return: 排班表
        '''
        #tasks=self.taskMergeByPatientID()
        startrow = 0
        if self.overLoadcheck():
            print("治疗任务超出最大排班负荷。")
            # return False
            # step2：排班继承，
        if not self.YesterdaySchedule.empty:
            self.taskinherit()
            print('继承排班结束！')
        # step2:按时间片优先搜索排班
        patientstasks = self.taskMergeByPatientID()
        if len(patientstasks) > 0:
            waitingtasks=self.TPtaskdistribute(patientstasks,startrow) #基于医患熟悉度优先排班
            if len(waitingtasks)==0:
                print("排班结束！")
            else:
                print("有待排任务，开始基于完成任务时间优先排班")
                self.PatientsTasks=self.taskSplit(waitingtasks)
                if self.taskdistribute(self.PatientsTasks, startrow):
                    print("排班结束！")
                else:
                    print("排班结束，但有未排任务")
        else:  # 通过排班继承安排了所有的治疗任务
            print('无需要排班的治疗任务')

    def taskSplit(self,persontasks):
        '''
        :param persontasks-未排班的个人合并项目
        :return:tasks-拆分后的单个项目
        '''
        tasks=[]
        for each  in persontasks:
            for task in each['tasks']:
                tasks.append(task)
        return tasks

    # 基于医患熟悉度优先治疗任务排班--所有任务
    def TPtaskdistribute(self,tasks,startrow):
        '''
        :param TodaySchedule: 排班表
        :param PatientsTasks: 待排任务
        :return: True--排班结束，False--排班异常
        '''
        unArrangementPatients=[]
        # 任务遍历
        for i in range(len(tasks)):  # 提前整理为[patientID projects advices times]
            success,msg=self.TPArrangement(tasks[i],startrow)
            if not success:
                tasks[i]['msg']=msg
                unArrangementPatients.append(tasks[i])
        # 结束所有任务
        return unArrangementPatients

    # 基于最短完成时间治疗任务排班--所有任务
    def taskdistribute(self, tasks, startrow):
        '''
        :param TodaySchedule: 排班表
        :param PatientsTasks: 待排任务
        :return: True--排班结束，False--排班异常
        '''
        # 任务遍历
        for each in tasks:  # 提前整理为[patientID projects advices times]
            success, msg = self.arrangement(each, startrow)
            if not success:
                each['msg'] = msg
                self.unArrangementTask.append(each)

        # 结束所有任务
        if self.unArrangementTask:
            return False
        else:
            return True

    #多次任务排班可行性检查(检查患者和设备时间)
    def moreTaskCheck(self,task,row):
        '''
        task：任务字典
        row:排班表起始行
        return
        isfeasible:是否可行
        availableTable:可用排班信息列表，元素为字典，数据项如下：
             row:排班时间段
             device：需要的设备编号列表
        '''
        msg='Device'
        currentRow=row
        #print("moreTaskCheck",row)
        availableTable=[]
        for i in range(task['times']):
            while currentRow<len(self.TodaySchedule): #索引从0开始
            #查询当前时间段可用设备
                succ, devices = self.freeDevicesQuery(currentRow, task)
                for j in range(len(devices)):
                    msg+=' '+self.Devices[devices[j]]
                if succ and self.PatientSchedule.iloc[currentRow, self.Patients.index(task['patient'])] == 0:
                    availableTable.append({'row': currentRow, 'devices': devices})
                    currentRow += self.ProjectIntervalSlice[self.Projects.index(task['project'])]
                    break
                else:
                    currentRow+=1
            else:
                return False, availableTable,msg+' busy'

        else:
            return True,availableTable,msg

    # def moreTaskMoreProjectCheck(self, tasks, slices):
    #     '''
    #     task：任务字典
    #     row:排班表起始行
    #     return
    #     isfeasible:是否可行
    #     availableTable:可用排班信息列表，元素为字典，数据项如下：
    #          row:排班时间段
    #          device：需要的设备编号列表
    #     '''
    #     msg = 'Device'
    #     availableTable = []
    #     for task in tasks['tasks']: #逐个项目排班
    #         count=0
    #         rows=slices
    #         usedrow=[]
    #         for i in range(task['times']):#多次数排班
    #             while count <len(rows):  # 索引从0开始
    #                 # 查询当前时间段可用设备
    #                 currentRow = rows[count]
    #                 succ, devices = self.freeDevicesQuery(currentRow, task)
    #                 for j in range(len(devices)):
    #                     msg += ' ' + self.Devices[devices[j]]
    #                 if succ and self.PatientSchedule.iloc[currentRow, self.Patients.index(task['patient'])] == 0:
    #                     availableTable.append({'task':task,'row': currentRow, 'devices': devices})
    #                     usedrow.append(currentRow)
    #                     currentRow += self.ProjectIntervalSlice[self.Projects.index(task['project'])]
    #                     if currentRow<=max(rows):
    #                         while rows[count]<currentRow:
    #                               count+=1
    #                     break
    #                     #else:
    #                     #     break
    #                 else:
    #                     count += 1
    #             else:
    #                 return False, availableTable, msg + ' busy'
    #         #一个项目任务排完，从slices删除已试用的时间片段
    #         slices=list(set(slices)-set(usedrow))
    #
    #     return True, availableTable, msg

    def moreTaskMoreProjectCheck(self, tasks, slices):
        '''
        task：任务字典
        row:排班表起始行
        return
        isfeasible:是否可行
        availableTable:可用排班信息列表，元素为字典，数据项如下：
             row:排班时间段
             device：需要的设备编号列表
        '''
        msg = 'Device'
        availableTable = []
        for task in tasks['tasks']: #逐个项目排班
            count=0
            rows=slices
            usedrow=[]
            for i in range(task['times']):#多次数排班

                while count <len(rows):  # 索引从0开始
                    # 查询当前时间段可用设备
                    currentRow = rows[count]
                    succ, devices = self.freeDevicesQuery(currentRow, task)
                    for j in range(len(devices)):
                        msg += ' ' + self.Devices[devices[j]]
                    if succ and self.PatientSchedule.iloc[currentRow, self.Patients.index(task['patient'])] == 0:
                        availableTable.append({'task':task,'row': currentRow, 'devices': devices})
                        usedrow.append(currentRow)
                        currentRow += self.ProjectIntervalSlice[self.Projects.index(task['project'])]
                        if currentRow<=max(rows):
                            while count<len(rows) and rows[count]<currentRow:
                                count+=1
                                #print(rows,'count:',count,'CR:',currentRow)
                            break
                        else:
                            if i==task['times']-1:
                                break #如果当前项目已经安排完，进行下一个项目，否则返回无法安排
                            else:
                                return False, availableTable, msg + ' busy'
                        #     # if count
                        #      return False, availableTable, msg + ' busy'
                    else:
                        count += 1
                else:
                    return False, availableTable, msg + ' busy'
            #一个项目任务排完，从slices删除已试用的时间片段
            slices=list(set(slices)-set(usedrow))

        return True, availableTable, msg
    # 当前患者治疗任务排班--一个患者任务
    def TPArrangement(self,task,startrow):
        '''
        :param task: 患者任务，同一患者任务优先安排给同一治疗师
        :param startrow: 排班开始时间段
        :return: Boolean，message,是否成功，未成功，给出消息
        '''
        msg=''
        print(task)
        # 逐个时间段遍历
        for row in range(startrow,len(self.TodaySchedule)):
            #查询具备患者所有项目资质的康复师名单
            therapists=self.queryTherapist(task)
            #逐个匹配康复师的时间和设备
            for col in therapists:
                #当前治疗师空闲时间查询
                isfree,Thefreeslices=self.checkTheTimeslice(task,col,startrow)
                if isfree:
                    #可用的的项目所需设备空闲时间查询
                    isfeasible,availableTable,msg=self.moreTaskMoreProjectCheck(task,Thefreeslices)
                    if isfeasible:
                        self.executeTPArrangement(availableTable,col)
                        return True,msg
                    else:
                        msg='Therapist'+self.TodaySchedule.columns[col]+' busy' #无法排班返回具体原因

            else:
                return False,msg



    def checkTheTimeslice(self,task,col,startrow):
        '''
        :param task--治疗任务
        :param col--治疗师索引
        :return: True--治疗师有足够时间为患者治疗
                 False--无足够时间
        '''
        count=0 #治疗项目需要的时间段数目
        for each in task['tasks']:
            count+=each['times']

        #治疗师空闲时间段数目
        freeslices=[]
        for i in range(startrow,len(self.TodaySchedule)):
            if self.TodaySchedule.iloc[i,col]==0:
                freeslices.append(i)

        if count<=len(freeslices):
            return True,freeslices
        else:
            return False,''


    #当前患者治疗任务排班
    def arrangement(self,task,startrow):
        msg=''
        # 逐个时间段遍历
        for row in range(startrow,len(self.TodaySchedule)):
            #检查患者和设备情况
            isfeasible,availableTable,msg=self.moreTaskCheck(task,row)
            if isfeasible:
                # 逐个康复师遍历
                for col in range(len(self.TodaySchedule.columns)):
                    #治疗师资质检查
                    if self.qualificaitoncheck(task['project'], self.TodaySchedule.columns[col]):
                        #多任务时间检查，满足多时段空闲
                        for i in range(len(availableTable)):
                            if self.TodaySchedule.iloc[availableTable[i]['row'], col]==0:
                                available= True
                            else:
                                available = False
                                break
                        if available:
                            self.executeArrangement(task,availableTable,col)
                            return True,msg
                        else:
                            msg='Therapist'+self.TodaySchedule.columns[col]+' busy' #无法排班返回具体原因

        else:
            return False,msg



    def queryTherapist(self,task):
        #患者项目资质合集
        projects=[]
        for each in task['tasks']:
            projects.append(each['project'])
        #去除重复项目
        projects=list(set( projects))
        #查找具备患者所有项目资质的治疗师
        therapists=[]
        for i in range(len(self.TheProject)):
            flag=True
            for each in projects:
                if not self.TheProject[i][self.Projects.index(each)]:
                    flag=False
                    break;
            else:
                therapists.append(i)

        return therapists

    #排班执行
    def executeTPArrangement(self,availableTable, col):
        '''
        task:待排任务
        availableTable：可用排班单元
        col:治疗师索引
        '''
        for i in range(len(availableTable)):
            task=availableTable[i]['task']
            row=availableTable[i]['row']
            devices=availableTable[i]['devices']
            advices=task['advice']
            strdevices=''
            for j in range(len(devices)):
                strdevices+=' '+self.Devices[devices[j]]

            #治疗师排班表
            self.TodaySchedule.iloc[row,col]=task['patient'][0]+' '+task['patient'][1]+' '+task['project']+' '+advices[0][0]+strdevices
            #患者排班表
            self.PatientSchedule.iloc[row,self.Patients.index(task['patient'])] = task['project'] + ' ' + advices[0][
                0] + strdevices+' '+self.Therapists[col]
            #设备排班
            for j  in range(len(devices)):
                self.DeviceSchedule.iloc[row,devices[j]]=task['patient'][0]+' '+task['patient'][1]+' '+task['project']+' '+advices[0][0]+' '+self.Therapists[col]

            print("时间段:", row, "治疗师:", col, '医嘱:', advices[0][0], task['patient'], task['project'], strdevices, 'OK')
            #医嘱处理
            advices[0][1]-=1
            if advices[0][1]==0:
                del advices[0]



    #排班执行
    def executeArrangement(self,task, availableTable, col):
        '''
        task:待排任务
        availableTable：可用排班单元
        col:治疗师索引
        '''
        for i in range(len(availableTable)):
            row=availableTable[i]['row']
            devices=availableTable[i]['devices']
            advices=task['advice']
            strdevices=''
            for j in range(len(devices)):
                strdevices+=' '+self.Devices[devices[j]]

            #治疗师排班表
            self.TodaySchedule.iloc[row,col]=task['patient'][0]+' '+task['patient'][1]+' '+task['project']+' '+advices[0][0]+strdevices
            #患者排班表
            self.PatientSchedule.iloc[row,self.Patients.index(task['patient'])] = task['project'] + ' ' + advices[0][
                0] + strdevices+' '+self.Therapists[col]
            #设备排班
            for j  in range(len(devices)):
                self.DeviceSchedule.iloc[row,devices[j]]=task['patient'][0]+' '+task['patient'][1]+' '+task['project']+' '+advices[0][0]+' '+self.Therapists[col]

            print("时间段:", row, "治疗师:", col, '医嘱:', advices[0][0], task['patient'], task['project'], strdevices, 'OK')
            #医嘱处理
            advices[0][1]-=1
            if advices[0][1]==0:
                del advices[0]


    #治疗师资质核查
    def qualificaitoncheck(self,task, therapistName):
        '''
        校验治疗师项目资质
        task:治疗项目名称
        therapistName：治疗师名称
        return bool
        '''
        therapistIndex = self.Therapists.index(therapistName)
        taskIndex = self.Projects.index(task)
        if self.TheProject[therapistIndex][taskIndex] == 1:
            return True
        else:
            return False

    #异常排班：（1）治疗师临时请假 （2）设备临时故障
    def devicefaultRedistribute(self, deviceID, time):
        '''
        设备故障余下的任务重排
        deviceID：故障设备编号
        time:设备故障时间:字符串
        TodaySchedule：当日排班
        DeviceSchedule：设备排班
        PatientSchedule：患者排班
        '''
        # todo
        for i in range(1, len(self.TimeSlices)):
            if self.TimeSlices[i] >= time:
                startrow = i - 1  # 如果正在执行的任务也要重排，则为i-1
                # 移除设备相关任务，产生新的待排任务
                newtasks = self.canceltaskbydeviceID(deviceID, startrow)
                # 重新排班
                if self.taskdistribute(newtasks, startrow + 1):
                    print("设备故障重排结束！")
                else:
                    print("排班结束，但有未排任务")
                break;  # 处理后退出

    # 故障设备未完成任务提取
    def canceltaskbydeviceID(self, deviceID, startrow):
        deviceTask = []  # 存放取消的设备任务
        for row in range(startrow, len(self.TodaySchedule)):
            # 逐个康复师遍历：在deviceSchedule中查找更方便
            self.DeviceSchedule.iloc[row, self.Devices.index(deviceID)] = '故障'
            for col in range(len(self.TodaySchedule.columns)):
                item = self.TodaySchedule.iloc[row, col]
                # 设备故障标识
                if (type(item)) != 'str':
                    item = str(item)
                if len(item) > 4:
                    item = item.split(' ')
                    patientid = [item[0], item[1]]
                    task = item[2]  # 格式为[项目，次数]
                    advice = item[3]
                    devices = item[4:]
                    if deviceID in devices:
                        self.TodaySchedule.iloc[row, col] = 0  # 取消该任务
                        deviceTask.append(
                            {'patient': patientid, 'project': task, 'advice': [[advice, 1]], 'times': 1})  # 待排任务
                        self.PatientSchedule.iloc[row, self.Patients.index(patientid)] = 0  # 患者任务取消
                        # 多设备任务取消
                        devices.remove(deviceID)
                        for i in range(len(devices)):
                            self.DeviceSchedule.iloc[row, self.Devices.index(devices[i])] = 0

        print('影响的任务数:', len(deviceTask), deviceTask)
        return deviceTask

    # 治疗师请假任务重排
    def therapistLeaveRedistribute(self, therapistID, starttime, endtime):
        # todo
        slices = []
        # 存放取消的设备任务
        for i in range(len(self.TimeSlices)):
            time = self.TimeSlices[i]
            if time >= starttime and time < endtime:
                slices.append(i)
        # 获取时间端的范围
        maxrow = max(slices)
        minrow = min(slices)
        # 移除设备相关任务，产生新的待排任务
        newtasks = self.canceltaskbytherapistID(therapistID, minrow, maxrow + 1)
        # 重新排班
        if self.taskdistribute(newtasks, minrow + 1):  # 从下一个时段开始重排
            print("人员请假重排结束！")
        else:
            print("排班结束，但有未排任务")

    # 请假重排
    def canceltaskbytherapistID(self, therapistID, startrow, endrow):
        canceltask = []  # 存放取消的排班任务
        for row in range(startrow, endrow):
            # 逐个康复师遍历
            col = self.Therapists.index(therapistID)
            item = self.TodaySchedule.iloc[row, col]
            self.TodaySchedule.iloc[row, col] = '请假'  # 取消该任务
            if (type(item)) != 'str':
                item = str(item)
            if len(item) > 4:
                item = item.split(' ')
                patientid = [item[0], item[1]]
                task = item[2]  # 格式为[项目，次数]
                advice = item[3]
                devices = item[4:]
                canceltask.append(
                    {'patient': patientid, 'project': task, 'advice': [[advice, 1]], 'times': 1})  # 待排任务

                self.PatientSchedule.iloc[row, self.Patients.index(patientid)] = 0  # 患者任务取消
                #取消设备任务
                for i in range(len(devices)):
                    self.DeviceSchedule.iloc[row, self.Devices.index(devices[i])] = 0
        print('影响的任务数:', len(canceltask), canceltask)
        return canceltask

    #任务合并：按患者ID合并任务
    def taskMergeByPatientID(self):
        #获取患者信息
        patients=[]
        for i in range(len(self.PatientsTasks)):
            temp=self.PatientsTasks[i]['patient']
            if temp not in patients:
                patients.append((temp))

        #依次获取患者任务
        pTasks=[]
        for i in range(len(patients)):
            tasks=[];
            for j in range(len(self.PatientsTasks)):
                if patients[i]==self.PatientsTasks[j]['patient']:
                    tasks.append((self.PatientsTasks[j]))

            pTasks.append({'patient':patients[i],'tasks':tasks})

        return pTasks






