import json
import sqlite3

from django.shortcuts import render
import smtplib
from django.http import HttpResponse
import base64
import urllib
import httplib2
import http.client
import time
import requests


# Create your views here.

# 存放原始拓扑信息
oriSourNode = {}
oriDestNode = {}
k = 0
for k in range(0, 30):
    oriSourNode[k] = '0'
    oriDestNode[k] = '0'
    k = k + 1


# 两个字典取不同
def compareDiff(dict1, dict2, num):
    result = {}
    numk = 0
    clockNum = 0
    k = 0
    for ky1 in dict1.keys():
        clockNum = 0
        for ky2 in dict2.keys():
            if (dict2[ky2] == dict1[ky1]):
                break
            elif (dict2[ky2] != dict1[ky1]) and (clockNum + 1) > num:
                result[numk] = dict1[ky1]
                numk = numk + 1
            else:
                k = k + 1
            clockNum = clockNum + 1
    return result


# 获取字典对象个数
def get_number(dict):
    k = 0
    for key in dict.keys():
        k = k + 1
    return k - 1


# 定义连接类
class OdlUtil:
    url = ''

    def __init__(self, host, port):
        self.url = 'http://' + host + ':' + str(port)

    # 通过http请求向ODL进行认证和得到网络中的拓扑信息
    def get_topology(self, container_name='default', username="admin", password="admin"):
        http = httplib2.Http()
        http.add_credentials(name=username, password=password)
        headers = {'Accept': 'application/json'}
        response, content = http.request(uri=self.url + '/restconf/operational/network-topology:network-topology',
                                         headers=headers)
        return content.decode()

    # 获取通信链路信息
    def get_connect(self, container_name='default', username="admin", password="admin"):
        http = httplib2.Http()
        http.add_credentials(name=username, password=password)
        headers = {'Accept': 'application/json'}
        response, content = http.request(uri=self.url + '/restconf/operational/opendaylight-inventory:nodes',
                                         headers=headers)
        return content.decode()


# 拓扑信息获取
def index(request):
    try:
        odl = OdlUtil('127.0.0.1', '8080')
        topo = odl.get_topology(username="admin", password="admin")  # 从ODL中获得的原始json数据
    except Exception as e:
        return render(request, 'error.html')
    # print(topo)
    # mid = json.dumps(topo)                                       #转换为str
    de_topo = json.loads(topo)  # 转换为python对象-字典

    sourPort = {}  # 存放源端口
    destPort = {}  # 存放目地端口

    ############################
    oriLinkSour = {}
    oriLinkDest = {}
    kk = 0
    for nod in oriSourNode.keys():
        oriLinkSour[kk] = oriSourNode[nod]
        kk = kk + 1
    kk = 0
    for nod in oriDestNode.keys():
        oriLinkDest[kk] = oriDestNode[nod]
        kk = kk + 1
    ############################
    # -----获取节点信息-----#
    n = de_topo["network-topology"]["topology"][1]["node"]  # 进入到节点所在的list中
    x2 = str(n[0]["node-id"])  ###测试节点###
    nodes = {}  # 存放节点信息,其中,×××若以openflow开头则为交换机,若以host开头则为主机×××
    i = 0
    for y in n:  # 遍历node,取出节点信息放入nodes{}
        y2 = str(y["node-id"])
        nodes[i] = y2
        i = i + 1

    # -----获取链接信息-----#
    l = de_topo["network-topology"]["topology"][1]["link"]  # 进入到链接所在的list中
    x3 = str(l[0]["source"]["source-node"])  ###测试节点###
    x4 = str(l[0]["source"]["source-tp"])
    link_source_id = {}  # 存放链接的源节点
    link_destination_id = {}  # 存放链接的目地节点
    k = 0
    for y in l:  # 遍历link,取出链接信息存入link_source_id和link_destination_id
        y3 = str(y["source"]["source-node"])
        y4 = str(y["destination"]["dest-node"])
        y5 = str(y["source"]["source-tp"])
        y6 = str(y["destination"]["dest-tp"])
        link_source_id[k] = y3
        link_destination_id[k] = y4
        sourPort[k] = y5
        destPort[k] = y6
        k = k + 1
    ##############################
    knum = get_number(link_source_id)
    redSour = compareDiff(oriLinkSour, sourPort, knum)

    ##############################
    con = odl.get_connect(username="admin", password="admin")
    # print(con)
    de_con = json.loads(con)
    n = de_con["nodes"]["node"]
    # topology(request)   #必不可少
    errorNode = {}  # 存放故障节点端口
    numK = 0
    for ny in n:
        ny1 = ny["node-connector"]
        for ny2 in ny1:
            if ny2["flow-node-inventory:state"]["link-down"] == True or ny2["flow-node-inventory:state"][
                "live"] == True or ny2["flow-node-inventory:state"]["blocked"] == True:
                errorNode[numK] = ny2["id"]
                numK = numK + 1

    if oriSourNode[0] == '0' and oriSourNode[19] != '999':
        kk = 0
        for nod in sourPort.keys():
            oriSourNode[kk] = sourPort[nod]
            kk = kk + 1
        kk = 0
        for nod in destPort.keys():
            oriDestNode[kk] = destPort[nod]
            kk = kk + 1
        oriSourNode[19] = '999'
    # return HttpResponse(str(redSour))
    return render(request, 'index.html', {'redSour': json.dumps(redSour), 'node': json.dumps(nodes),
                                          'link_source_id': json.dumps(link_source_id),
                                          'link_destination_id': json.dumps(link_destination_id),
                                          'errorNode': json.dumps(errorNode), 'sourPort': json.dumps(oriSourNode),
                                          'destPort': json.dumps(oriDestNode)})


