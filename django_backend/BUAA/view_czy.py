from rest_framework.viewsets import ModelViewSet
from BUAA.models import *
from BUAA.accessPolicy import *
from BUAA.authentication import *
from .serializers import *
import time, datetime
from datetime import datetime

# base_dir = '/root/server_files/'
base_dir = 'C:/test/'
web_dir = 'http://114.116.194.3/server_files/'

# 帖子（管理端）
class TopicWebViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (TopicWebAccessPolicy,)
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    # TODO
    def get_serializer_class(self):
        return TopicSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 获取帖子列表
    def get_topic_list(self, request):
        topics = Topic.objects.all()
        res_list = []
        for topic in topics:
            user_id = topic.user_id.id
            user_nickname = WXUser.objects.filter(id = user_id)[0].name
            topic.user_nickname = user_nickname
            res = {
                "id":topic.id,
                "user_nickname":user_nickname,
                "create_time": topic.create_time,
                "content": topic.content
            }
            res_list.append(res)
        return Response(res_list, 200)

    # 根据发帖人昵称查找帖子, 模糊查询
    def search_topic_by_username(self, request):
        username = request.data.get("name")
        users = WXUser.objects.filter(name__contains=username)
        res_list = []
        for user in users:
            user_id = user.id
            username = user.name # nickname
            topics = Topic.objects.filter(user_id = user_id)
            for topic in topics:
                content = topic.content
                if len(topic.content) > 20:
                    content = topic.content[0:20] + "..."
                res = {
                    "id": user_id,
                    "user_nickname": username,
                    "create_time": topic.create_time,
                    "content": content
                }
                res_list.append(res)
        return Response(res_list, 200)

    # 删除帖子
    def topic_delete(self, request, pk):
        admin_name = request.user
        Topic.objects.filter(id = pk).delete()
        res = {
            "detail": '删除成功'
        }
        content = str(admin_name) + ": 删除了id为" + pk + "的帖子"
        Log.objects.create(content=content, pub_time=datetime.now())
        return Response(res, 200)

# 标签（管理端）
class TagWebViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (TagWebAccessPolicy,)
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def get_serializer_class(self):
        return TagSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 获取标签列表
    def get_tag_list(self, request):
        tags = Tag.objects.all()
        return self.paginate(tags)

    # 添加标签
    def add_tag(self, request):
        admin_name = request.user
        name = request.data.get("name")
        status = 0
        if Tag.objects.filter(name = name).count() > 0:
            status = 409
            res = {"detail":"同名标签已存在，添加失败"}
        else:
            status = 200
            res = {"detail":"添加成功"}
            Tag.objects.create(name = name)
            content = str(admin_name) + ": 新建了一个名叫“" + name + "”的标签"
            Log.objects.create(content=content, pub_time=datetime.now())
        return Response(res, status)

    # 修改标签名
    def update_tag_name(self, request, pk):
        admin_name = request.user
        new_name = request.data.get("name")
        old_name = ""
        tag_id = request.data.get("id")
        tag = Tag.objects.filter(id = tag_id)
        status = 404
        res = {}
        if tag.count() == 0:
            res = {"detail" : '标签不存在'}
        else:
            tags_samename = Tag.objects.filter(name = new_name)
            if tags_samename.count() >= 1:
                status = 409
                res = {"detail" : "标签不可重名"}
            else:
                status = 200
                old_name = tag[0].name
                tag.update(name = new_name)
                res = {"detail" : '修改成功'}
                content = str(admin_name) + ": 将标签“" + old_name + "”名字改为“" + new_name + "”"
                Log.objects.create(content = content, pub_time = datetime.now())
        return Response(res, status)

    # 删除标签
    def tag_delete(self, request, pk):
        admin_name = request.user
        name = Tag.objects.get(id = pk).name
        Tag.objects.filter(id = pk).delete()
        res = {"detail":'删除成功'}
        content = str(admin_name) + ": 删除了标签id为“" + str(pk) + "”, 标签名为“" + name + "”的标签"
        Log.objects.create(content = content, pub_time = datetime.now())
        return Response(res, 200)

    # 获取某个id的标签信息
    def get_tag(self, request, pk):
        tag = Tag.objects.filter(id = pk)
        status = 404
        if tag.count() == 0:
            res = {"detail": '标签不存在'}
        else:
            status = 200
            res = {
                "id": tag[0].id,
                "name":tag[0].name
            }
        return Response(res, status)


