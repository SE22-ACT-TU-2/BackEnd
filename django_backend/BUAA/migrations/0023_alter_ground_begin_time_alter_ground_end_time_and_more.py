# Generated by Django 4.0.3 on 2022-04-23 18:06

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BUAA', '0022_alter_groundapply_apply_time_alter_notification_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ground',
            name='begin_time',
            field=models.TimeField(default='08:00:00', verbose_name='开放开始时间'),
        ),
        migrations.AlterField(
            model_name='ground',
            name='end_time',
            field=models.TimeField(default='22:00:00', verbose_name='开放结束时间'),
        ),
        migrations.AlterField(
            model_name='groundapply',
            name='apply_time',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 23, 18, 6, 47, 941888), verbose_name='申请提交的时间，同批次都相同'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.SmallIntegerField(choices=[(4, '新博雅通知'), (8, '被设置为管理员通知'), (6, '创建组织请求审批结果'), (3, '被移除出活动通知'), (5, '管理的活动被评价的通知'), (2, '参与的活动被取消通知'), (10, '管理的活动评论被修改的通知'), (1, '参与的活动的内容变更通知'), (9, '被移出管理员通知'), (7, '被转让为负责人通知')], verbose_name='通知类型'),
        ),
    ]