def pcInfo(request):
    odl = OdlUtil('127.0.0.1', '8080')
    topo = odl.get_topology(username="admin", password="admin")  # 拓扑包含的节点信息和连接链路的信息
    link = odl.get_connect(username="admin", password="admin")  # 节点详细信息
    py_topo = json.loads(topo)
    py_link = json.loads(link)
    return render(request, 'pc.html', {'topo': json.dumps(py_topo), 'link': json.dumps(py_link)})


def switchInfo(request):
    odl = OdlUtil('127.0.0.1', '8080')
    topo = odl.get_topology(username="admin", password="admin")  # 拓扑包含的节点信息和连接链路的信息
    link = odl.get_connect(username="admin", password="admin")  # 节点详细信息
    py_topo = json.loads(topo)
    py_link = json.loads(link)
    return render(request, 'switch.html', {'topo': json.dumps(py_topo), 'link': json.dumps(py_link)})


def linkInfo(request):
    odl = OdlUtil('127.0.0.1', '8080')
    topo = odl.get_topology(username="admin", password="admin")  # 拓扑包含的节点信息和连接链路的信息
    link = odl.get_connect(username="admin", password="admin")  # 节点详细信息
    py_topo = json.loads(topo)
    py_link = json.loads(link)
    return render(request, 'link.html', {'topo': json.dumps(py_topo), 'link': json.dumps(py_link)})


