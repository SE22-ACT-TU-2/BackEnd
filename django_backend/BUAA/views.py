from __future__ import unicode_literals
import matplotlib.pyplot as plt
import plotly.offline as opy
import plotly.graph_objects as go
from django.forms import model_to_dict
from django.template import loader
from django.http import HttpResponse
import numpy as np
import pandas as pd
import BUAA.models
import BUAA.utils as utils
import json
import uuid
import hashlib
import backend.settings as settings
from django.core.cache import cache
import requests
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from .serializers import *
from rest_framework.response import Response
from rest_framework.viewsets import *
from rest_framework import status
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from django_redis import get_redis_connection
from BUAA.authentication import *
import datetime
from BUAA.const import NOTIF, BLOCKID, NOTIF_TYPE_DICT, APPLY
import time
import os
from BUAA.accessPolicy import *
import random
import traceback
from BUAA.recommend import update_kwd_typ, add_kwd_typ, delete_kwd_typ, get_keyword, get_recommend
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt

# from datetime import datetime

base_dir = '/root/server_files/'
web_dir = 'https://www.reedsailing.xyz/server_files/'
web_dir = 'http://114.116.194.3/server_files/'

sender = utils.MailSender()


def testHmb(request):
    print(request)
    res = {"res": 1}
    return Response(data=res, status=200)


def get_random_str():
    uuid_val = uuid.uuid4()
    uuid_str = str(uuid_val).encode("utf-8")
    md5 = hashlib.md5()
    md5.update(uuid_str)
    return md5.hexdigest()


# 仅供文件内部调用


def _create_notif_for_all(user_id_list, notif, add_receivers=None):
    """revoke when user keeps online"""
    user_id_list = [int(x) for x in user_id_list]
    if add_receivers is not None:
        add_receivers['__receivers__'] = user_id_list
    for p_id in user_id_list:
        p_id = int(p_id)
        if notif['type'] == NOTIF.NewBoya:
            sender.send_mail(
                '【一苇以航】' + NOTIF_TYPE_DICT[notif['type']], notif['content'], _user_id2user_email(p_id))
        new_send_notification(notif['id'], p_id)

        # if p_id in clients :
        #     p_ws = clients[p_id]
        #     utils.push_all_notif(p_id, p_ws)


def _act_id2act_name(pk):
    pk = int(pk)
    return BUAA.models.Activity.objects.get(id=pk).name


def _org_id2org_name(pk):
    pk = int(pk)
    return BUAA.models.Organization.objects.get(id=pk).name


def _user_id2user_name(pk):
    pk = int(pk)
    return BUAA.models.WXUser.objects.get(id=pk).name


def _user_id2user_email(pk):
    pk = int(pk)
    return BUAA.models.WXUser.objects.get(id=pk).email


def _user_id2user_money(pk):
    pk = int(pk)
    return WXUser.objects.get(id=pk).money


def _ground_id2ground_area(ground_id):
    ground = Ground.objects.get(id=ground_id)
    return [ground.area, ground.name]


def _get_hour(date_time):
    dt_str = str(date_time)
    return int(dt_str.split()[1].split(':')[0])


def _get_date(date_time):
    dt_str = str(date_time)
    return dt_str.split()[0]


def _get_price_hour(ground_id, begin_time, end_time):
    price = Ground.objects.get(id=ground_id).price
    return price * (end_time - begin_time)


def _get_price(ground_id, begin_time, end_time):
    price = Ground.objects.get(id=ground_id).price
    hours = _get_hour(end_time) - _get_hour(begin_time)
    return price * hours


def _to_datetime(date, time_):  # "2022-04-20", 15
    if time_ < 10:
        return date + " 0" + str(time_) + ":00:00"
    else:
        return date + " " + str(time_) + ":00:00"


def _to_standard_date(date):  # "2022-4-13"
    yy = date.split('-')[0]
    mm = date.split('-')[1]
    dd = date.split('-')[2]
    if len(mm) == 1:
        mm = "0" + mm
    if len(dd) == 1:
        dd = "0" + dd
    return yy + "-" + mm + "-" + dd


def _get_booking_time(ground_id, date, user_id):
    # 获取指定用户在某一天某个区域所预约的时长（仅限普通预约）
    area = Ground.objects.get(id=ground_id).area
    grounds = Ground.objects.filter(area=area)
    applies = []
    for ground in grounds:
        applies.extend(
            GroundApply.objects.filter(user_id=user_id, ground_id=ground.id, begin_time__contains=date).exclude(
                state=2).exclude(identity=1))
    res = 0
    for apply in applies:
        res = res + apply.end_time.hour - apply.begin_time.hour
    return res


def send_new_boya_notf(data):
    """interface for external boya creating function"""
    content = utils.get_notif_content(NOTIF.NewBoya, act_name=data['name'])
    notif = new_notification(NOTIF.NewBoya, content,
                             act_id=data['act'], org_id=None)
    followers = _get_boya_followers()
    receivers = [f.id for f in followers]
    _create_notif_for_all(receivers, notif)
    # return receivers


"""
新建通知

输入：
    content：通知内容
输出：
    数据字典
        id：该notification的id
        time： 发布时间
        content： 通知内容
"""


def new_notification(type, content, act_id=None, org_id=None):
    data = {
        'type': type,
        'content': content,
    }
    if act_id:
        data['act'] = act_id
    if org_id:
        data['org'] = org_id
    serializer = NotificationSerializer(data=data)
    serializer.is_valid()
    serializer.save()
    return serializer.data


"""
新建发送通知关系

输入：
    notif_id: 通知的id
    user_id: 接收通知的用户id
输出：
    数据字典：
        id：发送通知关系的id
        notif： 通知的id
        person： 接收通知的用户的id
        already_read： 是否已读（为false）
"""


def new_send_notification(notif_id, user_id):
    data = {
        'notif': notif_id,
        'person': user_id
    }
    serializer = SentNotificationSerializer(data=data)
    serializer.is_valid()
    serializer.save()
    return serializer.data


@api_view(['POST'])
@csrf_exempt
def web_token_identify(request):
    token = request.data['token']
    username = cache.get(token)
    if not username:
        res = {'status': 0, 'name': ''}
    else:
        res = {'status': 1, 'name': username if len(
            username) <= 15 else "regular user"}
        cache.set(token, username, 24 * 60 * 60)
    return Response(res, 200)


@api_view(['POST'])
@authentication_classes([UserAuthentication, SuperAdminAuthentication, ErrorAuthentication])
def get_page_qrcode(request):
    body = {
        "path": request.data["path"],
        "width": request.data["width"],
    }
    r = requests.post(url="https://api.weixin.qq.com/cgi-bin/wxaapp/createwxaqrcode?access_token=" +
                          utils.get_access_token(), data=json.dumps(body), headers={"Content-Type": "application/json"})

    path = "qrcode/" + get_random_str() + '.png'
    with open(base_dir + path, 'wb') as f:
        f.write(r.content)

    res = {
        "img": web_dir + path
    }

    return Response(data=res, status=200)


def _get_boya_followers():
    return WXUser.objects.filter(follow_boya=True)


@api_view(['POST'])
@authentication_classes([UserAuthentication, ErrorAuthentication])
def send_email(request):
    email_address = request.data['email']
    if not email_address.endswith("@buaa.edu.cn"):
        res = {
            'status': 1,
            'msg': 'Email address not belong to BUAA'
        }
        return Response(data=res, status=400)

    random_str = get_random_str()[:6]
    sender.send_mail('ReedSailing Certification', 'Your verify code is {}, valid in 5 minutes.'.format(random_str),
                     email_address)

    cache.set(random_str, email_address, 300)  # 验证码时效5分钟
    # # 用redis代替
    # redis_conn = get_redis_connection("code")
    # redis_conn.set("sms_code_%s" % email_address, random_str, 300)

    res = {
        'status': 0,
        'msg': 'Email send'
    }
    # print("successfully send email to", email_address)
    return Response(data=res, status=200)
    # return my_response(res)


@api_view(['POST'])
@authentication_classes([UserAuthentication, ErrorAuthentication])
@permission_classes((OtherAccessPolicy,))
def verify_email(request):
    verifyCode = request.data['verifyCode']
    config_email = request.data['email']
    id = request.data['id']

    # token = request.COOKIES.get('token')
    # openid = utils.decode_openid(token)
    email = cache.get(verifyCode)
    if config_email == email:
        res = {
            'status': 0,
            'detail': 'Valid Code'
        }
        WXUser.objects.filter(id=id).update(email=config_email)
        status = 200
    else:
        res = {
            'status': 1,
            'detail': '验证码错误',
        }
        status = 400

    # # 用redis代替
    # redis_conn = get_redis_connection("code")
    # redis_sms_code = redis_conn.get("sms_code_%s" % config_email)
    # if verifyCode == redis_sms_code:
    #     res = {
    #         'status': 0,
    #         'msg': 'Valid Code'
    #     }
    #     WXUser.objects.filter(id=id).update(email=config_email)
    #     status = 200
    #
    # else:
    #     res = {
    #         'status': 1,
    #         'msg': 'Invalid Code',
    #     }
    #     status = 400

    return Response(res, status)
    # return my_response(res)


