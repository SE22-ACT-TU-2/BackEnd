"""backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from BUAA.views import *
from BUAA.view_hmb import *
from BUAA.view_czy import *
from BUAA.superUser import *
from django.urls import re_path as url
from rest_framework.documentation import include_docs_urls
from rest_framework.routers import SimpleRouter

from BUAA.view_l import *

urlpatterns = [
    path('api/', include([
        path('show/', avoid_fxxking_censorship),
        path('admin/', admin.site.urls),
        path('rank/', lines),
        # 用户端
        path('sendVerify/', send_email),
        path('verify/', verify_email),
        path('userLogin/', user_login),
        path('userRegister/', user_register),
        path('adminLogIn/', sudo_login),
        path('register/', sudo_register),
        path('userOrgRelation/', user_org_relation),
        path('userActRelation/', user_act_relation),
        path('qrcode/', get_page_qrcode),
        #        path('boyaFollowers/', get_boya_followers),

        # 管理端
        path('identify/', web_token_identify),

        # 自动生成接口文档
        url(r'^docs/', include_docs_urls(title='一苇以航API接口')),

        # 版块
        url(r'^blocks/$',
            BlockViewSet.as_view({"get": "list", "post": "create"})),
        url(r'^blocks/(?P<pk>\d+)/$',
            BlockViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"})),

        # 用户
        url(r'^users/$', WXUserViewSet.as_view({"get": "list"})),
        url(r'^users/(?P<pk>\d+)/$', WXUserViewSet.as_view(
            {"get": "retrieve", "delete": "destroy", "put": "update"})),
        url(r'^users/boya_followers/', WXUserViewSet.as_view({"get": "get_boya_followers"})),
        url(r'^users/search/$', WXUserViewSet.as_view({"post": "search_user"})),

        # 组织申请
        url(r'^organizations/applications/$',
            OrgApplicationViewSet.as_view({"post": "create", "get": "list"})),
        url(r'^organizations/applications/(?P<pk>\d+)/$',
            OrgApplicationViewSet.as_view({"delete": "destroy", "get": "retrieve"})),
        # url(r'^users/organizations/applications/(?P<user_id>\d+)/$',
        #     OrgApplicationViewSet.as_view({"get": "user_get_all"})),
        url(r'^organizations/applications/verifications/(?P<pk>\d+)/$',
            OrgApplicationViewSet.as_view({"put": "verify"})),

        # 组织
        url(r'^organizations/$',
            OrganizationModelViewSet.as_view({"post": "create", "get": "list"})),
        url(r'^organizations/(?P<pk>\d+)/$', OrganizationModelViewSet.as_view(
            {"get": "retrieve", "put": "update", "delete": "destroy"})),
        url(r'^blocks/organizations/(?P<block_id>\d+)/$',
            OrganizationModelViewSet.as_view({"get": "get_org_by_block"})),
        url(r'^organizations/owner/(?P<pk>\d+)/$',
            OrganizationModelViewSet.as_view({"post": "change_org_owner"})),
        url(r'^organizations/search/$',
            OrganizationModelViewSet.as_view({"post": "search_all"})),
        url(r'^blocks/organizations/search/(?P<block_id>\d+)/$',
            OrganizationModelViewSet.as_view({"post": "search_org_by_block"})),

        # 关注组织
        url(r'^users/followed_organizations/$',
            FollowedOrgViewSet.as_view({"post": "create", "delete": "destroy"})),
        url(r'^users/followed_organizations/(?P<pk>\d+)/$',
            FollowedOrgViewSet.as_view({"get": "get_followed_org"})),

        # 组织管理
        url(r'^organizations/managers/$',
            OrgManageViewSet.as_view({"post": "create_wrapper", "delete": "destroy", })),
        url(r'^organizations/managers/(?P<pk>\d+)/$',
            OrgManageViewSet.as_view({"get": "get_all_managers"})),
        url(r'^users/managed_organizations/(?P<pk>\d+)/$',
            OrgManageViewSet.as_view({"get": "get_managed_org"})),
        url(r'^users/managed_organizations/search/(?P<pk>\d+)/$',
            OrgManageViewSet.as_view({"post": "search_managed_org"})),

        # 活动分类
        url(r'^activities/categories/$',
            CategoryViewSet.as_view({"get": "list", "post": "create"})),
        url(r'^activities/categories/(?P<pk>\d+)/$',
            CategoryViewSet.as_view({"put": "update", "delete": "destroy"})),

        # 活动地址
        url(r'^activities/addresses/$',
            AddressViewSet.as_view({"get": "list", "post": "create"})),
        url(r'^activities/addresses/(?P<pk>\d+)/$',
            AddressViewSet.as_view({"put": "update", "delete": "destroy"})),

        # 用户反馈
        url(r'^feedbacks/$',
            UserFeedbackViewSet.as_view({"get": "list", "post": "create"})),
        url(r'^feedbacks/(?P<pk>\d+)/$',
            UserFeedbackViewSet.as_view({"get": "retrieve", "delete": "destroy"})),
        url(r'^feedbacks/search/$',
            UserFeedbackViewSet.as_view({"get": "search_all_feedback"})),
        url(r'^feedbacks/user/(?P<user_id>\d+)/search/$',
            UserFeedbackViewSet.as_view({"get": "search_user_feedback"})),

        # 活动
        url(r'^activities/$',
            ActivityViewSet.as_view({"post": "create_wrapper", "get": "list"})),
        url(r'^activities/(?P<pk>\d+)/$', ActivityViewSet.as_view(
            {"get": "retrieve", "delete": "destroy_wrapper", "put": "update_wrapper"})),
        #         url(r'^activities/(?P<pk>\d+)/$', ActivityViewSet.as_view(
        #             {"get": "retrieve", "delete": "destroy", "put": "update"})),
        url(r'^activities/search/$',
            ActivityViewSet.as_view({"post": "search_all"})),

        url(r'^organizations/activities/(?P<org_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_org_act"})),
        url(r'^organizations/activities/search/(?P<org_id>\d+)/$',
            ActivityViewSet.as_view({"post": "search_act_by_org"})),

        url(r'^users/released_activities/(?P<user_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_user_act"})),
        url(r'^users/released_activities/search/(?P<user_id>\d+)/$',
            ActivityViewSet.as_view({"post": "search_user_released_act"})),

        url(r'^blocks/activities/(?P<block_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_block_act"})),
        url(r'^blocks/activities/search/(?P<block_id>\d+)/$',
            ActivityViewSet.as_view({"post": "search_act_by_block"})),

        # 活动参与
        url(r'activities/participants/$',
            JoinedActViewSet.as_view({"post": "create", "delete": "destroy_wrapper"})),
        url(r'activities/(?P<act_id>\d+)/participants/$',
            JoinedActViewSet.as_view({"get": "get_act_participants"})),
        url(r'users/joined_acts/(?P<user_id>\d+)/$',
            JoinedActViewSet.as_view({"get": "get_user_joined_act"})),
        url(r'users/joined_acts/search/(?P<user_id>\d+)/$',
            JoinedActViewSet.as_view({"post": "search_user_joined_act"})),
        url(r'activities/joined_numbers/(?P<act_id>\d+)/$',
            JoinedActViewSet.as_view({"get": "get_act_participants_number"})),
        url(r'users/joined_acts/(?P<user_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/$',
            JoinedActViewSet.as_view({"get": "get_user_joined_act_begin_order"})),

        # 活动评论
        url(r'activities/comments/$',
            CommentViewSet.as_view({"get": "list", "post": "create_wrapper"})),
        url(r'activities/(?P<act_id>\d+)/comments/$',
            CommentViewSet.as_view({"get": "get_act_comments"})),
        url(r'activities/(?P<act_id>\d+)/users/(?P<user_id>\d+)/comments',
            CommentViewSet.as_view({"get": "get_user_comment"})),
        url(r'activities/comments/(?P<pk>\d+)/$', CommentViewSet.as_view(
            {"delete": "destroy", "put": "update_wrapper", "get": "retrieve"})),

        url(r'activities/comments/search/$',
            CommentViewSet.as_view({"get": "search_all_comment"})),
        url(r'activities/(?P<act_id>\d+)/comments/search/$',
            CommentViewSet.as_view({"get": "search_by_act"})),
        url(r'activities/users/(?P<user_id>\d+)/comments/search/$',
            CommentViewSet.as_view({"get": "search_by_user"})),

        # 个性化推荐
        #        url(r'recommended/activities/(?P<user_id>\d+)/$',
        #            ActivityViewSet.as_view({"get": "get_recommended_act"})),
        #        url(r'recommended/organizations/(?P<user_id>\d+)/$',
        #            OrganizationModelViewSet.as_view({"get": "get_recommended_org"})),

        url(r'recommended/(?P<user_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_recommended_act"})),

        # 关注组织发布的活动
        url(r'users/followed_organizations/activities/(?P<user_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_followed_org_act"})),

        # 上传图片
        url(r'activities/(?P<act_id>\d+)/avatar/$',
            ImageUploadViewSet.as_view({"post": "upload_act_avatar", "delete": "remove_act_avatar"})),
        url(r'organizations/(?P<org_id>\d+)/avatar/$',
            ImageUploadViewSet.as_view({"post": "upload_org_avatar"})),

        # 通知
        url(r'^notifications/read/(?P<user_id>\d+)/$', SentNotifViewSet.as_view({"put": "read_notification"})),

        # 测试使用
        url(r'^test/users/$', WXUserViewSet.as_view({"post": "create"})),
        url(r'^test/notifications/', NotificationViewSet.as_view({"post": "create", "get": "list"})),
        url(r'^test/read/notifications/', SentNotifViewSet.as_view({"post": "create", "get": "list"})),
        # wzk优化
        url(r'users/joined_acts/status/(?P<user_id>\d+)/$',
            JoinedActViewSet.as_view({"get": "get_user_joined_act_status"})),
        url(r'^users/released_activities/status/(?P<user_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_user_act_status"})),
        url(r'^organizations/activities/status/(?P<org_id>\d+)/$',
            ActivityViewSet.as_view({"get": "get_org_act_status"})),
        url(r'^blocks/activities/status/(?P<block_id>\d+)/$', ActivityViewSet.as_view({"get": "get_block_act_status"})),

        ###############################################################################################

        # 用户端（新）
        # 钱包
        url(r'^users/wallet/(?P<pk>\d+)/$', WXUserViewSet.as_view({"get": "get_wallet"})),  # 查询余额
        url(r'^users/wallet/$', WXUserViewSet.as_view({"post": "recharge"})),  # 充值
        # 场地申请
        url(r'^sites/used/$', GroundApplyViewSet.as_view({"post": "get_used_ground"})),  # 查看被占用的场地（已被预约，审核中）
        url(r'sites/$', GroundApplyViewSet.as_view({"post": "book_ground"})),  # 预约场地
        url(r'^users/booked_ground/(?P<pk>\d+)/$', GroundApplyViewSet.as_view({"get": "get_booking"})),  # 查看自己的预约
        url(r'^users/booked_ground/$', GroundApplyViewSet.as_view({"post": "rebook_ground"})),  # 预约改期
        url(r'^users/cancel_booking/(?P<apply_id>\d+)/$', GroundApplyViewSet.as_view({"get": "cancel_booking"})),  # 取消
        url(r'^sites/(?P<pk>\w+)/$', GroundViewSet.as_view({"get": "get_grounds_by_area"})),  # 根据区域获取场地
        # 用户审核
        url(r'^users/verify/(?P<pk>\w+)/$', UserVerifyViewSet.as_view({"get": "if_verified"})),  # 查看认证信息
        url(r'^users/verify/', ImageUploadViewSet.as_view({"post": "verify"})),  # 认证
        # view_hmb
        url(r'^hmb_test/$', HMBTestViewSet.as_view({"get": "hmb_test"})),

        ###############################################################################################

        # 管理端（新）
        url(r'^users/blackList/$', WXUserViewSet.as_view({"get": "blackList"})),  # 黑名单列表
        url(r'^users/blackList/(?P<pk>\d+)/$', WXUserViewSet.as_view({"put": "blackList_out"})),  # 黑名单修改
        url(r'^users/blackList/black_search/$', WXUserViewSet.as_view({"post": "black_search"})),  # 黑名单查询
        url(r'^users/mul/(?P<pk>\d+)/$', WXUserViewSet.as_view({"put": "mul_update"})),  # 用户列表批量修改
        url(r'^users/sig/(?P<pk>\d+)/$', WXUserViewSet.as_view({"put": "sig_update"})),  # 用户列表单独修改
        url(r'^userVerify/$', UserVerifyViewSet.as_view({"get": "userVery_list"})),  # 用户审核列表
        url(r'^userVerify/search/$', UserVerifyViewSet.as_view({"post": "search_user"})),  # 用户审核列表查询
        url(r'^userVerify/(?P<pk>\d+)/$', UserVerifyViewSet.as_view({"put": "userVerify"})),  # 用户审核列表审核操作
        url(r'^userVerify/show/(?P<pk>\d+)/$', UserVerifyViewSet.as_view({"get": "show_verify"})),  # 显示指定id的审核信息
        # 场地管理
        url(r'^web/ground/$', GroundViewSet.as_view({"get": "ground_list"})),  # 场地列表
        url(r'^web/ground/add_ground/$', GroundViewSet.as_view({"post": "add_ground"})),  # 添加场地
        url(r'^web/ground/add_ground_test/$', GroundViewSet.as_view({"post": "add_ground_test"})),
        url(r'^web/ground/(?P<pk>\d+)/$',
            GroundViewSet.as_view({"put": "ground_update", "delete": "ground_delete", "get": "ground_msg"})),
        url(r'^web/ground/mul/$', GroundViewSet.as_view({"post": "ground_mul_price"})),
        url(r'^web/ground/check/$', GroundApplyViewSet.as_view({"post": "ground_check"})),  # 场地使用情况查询
        url(r'^web/ground_verify/$', GroundApplyViewSet.as_view({"get": "groundVerify_list"})),  # 场地审核列表
        url(r'^web/ground_verify/(?P<pk>\d+)/$',
            GroundApplyViewSet.as_view({"get": "groundVerify_msg", "put": "groundVerify"})),
        url(r'^web/ground_apply/$', GroundApplyViewSet.as_view({"get": "groundApply_list"})),  # 场地预约列表
        url(r'^web/ground_apply/(?P<pk>\d+)/$',
            GroundApplyViewSet.as_view({"delete": "groundApply_delete", "put": "groundApply_update"})),
        url(r'^web/ground_apply/search/$', GroundApplyViewSet.as_view({"post": "search_apply"})),  # 查询
        url(r'^web/ground_verify/search/$', GroundApplyViewSet.as_view({"post": "search_verify"})),  # 查询
        url(r'^web/admin_log/$', WXUserViewSet.as_view({"get": "log_list"})),  # 0513
        url(r'^web/admin_log/time_search/$', WXUserViewSet.as_view({"post": "log_search"})),  # 0515
        url(r'^users/topics/$', TopicViewSet.as_view({"get": "topic_list"})),    
        url(r'^users/topics/delete/(?P<pk>\d+)/$', TopicViewSet.as_view({"get": "topic_delete"})),    
        url(r'^users/topics/topic_add/$', TopicViewSet.as_view({"post": "topic_add"})),    
        url(r'^users/topics/detail/(?P<pk>\d+)/$', TopicViewSet.as_view({"get": "topic_detail"})),    
        url(r'^users/topics/get/$', TopicViewSet.as_view({"post": "topic_get"})),    
        url(r'^users/topics/comment/$', TopicViewSet.as_view({"post": "comment_creat"})),    
        url(r'^users/topics/comment/delete/(?P<pk>\d+)/$', TopicViewSet.as_view({"get": "comment_delete"})),    
        url(r'^users/topics/star/$', TopicViewSet.as_view({"post": "topic_star"})),    
        url(r'^users/topics/check_others/$', TopicViewSet.as_view({"post": "check_others"})),    
        url(r'^users/topics/person_follow/$', TopicViewSet.as_view({"post": "person_follow"})),    
        url(r'^users/topics/tags/$', TopicViewSet.as_view({"get": "tag_list"})),
        url(r'^users/topics/follow_list/(?P<pk>\d+)/$', TopicViewSet.as_view({"get": "follow_list"})),
        url(r'^users/recommend/$', TopicViewSet.as_view({"get": "recommend"})),

        # 帖子管理
        url(r'^web/post/$', TopicWebViewSet.as_view({"get": "get_topic_list"})),
        url(r'^web/post/search/$', TopicWebViewSet.as_view({"post": "search_topic_by_username"})),
        url(r'^web/post/(?P<pk>\d+)/$', TopicWebViewSet.as_view({"delete": "topic_delete"})),
        # 标签管理
        url(r'^web/tag/$', TagWebViewSet.as_view({"get": "get_tag_list"})),
        url(r'^web/tag/add_tag/$', TagWebViewSet.as_view({"post": "add_tag"})),
        url(r'^web/tag/(?P<pk>\d+)/$', TagWebViewSet.as_view({"put": "update_tag_name", "delete": "tag_delete", "get": "get_tag"})),
        # url(r'^web/tag/(?P<pk>\d+)/$', TagWebViewSet.as_view({"delete": "tag_delete"})),
        # url(r'^web/tag/(?P<pk>\d+)/$', TagWebViewSet.as_view({"get": "get_tag"})),
    ]))

]

# router = SimpleRouter()
# router.register('activities/join_applications', JoinActApplicationViewSet)
# urlpatterns += router.urls