def repaire(request):
    odl = OdlUtil('127.0.0.1', '8080')
    topo = odl.get_topology(username="admin", password="admin")
    de_topo = json.loads(topo)
    sourPort = {}  #存放源端口
    destPort = {}  #
    #获取节点信息
    n = de_topo["network-topology"]["topology"][1]["node"]
    nodes = {}  # 存放节点信息
    i = 0
    for y in n:
        y2 = str(y["node-id"])  # y2表示node-id
        nodes[i] = y2
        i = i + 1

    oriLinkSour = {}
    oriLinkDest = {}
    link_source_id = {}  # 存放链接的源节点
    link_destination_id = {}  # 存放链接的目地节点
    kk = 0
    for nod in oriSourNode.keys():
        oriLinkSour[kk] = oriSourNode[nod]
        kk = kk + 1
    kk = 0
    for nod in oriDestNode.keys():
        oriLinkDest[kk] = oriDestNode[nod]
        kk = kk + 1

        # 获取连接信息
        l = de_topo["network-topology"]["topology"][1]["link"]
        k = 0
        for y in l:
            y3 = str(y["source"]["source-node"])
            y4 = str(y["destination"]["dest-node"])
            y5 = str(y["source"]["source-tp"])
            y6 = str(y["destination"]["dest-tp"])
            link_source_id[k] = y3
            link_destination_id[k] = y4
            sourPort[k] = y5
            destPort[k] = y6
            k = k + 1

    knum = get_number(link_source_id)
    redSour = compareDiff(oriLinkSour,sourPort,knum)

    con = odl.get_connect(username="admin", password="admin")
    # mid = json.dumps(con)
    de_con = json.loads(con)
    n = de_con["nodes"]["node"]
    errorNode = {}   ############ 存放故障节点端口id
    numK = 0
    for ny in n:
        ny1 = ny["node-connector"]
        for ny2 in ny1:
            if ny2["flow-node-inventory:state"]["link-down"] == True or ny2["flow-node-inventory:state"][
                "live"] == True or ny2["flow-node-inventory:state"]["blocked"] == True:
                errorNode[numK] = ny2["id"]
                numK = numK + 1

    if oriSourNode[0] == '0' and oriSourNode[19] != '999':
        kk = 0
        for nod in sourPort.keys():
            oriSourNode[kk] = sourPort[nod]
            kk = kk + 1
        kk = 0
        for nod in destPort.keys():
            oriDestNode[kk] = destPort[nod]
            kk = kk + 1
        oriSourNode[19] = '999'
    return render(request,'errornode.html',{'errorNode':json.dumps(errorNode),'sourPort': json.dumps(oriSourNode),'destPort': json.dumps(oriDestNode)})



def insert_flow():
    url = "http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:1/table/0/flow/111"

    payload = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<flow xmlns=\"urn:opendaylight:flow:inventory\">\n\t<priority>400</priority>\n\t<flow-name>Foo1</flow-name>\n\t<idle-timeout>0</idle-timeout>\n\t<hard-timeout>0</hard-timeout>\n\t<match>\n\t\t<ethernet-match>\n\t\t\t<ethernet-type>\n\t\t\t\t<type>2048</type>\n\t\t\t</ethernet-type>\n\t\t</ethernet-match>\n\t\t<ipv4-source>10.0.0.1/32</ipv4-source>\n\t</match>\n\t<id>111</id>\n\t<table_id>0</table_id>\n\t<instructions>\n\t\t<instruction>\n\t\t\t<order>0</order>\n\t\t\t<apply-actions>\n\t\t\t\t<action>\n\t\t\t\t\t<order>0</order>\n\t\t\t\t\t<output-action>\n\t\t\t\t\t\t<output-node-connector>3</output-node-connector>\n\t\t\t\t\t\t<max-length>0</max-length>\n\t\t\t\t\t</output-action>\n\t\t\t\t</action>\n\t\t\t</apply-actions>\n\t\t</instruction>\n\t</instructions>\n</flow>"
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml',
        'Authorization': 'Basic YWRtaW46YWRtaW4=',
        'Authorization': 'Basic YWRtaW46YWRtaW4='
    }

    response = requests.request("PUT", url, headers=headers, data=payload)


