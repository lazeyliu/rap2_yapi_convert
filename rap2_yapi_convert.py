#!/usr/bin/env python
# encoding: utf-8
# -*- coding: utf-8 -*-
import re
import json
import sys
import requests
import argparse

RAP2_HOST = 'http://xxxxx.xxxx.com'
YAPI_HOST = 'http://192.20.1.19:1000'

RAP2_COOKIE = ''
YAPI_COOKIe = ''


# 创建分类
def create_cat(name, desc, project_id):
    if desc is None:
        desc = "";
    headers = {
        'Content-type': 'Content-Type: application/json;charset=UTF-8',
        'Cookie': YAPI_COOKIe
    }
    get_cat_url = YAPI_HOST + '/api/interface/getCatMenu?project_id=' + str(project_id);
    ar = requests.get(get_cat_url, headers=headers)
    ar_result = json.loads(ar.text)
    catid = 0
    if ar.status_code == 200 and ar_result['errcode'] == 0:
        for cat in ar_result['data']:
            if cat['name'] == name:
                catid = cat['_id']
    else:
        raise Exception('查询 getCatMenu 异常')

    if catid == 0:
        headers = {
            'Cookie': YAPI_COOKIe
        }
        create_cat_url = YAPI_HOST + '/api/interface/add_cat'
        params = {"name": name, "desc": desc, "project_id": project_id}
        r = requests.post(
            create_cat_url,
            headers=headers,
            json=params
        )
        print params
        result = json.loads(r.text)
        if r.status_code == 200 and result['errcode'] == 0:
            print(u'创建分类成功: %s\n' % name)
            return result['data']['_id']
        else:
            print(u'创建分类失败! %s\n' % r.text)
            raise Exception("创建分类失败！")
    else:
        return catid


# 创建接口
def create_interface(param):
    headers = {
        'Content-type': 'application/json',
        'Cookie': YAPI_COOKIe
    }
    r = requests.post(YAPI_HOST + '/api/interface/save', headers=headers, json=param)
    result = json.loads(r.text)
    if r.status_code == 200 and result['errcode'] == 0:
        print u'save接口成功! ', r.text
    else:
        print u'save接口失败: ', r.text
        raise Exception('save接口失败！')


# 转换类型
def convert_type(param_type):
    if param_type == 'String':
        return 'string'
    elif param_type == 'Number':
        return 'int'
    elif param_type == 'Boolean':
        return 'boolean'
    elif param_type == 'Array':
        return 'array'
    elif param_type == 'Object':
        return 'object'
    else:
        return 'string'


# 加载rap2 配置
def load_api(repository_id):
    if RAP2_HOST and RAP2_HOST.endswith('/'):
        raise Exception('RAP2_HOST 不能/ 结尾')
    headers = {
        'Content-type': 'application/json',
        'Cookie': RAP2_COOKIE
    }
    repository_url = RAP2_HOST + '/repository/get?id=' + str(repository_id)
    r = requests.get(repository_url, headers=headers, json={})
    if r.status_code == 200:
        apis = json.loads(r.text)
        modules = apis['data']['modules']
        return modules
    else:
        raise Exception('拉取rap2 配置文件失败！')


# 加载接口列表 配置
def load_interface_multi(rap2_repository_id, project_id):
    if YAPI_HOST and YAPI_HOST.endswith('/'):
        raise Exception('YAPI_HOST 不能/ 结尾')

    modules = load_api(rap2_repository_id)
    for module in modules:
        # 创建分类
        catid = create_cat(module['name'], module['description'], project_id);
        # 便利rap2 接口 并构建
        for interface in module['interfaces']:
            # 构建创建接口参数
            param = load_interface(project_id, catid, interface)
            # 创建接口！！！
            create_interface(param)
    print '================导入结束 rap2_repository_id:' + str(rap2_repository_id) + '结束'
    print '================导入结束 rap2_repository_id:' + str(rap2_repository_id) + '结束'
    print '================导入结束 rap2_repository_id:' + str(rap2_repository_id) + '结束'
    print ""


