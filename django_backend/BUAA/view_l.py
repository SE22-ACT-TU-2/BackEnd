from rest_framework.viewsets import ModelViewSet
from BUAA.models import *
from BUAA.accessPolicy import *
from BUAA.authentication import *

# base_dir = '/root/server_files/'
base_dir = 'C:/test/'
web_dir = 'http://114.116.194.3/server_files/'


sender = utils.MailSender()

class TopicViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (TopicAccessPolicy,)

    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_serializer_class(self):
        return TopicSerializer

    def paginate(self, objects):
        page = self.paginate_queryset(objects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(objects, many=True)
        return Response(serializer.data)

    # 帖子列表
    def topic_list(self, request):
        topics = Topic.objects.all()
        topic_list = []
        for topic in topics:
            has_star = True
            has_comment = True
            comment_list = TopicComment.objects.filter(topic_id=topic.id).__len__()
            star_list = Star.objects.filter(topic_id=topic.id).__len__()
            if star_list == 0:
                has_star = False
            if comment_list == 0:
                has_comment = False
            res = {
                "id": topic.id,
                "user": {"avatar": topic.user_id.avatar, "id": topic.user_id.id, "nickName": topic.user_id.name},
                "create_time": topic.create_time,
                "content": topic.content,
                "comment_count": topic.comment_count,
                "click_count": topic.click_count,
                "star_count": topic.star_count,
                "has_star": has_star,
                "has_comment": has_comment
            }
            topic_list.append(res)
        return Response(topic_list)

    # 删除帖子
    def topic_delete(self, request, pk):
        try:
            topic = Topic.objects.get(id=pk)
        except:
            res = {
                "msg": "该帖子已不存在"
            }
            return Response(data=res, status=404)
        Topic.objects.filter(id=pk).delete()
        res = {
            "msg": "删除成功"
        }
        return Response(data=res, status=201)

    # 发帖
    def topic_add(self, request):
        labels = request.data.get("labels")
        user_id = request.data.get("userId")
        user = WXUser.objects.get(id=user_id)
        content = request.data.get("content")
        topic = Topic.objects.create(create_time=datetime.now(), content=content, click_count=0, comment_count=0,
                             star_count=0, user_id_id=user_id)
        for label in labels:
            active = label["active"]
            tag_id = label["id"]
            if active:
                TopicTag.objects.create(tag_id_id=tag_id, topic_id_id=topic.id)
        res = {
            "msg": "发帖成功"
        }
        return Response(data=res, status=201)

    # 话题详情
    def topic_detail(self, request, pk):
        the_topic = Topic.objects.get(id=pk)
        has_star = True
        has_comment = True
        comment_len = TopicComment.objects.filter(topic_id=the_topic.id).__len__()
        star_len = Star.objects.filter(topic_id=the_topic.id).__len__()
        if star_len == 0:
            has_star = False
        if comment_len == 0:
            has_comment = False
        topic = {
            "id": the_topic.id,
            "user": {"avatar": the_topic.user_id.avatar, "id": the_topic.user_id.id, "nickName": the_topic.user_id.name},
            "create_time": the_topic.create_time,
            "content": the_topic.content,
            "comment_count": the_topic.comment_count,
            "click_count": the_topic.click_count,
            "star_count": the_topic.star_count,
            "has_star": has_star,
            "has_comment": has_comment
        }
        topicComment_list = []
        topicComments = TopicComment.objects.filter(topic_id=pk)
        for topicComment in topicComments:
            the_comment = {
                "userId": topicComment.user_id.id,
                "user": {"avatar": topicComment.user_id.avatar, "id": topicComment.user_id.id, "nickName": topicComment.user_id.name},
                "content": topicComment.content,
                "id": topicComment.id,   
                "create_time": topicComment.create_time   
            }
            topicComment_list.append(the_comment)
        star_list = []
        stars = Star.objects.filter(topic_id=pk)
        for star in stars:
            the_comment = {
                "userId": star.user_id.id,
                "user": {"avatar": star.user_id.avatar, "id": star.user_id.id, "nickName": star.user_id.name}
            }
            star_list.append(the_comment)
        res = {
            "topic": topic,
            "comments": topicComment_list,
            "stars": star_list
        }
        click_count = Topic.objects.get(id=pk).click_count + 1   
        Topic.objects.filter(id=pk).update(click_count=click_count)   
        return Response(res)

    # 获取话题
    def topic_get(self, request):
        tag_id = request.data.get("labelId")
        user_id = request.data.get("userId")
        topics = Topic.objects.all()
        topic_list = []
        for topic in topics:
            topic_tags = TopicTag.objects.filter(topic_id=topic.id)
            if_have = False
            if tag_id == 0:
                if_have = True
            else:
                for topic_tag in topic_tags:
                    if topic_tag.tag_id.id == tag_id:
                        if_have = True
            if if_have:
                has_star = True
                has_comment = True
                comment_len = TopicComment.objects.filter(topic_id=topic.id, user_id=user_id).__len__()
                star_len = Star.objects.filter(topic_id=topic.id, user_id=user_id).__len__()
                if star_len == 0:
                    has_star = False
                if comment_len == 0:
                    has_comment = False
                res = {
                    "id": topic.id,
                    "user": {"avatar": topic.user_id.avatar, "id": topic.user_id.id,
                             "nickName": topic.user_id.name},
                    "create_time": topic.create_time,
                    "content": topic.content,
                    "comment_count": topic.comment_count,
                    "click_count": topic.click_count,
                    "star_count": topic.star_count,
                    "has_star": has_star,
                    "has_comment": has_comment
                }
                topic_list.append(res)
        return Response(topic_list)

    # 发表评论
    def comment_creat(self, request):
        user_id = request.data.get("userId")
        topic_id = request.data.get("topicId")
        content = request.data.get("content")
        TopicComment.objects.create(user_id_id=user_id, topic_id_id=topic_id, content=content)
        comment_count = Topic.objects.get(id=topic_id).comment_count + 1   
        Topic.objects.filter(id=topic_id).update(comment_count=comment_count)   
        res = {
            "msg": "评论成功"
        }
        return Response(data=res, status=201)

    # 删除评论
    def comment_delete(self, request, pk):
        try:
            comment = TopicComment.objects.get(id=pk)
        except:
            res = {
                "msg": "该评论已不存在"
            }
            return Response(data=res, status=404)
        topic_id = TopicComment.objects.get(id=pk).topic_id
        comment_count = Topic.objects.get(id=topic_id.id).comment_count - 1
        Topic.objects.filter(id=topic_id.id).update(comment_count=comment_count)
        TopicComment.objects.filter(id=pk).delete()
        res = {
            "msg": "评论删除成功"
        }
        return Response(data=res, status=201)

    # 收藏/取消收藏帖子
    def topic_star(self, request):
        user_id = request.data.get("userId")
        topic_id = request.data.get("topicId")
        try:
            star = Star.objects.get(user_id=user_id, topic_id=topic_id)
        except:
            Star.objects.create(user_id_id=user_id, topic_id_id=topic_id)
            star_count = Topic.objects.get(id=topic_id).star_count + 1   
            Topic.objects.filter(id=topic_id).update(star_count=star_count)   
            res = {
                "msg": "收藏成功"
            }
            return Response(data=res, status=201)
        else:
            Star.objects.filter(user_id=user_id, topic_id=topic_id).delete()
            star_count = Topic.objects.get(id=topic_id).star_count - 1   
            Topic.objects.filter(id=topic_id).update(star_count=star_count)   
            res = {
                "msg": "取消收藏成功"
            }
            return Response(data=res, status=201)

    # 查看他人信息
    def check_others(self, request):
        user_id = request.data.get("userId")
        user = WXUser.objects.get(id=user_id)
        others_id = request.data.get("otheruserid")
        others = WXUser.objects.get(id=others_id)
        has_follow = True
        if Follow.objects.filter(person_do=user_id, person_done=others_id, tag=0).__len__() == 0:
            has_follow = False
        follower = Follow.objects.filter(person_done=user_id).__len__()
        following = Follow.objects.filter(person_do=user_id).__len__()
        topic_list = []
        topics = Topic.objects.filter(user_id=others_id)
        for topic in topics:
            has_star = True
            has_comment = True
            comment_list = TopicComment.objects.filter(topic_id=topic.id, user_id=user_id).__len__()
            star_list = Star.objects.filter(topic_id=topic.id, user_id=user_id).__len__()
            if star_list == 0:
                has_star = False
            if comment_list == 0:
                has_comment = False
            res = {
                "id": topic.id,
                "user": {"avatar": topic.user_id.avatar, "id": topic.user_id.id, "nickName": topic.user_id.name},
                "create_time": topic.create_time,
                "content": topic.content,
                "comment_count": topic.comment_count,
                "click_count": topic.click_count,
                "star_count": topic.star_count,
                "has_star": has_star,
                "has_comment": has_comment
            }
            topic_list.append(res)
        res = {
            "user": {
                "id": others_id,
                "avatar": others.avatar,
                "nickName": others.name,
                "has_follow": has_follow,
                "motto": others.sign,
                 "follower": following,   
                "following": follower   
            },
            "topics": topic_list
        }
        return Response(data=res, status=201)

    # 关注/拉黑   取消关注/取消拉黑
    def person_follow(self, request):
        tag = request.data.get("tag")
        user_id = request.data.get("userId")
        others_id = request.data.get("otheruserid")
        if tag == 0:  # 关注
            try:
                follow = Follow.objects.get(person_do=user_id, person_done=others_id)
            except:
                Follow.objects.create(person_do_id=user_id, person_done_id=others_id, tag=0)
                res = {
                    "msg": "关注成功"
                }
                return Response(data=res, status=201)
            else:
                follow = Follow.objects.get(person_do=user_id, person_done=others_id)
                now_tag = follow.tag
                if now_tag == 0:
                    Follow.objects.filter(person_do=user_id, person_done=others_id).delete()
                    res = {
                        "msg": "取消关注成功"
                    }
                    return Response(data=res, status=201)
                else:
                    Follow.objects.filter(person_do=user_id, person_done=others_id).update(tag=0)
                    res = {
                        "msg": "关注成功"
                    }
                    return Response(data=res, status=201)
        else:  # 拉黑
            try:
                follow = Follow.objects.get(person_do=user_id, person_done=others_id)
            except:
                Follow.objects.create(person_do_id=user_id, person_done_id=others_id, tag=1)
                res = {
                    "msg": "拉黑成功"
                }
                return Response(data=res, status=201)
            else:
                follow = Follow.objects.get(person_do=user_id, person_done=others_id)
                now_tag = follow.tag
                if now_tag == 1:
                    Follow.objects.filter(person_do=user_id, person_done=others_id).delete()
                    res = {
                        "msg": "取消拉黑成功"
                    }
                    return Response(data=res, status=201)
                else:
                    Follow.objects.filter(person_do=user_id, person_done=others_id).update(tag=1)
                    res = {
                        "msg": "拉黑成功"
                    }
                    return Response(data=res, status=201)

    # 获取所有标签
    def tag_list(self, request):
        tag_list = []
        tags = Tag.objects.all()
        for tag in tags:
            res = {
                "active": False,
                "name": tag.name,
                "id": tag.id
            }
            tag_list.append(res)
        return Response(tag_list)

    # 关注列表
    def follow_list(self, request, pk):   
        follow_list = []
        followed_list = []
        friend_list = []
        follows = Follow.objects.filter(person_do=pk)
        followeds = Follow.objects.filter(person_done=pk)
        for follow in follows:
            the_res = {
                "user": {"avatar": follow.person_done.avatar, "id": follow.person_done.id,
                         "nickName": follow.person_done.name}
            }
            follow_list.append(the_res)
        for followed in followeds:
            the_res = {
                "user": {"avatar": followed.person_do.avatar, "id": followed.person_do.id,
                         "nickName": followed.person_do.name}
            }
            followed_list.append(the_res)
        for follow in follows:
            if_friend = Follow.objects.filter(person_do=follow.person_done, person_done=follow.person_do).__len__()
            if if_friend != 0:
                the_res = {
                    "user": {"avatar": follow.person_done.avatar, "id": follow.person_done.id,
                             "nickName": follow.person_done.name}
                }
                friend_list.append(the_res)
        res = {
            "follow": follow_list,
            "followed": followed_list,
            "friend": friend_list
        }
        return Response(data=res, status=201)

    # 推荐用户接口
    def recommend(self, request):
        users = WXUser.objects.all()
        user_list = []
        for user in users:
            res = {
                "avatar": user.avatar,
                "nickName": user.name,
                "id": user.id
            }
            user_list.append(res)
        return Response(user_list)