def insert_flow2():
    # openflow:1
    url = "http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/openflow:1/table/0/flow/111"

    payload = "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"no\"?>\n<flow xmlns=\"urn:opendaylight:flow:inventory\">\n\t<priority>400</priority>\n\t<flow-name>Foo1</flow-name>\n\t<idle-timeout>0</idle-timeout>\n\t<hard-timeout>0</hard-timeout>\n\t<match>\n\t\t<ethernet-match>\n\t\t\t<ethernet-type>\n\t\t\t\t<type>2048</type>\n\t\t\t</ethernet-type>\n\t\t</ethernet-match>\n\t\t<ipv4-source>10.0.0.1/32</ipv4-source>\n\t</match>\n\t<id>111</id>\n\t<table_id>0</table_id>\n\t<instructions>\n\t\t<instruction>\n\t\t\t<order>0</order>\n\t\t\t<apply-actions>\n\t\t\t\t<action>\n\t\t\t\t\t<order>0</order>\n\t\t\t\t\t<output-action>\n\t\t\t\t\t\t<output-node-connector>2</output-node-connector>\n\t\t\t\t\t\t<max-length>0</max-length>\n\t\t\t\t\t</output-action>\n\t\t\t\t</action>\n\t\t\t</apply-actions>\n\t\t</instruction>\n\t</instructions>\n</flow>"
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml',
        'Authorization': 'Basic YWRtaW46YWRtaW4=',
        'Authorization': 'Basic YWRtaW46YWRtaW4='
    }

    response = requests.request("PUT", url, headers=headers, data=payload)


def xiufu(request):
    odl = OdlUtil('127.0.0.1', '8080')
    topo = odl.get_topology(username="admin", password="admin")  # 拓扑包含的节点信息和连接链路的信息
    link = odl.get_connect(username="admin", password="admin")  # 节点详细信息
    py_topo = json.loads(topo)
    py_link = json.loads(link)

    errorNode = {}  # 存放故障节点端口
    differ = {}
    differ[0] = '0'
    n = py_link["nodes"]["node"]
    index(request)  # 必不可少!!!!!!!!
    numK = 0
    for ny in n:
        ny1 = ny["node-connector"]
        for ny2 in ny1:
            if ny2["flow-node-inventory:state"]["link-down"] == True or ny2["flow-node-inventory:state"][
                "live"] == True or ny2["flow-node-inventory:state"]["blocked"] == True:
                errorNode[numK] = ny2["id"]
                numK = numK + 1

    numk2 = 0
    for ken in errorNode.keys():
        if (errorNode[ken][-1] != 'L'):
            differ[numk2] = errorNode[ken]
            numk2 = numk2 + 1

    key = differ[0]

    # 如果故障节点是2就插入出口为3的流表
    if (key[0] != '0' and key[-3] == '1'):
        if (key[-3] == '1' and key[-1] == '2'):
            insert_flow()
        if (key[-3] == '1' and key[-1] == '3'):
            insert_flow2()
    return render(request, 'index.html')


# 自写测试模块

def my_insert_flow(openflow_name, openflow_port, source_ip, dest_ip, priority, flow_id=111):
    # openflow_name示例： openflow:1
    url = "http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/{0}/table/0/flow/{1}".format(
        openflow_name,flow_id)

    payload = """<?xml version="1.0" encoding="UTF-8" standalone="no"?>
    <flow xmlns="urn:opendaylight:flow:inventory">
    <priority>{0}</priority>
    <flow-name>Foo1</flow-name>
    <idle-timeout>0</idle-timeout>
    <hard-timeout>0</hard-timeout>
    <match>
        <ethernet-match>
            <ethernet-type>
                <type>2048</type>
            </ethernet-type>
        </ethernet-match>
        <ipv4-source>{1}/32</ipv4-source>
        <ipv4-destination>{2}/32</ipv4-destination>
    </match>
    <id>111</id>
    <table_id>0</table_id>
    <instructions>
        <instruction>
            <order>0</order>
            <apply-actions>
                <action>
                    <order>0</order>
                    <output-action>
                        <output-node-connector>{3}</output-node-connector>
                        <max-length>0</max-length>
                    </output-action>
                </action>
            </apply-actions>
        </instruction>
    </instructions>
    </flow>""".format(
        priority, source_ip, dest_ip, openflow_port
    )
    headers = {
        'Content-Type': 'application/xml',
        'Accept': 'application/xml',
        'Authorization': 'Basic YWRtaW46YWRtaW4=',
        'Authorization': 'Basic YWRtaW46YWRtaW4='
    }

    response = requests.request("PUT", url, headers=headers, data=payload)

