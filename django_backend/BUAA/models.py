from datetime import datetime

from django.core.validators import MinValueValidator
from django.db import models
from django.contrib.auth.models import User
from BUAA.const import NOTIF_TYPE_CHOICES


# Create your models here.


# 用户
class WXUser(models.Model):
    objects = models.Manager()
    openid = models.CharField(unique=True, verbose_name="微信openid", max_length=200, help_text="微信openid --string")
    name = models.CharField(max_length=30, verbose_name="昵称", help_text="昵称 --string")
    avatar = models.CharField(max_length=500, null=True, blank=True, verbose_name="头像", help_text="头像 --string")
    email = models.EmailField(max_length=100, null=True, verbose_name="邮箱", help_text="邮箱 --string")
    sign = models.CharField(max_length=200, null=True, blank=True, verbose_name="个性签名", help_text="个性签名 --string")
    contact = models.CharField(max_length=50, verbose_name="联系方式", null=True, blank=True, help_text="联系方式 --string")
    follow_boya = models.BooleanField(verbose_name="是否关注博雅版块", default=False)
    user_portrait = models.CharField(max_length=200, null=True, blank=True, verbose_name="用户画像路径")
    '''--------------------------------------------------'''
    defaults_number = models.IntegerField(verbose_name="违约次数", default=0, validators=[MinValueValidator(1)])
    money = models.FloatField(verbose_name="钱包", default=0, validators=[MinValueValidator(1)])
    is_csstd = models.BooleanField(verbose_name="是否是院内学生", default=False)
    student_id = models.CharField(max_length=10, null=True, blank=True, verbose_name="学号")
    real_name = models.CharField(max_length=30, verbose_name="真实姓名", null=True, blank=True)


# 超级管理员
class SuperAdmin(User):
    objects = models.Manager()
    avatar = models.CharField(max_length=500, null=True, blank=True, verbose_name="头像")
    '''--------------------------------------------------'''
    type = models.CharField(max_length=50, verbose_name="管理员类别", default="normal")


# 活动
class Activity(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=100, verbose_name="活动名称", help_text="活动名称 --string")
    begin_time = models.DateTimeField(verbose_name="开始时间", help_text="开始时间")
    end_time = models.DateTimeField(verbose_name="结束时间")
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    contain = models.IntegerField(verbose_name="人数限制", validators=[MinValueValidator(1)])
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name="活动描述")
    review = models.BooleanField(verbose_name="是否需要审核", default=False)
    # is_personal = models.BooleanField(verbose_name="是否个人活动", default=True)

    owner = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="发起者")
    type = models.ForeignKey('Category', on_delete=models.CASCADE, null=True, verbose_name="分类")
    org = models.ForeignKey('Organization', on_delete=models.CASCADE, null=True, verbose_name="所属组织")
    location = models.ForeignKey('Address', on_delete=models.CASCADE, verbose_name="活动地点")
    block = models.ForeignKey('Block', on_delete=models.CASCADE, verbose_name="所属版块")  # 组织需要与组织模块保证一致
    avatar = models.CharField(max_length=500, null=True, blank=True, verbose_name="活动图片")

    keywords = models.CharField(max_length=500, null=True, blank=True, verbose_name="关键词")

    # person = models.ManyToManyField('WXUser', verbose_name="报名人员")


# 活动参与
class JoinedAct(models.Model):
    objects = models.Manager()
    act = models.ForeignKey('Activity', on_delete=models.CASCADE, verbose_name='活动')
    person = models.ForeignKey('WXUser', verbose_name="报名人员", on_delete=models.CASCADE)


# 分类
class Category(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=50, unique=True, verbose_name="分类名称")


# 地址
class Address(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=50, verbose_name="地址名称")
    longitude = models.DecimalField(max_digits=30, decimal_places=25, verbose_name="经度")
    latitude = models.DecimalField(max_digits=30, decimal_places=25, verbose_name="纬度")


# 组织
class Organization(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=50, unique=True, verbose_name="组织名称")
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name="组织描述")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    avatar = models.CharField(max_length=500, null=True, blank=True, verbose_name="头像")

    owner = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="负责人")
    block = models.ForeignKey('Block', on_delete=models.CASCADE, verbose_name="所属版块")


# 组织管理员
class OrgManager(models.Model):
    objects = models.Manager()
    org = models.ForeignKey('Organization', verbose_name='组织', on_delete=models.CASCADE)
    person = models.ForeignKey('WXUser', verbose_name="组织管理员", on_delete=models.CASCADE)


# 关注组织
class FollowedOrg(models.Model):
    objects = models.Manager()
    org = models.ForeignKey('Organization', verbose_name='关注的组织', on_delete=models.CASCADE)
    person = models.ForeignKey('WXUser', verbose_name="用户", on_delete=models.CASCADE)


# 评价
class Comment(models.Model):
    objects = models.Manager()
    content = models.CharField(max_length=500, null=True, verbose_name="内容")
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    score = models.DecimalField(max_digits=2, decimal_places=1, verbose_name="评分")

    act = models.ForeignKey('Activity', on_delete=models.CASCADE, verbose_name="所属活动")
    user = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="所属用户")