@api_view(['POST'])
def user_login(request):
    # raise Exception
    # 取出数据
    # print('login')
    js_code = request.data['code']

    # 获取openid和session_key
    appid = settings.APPID
    secret = settings.SECRET
    url = 'https://api.weixin.qq.com/sns/jscode2session' + '?appid=' + appid + \
          '&secret=' + secret + '&js_code=' + js_code + '&grant_type=authorization_code'
    response = json.loads(requests.get(url).content)  # 将json数据包转成字典

    if 'errcode' in response:
        # 有错误码
        # print("err msg" + response['errmsg'])
        return Response(data={
            'status': 1,
            'code': response['errcode'],
            'msg': response['errmsg']
        }, status=400)
    # 登录成功
    openid = response['openid']
    session_key = response['session_key']

    # 保存openid, name, avatar
    user, create = WXUser.objects.get_or_create(openid=openid)

    # print(WXUser.objects.get_or_create(openid=openid))

    token = utils.encode_openid(openid, 24 * 60 * 60)
    cache.set(token, openid, 24 * 60 * 60)

    res = {
        "status": 0,
        "userExist": 0 if create else 1,
        "token": token,
        "email": user.email,
        "id": user.id,
        "avatar": user.avatar,
        "sign": user.sign,
        "name": user.name,
        "contact": user.contact,
        "follow_boya": user.follow_boya
    }
    return Response(data=res, status=200)


@api_view(['POST'])
@authentication_classes([])  # 用户认证
def user_register(request):
    # 取出数据
    id_ = request.data['id']
    user_info = request.data['userInfo']

    WXUser.objects.filter(id=id_).update(name=user_info.get(
        "nickName"), avatar=user_info.get("avatarUrl"))

    # print("register user", WXUser.objects.get_or_create(id=id_))

    res = {
        "status": 0
    }
    return Response(data=res, status=200)


@api_view(['POST'])
@authentication_classes([UserAuthentication, SuperAdminAuthentication, ErrorAuthentication])
@permission_classes((OtherAccessPolicy,))
def user_org_relation(request):
    user_id = request.data['user']
    org_id = request.data['org']
    try:
        user = WXUser.objects.get(id=user_id)
    except:
        res = {
            "detail": '未找到用户'
        }
        status = 404
        return Response(res, status)
    try:
        org = Organization.objects.get(id=org_id)
    except:
        res = {
            "detail": '未找到组织'
        }
        status = 404
        return Response(res, status)
    res = {
        "isFollower": False,
        "isOwner": False,
        "isManager": False,
    }
    if FollowedOrg.objects.filter(org=org_id, person=user_id):
        res["isFollower"] = True
    if Organization.objects.filter(id=org_id, owner=user_id):
        res["isOwner"] = True
    if OrgManager.objects.filter(org=org_id, person=user_id):
        res["isManager"] = True
    return Response(res)


@api_view(['POST'])
@authentication_classes([UserAuthentication, SuperAdminAuthentication, ErrorAuthentication])
@permission_classes((OtherAccessPolicy,))
def user_act_relation(request):
    user_id = request.data['user']
    act_id = request.data['act']
    try:
        user = WXUser.objects.get(id=user_id)
    except:
        res = {
            "detail": '未找到用户'
        }
        status = 404
        return Response(res, status)
    try:
        act = Activity.objects.get(id=act_id)
    except:
        res = {
            "detail": '未找到活动'
        }
        status = 404
        return Response(res, status)
    res = {
        "hasJoined": False,
        "underReview": False,
        "isOwner": False,
        "isManager": False,
    }
    if JoinedAct.objects.filter(act=act_id, person=user_id):
        res["hasJoined"] = True
    if Activity.objects.filter(id=act_id, owner=user_id):
        res["isOwner"] = True
        res["isManager"] = True
    org_id = act.org_id
    if Organization.objects.filter(id=org_id, owner=user_id):
        res["isManager"] = True
    if OrgManager.objects.filter(org=org_id, person=user_id):
        res["isManager"] = True
    return Response(res)


class JoinActApplicationViewSet(ModelViewSet):
    queryset = JoinActApplication.objects.all()
    serializer_class = JoinActApplicationSerializer


"""-------------------完成--------------------"""


# 用户
class WXUserViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (WXUserAccessPolicy,)

    queryset = WXUser.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return TestUserSerializer
        return WXUserSerializer

    def get_boya_followers(self, request):
        users = _get_boya_followers()
        serializer = self.get_serializer(users, many=True)

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    def search_user(self, request):
        name = request.data.get("name")
        users = WXUser.objects.filter(name__contains=name)
        return self.paginate(users)

    def get_wallet(self, request, pk):
        money = WXUser.objects.get(id=pk).money
        res = {
            "money": money
        }
        return Response(data=res, status=201)

    def recharge(self, request):
        user_id = request.data['user_id']
        add_money = float(request.data['money'])
        pre_money = _user_id2user_money(user_id)
        WXUser.objects.filter(id=user_id).update(money=pre_money + add_money)
        res = {
            "msg": "充值成功"
        }
        return Response(data=res, status=201)

    # 黑名单列表（管理端）
    def blackList(self, request):
        users = WXUser.objects.filter(defaults_number__gt=3)
        return self.paginate(users)

    # 移出黑名单（管理端）
    def blackList_out(self, request, pk):
        WXUser.objects.filter(id=pk, defaults_number__gt=3).update(defaults_number=3)
        users = WXUser.objects.filter(id=pk)
        return self.paginate(users)

    # 用户列表批量修改（管理端）
    def mul_update(self, request, pk):
        content = request.data.get("content")
        is_black = request.data.get("is_black")
        defaults_number = request.data.get("defaults_number")
        if (content == "state"):
            if (is_black == "in"):
                WXUser.objects.filter(id=pk, defaults_number__lte=4).update(defaults_number=4)
            else:
                WXUser.objects.filter(id=pk, defaults_number__gt=3).update(defaults_number=3)
        else:
            WXUser.objects.filter(id=pk).update(defaults_number=defaults_number)
        users = WXUser.objects.filter(id=pk)
        return self.paginate(users)

    # 用户列表单独修改（管理端）
    def sig_update(self, request, pk):
        name = request.data.get("name")
        sign = request.data.get("sign")
        defaults_number = request.data.get("defaults_number")
        if (name):
            WXUser.objects.filter(id=pk).update(name=name)
        if (sign):
            WXUser.objects.filter(id=pk).update(sign=sign)
        if (defaults_number != None):
            WXUser.objects.filter(id=pk).update(defaults_number=defaults_number)
        users = WXUser.objects.filter(id=pk)
        return self.paginate(users)

    # 黑名单查询（管理端）
    def black_search(self, request):
        name = request.data.get("name")
        users = WXUser.objects.filter(name__contains=name, defaults_number__gt=2)
        return self.paginate(users)


# 版块
class BlockViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (BlockAccessPolicy,)
    queryset = Block.objects.all()
    serializer_class = BlockSerializer


