from channels.exceptions import StopConsumer
from channels.generic.websocket import WebsocketConsumer
import json
import time
import BUAA.utils as utils
import requests

# from BUAA.global_var import OnlineClientPool
# from backend.settings import GlobalVar

# clients = OnlineClientPool()
clients = {}
chat_clients = {}


class NotificationConsumer(WebsocketConsumer):
    def websocket_connect(self, message):
        """
        客户端请求链接之后自动触发
        :param message: 消息数据
        """
        print('请求链接')
        self.accept()  # 建立链接
        self.user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        if self.user_id == -1: return
        # print(f'client user id is {self.user_id}')

        # clients.add(self.user_id, self)
        clients[self.user_id] = self
        # 客户登录时无条件push新通知
        utils.push_all_notif(self.user_id, self)

    def websocket_receive(self, message):
        """
        客户端浏览器发送消息来的时候自动触发
        """
        try:
            receivers = json.loads(message['text'])
            print(f'message from the {self.user_id}th client: ' + message['text'])
        except:
            print(f'message from the {self.user_id}th client: ' + message['text'])
            return

        for r in receivers:
            if r in clients:
                utils.push_all_notif(r, clients[r])
        # for test
        # INTERVAL = 5
        # for i in range(3):
        #     text = f'The {i+1}th notification from server'
        #     self.send(text_data=text)
        #     time.sleep(INTERVAL)

        # with open('log', 'a') as f :
        #     f.write('In NOtificationConsumer receive, online client is ' +
        #             str(clients.keys()) + '\n')

    def websocket_disconnect(self, message):
        """
        客户端断开链接之后自动触发
        :param message:
        """
        # with open('log', 'a') as f :
        #     f.write('In NOtificationConsumer disconnect, online client is '
        #             + str(clients.keys()) + '\n')

        # 客户端断开链接之后 应该将当前客户端对象从列表中移除
        # clients.remove(self.user_id)
        if self.user_id in clients:
            clients.pop(self.user_id)
        raise StopConsumer()  # 主动报异常 无需做处理 内部自动捕获


def chat_robot(content):
    response = requests.get(f"http://api.qingyunke.com/api.php?key=free&appid=0&msg={content}")
    return response.json()['content']


class MessageConsumer(WebsocketConsumer):

    def connect(self):
        print("聊天功能，建立连接...")
        user_id = int(self.scope["url_route"]["kwargs"]["user_id"])
        if user_id == -1:
            return
        self.accept()
        self.user_id = user_id
        chat_clients[user_id] = self
        print("聊天功能，建立连接成功，user_id=", end='')
        print(user_id)
        # 推送所有未读消息
        utils.push_all_messages(self.user_id, self)

    def disconnect(self, code):
        if self.user_id in chat_clients:
            chat_clients.pop(self.user_id)
        print("聊天功能，断开连接成功，user_id=", end='')
        print(self.user_id)

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        request_type = data.get('type', '')
        if request_type == 'send_message':
            from_user_id = self.user_id
            to_user_id = data.get('to_user')
            message = data.get('message')
            print("发送消息，from_user_id:", end='')
            print(from_user_id, end='')
            print(" ===> to_user_id:", end='')
            print(to_user_id)
            ws = chat_clients.get(to_user_id, None)
            if not utils.save_and_send_message(from_user_id, to_user_id, message, ws, self):
                print("utils.save_and_send_message失败")
                self.send(json.dumps({"type": "send_message_failed"}, ensure_ascii=False))
        elif request_type == 'receive_message':
            message_ids = data.get('message_ids', '')
            if not utils.receive_message(message_ids):
                print("utils.receive_message失败")
            print("接收消息，user_id:", end='')
            print(self.user_id, end='，')
            print("message_ids:", end='')
            print(message_ids)
        elif request_type == 'chat_robot':
            ret_answer = {
                "type": "chat_robot_reply",
                "message": chat_robot(data.get('message'))
            }
            self.send(json.dumps(ret_answer, ensure_ascii=False))
        elif request_type == 'ping':
            res = {"type": "pong"}
            self.send(json.dumps(res, ensure_ascii=False))
        else:
            print("request_type错误，data=", end='')
            print(data)