# 版块
class Block(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=50, unique=True, verbose_name="版块名称")


# 组织管理员申请
class ManagerApplication(models.Model):
    objects = models.Manager()
    org = models.ForeignKey('Organization', on_delete=models.CASCADE, verbose_name="组织")
    user = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="申请用户")
    content = models.CharField(max_length=500, null=True, blank=True, verbose_name="理由")
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")


# Log
class Log(models.Model):
    objects = models.Manager()
    content = models.CharField(max_length=500, verbose_name="操作内容")
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")


# 用户反馈
class UserFeedback(models.Model):
    objects = models.Manager()
    content = models.CharField(max_length=500, verbose_name="反馈内容")
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name="反馈时间")

    user = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="用户名")


# 组织申请
class OrgApplication(models.Model):
    objects = models.Manager()
    STATUS = (
        (0, '待审批'),
        (1, '审批通过'),
        (2, '审批未通过')
    )
    name = models.CharField(max_length=50, verbose_name="组织名称")
    description = models.CharField(max_length=500, verbose_name="申请描述")
    pub_time = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")
    status = models.SmallIntegerField(choices=STATUS, default=0, verbose_name="审批状态")

    user = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="申请人")
    block = models.ForeignKey('Block', on_delete=models.CASCADE, verbose_name="所属版块")


# 加入活动申请
class JoinActApplication(models.Model):
    objects = models.Manager()
    act = models.ForeignKey('Activity', on_delete=models.CASCADE, verbose_name="申请活动")
    user = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="申请人")


# 通知
class Notification(models.Model):
    objects = models.Manager()
    type = models.SmallIntegerField(choices=NOTIF_TYPE_CHOICES, verbose_name='通知类型')
    time = models.DateTimeField(auto_now_add=True, verbose_name="发布时间")
    content = models.CharField(max_length=500, blank=False, verbose_name="通知内容")
    act = models.ForeignKey('Activity', null=True, on_delete=models.CASCADE, verbose_name="活动")
    org = models.ForeignKey('Organization', null=True, on_delete=models.CASCADE, verbose_name="组织")


# 发送通知
class SentNotif(models.Model):
    objects = models.Manager()
    notif = models.ForeignKey('Notification', on_delete=models.CASCADE, verbose_name='通知')
    person = models.ForeignKey('WXUser', verbose_name="接收人员", on_delete=models.CASCADE)
    already_read = models.BooleanField(verbose_name="是否已读", default=False)


# 场地
class Ground(models.Model):
    objects = models.Manager()
    name = models.CharField(max_length=30, verbose_name="场地名称")
    area = models.CharField(max_length=50, null=True, blank=True, verbose_name="场地区域")
    price = models.FloatField(verbose_name="价格", default=0, validators=[MinValueValidator(1)])
    apply_needed = models.BooleanField(verbose_name="是否需要预约", default=False)
    description = models.CharField(max_length=500, null=True, blank=True, verbose_name="场地信息")
    avatar = models.CharField(max_length=500, null=True, blank=True, verbose_name="场地图片")
    begin_time = models.TimeField(verbose_name="开放开始时间", default="08:00:00")
    end_time = models.TimeField(verbose_name="开放结束时间", default="22:00:00")
    administrator = models.ForeignKey('SuperAdmin', null=True, on_delete=models.CASCADE, verbose_name="场地管理员")
    code = models.CharField(max_length=30, verbose_name="编码", default="999999")


# 场地申请
class GroundApply(models.Model):
    objects = models.Manager()
    STATE = (
        (0, '已通过'),
        (1, '审核中'),
        (2, '已失效')
    )
    IDENTITY = (
        (0, '普通用户'),
        (1, '组织者')
    )
    ground_id = models.ForeignKey('Ground', on_delete=models.CASCADE, verbose_name="申请场地id")
    user_id = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="申请用户id")
    begin_time = models.DateTimeField(verbose_name="申请开始时间", default="2001-01-01 00:00:00")
    end_time = models.DateTimeField(verbose_name="申请结束时间", default="2001-01-01 00:00:00")
    state = models.SmallIntegerField(choices=STATE, default=0, verbose_name="申请状态")
    feedback = models.CharField(max_length=500, verbose_name="申请反馈")
    can_change = models.BooleanField(verbose_name="是否可改期", default=True)
    file = models.CharField(max_length=500, null=True, verbose_name="申请材料")
    identity = models.SmallIntegerField(choices=IDENTITY, default=0, verbose_name="申请者身份")
    # apply_group = models.SmallIntegerField(default=0, verbose_name="预约组号")
    apply_time = models.DateTimeField(verbose_name="申请提交的时间，同批次都相同", default=datetime.now())


# 审核用户
class UserVerify(models.Model):
    objects = models.Manager()
    user_id = models.ForeignKey('WXUser', on_delete=models.CASCADE, verbose_name="审核用户id")
    name = models.CharField(max_length=30, verbose_name="用户名称")
    student_number = models.CharField(max_length=20, verbose_name="学号")
    student_id = models.CharField(max_length=20, default="-1", verbose_name="学号")  # 2022-4-16 whl修改
    avatar = models.CharField(max_length=500, verbose_name="校园卡图片")
