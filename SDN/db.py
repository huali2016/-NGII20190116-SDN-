import requests

def my_insert_flow(openflow_name, openflow_port, source_ip, dest_ip, priority):
    # openflow_name示例： openflow:1
    url = "http://127.0.0.1:8080/restconf/config/opendaylight-inventory:nodes/node/{}/table/0/flow/111".format(
        openflow_name)

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


# for i in range(65,71):
#    my_delet
#    e_flow('openflow:{}'.format(i))
# 只需要修改第二个参数，出端口根据实际网络拓扑修改
my_insert_flow('openflow:69',3,'20.0.0.3','20.0.0.4',400)
my_insert_flow('openflow:70',1,'20.0.0.3','20.0.0.4',400)