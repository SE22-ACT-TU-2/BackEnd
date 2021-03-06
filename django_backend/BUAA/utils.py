from smtplib import SMTP, SMTPException
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from itsdangerous.jws import TimedJSONWebSignatureSerializer as TJWSSerializer
from django.conf import settings

try:
    import BUAA.models as models
    import BUAA.serializers as serializers
    from BUAA.const import NOTIF
except ImportError:
    print("BUAA module is not found")
import os
import json
import requests
import time

mail_host = "smtp.126.com"  # 设置SMTP服务器，如smtp.qq.com
mail_user = "reedsailing@126.com"  # 发送邮箱的用户名，如xxxxxx@qq.com
mail_user = "se2022_act_tu_2@126.com"
mail_pass = "SJHDAZYRQSGNXCTH"  # 发送邮箱的密码（注：QQ邮箱需要开启SMTP服务后在此填写授权码）
mail_pass = "RLUZVOSJBRVZGAPD"
sender_name = "一苇以航"
sender = mail_user  # 发件邮箱，如xxxxxx@qq.com

access_token_path = "/root/access_token.txt"


def get_access_token():
    def get_from_wx_api():
        appid = settings.APPID
        secret = settings.SECRET
        url = 'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid=' + appid + '&secret=' + secret
        response = json.loads(requests.get(url).content)
        with open("./access_token.txt", "w") as f:
            print(response["access_token"], file=f)
            print(time.time(), file=f)
            print(response["expires_in"], file=f)
        return response["access_token"]

    if not os.path.exists(access_token_path):
        return get_from_wx_api()

    with open(access_token_path) as f:
        lines = f.readlines()
        if time.time() - int(lines[1].strip()) > int(lines[2].strip()):
            return get_from_wx_api()
        return lines[0].strip()


# Notification part
def get_notif_content(type_, **kwargs):
    act = kwargs['act_name'] if 'act_name' in kwargs else ''
    org = kwargs['org_name'] if 'org_name' in kwargs else ''
    ground_apply = kwargs['ground_apply'] if 'ground_apply' in kwargs else ''
    user = kwargs['user_name'] if 'user_name' in kwargs else ''
    comment = kwargs['comment'] if 'comment' in kwargs else ''
    status = kwargs['status'] if 'status' in kwargs else False

    content = ''
    if type_ == NOTIF.ActContent:
        content = f"您参与的活动\'{act}\'内容发生了改变，请及时查看"
    elif type_ == NOTIF.ActCancel:
        content = f"您参与的活动\'{act}\'已被取消"
    elif type_ == NOTIF.RemovalFromAct:
        content = f"您已被管理员从活动\'{act}\'中移除"
    elif type_ == NOTIF.NewBoya:
        content = f"有新的博雅\'{act}\', 如有需要请及时报名"
    elif type_ == NOTIF.ActCommented:
        content = f"用户\'{user}\'评论了您管理的活动\'{act}\'：\n{comment}"
    elif type_ == NOTIF.ActCommentModified:
        content = f"用户\'{user}\'在您管理的活动\'{act}\'中修改了评论：\n{comment}"
    elif type_ == NOTIF.OrgApplyRes:
        if status:
            content = f"您创建\'{org}\'组织的申请已经通过"
        else:
            content = f"您创建\'{org}\'组织的申请被拒绝了"
    elif type_ == NOTIF.BecomeOwner:
        content = f"您被转让成为\'{org}\'组织的负责人"
    elif type_ == NOTIF.BecomeAdmin:
        content = f"您成为\'{org}\'组织的管理员"
    elif type_ == NOTIF.RemovalFromAdmin:
        content = f"您被\'{org}\'组织的负责人移除了管理员身份"
    elif type_ == NOTIF.GroundApplyReminder:
        content = f"您预约的场地\'{ground_apply}\'还有半小时生效，请及时入场"

    return content + '\n'


def push_all_notif(user_id, ws):
    print("push_all_notif to user_id:", end='')
    print(user_id)
    """revoke when user gets online"""
    unread_send_notifs = models.SentNotif.objects.filter(person=user_id, already_read=False)
    unread_notifs = list(map(lambda x: serializers.NotificationSerializer(x.notif).data, unread_send_notifs))
    ws.send(json.dumps(unread_notifs, ensure_ascii=False))
    # unread_send_notifs.update(already_read = True)


def get_all_user_with_notif():
    """return a id list where the user corresponding with the id has unread notification"""
    unread_send_notifs = models.SentNotif.objects.filter(already_read=False)
    unread_user = set(map(lambda x: int(x.person.id), unread_send_notifs))
    return unread_user