# 加载接口
def load_interface(project_id, catid, interface):
    domain = 'http://'
    yapi_req_property = {}
    url = interface['url']
    if url is not None:
        url = url.replace(" ", "")
        url = url.replace("+", "")

        # 消除中文url
    regex = re.compile(ur"[\u4e00-\u9fa5]")
    url = regex.sub('', url)
    if domain in url:
        url = str(url[url.index(domain) + len(domain):] + '')
    yapi_req_property['title'] = interface['name']
    yapi_req_property['project_id'] = project_id
    if not url.startswith('/'):
        url = ('/' + url)
    url = re.sub(r"(/http://|/https://).*?/", "/", url)

    yapi_req_property['path'] = url.strip()
    yapi_req_property['catid'] = catid
    yapi_req_property['desc'] = interface['description']
    yapi_req_property['method'] = interface['method']
    yapi_req_property['req_headers'] = []
    yapi_req_property['status'] = 'done'
    yapi_req_property['res_body_type'] = 'json'
    yapi_req_property['res_body_is_json_schema'] = 'true'

    if interface['method'] == 'POST':
        yapi_req_property['req_body_form'] = []
        yapi_req_property['req_body_type'] = 'form'
    else:
        yapi_req_property['req_query'] = []

    # 响应体
    res_body = {"title": "empty object", 'type': 'object', 'properties': {}}

    interface['properties'].sort(key=lambda x: x["parentId"])

    y_dict_tree = {'-1': {'type': 'object', 'title': 'empty object', 'properties': {}, 'required': []}}
    for rap_property in interface['properties']:
        if rap_property['scope'] == 'request' and rap_property['pos'] == 1:
            yapi_header_param = rap2yap_header_obj_convert(rap_property)
            yapi_req_property['req_headers'].append(yapi_header_param)
        elif rap_property['scope'] == 'request' and rap_property['pos'] != 1:
            # 请求参数
            y_req_param = rap2yap_req_obj_convert(interface['method'], rap_property)
            if interface['method'] == 'POST':
                yapi_req_property['req_body_form'].append(y_req_param)
            else:
                yapi_req_property['req_query'].append(y_req_param)
        else:
            parent_id = str(rap_property['parentId'])
            rap_param_name = rap_property['name']  # key
            rap_param_type = rap_property['type']  # type
            rap_param_value = rap_property['value']  # type
            yapi_res_params = {
                'type': convert_type(rap_property['type']),
                'description': "" if rap_property['description'] is None else rap_property['description'],
                'required': [],
                'properties': {}
            }
            if rap_param_type == 'Object' or rap_param_type == 'Array':
                y_dict_tree[str(rap_property['id'])] = yapi_res_params
            if rap_param_type == 'Array':
                yapi_res_params["items"] = {
                    "type": "string",
                    "required": [],
                    "properties": {}
                }

            yapi_res_params["default"] = rap_param_value
            y_dict_tree.setdefault(parent_id, None)
            y_tree_parent = y_dict_tree[parent_id]
            if y_tree_parent is not None:
                if y_tree_parent["type"] == 'array':
                    y_tree_parent["items"]["type"] = 'object'
                    y_tree_parent["items"]["properties"][rap_param_name] = yapi_res_params
                    if rap_property['required'] is not None and rap_property['required'] is True:
                        y_tree_parent["items"]["required"].append(rap_param_name)
                else:
                    y_dict_tree[parent_id]['properties'][rap_param_name] = yapi_res_params;
                    if rap_property['required'] is not None and rap_property['required'] is True:
                        y_dict_tree[parent_id]['required'].append(rap_param_name)

    res_body['properties'] = y_dict_tree['-1']['properties']
    yapi_req_property['res_body'] = json.dumps(res_body, ensure_ascii=False)

    print "  接口名称：", yapi_req_property['title']
    print "  原始地址：", interface['url']
    print "  请求地址：", yapi_req_property['path']
    print "  请求类型：", yapi_req_property['method']
    print "    请求头：", yapi_req_property['req_headers']
    print "GET 请求体：", yapi_req_property.setdefault('req_query', [])
    print "POST请求体：", yapi_req_property.setdefault('req_body_form', [])
    print "    响应体：", yapi_req_property['res_body']
    return yapi_req_property


# 请求头属性转换
def rap2yap_header_obj_convert(rap_obj):
    # 请求属性
    req_header = {
        'name': rap_obj['name'],
        'value': rap_obj['value'],
        'type': 'text',
        'example': rap_obj['value'],
        'desc': rap_obj['description']
    }
    return req_header


# 请求属性转换
def rap2yap_req_obj_convert(req_method, rap_obj):
    # 请求属性
    req_param = {
        'name': rap_obj['name'],
        'value': rap_obj['value'],
        'type': 'text',
        'example': rap_obj['value'],
        'desc': rap_obj['description'],
        'required': ("0" if rap_obj["required"] is False else "1")
    }
    return req_param


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project_id', help='项目id')
    parser.add_argument('-f', '--file', help='json文件路径')
    parser.add_argument('-H', "--YAPI_HOST", help='主机地址 例如 https://www.xxx.com')
    parser.add_argument('-d', "--domain", help='需要过滤的域名')
    parser.add_argument('-t', "--token", help='项目的ACCESS_TOKEN')

    args = parser.parse_args()

    load_interface_multi(56, 79)

    load_interface_multi(58, 103)

    load_interface_multi(27, 147)
    load_interface_multi(28, 143)
    load_interface_multi(29, 139)
    load_interface_multi(37, 135)

    load_interface_multi(22, 131)

    load_interface_multi(38, 127)

    load_interface_multi(32, 123)

    load_interface_multi(42, 119)

    load_interface_multi(53, 115)

    load_interface_multi(47, 111)

    load_interface_multi(30, 99)
    load_interface_multi(24, 95)
    load_interface_multi(36, 91)
    load_interface_multi(33, 87)

    load_interface_multi(49, 83)
    load_interface_multi(25, 151)

    load_interface_multi(21, 66)
    load_interface_multi(18, 155)
#