# 组织申请
class OrgApplicationViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (OrgAppAccessPolicy,)
    queryset = OrgApplication.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return OrgAppCreateSerializer
        if self.action == "verify":
            return OrgAppVerifySerializer
        return OrgApplySerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 获取用户的组织申请
    def user_get_all(self, request, user_id):
        applications = OrgApplication.objects.filter(user=user_id)
        return self.paginate(applications)

    # 审批组织申请
    def verify(self, request, pk):
        application = self.get_object()
        old_status = application.status
        if old_status != 0:
            return Response(data={"detail": ["该组织申请已审批。"]}, status=400)
        status = int(request.data.get('status'))
        org_name = application.name
        if status == 1:
            # 审核通过
            # 1.创建组织
            data = {
                "name": application.name,
                "owner": application.user.id,
                "block": application.block.id
            }
            serializer = OrganizationSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            org_id = serializer.data.get('id')
            owner_id = application.user.id
            # 2.添加负责人为管理员
            data = {
                "org": org_id,
                "person": owner_id
            }
            serializer = OrgManagerSerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # test
            serializer = self.get_serializer(
                instance=application, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # notification
            content = utils.get_notif_content(
                NOTIF.OrgApplyRes, org_name=org_name, status=True)
            notif = new_notification(NOTIF.OrgApplyRes, content, org_id=org_id)

            data = serializer.data
            _create_notif_for_all([owner_id], notif, data)

            return Response(data, 201)

        else:
            serializer = self.get_serializer(
                instance=application, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            # notification
            content = utils.get_notif_content(
                NOTIF.OrgApplyRes, org_name=org_name, status=False)
            notif = new_notification(NOTIF.OrgApplyRes, content, org_id=None)
            data = serializer.data
            _create_notif_for_all([application.user.id], notif, data)

            return Response(data, 200)


# 组织
class OrganizationModelViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (OrgAccessPolicy,)
    queryset = Organization.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return OrganizationSerializer
        if self.action == "change_org_owner":
            return OrgOwnerSerializer
        return OrgDetailSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        ret_data = serializer.data
        # 添加负责人为管理员
        data = {
            "org": serializer.data.get('id'),
            "person": request.data.get('owner')
        }
        serializer = OrgManagerSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(ret_data, status=status.HTTP_201_CREATED, headers=headers)

    # def create_wrapper(self, request):
    #     self.create(request)
    #     content = utils.get_notif_content(NOTIF.OrgApplyRes, )

    # 获取版块下的组织
    def get_org_by_block(self, request, block_id):
        organizations = Organization.objects.filter(block=block_id)
        return self.paginate(organizations)

    # 修改组织负责人
    def change_org_owner(self, request, pk):
        organization = self.get_object()
        serializer = self.get_serializer(
            instance=organization, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        content = utils.get_notif_content(
            NOTIF.BecomeOwner, org_name=_org_id2org_name(pk))
        notif = new_notification(NOTIF.BecomeOwner, content, org_id=pk)

        data = serializer.data
        _create_notif_for_all([request.data['owner']], notif, data)

        return Response(data, 200)

    # 搜索组织
    def search_all(self, request):
        org_name = request.data.get('name')
        organizations = Organization.objects.filter(name__contains=org_name)
        return self.paginate(organizations)

    # 板块下搜索组织
    def search_org_by_block(self, request, block_id):
        org_name = request.data.get('name')
        organizations = Organization.objects.filter(
            name__contains=org_name, block=block_id)
        return self.paginate(organizations)


# 关注组织
class FollowedOrgViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (FollowedOrgAccessPolicy,)
    queryset = FollowedOrg.objects.all()

    def get_serializer_class(self):
        if self.action == "get_followed_org":
            return UserFollowedOrgSerializer
        return FollowedOrgSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        user_id = request.query_params.get('user')
        org_id = request.query_params.get('org')
        FollowedOrg.objects.filter(org=org_id, person=user_id).delete()
        return Response(status=204)

    # 获取用户关注的组织
    def get_followed_org(self, request, pk):
        followed = FollowedOrg.objects.filter(person=pk)
        return self.paginate(followed)


# 组织管理
class OrgManageViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (OrgManagerAccessPolicy,)
    queryset = OrgManager.objects.all()

    def get_serializer_class(self):
        if self.action == "get_managed_org" or self.action == "search_managed_org":
            return UserManagedOrgSerializer
        if self.action == "get_all_managers":
            return OrgAllManagersSerializer
        return OrgManagerSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    def create_wrapper(self, request):
        res = self.create(request)
        user_id = request.data['person']
        org_id = request.data['org']
        content = utils.get_notif_content(
            NOTIF.BecomeAdmin, org_name=_org_id2org_name(org_id))
        notif = new_notification(NOTIF.BecomeAdmin, content, org_id=org_id)
        _create_notif_for_all([user_id], notif, res.data)

        return res

    def destroy(self, request, *args, **kwargs):
        user_id = request.query_params.get('user')
        org_id = request.query_params.get('org')
        OrgManager.objects.filter(org=org_id, person=user_id).delete()

        content = utils.get_notif_content(
            NOTIF.RemovalFromAdmin, org_name=_org_id2org_name(org_id))
        notif = new_notification(
            NOTIF.RemovalFromAdmin, content, org_id=org_id)
        data = {}
        _create_notif_for_all([user_id], notif, data)
        return Response(data, status=200)

    # 获取用户管理的组织
    def get_managed_org(self, request, pk):
        managed = OrgManager.objects.filter(person=pk)
        return self.paginate(managed)

    # 获取组织的管理员
    def get_all_managers(self, request, pk):
        managers = OrgManager.objects.filter(org=pk)
        return self.paginate(managers)

    # 搜索用户管理的组织
    def search_managed_org(self, request, pk):
        org_name = request.data.get("name")
        managed = OrgManager.objects.filter(
            person=pk, org__name__contains=org_name)
        return self.paginate(managed)


# 活动分类
class CategoryViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (CategoryAccessPolicy,)
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


# 活动地址
class AddressViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (AddressAccessPolicy,)
    queryset = Address.objects.all()
    serializer_class = AddressSerializer


# 用户反馈
class UserFeedbackViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (FeedbackAccessPolicy,)
    queryset = UserFeedback.objects.all()
    serializer_class = UserFeedbackSerializer

    def get_serializer_class(self):
        if self.action == "search_all_feedback":
            return FeedbackDetailSerializer
        return UserFeedbackSerializer

    def search_all_feedback(self, request):
        content = request.data.get("content")
        feedbacks = UserFeedback.objects.filter(content__contains=content)
        serializer = self.get_serializer(feedbacks, many=True)
        return Response(serializer.data)

    def search_user_feedback(self, request, user_id):
        content = request.data.get("content")
        feedbacks = UserFeedback.objects.filter(
            content__contains=content, user=user_id)
        serializer = self.get_serializer(feedbacks, many=True)
        return Response(serializer.data)


# 活动
class ActivityViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (ActAccessPolicy,)
    queryset = Activity.objects.all()

    def get_serializer_class(self):
        if self.action in ["create", "create_wrapper"]:
            return ActivitySerializer
        if self.action in ["destroy", "destroy_wrapper"]:
            return ActivitySerializer
        if self.action in ["update", "update_wrapper"]:
            return ActUpdateSerializer
        if self.action == 'get_recommended_act':
            return RecommendActSerializer
        return ActDetailSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    def create_wrapper(self, request):
        res = self.create(request)

        act = Activity.objects.get(id=res.data['id'])
        act.keywords = get_keyword(act.name + ' ' + act.description)
        act.save()
        return res

    # update_wrapper
    def update_wrapper(self, request, pk):
        pk = int(pk)
        act = Activity.objects.get(id=pk)
        old_typ = act.type.name.lower() if act.type else None
        res = self.update(request)

        act = Activity.objects.get(id=pk)
        old_keys = act.keywords
        new_typ = act.type.name.lower() if act.type else None
        act.keywords = get_keyword(act.name + ' ' + act.description)
        new_keys = act.keywords
        act.save()

        # create notif
        content = utils.get_notif_content(
            NOTIF.ActContent, act_name=_act_id2act_name(pk))
        notif = new_notification(
            NOTIF.ActContent, content, act_id=pk, org_id=None)
        # send notification
        persons = JoinedAct.objects.filter(act=pk)
        for p in persons:
            update_kwd_typ(p.person_id, old_keys, new_keys, old_typ, new_typ)
        _create_notif_for_all([p.person_id for p in persons], notif, res.data)
        return res

    def destroy_wrapper(self, request, pk):
        pk = int(pk)
        # res = self.destroy(request)
        content = utils.get_notif_content(
            NOTIF.ActCancel, act_name=_act_id2act_name(pk))
        # notif = new_notification(NOTIF.ActCancel, content, act_id=pk, org_id=None)
        # Here we MUST set act_id to null, because the act will be deleted later.
        # If we don't set act_id to null, the related notification will be deleted under CASCADE model.
        notif = new_notification(
            NOTIF.ActCancel, content, act_id=None, org_id=None)
        persons = JoinedAct.objects.filter(act=pk)
        receivers = [p.person_id for p in persons]
        _create_notif_for_all(receivers, notif)

        act = Activity.objects.get(id=pk)
        kwds = act.keywords
        typ = act.type.name.lower() if act.type else None
        for id_ in receivers:
            delete_kwd_typ(id_, kwds, typ)

        res = self.destroy(request)
        res.status_code = 200
        if res.data is None:
            res.data = {}
        res.data['__receivers__'] = receivers
        return res

    # 获取组织下的活动

    def get_org_act(self, request, org_id):
        acts = Activity.objects.filter(org=org_id)
        return self.paginate(acts)

    def get_org_act_status(self, request, org_id):
        now = datetime.datetime.now()
        ret = {
            'unstart': self.get_serializer(Activity.objects.filter(org=org_id, begin_time__gt=now), many=True).data,
            'cur': self.get_serializer(Activity.objects.filter(org=org_id, end_time__gte=now, begin_time__lte=now),
                                       many=True).data,
            'end': self.get_serializer(Activity.objects.filter(org=org_id, end_time__lt=now), many=True).data
        }
        return Response(ret, 200)

    # 获取用户发布的活动
    def get_user_act(self, request, user_id):
        acts = Activity.objects.filter(owner=user_id)
        return self.paginate(acts)

    def get_user_act_status(self, request, user_id):
        now = datetime.datetime.now()
        ret = {
            'unstart': self.get_serializer(Activity.objects.filter(owner=user_id, begin_time__gt=now), many=True).data,
            'cur': self.get_serializer(Activity.objects.filter(owner=user_id, end_time__gte=now, begin_time__lte=now),
                                       many=True).data,
            'end': self.get_serializer(Activity.objects.filter(owner=user_id, end_time__lt=now), many=True).data
        }
        return Response(ret, 200)

    # 获取用户管理的未开始活动 开始时间>现在
    def get_user_unstart_act(self, request, user_id):
        now = datetime.datetime.now()
        acts = Activity.objects.filter(owner=user_id, begin_time__gt=now)
        return self.paginate(acts)

    # 获取用户管理的进行中活动 开始时间 < 现在 < 结束时间
    def get_user_ing_act(self, request, user_id):
        now = datetime.datetime.now()
        acts = Activity.objects.filter(
            owner=user_id, end_time__gte=now, begin_time__lte=now)
        return self.paginate(acts)

    # 获取用户管理的已结束活动,结束时间 < 现在
    def get_user_finish_act(self, request, user_id):
        now = datetime.datetime.now()
        acts = Activity.objects.filter(owner=user_id, end_time__lt=now)
        return self.paginate(acts)

    # 获取板块下的活动
    def get_block_act(self, request, block_id):
        acts = Activity.objects.filter(block=block_id)
        return self.paginate(acts)

    def get_block_act_status(self, request, block_id):
        now = datetime.datetime.now()
        ret = {
            'unstart': self.get_serializer(Activity.objects.filter(block=block_id, begin_time__gt=now), many=True).data,
            'cur': self.get_serializer(Activity.objects.filter(block=block_id, end_time__gte=now, begin_time__lte=now),
                                       many=True).data,
            'end': self.get_serializer(Activity.objects.filter(block=block_id, end_time__lt=now), many=True).data
        }
        return Response(ret, 200)

    # 获取用户关注的组织发布的活动
    def get_followed_org_act(self, request, user_id):
        orgs = FollowedOrg.objects.filter(person=user_id)
        acts = Activity.objects.filter(
            org__in=[org.org_id for org in orgs]).order_by('pub_time').reverse()
        return self.paginate(acts)

    # 推荐活动
    def get_recommended_act(self, request, user_id):
        user = WXUser.objects.get(id=user_id)
        now = datetime.datetime.now()
        not_end_acts = list(Activity.objects.filter(end_time__gte=now))
        k = min(len(not_end_acts), 1000)
        random_acts = random.sample(not_end_acts, k)
        recommend_acts, recommend_orgs = get_recommend(user, random_acts)
        ret = {
            'acts': self.get_serializer(recommend_acts, many=True).data,
            'orgs': OrgDetailSerializer(recommend_orgs, many=True).data,
        }
        return Response(ret, 200)

    # 搜索活动
    def search_all(self, request):
        act_name = request.data.get("name")
        activities = Activity.objects.filter(name__contains=act_name)
        return self.paginate(activities)

    # 板块下搜索活动
    def search_act_by_block(self, request, block_id):
        act_name = request.data.get("name")
        activities = Activity.objects.filter(
            name__contains=act_name, block=block_id)
        return self.paginate(activities)

    # 组织下搜索活动
    def search_act_by_org(self, request, org_id):
        act_name = request.data.get("name")
        activities = Activity.objects.filter(
            name__contains=act_name, org=org_id)
        return self.paginate(activities)

    # 搜索指定用户发布的活动
    def search_user_released_act(self, request, user_id):
        act_name = request.data.get("name")
        activities = Activity.objects.filter(
            name__contains=act_name, owner=user_id)
        return self.paginate(activities)


# 活动参与
class JoinedActViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (JoinedActAccessPolicy,)
    queryset = JoinedAct.objects.all()

    def get_serializer_class(self):
        if self.action == "get_user_joined_act":
            return UserJoinedActSerializer
        if self.action == "get_user_joined_act_begin_order":
            return UserJoinedActSerializer
        if self.action == "get_user_joined_act_status":
            return UserJoinedActSerializer
        if self.action == "search_user_joined_act":
            return UserJoinedActSerializer
        if self.action == "get_act_participants":
            return JoinedActParticipants
        return JoinedActSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 加入活动
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        act_id = request.data.get("act")
        current_number = JoinedAct.objects.filter(act=act_id).count()
        act = Activity.objects.get(id=act_id)
        limit_number = act.contain
        kwds = act.keywords
        typ = act.type.name.lower() if act.type else None
        if current_number < limit_number:
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            user = request.data.get("person")
            add_kwd_typ(user, kwds, typ)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        else:
            return Response({"detail": "活动人数已满。"}, 400)

    # 退出活动
    def destroy(self, request, *args, **kwargs):
        user_id = request.query_params.get('person')
        act_id = request.query_params.get('act')
        JoinedAct.objects.filter(act=act_id, person=user_id).delete()
        act = Activity.objects.get(id=act_id)
        kwds = act.keywords
        typ = act.type.name.lower() if act.type else None
        delete_kwd_typ(user_id, kwds, typ)

    def destroy_wrapper(self, request):
        user_id = request.query_params.get('person')
        act_id = request.query_params.get('act')
        operator_id = request.query_params.get('operator')

        data = {}
        # self.destroy(request)
        if operator_id != user_id:
            content = utils.get_notif_content(
                NOTIF.RemovalFromAct, act_name=_act_id2act_name(act_id))
            # content = utils.get_notif_content(NOTIF.RemovalFromAct, act_name=None)
            notif = new_notification(
                NOTIF.RemovalFromAct, content, act_id=act_id, org_id=None)
            _create_notif_for_all([user_id], notif, data)
        self.destroy(request)

        return Response(data, 200)

    # 获取活动的参与人数
    def get_act_participants_number(self, request, act_id):
        number = JoinedAct.objects.filter(act=act_id).count()
        return Response({"number": number}, 200)

    # 获取活动的所有的参与者
    def get_act_participants(self, request, act_id):
        users = JoinedAct.objects.filter(act=act_id)
        return self.paginate(users)

    # 获取用户参与的活动
    def get_user_joined_act(self, request, user_id):
        acts = JoinedAct.objects.filter(person=user_id)
        return self.paginate(acts)

    def get_user_joined_act_status(self, request, user_id):
        now = datetime.datetime.now()
        ret = {
            'unstart': self.get_serializer(JoinedAct.objects.filter(act__begin_time__gt=now, person=user_id),
                                           many=True).data,
            'cur': self.get_serializer(
                JoinedAct.objects.filter(act__end_time__gte=now, act__begin_time__lte=now, person=user_id),
                many=True).data,
            'end': self.get_serializer(JoinedAct.objects.filter(act__end_time__lt=now, person=user_id), many=True).data
        }
        return Response(ret, 200)

    # 获取指定用户指定年月中参与的所有活动
    def get_user_joined_act_begin_order(self, request, user_id, month, year):
        acts = JoinedAct.objects.filter(
            person=user_id, act__begin_time__month=month, act__begin_time__year=year)
        serializer = self.get_serializer(acts, many=True)
        data = serializer.data
        ret = {}
        for d in data:
            act = d['act']
            if act['begin_time'].split('T')[0] in ret.keys():
                ret[act['begin_time'].split('T')[0]].append(act)
            else:
                ret[act['begin_time'].split('T')[0]] = [act]
        return Response(ret, 200)

    # 搜索用户参与的活动
    def search_user_joined_act(self, request, user_id):
        act_name = request.data.get("name")
        acts = JoinedAct.objects.filter(
            person=user_id, act__name__contains=act_name)
        return self.paginate(acts)


# 活动评价
class CommentViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (CommentAccessPolicy,)
    queryset = Comment.objects.all()

    def get_serializer_class(self):
        if self.action == "get_act_comments" or self.action == "search_by_act":
            return CommentDetailSerializer
        if self.action == "list":
            return CommentListSerializer
        if self.action == "get_user_comment":
            return CommentDetailSerializer
        if self.action == "update" or "update" in self.action:
            return CommentUpdateSerializer
        if self.action == "retrieve":
            return CommentUpdateSerializer
        if self.action == "search_all_comment":
            return CommentListSerializer
        if self.action == "search_by_user":
            return CommentActDetailSerializer

        return CommentSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 获取指定活动的所有评价
    def get_act_comments(self, request, act_id):
        comments = Comment.objects.filter(act=act_id)
        return self.paginate(comments)

    # 获取指定用户的指定活动的评论
    def get_user_comment(self, request, act_id, user_id):
        if Comment.objects.filter(user=user_id, act=act_id).exists():
            comment = Comment.objects.get(user=user_id, act=act_id)
            serializer = self.get_serializer(instance=comment)
            return Response(serializer.data)
        return Response({"id": -1}, 404)

    def search_all_comment(self, request):
        content = request.data.get("query")
        comments = Comment.objects.filter(content__contains=content)
        return self.paginate(comments)

    def search_by_user(self, request, user_id):
        content = request.data.get("query")
        comments = Comment.objects.filter(
            user=user_id, content__contains=content)
        return self.paginate(comments)

    def search_by_act(self, request, act_id):
        content = request.data.get("query")
        comments = Comment.objects.filter(
            act=act_id, content__contains=content)
        return self.paginate(comments)

    def create_wrapper(self, request):
        res = self.create(request)
        act_id = int(request.data['act'])
        user_id = int(request.data['user'])
        comment = request.data['content']
        content = utils.get_notif_content(NOTIF.ActCommented, user_name=_user_id2user_name(user_id),
                                          act_name=_act_id2act_name(act_id), comment=comment)
        notif = new_notification(NOTIF.ActCommented, content, act_id=act_id)
        act = BUAA.models.Activity.objects.get(id=act_id)
        if act.block_id == BLOCKID.PERSONAL:
            _create_notif_for_all([act.owner.pk], notif, res.data)
        elif act.block_id == BLOCKID.BOYA:
            pass
        else:
            # manegers = BUAA.models.OrgManager.objects.filter(org_id=act.org.pk).values('person')
            # _create_notif_for_all([m['person'] for m in manegers], notif, res.data)
            _create_notif_for_all([act.owner.pk], notif, res.data)
        return res

    def update_wrapper(self, request, pk):
        res = self.update(request)
        comment_obj = BUAA.models.Comment.objects.get(id=pk)
        act_id = comment_obj.act.id
        user_id = comment_obj.user.id
        comment = request.data['content']
        content = utils.get_notif_content(NOTIF.ActCommentModified, user_name=_user_id2user_name(user_id),
                                          act_name=_act_id2act_name(act_id), comment=comment)
        notif = new_notification(
            NOTIF.ActCommentModified, content, act_id=act_id)
        act = BUAA.models.Activity.objects.get(id=act_id)
        if act.block_id == BLOCKID.PERSONAL:
            _create_notif_for_all([act.owner.pk], notif, res.data)
        elif act.block_id == BLOCKID.BOYA:
            pass
        else:
            # manegers = BUAA.models.OrgManager.objects.filter(org_id=act.org.pk).values('person')
            # _send_notif(m.id, notif)
            # m is dict which has key list ['person']
            # receivers = [m['person'] for m in manegers]
            # _create_notif_for_all(receivers, notif, res.data)
            _create_notif_for_all([act.owner.pk], notif, res.data)
        return res


# WebSocket实时通信
class SentNotifViewSet(ModelViewSet):
    queryset = SentNotif.objects.all()
    serializer_class = SentNotificationSerializer

    def read_notification(self, request, user_id):
        notifications = request.data.get("notifications")
        for notification in notifications:
            if SentNotif.objects.filter(notif=notification, person=user_id).exists():
                sent = SentNotif.objects.get(
                    notif=notification, person=user_id)
                serializer = self.get_serializer(instance=sent, data={
                    "notif": notification, "person": user_id, "already_read": True})
                serializer.is_valid()
                serializer.save()
        return Response(data=None, status=200)


class NotificationViewSet(ModelViewSet):
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer


class ImageUploadViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (ImageAccessPolicy,)
    parser_classes = [JSONParser, FormParser, MultiPartParser, ]
    serializer_class = ImageUploadSerializer

    def remove_act_avatar(self, request, act_id):
        try:
            act = Activity.objects.get(id=act_id)
        except:
            res = {
                "detail": '未找到活动'
            }
            status = 404
            return Response(res, status)

        act.avatar = None
        act.save()
        return Response(status=204)

    def upload_act_avatar(self, request, act_id):
        image = request.FILES['image']
        try:
            act = Activity.objects.get(id=act_id)
        except:
            res = {
                "detail": '未找到活动'
            }
            status = 404
            return Response(res, status)
        path = "acts/" + str(act_id) + '_' + get_random_str() + '.jpg'
        with open(base_dir + path, 'wb') as f1:
            f1.write(image.read())
            f1.close()
            act.avatar = web_dir + path
            act.save()
        res = {
            "img": web_dir + path
        }
        return Response(res, 200)

    def upload_org_avatar(self, request, org_id):
        image = request.FILES['image']
        try:
            org = Organization.objects.get(id=org_id)
        except:
            res = {
                "detail": '未找到组织'
            }
            status = 404
            return Response(res, status)

        path = "orgs/" + str(org_id) + '_' + get_random_str() + '.jpg'
        with open(base_dir + path, 'wb') as f:
            f.write(image.read())
            f.close()
            org.avatar = web_dir + path
            org.save()
        res = {
            "img": web_dir + path
        }
        return Response(res, 200)
    
    # 认证（用户端）
    def verify(self, request):
        # image = request.FILES['picture']
        # user_id = request.data['user_id']
        # name = request.data['name']
        # student_id = request.data['student_id']
        # avatar = request.data['avatar']
        # data = {
        #     "user_id": user_id,
        #     "name": name,
        #     "student_id": student_id,
        #     "avatar": avatar
        # }
        # serializer = UserVerifySerializer(data=data)
        # serializer.is_valid(raise_exception=True)
        # serializer.save()
        # return Response(data={"msg": "提交成功"}, status=201)
        image = request.FILES['picture']
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        student_id = request.POST.get('student_id')
        path = "userVerify/" + str(user_id) + '_' + get_random_str() + '.jpg'
        with open(base_dir + path, 'wb') as f1:
            f1.write(image.read())
            f1.close()
        avatar = web_dir + path
        verify = UserVerify.objects.filter(user_id=user_id)
        if verify.exists():
            verify.update(avatar=avatar)
        else:
            data = {
                "user_id": user_id,
                "name": name,
                "student_id": student_id,
                "student_number": student_id,
                "avatar": avatar
            }
            serializer = UserVerifySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(data={"msg": "提交成功"}, status=201)


@api_view(['GET'])
def lines(request):
    template = loader.get_template('index.html')

    df = pd.read_csv('/root/rank.csv')

    x = df.Time.values
    col_num = df.shape[1]
    # 👴 比较喜欢用的 colormap 之一，参见 matplotlib.pyplot.cm，matplotlib.colors，matplotlib.colormap
    colors = plt.cm.Spectral(list(range(1, col_num)))
    fig = go.Figure()  # 参见 plotly 文档
    fig.update_layout(
        title="《实时战况》",
        xaxis={'title': '时间'},
        yaxis={'title': '通过人数', 'range': [0, 460]}
    )
    for i in range(1, col_num):
        y = df['{}'.format(i)].values

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                marker={'color': colors[i - 1], 'symbol': 104, 'size': 10},
                mode="lines",
                name='Problem {}'.format(i)
            )
        )

    div = opy.plot(fig, auto_open=False, output_type='div')

    context = {}
    context['graph'] = div

    return HttpResponse(template.render(context, request))


@api_view(['GET'])
@authentication_classes([])
def avoid_fxxking_censorship(request):
    # f**k tencent
    res = {
        'show': True,
    }
    return Response(data=res, status=200)


# 用户审核视图 -----2022-4 新增
class UserVerifyViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (UserVerifyAccessPolicy,)

    queryset = UserVerify.objects.all()
    serializer_class = UserVerifySerializer

    def get_serializer_class(self):
        return UserVerifySerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    def search_user(self, request):
        student_id = request.data.get("search_number")
        users = UserVerify.objects.filter(student_id=student_id)
        return self.paginate(users)

    # 用户审核列表
    def userVery_list(self, request):
        users = UserVerify.objects.all()
        return self.paginate(users)

    # 审核用户操作
    def userVerify(self, request, pk):
        verify = UserVerify.objects.get(id=pk)
        user_id = model_to_dict(verify)["user_id"]
        wx_user = WXUser.objects.get(id=user_id)
        is_csstd = request.data.get("is_csstd")
        student_id = request.data.get("student_id")
        real_name = request.data.get("name")
        if (is_csstd):
            WXUser.objects.filter(id=user_id).update(is_csstd=True)
            WXUser.objects.filter(id=user_id).update(student_id=student_id)
            WXUser.objects.filter(id=user_id).update(real_name=real_name)
        else:
            WXUser.objects.filter(id=user_id).update(is_csstd=False)
            WXUser.objects.filter(id=user_id).update(student_id=student_id)
            WXUser.objects.filter(id=user_id).update(real_name=real_name)
        res = {
            "detail": '审核完毕'
        }
        UserVerify.objects.filter(id=pk).delete()
        return Response(res)

    # 显示指定id的审核信息
    def show_verify(self, request, pk):
        verify = UserVerify.objects.filter(id=pk)
        return self.paginate(verify)

    # 查看认证信息（用户端）
    def if_verified(self, request, pk):
        user = WXUser.objects.get(id=pk)
        if user.real_name is not None:
            res = {
                "msg": "已认证",
                "real_name": user.real_name,
                "student_id": user.student_id,
                "is_csstd": user.is_csstd
            }
            return Response(data=res, status=201)
        if UserVerify.objects.filter(user_id=pk).exists():
            res = {
                "msg": "审核中"
            }
            return Response(data=res, status=201)
        res = {
            "msg": "未认证"
        }
        return Response(data=res, status=201)

    # 认证（用户端）
    def verify(self, request):
        print("111111111111111")
        print(request)
        image = request.POST["picture"]
        user_id = request.data['user_id']
        name = request.data['name']
        student_id = request.data['student_id']
        path = "userVerify/" + str(user_id) + '_' + get_random_str() + '.jpg'
        with open(base_dir + path, 'wb') as f1:
            f1.write(image.read)
            f1.close()
        avatar = web_dir + path
        verify = UserVerify.objects.filter(user_id=user_id)
        if verify.exists():
            verify.update(avatar=avatar)
        else:
            data = {
                "user_id": user_id,
                "name": name,
                "student_id": student_id,
                "avatar": avatar
            }
            serializer = UserVerifySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
        return Response(data={"msg": "提交成功"}, status=201)


# 场地预约
class GroundApplyViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (GroundApplyPolicy,)
    queryset = GroundApply.objects.all()

    def get_serializer_class(self):
        return GroundApplySerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    '-------------------------用户端-------------------------'

    # 查询已占用场地（用户端）
    def get_used_ground(self, request):
        """
            输入：date日期，area区域，ground_id场地id

            第一种情况：查询该日期该区域中所有场地的被占用情况，这时ground_id=-1忽略
            第二种情况：查询该日期该场地的被占用情况，这是ground_id有效，area为空串

            输出：该日期该区域所有场地（某个场地）被占用情况
                每一个场地为一项，包括ground_id，ground_name，period，
                其中period为长度14的列表，代表8到22点，1表示被占用（被成功预约或者审核中），0表示未被预约
                区域查询则输出多条，单场地查询则输出一条
        """

        date = request.data['date']
        date = _to_standard_date(date)
        area = request.data['area']
        raw_ground_id = request.data['ground_id']

        # 如果查询的是一片区域
        if raw_ground_id == -1:
            ground_ids = Ground.objects.filter(area=area).values_list("id", flat=True)
        # 如果查询的是单独一个场地
        else:
            ground_ids = [raw_ground_id]

        # 遍历所有场地，依次到预约表中查询该场地被占用情况，放到res中
        res = []
        for ground_id in ground_ids:
            period = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            date_ground_applies = GroundApply.objects.filter(begin_time__contains=date, ground_id=ground_id).exclude(
                state=2)
            # 如果某场地有有效的预约，则将改天的预约时间整合到一个period中
            if date_ground_applies.exists():

                for raw_apply in date_ground_applies:
                    begin_hour = raw_apply.begin_time.hour
                    end_hour = raw_apply.end_time.hour
                    for index in range(begin_hour - 8, end_hour - 8):
                        period[index] = 1
            apply = {
                "ground_id": ground_id,
                "ground_name": Ground.objects.get(id=ground_id).name,
                "period": period
            }
            res.append(apply)
        return Response(data=res, status=201)

    # 查看我的预约（用户端）
    def get_booking(self, request, pk):
        """
        输入：用户id（url中）
        输出：该用户所有预约记录
        """
        applies = GroundApply.objects.filter(user_id=pk)
        success = []
        checking = []
        invalid = []
        for apply in applies:
            ground_id = apply.ground_id.id
            ground_area = _ground_id2ground_area(ground_id)
            data = {
                "apply_id": apply.id,
                "user_id": apply.user_id.id,
                "ground_id": ground_id,
                "area1": ground_area[0],
                "area2": ground_area[1],
                "date": apply.begin_time.strftime('%Y-%m-%d'),
                "begin_time": apply.begin_time.hour,
                "end_time": apply.end_time.hour,
                "feedback": apply.feedback,
                "identity": apply.identity,
                "can_change": apply.can_change
            }
            if apply.state == 0:
                success.append(data)
            elif apply.state == 1:
                checking.append(data)
            else:
                invalid.append(data)
        res = {
            "success": list(reversed(success)),
            "checking": list(reversed(checking)),
            "invalid": list(reversed(invalid))
        }
        return Response(data=res, status=201)
        # applies = GroundApply.objects.filter(user_id=pk)
        # return self.paginate(applies)

    # 预约场地（用户端）
    def book_ground(self, request):
        """
        输入：user_id用户id，identity申请身份（0为普通预约，1为批量预约），file申请材料（可有可无），
            ground_times场地时间对的列表，其中每一项有ground_id场地id，date日期，begin_time开始时间，end_time结束时间

        业务流程：
            普通预约检查点：
            1.违约次数
            2.余额
            3.预约时长上限
            4.场地是否需要审核->决定审核通过（state=0）还是审核中（state=1）
            5.入库校验（场地是否可预约）
            影响：
            1.增加一条预约
            2.扣钱

            批量预约检查点：
            1.违约次数
            2.余额
            3.入库校验
            影响：
            1.增加一条预约，必然需要审核（state=1）
            2.扣钱
            3.同一批预约的预约提交时间相同

        输出：预约成功/失败信息
        """
        user_id = request.data['user_id']
        identity = request.data['identity']
        file = request.data['file']
        ground_times = request.data['ground_times']
        pre_money = _user_id2user_money(user_id)

        # 判断违约次数是否>3，是则不能预约
        defaults_number = WXUser.objects.get(id=user_id).defaults_number
        if defaults_number > APPLY.MAX_DEFAULT:
            return Response(data={"msg": "您的违约次数>3，预约失败"}, status=201)

        # 普通预约，可能需要审核（场地决定），需要检查预约时长是否已达上限
        if identity == 0:
            ground_time = ground_times[0]  # 普通预约只有一项，所以取[0]
            ground_id = ground_time['ground_id']
            date = ground_time['date']  # "2022-04-20"
            date = _to_standard_date(date)
            begin_time = ground_time['begin_time']  # 16
            end_time = ground_time['end_time']  # 17
            apply_needed = Ground.objects.get(id=ground_id).apply_needed

            # 检查余额
            price = _get_price_hour(ground_id, begin_time, end_time)
            if pre_money < price:
                return Response(data={"msg": "余额不足，预约失败"}, status=201)

            # 检查预约时长是否已达上限
            booking_time = _get_booking_time(ground_id, date, user_id)
            if booking_time + end_time - begin_time > APPLY.MAX_TIME:
                return Response(data={"msg": "已达当日预约时长上限，预约失败"}, status=201)

            # 不需要审核
            if apply_needed == 0:
                data = {
                    "state": 0,
                    "feedback": "预约成功",
                    "ground_id": ground_id,
                    "user_id": user_id,
                    "identity": identity,
                    "begin_time": _to_datetime(date, begin_time),
                    "end_time": _to_datetime(date, end_time),
                }
                res = {
                    "msg": "预约成功"
                }

            # 需要审核
            else:
                data = {
                    "state": 1,
                    "feedback": "审核中",
                    "ground_id": ground_id,
                    "user_id": user_id,
                    "identity": identity,
                    "begin_time": _to_datetime(date, begin_time),
                    "end_time": _to_datetime(date, end_time),
                    "file": file
                }
                res = {
                    "msg": "已提交申请，等待审核"
                }

            # 增加一条预约记录（入库校验）
            serializer = GroundApplySerializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            # 扣钱
            WXUser.objects.filter(id=user_id).update(money=pre_money - price)
            return Response(data=res, status=201)

        # 批量预约，必须审核，需要检查余额，不需要检查预约时长，预约提交时间设为相同
        else:
            # 检查余额，先检查场地是否空余（和普通预约不同，这一步和入库需要分开）
            price = 0
            serializer_list = []
            for ground_time in ground_times:
                ground_id = ground_time['ground_id']
                date = ground_time['date']  # "2022-04-20"
                date = _to_standard_date(date)
                begin_time = ground_time['begin_time']  # 16
                end_time = ground_time['end_time']  # 17
                price = price + _get_price_hour(ground_id, begin_time, end_time)
                data = {
                    "state": 1,
                    "feedback": "审核中",
                    "ground_id": ground_id,
                    "user_id": user_id,
                    "identity": identity,
                    "begin_time": _to_datetime(date, begin_time),
                    "end_time": _to_datetime(date, end_time),
                    "file": file
                }
                serializer = GroundApplySerializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer_list.append(serializer)
            if pre_money < price:
                return Response(data={"msg": "余额不足，预约失败"}, status=201)

            # 入库
            applies = []
            for serializer in serializer_list:
                applies.append(serializer.save())

            # 设定预约提交时间为相同
            apply_time = applies[0].apply_time
            for apply in applies:
                apply.apply_time = apply_time

            # 扣钱
            WXUser.objects.filter(id=user_id).update(money=pre_money - price)

            return Response(data={"msg": "已提交申请，等待审核"}, status=201)

    # 预约改期（用户端）
    def rebook_ground(self, request):
        """
        输入：apply_id预约id，date日期，begin_time改期开始时间，end_time改期结束时间，file申请材料（可有可无）

        业务流程：
            检查点：
                1.是否已经失效
                2.是否可以改期
                3.余额
                4.预约时长是否已达上限（仅对于普通预约）
                5.根据原申请是否需要审核决定改期是否需要审核（state，file）
                6.入库校验（场地是否可预约）
            影响：
                1.原预约变成已失效
                2.新增一条预约（状态取决于原预约），预约提交时间和原预约保持一致
                3.扣钱

        输出：改期成功/失败信息
        """
        apply_id = request.data['apply_id']
        date = request.data['date']  # "2022-04-20"
        date = _to_standard_date(date)
        begin_time = request.data['begin_time']  # 10
        end_time = request.data['end_time']  # 12
        file = request.data['file']

        apply = GroundApply.objects.get(id=apply_id)
        state = apply.state
        can_change = apply.can_change
        ground_id = apply.ground_id.id
        user_id = apply.user_id.id
        old_begin_time = apply.begin_time
        old_end_time = apply.end_time
        old_date = _get_date(old_begin_time)
        identity = apply.identity
        old_apply_time = apply.apply_time
        old_price = _get_price(ground_id, old_begin_time, old_end_time)
        pre_money = _user_id2user_money(user_id)
        new_price = _get_price_hour(ground_id, begin_time, end_time)

        # 检查是否已失效
        if state == 2:
            return Response(data={"msg": "该预约已失效"}, status=201)

        # 检查是否可以改期
        if not can_change:
            return Response(data={"msg": "每个预约最多只能改期一次"}, status=201)

        # 检查余额
        if pre_money + old_price < new_price:
            return Response(data={"msg": "余额不足，预约失败"}, status=201)

        # 若为普通预约，则需要检查预约时长是否已达上限
        if identity == 0:
            booking_time = _get_booking_time(ground_id, date, user_id)
            if date == old_date:
                new_booking_time = booking_time - (_get_hour(old_end_time) - _get_hour(old_begin_time)) + (
                        end_time - begin_time)
            else:
                new_booking_time = booking_time + end_time - begin_time
            if new_booking_time > APPLY.MAX_TIME:
                return Response(data={"msg": "已达当日预约时长上限，预约失败"}, status=201)

        # 如果原申请是批量申请或者普通申请且需审核，则改期也需审核
        apply_needed = Ground.objects.get(id=ground_id).apply_needed or identity == 1
        if apply_needed == 0:
            data = {
                "state": 0,
                "feedback": "改期成功",
                "can_change": False,
                "ground_id": ground_id,
                "user_id": user_id,
                "identity": identity,
                "begin_time": _to_datetime(date, begin_time),
                "end_time": _to_datetime(date, end_time),
                "apply_time": old_apply_time
            }
            res = {
                "msg": "改期成功"
            }
        else:
            data = {
                "state": 1,
                "feedback": "改期审核中",
                "can_change": False,
                "ground_id": ground_id,
                "user_id": user_id,
                "identity": identity,
                "begin_time": _to_datetime(date, begin_time),
                "end_time": _to_datetime(date, end_time),
                "file": file,
                "apply_time": old_apply_time
            }
            res = {
                "msg": "已提交改期申请，等待审核"
            }

        # 入库校验
        serializer = GroundApplySerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 将原预约设为已失效
        GroundApply.objects.filter(id=apply_id).update(state=2, feedback="已改期")

        # 扣钱
        WXUser.objects.filter(id=user_id).update(money=pre_money + old_price - new_price)

        return Response(data=res, status=201)

    # 取消预约（用户端）
    def cancel_booking(self, request, apply_id):
        """
        输入：apply_id（url中）

        业务流程：
            1.检查原预约是否存在
            2.更新预约状态为已失效
            3.增加违约次数
            4.退钱

        输出：提示取消成功和违约次数
        """
        try:
            apply = GroundApply.objects.get(id=apply_id)
        except:
            res = {
                "msg": "没有此apply_id的预约"
            }
            return Response(data=res, status=404)
        user_id = apply.user_id.id
        ground_id = apply.ground_id.id
        begin_time = apply.begin_time
        end_time = apply.end_time
        price = _get_price(ground_id, begin_time, end_time)
        pre_money = _user_id2user_money(user_id)
        pre_defaults_number = WXUser.objects.get(id=user_id).defaults_number
        GroundApply.objects.filter(id=apply_id).update(state=2, feedback="已取消")
        WXUser.objects.filter(id=user_id).update(money=pre_money + price, defaults_number=pre_defaults_number + 1)
        res = {
            "msg": "取消成功",
            "defaults_number": pre_defaults_number + 1
        }

        return Response(data=res, status=201)

    '-------------------------管理端-------------------------'

    # 场地使用情况查询（web）
    def ground_check(self, request):
        area = request.data.get("area")
        begin_time = request.data.get("date")
        end_time = begin_time + " 23:59"
        apply = GroundApply.objects.filter(ground_id__area=area, begin_time__gte=begin_time, end_time__lte=end_time)
        return self.paginate(apply)

    # 场地审核列表（web）
    def groundVerify_list(self, request):
        admin_name = request.user
        admin = User.objects.get(username=admin_name)
        admin_id = admin.id
        buaa_admin = SuperAdmin.objects.get(user_ptr_id=admin_id)
        admin_type = buaa_admin.type
        if admin_type == "super" or admin_type == "monitor":
            applys = GroundApply.objects.filter(state=1)
            apply_list = []
            for apply in applys:
                user = WXUser.objects.get(id=apply.user_id.id)
                ground = Ground.objects.get(id=apply.ground_id.id)
                res = {
                    "id": apply.id,
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "ground_name": ground.name,
                    "begin_time": apply.begin_time,
                    "end_time": apply.end_time,
                    "state": apply.state,
                    "feedback": apply.feedback,
                    "can_change": apply.can_change,
                    "file": apply.file,
                    "identity": apply.identity,
                    "apply_time": apply.apply_time,
                    "ground_id": apply.ground_id.id,
                    "user_id": apply.user_id.id,
                    "email": user.email
                }
                apply_list.append(res)
            return Response(apply_list)
        if admin_type == "ground":
            applys = GroundApply.objects.filter(state=1)
            apply_list = []
            for apply in applys:
                user = WXUser.objects.get(id=apply.user_id.id)
                ground = Ground.objects.get(id=apply.ground_id.id)
                ground_admin = ground.administrator_id
                if ground_admin == admin_id:
                    res = {
                        "id": apply.id,
                        "student_id": user.student_id,
                        "student_name": user.real_name,
                        "ground_name": ground.name,
                        "begin_time": apply.begin_time,
                        "end_time": apply.end_time,
                        "state": apply.state,
                        "feedback": apply.feedback,
                        "can_change": apply.can_change,
                        "file": apply.file,
                        "identity": apply.identity,
                        "apply_time": apply.apply_time,
                        "ground_id": apply.ground_id.id,
                        "user_id": apply.user_id.id,
                        "email": user.email
                    }
                    apply_list.append(res)
            return Response(apply_list)

    def groundVerify_msg(self, request, pk):
        apply = GroundApply.objects.get(id=pk)
        time0 = model_to_dict(apply)["apply_time"]
        applys = GroundApply.objects.filter(apply_time=time0, state=1).exclude(id=pk)
        if applys.__len__() == 0:
            ret_apply = GroundApply.objects.filter(id=pk)
            apply_list = []
            for apply in ret_apply:
                user = WXUser.objects.get(id=apply.user_id.id)
                ground = Ground.objects.get(id=apply.ground_id.id)
                res = {
                    "id": apply.id,
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "ground_name": ground.name,
                    "begin_time": apply.begin_time,
                    "end_time": apply.end_time,
                    "state": apply.state,
                    "feedback": apply.feedback,
                    "can_change": apply.can_change,
                    "file": apply.file,
                    "identity": apply.identity,
                    "apply_time": apply.apply_time,
                    "ground_id": apply.ground_id.id,
                    "user_id": apply.user_id.id,
                    "is_batch": False
                }
                apply_list.append(res)
            return Response(apply_list)
        ret_apply = GroundApply.objects.filter(id=pk)
        apply_list = []
        for apply in ret_apply:
            user = WXUser.objects.get(id=apply.user_id.id)
            ground = Ground.objects.get(id=apply.ground_id.id)
            res = {
                "id": apply.id,
                "student_id": user.student_id,
                "student_name": user.real_name,
                "ground_name": ground.name,
                "begin_time": apply.begin_time,
                "end_time": apply.end_time,
                "state": apply.state,
                "feedback": apply.feedback,
                "can_change": apply.can_change,
                "file": apply.file,
                "identity": apply.identity,
                "apply_time": apply.apply_time,
                "ground_id": apply.ground_id.id,
                "user_id": apply.user_id.id,
                "is_batch": True
            }
            apply_list.append(res)
        return Response(apply_list)

    def groundVerify(self, request, pk):
        if_pass = request.data.get("pass")
        feedback = request.data.get("feedback")
        apply = GroundApply.objects.get(id=pk)
        time0 = model_to_dict(apply)["apply_time"]

        state = model_to_dict(apply)["state"]
        user_id = model_to_dict(apply)["user_id"]
        user = WXUser.objects.get(id=user_id)
        pri_money = model_to_dict(user)["money"]
        ground_id = model_to_dict(apply)["ground_id"]
        ground = Ground.objects.get(id=ground_id)
        price = model_to_dict(ground)["price"]
        now_money = pri_money + price
        if (state == 2 or state == 0):
            res = {
                "detail": "预约已失效或不存在"
            }
            return Response(res)
        if (if_pass == True):
            # GroundApply.objects.filter(apply_time__gte=time0, apply_time__lt=time1).update(state=0, feedback=feedback)
            GroundApply.objects.filter(apply_time=time0).update(state=0, feedback=feedback)
            res = {
                "detail": "审核成功"
            }
            return Response(res)
        GroundApply.objects.filter(apply_time=time0).update(state=2, feedback=feedback)
        WXUser.objects.filter(id=user_id).update(money=now_money)
        res = {
            "detail": "审核成功"
        }
        return Response(res)

    def groundApply_list(self, request):
        admin_name = request.user
        admin = User.objects.get(username=admin_name)
        admin_id = admin.id
        buaa_admin = SuperAdmin.objects.get(user_ptr_id=admin_id)
        admin_type = buaa_admin.type
        if admin_type == "super" or admin_type == "monitor":
            applys = GroundApply.objects.all()
            apply_list = []
            for apply in applys:
                user = WXUser.objects.get(id=apply.user_id.id)
                ground = Ground.objects.get(id=apply.ground_id.id)
                res = {
                    "id": apply.id,
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "ground_name": ground.name,
                    "begin_time": apply.begin_time,
                    "end_time": apply.end_time,
                    "state": apply.state,
                    "feedback": apply.feedback,
                    "can_change": apply.can_change,
                    "file": apply.file,
                    "identity": apply.identity,
                    "apply_time": apply.apply_time,
                    "ground_id": apply.ground_id.id,
                    "user_id": apply.user_id.id,
                    "email": user.email
                }
                apply_list.append(res)
            return Response(apply_list)
        if admin_type == "ground":
            applys = GroundApply.objects.all()
            apply_list = []
            for apply in applys:
                user = WXUser.objects.get(id=apply.user_id.id)
                ground = Ground.objects.get(id=apply.ground_id.id)
                ground_admin = ground.administrator_id
                if ground_admin == admin_id:
                    res = {
                        "id": apply.id,
                        "student_id": user.student_id,
                        "student_name": user.real_name,
                        "ground_name": ground.name,
                        "begin_time": apply.begin_time,
                        "end_time": apply.end_time,
                        "state": apply.state,
                        "feedback": apply.feedback,
                        "can_change": apply.can_change,
                        "file": apply.file,
                        "identity": apply.identity,
                        "apply_time": apply.apply_time,
                        "ground_id": apply.ground_id.id,
                        "user_id": apply.user_id.id,
                        "email": user.email
                    }
                    apply_list.append(res)
            return Response(apply_list)

    def groundApply_delete(self, request, pk):
        """
        输入：apply_id（url中）

        业务流程：
            1.检查原预约是否存在
            2.更新预约状态为已失效
            3.退钱

        输出：提示取消成功
        """
        try:
            apply = GroundApply.objects.get(id=pk)
        except:
            res = {
                "msg": "没有此apply_id的预约"
            }
            return Response(data=res, status=404)
        user_id = apply.user_id.id
        ground_id = apply.ground_id.id
        begin_time = apply.begin_time
        end_time = apply.end_time
        state = apply.state
        if state == 1:
            return Response(data={"msg": "不能删除正在审核的预约，请先审核"}, status=202)
        price = _get_price(ground_id, begin_time, end_time)
        pre_money = _user_id2user_money(user_id)
        GroundApply.objects.filter(id=pk).update(state=2, feedback="已被管理员取消")
        WXUser.objects.filter(id=user_id).update(money=pre_money + price)
        res = {
            "msg": "取消成功"
        }
        return Response(data=res, status=201)

    # 预约改期(web)
    def groundApply_update(self, request, pk):
        from datetime import datetime
        apply = GroundApply.objects.get(id=pk)
        state = apply.state
        # date = request.data['date']  # "2022-04-20"
        begin_time = request.data['begin_time']  # 10
        begin_time = datetime.strptime(begin_time, '%Y-%m-%d %H:%M:%S')
        end_time = request.data['end_time']  # 12
        end_time = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')
        ground_id = apply.ground_id.id
        user_id = apply.user_id.id
        old_begin_time = apply.begin_time
        old_end_time = apply.end_time
        old_date = old_end_time.date
        old_apply_time = apply.apply_time
        old_price = _get_price(ground_id, old_begin_time, old_end_time)
        pre_money = _user_id2user_money(user_id)
        begin_time_time = str(begin_time).split(' ')[1]
        begin_time_hour = begin_time_time.split(':')[0]
        end_time_time = str(end_time).split(' ')[1]
        end_time_hour = end_time_time.split(':')[0]
        new_price = _get_price_hour(ground_id, int(begin_time_hour), int(end_time_hour))
        if state == 2:
            res = {
                "detail": "该预约已失效"
            }
            return Response(res)
        # 检查余额
        if pre_money + old_price < new_price:
            res = {
                "detail": "余额不足，预约失败"
            }
            return Response(res)
        # 检查哪个场地符合时间
        ground = Ground.objects.get(id=ground_id)
        area = ground.area
        ground_list = Ground.objects.filter(area=area)
        for gd in ground_list:
            apply_list = GroundApply.objects.filter(ground_id=gd.id)
            if_left = False
            if_right = False
            if_in = False
            if_have = False
            for aply in apply_list:
                bt = aply.begin_time
                et = aply.end_time
                if begin_time < et < end_time:
                    if_left = True
                if begin_time < bt < end_time:
                    if_right = True
                if bt > begin_time and et < end_time:
                    if_have = True
                if bt < begin_time and et > end_time:
                    if_in = True
                if bt == begin_time and et == end_time:
                    if_in = True
            if if_left or if_right or if_in or if_have:
                pass
            else:
                GroundApply.objects.filter(id=pk).update(ground_id=gd.id, begin_time=begin_time, end_time=end_time,
                                                         state=0)
                WXUser.objects.filter(id=user_id).update(money=pre_money + old_price - new_price)
                res = {
                    "detail": "改期成功"
                }
                return Response(res)
        res = {
            "detail": "该时段没有空余场地"
        }
        return Response(res)

    def search_apply(self, request):
        student_id = request.data.get("student_id")
        applys = GroundApply.objects.all()
        apply_list = []
        for apply in applys:
            user = WXUser.objects.get(id=apply.user_id.id)
            ground = Ground.objects.get(id=apply.ground_id.id)
            if student_id == user.student_id:
                res = {
                    "id": apply.id,
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "ground_name": ground.name,
                    "begin_time": apply.begin_time,
                    "end_time": apply.end_time,
                    "state": apply.state,
                    "feedback": apply.feedback,
                    "can_change": apply.can_change,
                    "file": apply.file,
                    "identity": apply.identity,
                    "apply_time": apply.apply_time,
                    "ground_id": apply.ground_id.id,
                    "user_id": apply.user_id.id
                }
                apply_list.append(res)
        return Response(apply_list)

    def search_verify(self, request):
        student_id = request.data.get("student_id")
        applys = GroundApply.objects.filter(state=1)
        apply_list = []
        for apply in applys:
            user = WXUser.objects.get(id=apply.user_id.id)
            ground = Ground.objects.get(id=apply.ground_id.id)
            if student_id == user.student_id:
                res = {
                    "id": apply.id,
                    "student_id": user.student_id,
                    "student_name": user.real_name,
                    "ground_name": ground.name,
                    "begin_time": apply.begin_time,
                    "end_time": apply.end_time,
                    "state": apply.state,
                    "feedback": apply.feedback,
                    "can_change": apply.can_change,
                    "file": apply.file,
                    "identity": apply.identity,
                    "apply_time": apply.apply_time,
                    "ground_id": apply.ground_id.id,
                    "user_id": apply.user_id.id
                }
                apply_list.append(res)
        return Response(apply_list)


class GroundViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (GroundAccessPolicy,)

    queryset = Ground.objects.all()
    serializer_class = GroundSerializer

    def get_serializer_class(self):
        return GroundSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 场地列表
    def ground_list(self, request):
        admin_name = request.user
        admin = User.objects.get(username=admin_name)
        admin_id = admin.id
        buaa_admin = SuperAdmin.objects.get(user_ptr_id=admin_id)
        admin_type = buaa_admin.type
        if admin_type == "super":
            grounds = Ground.objects.all().order_by('code')
            return self.paginate(grounds)
        if admin_type == "ground":
            grounds = Ground.objects.all().order_by('code')
            ground_list = []
            for ground in grounds:
                ground_admin = ground.administrator_id
                if ground_admin == admin_id:
                    res = {
                        "id": ground.id,
                        "name": ground.name,
                        "area": ground.area,
                        "apply_needed": ground.apply_needed,
                        "description": ground.description,
                        "avatar": ground.avatar,
                        "begin_time": ground.begin_time,
                        "end_time": ground.end_time
                    }
                    ground_list.append(res)
            return Response(ground_list)

    # 添加场地（web）
    def add_ground(self, request):
        from datetime import datetime
        name = request.data.get("name")
        area = request.data.get("area")
        price = request.data.get("price")
        apply_needed = request.data.get("apply_needed")
        description = request.data.get("description")
        avatar = request.data.get("avatar")
        begin_time = request.data.get("begin_time")
        end_time = request.data.get("end_time")
        administrator = request.data.get("administrator")
        begin_time_hour = begin_time.split('点')
        begin_time_min = begin_time_hour[1].split('分')
        end_time_hour = end_time.split('点')
        end_time_min = end_time_hour[1].split('分')
        begin_time0 = datetime(2022, 1, 1, int(begin_time_hour[0]), int(begin_time_min[0]), 0)
        end_time0 = datetime(2022, 1, 1, int(end_time_hour[0]), int(end_time_min[0]), 0)
        begin_time0 = begin_time0.strftime('%Y-%m-%d %H:%M:%S')
        begin_time1 = begin_time0.split(' ')[1]
        end_time0 = end_time0.strftime('%Y-%m-%d %H:%M:%S')
        end_time1 = end_time0.split(' ')[1]
        ground_code = ''
        if area == '羽毛球馆':
            now_id = Ground.objects.filter(area='羽毛球馆').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "01010" + next_id
            else:
                ground_code = "0101" + next_id
        elif area == '乒乓球馆':
            now_id = Ground.objects.filter(area='乒乓球馆').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "01020" + next_id
            else:
                ground_code = "0102" + next_id
        elif area == '新主C楼':
            now_id = Ground.objects.filter(area='新主C楼').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02010" + next_id
            else:
                ground_code = "0201" + next_id
        elif area == '新主D楼':
            now_id = Ground.objects.filter(area='新主D楼').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02020" + next_id
            else:
                ground_code = "0202" + next_id
        elif area == '新主E楼':
            now_id = Ground.objects.filter(area='新主E楼').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02030" + next_id
            else:
                ground_code = "0203" + next_id
        elif area == '新主F楼':
            now_id = Ground.objects.filter(area='新主F楼').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02040" + next_id
            else:
                ground_code = "0204" + next_id
        elif area == '新主G楼':
            now_id = Ground.objects.filter(area='新主G楼').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02050" + next_id
            else:
                ground_code = "0205" + next_id
        elif area == '教学楼1':
            now_id = Ground.objects.filter(area='教学楼1').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02060" + next_id
            else:
                ground_code = "0206" + next_id
        elif area == '教学楼2':
            now_id = Ground.objects.filter(area='教学楼2').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02070" + next_id
            else:
                ground_code = "0207" + next_id
        elif area == '教学楼3':
            now_id = Ground.objects.filter(area='教学楼3').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02080" + next_id
            else:
                ground_code = "0208" + next_id
        elif area == '主M':
            now_id = Ground.objects.filter(area='主M').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02090" + next_id
            else:
                ground_code = "0209" + next_id
        elif area == '教学楼5':
            now_id = Ground.objects.filter(area='教学楼5').__len__()
            next_id = str(now_id + 1)
            if now_id + 1 < 10:
                ground_code = "02100" + next_id
            else:
                ground_code = "0210" + next_id
        else:
            ground_code = "999999"

        Ground.objects.create(name=name, area=area, price=price, apply_needed=apply_needed,
                              description=description, avatar=avatar, begin_time=begin_time1,
                              end_time=end_time1, administrator_id=administrator, code=ground_code)
        grounds = Ground.objects.filter(name=name, area=area, price=price, apply_needed=apply_needed,
                                        description=description, avatar=avatar, begin_time=begin_time1,
                                        end_time=end_time1, administrator_id=administrator, code=ground_code)
        return self.paginate(grounds)

    # 修改场地信息(web)
    def ground_update(self, request, pk):
        from datetime import datetime
        name = request.data.get("name")
        area = request.data.get("area")
        price = request.data.get("price")
        apply_needed = request.data.get("apply_needed")
        description = request.data.get("description")
        avatar = request.data.get("avatar")
        begin_time = request.data.get("begin_time")
        end_time = request.data.get("end_time")
        administrator = request.data.get("administrator")
        begin_time_hour = begin_time.split('点')
        begin_time_min = begin_time_hour[1].split('分')
        end_time_hour = end_time.split('点')
        end_time_min = end_time_hour[1].split('分')
        begin_time0 = datetime(2022, 1, 1, int(begin_time_hour[0]), int(begin_time_min[0]), 0)
        end_time0 = datetime(2022, 1, 1, int(end_time_hour[0]), int(end_time_min[0]), 0)
        begin_time0 = begin_time0.strftime('%Y-%m-%d %H:%M:%S')
        begin_time1 = begin_time0.split(' ')[1]
        end_time0 = end_time0.strftime('%Y-%m-%d %H:%M:%S')
        end_time1 = end_time0.split(' ')[1]
        Ground.objects.filter(id=pk).update(name=name, area=area, price=price, apply_needed=apply_needed,
                                            description=description, avatar=avatar, begin_time=begin_time1,
                                            end_time=end_time1, administrator_id=administrator)
        grounds = Ground.objects.filter(id=pk)
        return self.paginate(grounds)

    # 删除场地（web）
    def ground_delete(self, request, pk):
        Ground.objects.filter(id=pk).delete()
        res = {
            "detail": '删除成功'
        }
        return Response(res)

    # 获取指定区域里的所有场地
    def get_grounds_by_area(self, request, pk):
        grounds = Ground.objects.filter(area=pk)
        return self.paginate(grounds)

    def ground_msg(self, request, pk):
        grounds = Ground.objects.filter(id=pk)
        return self.paginate(grounds)

    def ground_mul_price(self, request):
        admin_name = request.user
        admin = User.objects.get(username=admin_name)
        admin_id = admin.id
        buaa_admin = SuperAdmin.objects.get(user_ptr_id=admin_id)
        admin_type = buaa_admin.type
        area = request.data.get("area")
        new_price = request.data.get("price")
        if admin_type == "super":
            Ground.objects.filter(area=area).update(price=new_price)
            res = {
                "detail": "修改成功"
            }
            return Response(res)
        if admin_type == "ground":
            Ground.objects.filter(area=area, administrator_id=admin_id).update(price=new_price)
            res = {
                "detail": "修改成功"
            }
            return Response(res)
        res = {
            "detail": "管理员权限错误"
        }
        return Response(res)


if __name__ == "__main__":
    print(utils.get_access_token())