def push_all_messages(user_id, ws):
    unread_messages = models.Message.objects.filter(to_user_id=user_id, is_read=False)
    data = []
    for unread_message in unread_messages:
        msg = serializers.MessageSerializer(instance=unread_message).data
        raw_time = msg['created_time']
        date_ = raw_time.split('T')[0]
        time_ = raw_time.split('T')[1].split('.')[0]
        msg['created_time'] = date_ + " " + time_
        data.append(msg)
    # data = list(map(lambda x: serializers.MessageSerializer(x).data, unread_messages))
    res = {
        "type": "ws_connected",
        "messages": data
    }
    ws.send(json.dumps(res, ensure_ascii=False))


def save_and_send_message(from_user_id, to_user_id, message, ws, ws_self):
    message_data = {
        "from_user": from_user_id,
        "to_user": to_user_id,
        "content": message
    }
    serializer = serializers.MessageSerializer(data=message_data)
    if not serializer.is_valid(raise_exception=False):
        return False
    message_object = serializer.save()
    ws_self.send(json.dumps({"type": "send_message_success"}, ensure_ascii=False))
    if ws is not None:
        msg = serializers.MessageSerializer(instance=message_object).data
        raw_time = msg['created_time']
        date_ = raw_time.split('T')[0]
        time_ = raw_time.split('T')[1].split('.')[0]
        msg['created_time'] = date_ + " " + time_
        print(msg)
        res = {
            "type": "new_message",
            # "message": serializers.MessageSerializer(instance=message_object).data
            "message": msg
        }
        ws.send(json.dumps(res, ensure_ascii=False))
    return True


def receive_message(message_ids):
    try:
        messages = []
        for message_id in message_ids:
            messages.append(models.Message.objects.get(id=message_id))
    except:
        return False
    for message in messages:
        message.delete()
    return True


def receive_message_by_id(send_id, receive_id):
    try:
        messages = []
        messages.extend(models.Message.objects.filter(from_user_id=send_id, to_user_id=receive_id))
    except:
        return False
    for message in messages:
        message.delete()
    return True


class MailSender:
    def __init__(self):
        self.mail_host = mail_host  # 设置SMTP服务器，如smtp.qq.com
        self.mail_user = mail_user  # 发送邮箱的用户名，如xxxxxx@qq.com
        self.mail_pass = mail_pass  # 发送邮箱的密码（注：QQ邮箱需要开启SMTP服务后在此填写授权码）
        self.sender = mail_user  # 发件邮箱，如xxxxxx@qq.com

    def send_mail(self, title, content, receiver=None):
        if receiver is None:
            receiver = self.mail_user
        message = MIMEText(content, 'plain', 'utf-8')
        message['From'] = formataddr(pair=(sender_name, self.sender))  # 发件人
        message['To'] = receiver  # 收件人
        subject = title  # 主题
        message['Subject'] = Header(subject, 'utf-8')
        try:
            # print("中文测试")
            print('ready to send email to ' + receiver)
            smtpObj = SMTP()
            smtpObj.connect(self.mail_host, 25)  # 25 为 SMTP 端口号
            smtpObj.login(self.mail_user, self.mail_pass)
            smtpObj.sendmail(self.sender, receiver, str(message))
            print('mail send success')
            # print("邮件发送成功")
        except SMTPException:
            print("error")
            # print("ERROR：无法发送邮件")


# 1, 加密openid
def encode_openid(openid, ex):
    # 1, 创建加密对象
    serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=ex)

    # 2, 加密数据
    token = serializer.dumps({"openid": openid})

    # 3, 返回加密结果
    return token.decode()


# 2, 解密openid
def decode_openid(token, ex):
    # 1, 创建加密对象
    serializer = TJWSSerializer(settings.SECRET_KEY, expires_in=ex)

    # 2, 加密数据
    try:
        openid = serializer.loads(token).get("openid")
    except Exception as e:
        return None

    # 3, 返回加密结果
    return openid


import traceback
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger('default')
logger2 = logging.getLogger('django.server')


class ExceptionLoggingMiddleware(MiddlewareMixin):
    def process_exception(self, request, exception):
        import traceback
        # with open("/root/test.txt", "w") as f:
        #    f.write(traceback.format_exc())
        logger.error(traceback.format_exc())
        logger2.error(traceback.format_exc())


if __name__ == "__main__":
    a = MailSender()
    a.send_mail("asdaf", "ASdasdasd", "2209334160@qq.com")