def my_delete_flow(openflow_name,flow_id=111):
    # openflow_name : openflow:67
    url = "http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/{0}/table/0/flow/{1}".format(openflow_name,flow_id)

    payload = {}
    headers = {
        'Content-Type': 'application/xml',
        'Authorization': 'Basic YWRtaW46YWRtaW4='
    }

    response = requests.request("DELETE", url, headers=headers, data=payload)

def testview(request):
    odl = OdlUtil('127.0.0.1', '8080')
    topo = odl.get_topology(username="admin", password="admin")  # 拓扑包含的节点信息和连接链路的信息
    link = odl.get_connect(username="admin", password="admin")  # 节点详细信息

    topo_all_node = json.loads(topo)["network-topology"]["topology"][1]["node"]
    switchNum = 0       # 交换机数量
    node2numDict = {}  # 以交换机id为key，序号为value
    num2nodeDict = {}   # 和上面反过来
    mac2ipDict = {}     # mac->ip
    swport2macDict = {}    # switch和相连主机的信息,switch_name -> host_ip
    sw2hostipDict = {}  # switch->host_ip
    for i in topo_all_node:
        if i["node-id"].startswith("openflow"):
            node2numDict[i["node-id"]] = switchNum
            num2nodeDict[switchNum] = i["node-id"]
            switchNum += 1
        else:
            mac = i["host-tracker-service:addresses"][0]['mac']
            ip = i["host-tracker-service:addresses"][0]['ip']
            mac2ipDict[mac] = ip
    net_map = [[float('inf') for i in range(switchNum)] for j in range(switchNum)]
    link_map = {}
    re_link_map = {}
    py_topo_link = json.loads(topo)["network-topology"]["topology"][1]["link"]
    for i in py_topo_link:
        src = i["source"]["source-tp"]
        dest = i["destination"]["dest-tp"]
        # 交换机相连的链路，用来建立交换机网络拓扑
        if src.startswith("openflow") and dest.startswith("openflow"):
            x1 = i["source"]["source-node"]
            x2 = i["destination"]["dest-node"]
            x1 = node2numDict[x1]
            x2 = node2numDict[x2]
            # TODO distance now set 1, need to change
            net_map[x1][x2] = 1
            tmpdict = {}
            tmpdict['source'] = src
            tmpdict['destination'] = dest
            tmpstr = "{0},{1}".format(x1, x2)
            link_map[tmpstr] = tmpdict
            re_link_map[src] = tmpstr
        elif src.startswith("openflow"):
            x1 = i["source"]["source-node"]
            host_ip = i["destination"]["dest-node"][5:]
            sw2hostipDict[x1] = mac2ipDict[host_ip]
    # print('num2nodeDict------------------------')
    # print(num2nodeDict)
    # print('node2numDict---------------')
    # print(node2numDict)
    # print(sw2hostipDict)
    # print('mac2ipDict----------------------')
    # print(mac2ipDict)
    # print('sw2hostDict----------------')
    # print(swport2macDict)
    # print('sw2hostipDict------')
    # print(sw2hostipDict)
    # print('link_map-------------')
    # for i in link_map:
    #     print(i, link_map[i])
    # print('re_link_map-------------')
    # for i in re_link_map:
    #     print(i, re_link_map[i])
    # print('net_map --------------------------')
    # for i in range(switchNum):
    #     print(net_map[i])

    py_link = json.loads(link)
    errorNode = {}  # 存放故障节点端口
    differ = {}
    differ[0] = '0'
    n = py_link["nodes"]["node"]
    # index(request)  # 必不可少!!!!!!!!
    numK = 0
    for ny in n:
        ny1 = ny["node-connector"]
        for ny2 in ny1:
            if ny2["id"][-1] == "L":
                continue
            src_port = ny2["id"]
            src_mac = ny2["flow-node-inventory:hardware-address"]
            swport2macDict[src_port]=src_mac
            print(src_port, src_mac)
            if ny2["flow-node-inventory:state"]["link-down"] == True or ny2["flow-node-inventory:state"][
                "live"] == True or ny2["flow-node-inventory:state"]["blocked"] == True:
                # 这里ny2[id]就是故障的交换机的端口号，格式类似openflow:1:3，代表openflow:1的3端口故障
                errorNode[numK] = ny2["id"]
                numK = numK + 1
    print('errorNode---------------------')
    print(errorNode)
    from .dijkstra import NodeMap
    new_map = NodeMap(net_map)
    # 结果字典
    resultDict={}
    # if errorNode=={}:
    #     # 链路正常时删除下发的流表
    #     return HttpResponse(topo)
    errorNodeIndex1 = 0
    errorNodeIndex2 = 0
    totalIndex = 0
    while errorNodeIndex1 < len(errorNode)-1:
        errorNodeIndex2 = errorNodeIndex1+1
        while errorNodeIndex2<len(errorNode):
            node_name1 = errorNode[errorNodeIndex1][:-2]
            node_name2 = errorNode[errorNodeIndex2][:-2]
            # 同一台交换机上故障多个端口会出现，不管这种情况
            if node_name1 == node_name2:
                errorNodeIndex2 += 1
                continue
            # tmplist 记录这一条的最短路径
            tmplist = []
            print('本次调度: {0} ---> {1}'.format(node_name1,node_name2))
            i = node2numDict[node_name1]
            j = node2numDict[node_name2]
            sw_src_name = num2nodeDict[i]
            sw_dest_name = num2nodeDict[j]
            length, path = new_map.dijkstra(i, j)  # 从s1到s4
            print("{0}--->{1}, {2}, {3} ".format(num2nodeDict[i], num2nodeDict[j], length, path))
            src_host_ip = sw2hostipDict[num2nodeDict[i]]
            dest_host_ip = sw2hostipDict[num2nodeDict[j]]
            print('源ip: {0}------> 目的ip: {1}'.format(src_host_ip,dest_host_ip))
            tmppdict = {
                'source':src_host_ip,
                'destination':num2nodeDict[i]
            }
            tmplist.append(tmppdict)
            index1=0
            index2=0
            # 对最短路径的两相邻节点进行流表下发
            while index1<length:
                index2=index1+1
                s1 = "{0},{1}".format(path[index1], path[index2])
                result = link_map[s1]
                print(result)
                tmplist.append(result)
                openflow_name = 'openflow:' + result['source'].split(':')[1]
                openflow_port = result['source'].split(':')[2]
                # src_mac_tmp = swport2macDict[result['source']]
                # dest_mac_tmp = swport2macDict[result['destination']]

                priority = 400
                my_insert_flow(
                    openflow_name=openflow_name,
                    openflow_port=openflow_port,
                    source_ip=src_host_ip,
                    dest_ip=dest_host_ip,
                    priority=priority
                )
                index1+=1
            tmppdict = {
                'source':num2nodeDict[j],
                'destination':dest_host_ip
            }
            tmplist.append(tmppdict)
            resultDict[totalIndex]=tmplist
            totalIndex+=1
            errorNodeIndex2+=1
        errorNodeIndex1 +=1
    for i in resultDict:
        print('序号{}'.format(i))
        for j in resultDict[i]:
            print(j)
    #return HttpResponse(json.dumps(resultDict))
    print(resultDict)
    return render(request,'testview.html',{'resultDict': json.dumps(resultDict)})
