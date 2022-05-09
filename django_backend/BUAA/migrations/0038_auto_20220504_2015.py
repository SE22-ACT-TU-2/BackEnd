# Generated by Django 3.2.13 on 2022-05-04 20:15

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BUAA', '0037_auto_20220504_1759'),
    ]

    operations = [
        migrations.AlterField(
            model_name='groundapply',
            name='apply_time',
            field=models.DateTimeField(default=datetime.datetime(2022, 5, 4, 20, 15, 12, 640409), verbose_name='申请提交的时间，同批次都相同'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.SmallIntegerField(choices=[(3, '被移除出活动通知'), (5, '管理的活动被评价的通知'), (8, '被设置为管理员通知'), (1, '参与的活动的内容变更通知'), (7, '被转让为负责人通知'), (4, '新博雅通知'), (10, '管理的活动评论被修改的通知'), (6, '创建组织请求审批结果'), (9, '被移出管理员通知'), (2, '参与的活动被取消通知')], verbose_name='通知类型'),
        ),
    ]