###创建一个表,node,time,运行一次后注释掉这部分
# connect = sqlite3.connect('testsqlite.db')  # 连接一个数据库
# cursor = connect.cursor()
#
# sql = '''create table gzlogsss (
#            nodes text,
#            timess text)'''
# cursor.execute(sql)
# cursor.close()

def rizhi(request):
    try:
        odl = OdlUtil('127.0.0.1', '8080')
        topo = odl.get_topology(username="admin", password="admin")  #从ODL中获得的原始json数据
    except Exception as e:
        return render(request,'error.html')
    #mid = json.dumps(topo)                                       #转换为str
    de_topo = json.loads(topo)                                   #转换为python对象-字典

    sourPort = {}  #存放源端口
    destPort = {}  #存放目地端口

    ############################
    oriLinkSour = {}
    oriLinkDest = {}
    kk = 0
    for nod in oriSourNode.keys():
        oriLinkSour[kk] = oriSourNode[nod]
        kk = kk + 1
    kk = 0
    for nod in oriDestNode.keys():
        oriLinkDest[kk] = oriDestNode[nod]
        kk = kk + 1
    ############################
    #-----获取节点信息-----#解析json格式数据代码↓ n是列表
    n = de_topo["network-topology"]["topology"][1]["node"]       #进入到节点所在的list中
    x2 = str(n[0]["node-id"])                                    ###测试节点###
    nodes = {}                                                   #存放节点信息,其中,×××若以openflow开头则为交换机,若以host开头则为主机×××
    i = 0
    for y in n:                                                  #遍历node,取出节点信息放入nodes{}
        y2 = str(y["node-id"])#取出每一个结点的id信息，存入nodes中
        nodes[i] = y2
        i = i + 1             #i统计结点个数

    # -----获取链接信息-----#
    l = de_topo["network-topology"]["topology"][1]["link"]  #进入到链接所在的list中
    x3 = str(l[0]["source"]["source-node"])                               ###测试节点###
    x4 = str(l[0]["source"]["source-tp"])
    link_source_id = {}                                     #存放链接的源节点
    link_destination_id = {}                                #存放链接的目地节点
    k = 0
    for y in l:                                             #遍历link,取出链接信息存入link_source_id和link_destination_id
        y3 = str(y["source"]["source-node"])
        y4 = str(y["destination"]["dest-node"])
        y5 = str(y["source"]["source-tp"])
        y6 = str(y["destination"]["dest-tp"])
        link_source_id[k] = y3
        link_destination_id[k] = y4
        sourPort[k] = y5
        destPort[k] = y6
        k = k + 1
    ##############################解析json格式数据代码👆
    knum = get_number(link_source_id)               #字典值的个数减一
    redSour = compareDiff(oriLinkSour,sourPort,knum)#取两个字典不同的地方

    ##############################
    con = odl.get_connect(username="admin", password="admin")
    # mid = json.dumps(con)
    de_con = json.loads(con)
    n = de_con["nodes"]["node"]
    # topology(request)   #必不可少
    errorNode = {}  # 存放故障节点端口
    numK = 0
    for ny in n:
        ny1 = ny["node-connector"]
        for ny2 in ny1:
            if ny2["flow-node-inventory:state"]["link-down"] == True or ny2["flow-node-inventory:state"]["live"] == True or ny2["flow-node-inventory:state"]["blocked"] == True:
                errorNode[numK] = ny2["id"]
                numK = numK + 1

    if oriSourNode[0] == '0'and oriSourNode[19] != '999':
        kk = 0
        for nod in sourPort.keys():
            oriSourNode[kk] = sourPort[nod]
            kk = kk + 1
        kk = 0
        for nod in destPort.keys():
            oriDestNode[kk] = destPort[nod]
            kk = kk + 1
        oriSourNode[19] = '999'


    connect = sqlite3.connect('testsqlite.db')
    cursor = connect.cursor()
    for nn in errorNode.values():
        nodes = nn
        localtime = time.asctime(time.localtime(time.time()))
        timess = localtime
        sql = ''' insert into gzlogsss
                             (nodes, timess)
                             values
                             (:st_node, :st_Time)'''
        cursor.execute(sql, {'st_node': nodes, 'st_Time': timess})
        connect.commit()
    sql = '''select * from gzlogsss'''
    results = cursor.execute(sql)
    all_gzlogssss = results.fetchall()  ##all_gzlogss是一个列表，每一个元素都是node+time
    kk0 = 0
    kk1 = len(all_gzlogssss)
    all_gzlogss = {}
    for kk0 in range(0, kk1):
        all_gzlogss[kk0] = all_gzlogssss[kk0]
        kk0 += 1
    return render(request, 'rizhi.html', {'all_gzlogss': json.dumps(all_gzlogss)})
