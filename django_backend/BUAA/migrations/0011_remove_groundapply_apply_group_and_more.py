# Generated by Django 4.0.3 on 2022-04-17 15:30

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BUAA', '0010_userverify_student_id_alter_notification_type'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='groundapply',
            name='apply_group',
        ),
        migrations.AddField(
            model_name='groundapply',
            name='apply_time',
            field=models.DateTimeField(default=datetime.datetime(2022, 4, 17, 15, 30, 31, 532040), verbose_name='申请提交的时间，同批次都相同'),
        ),
        migrations.AlterField(
            model_name='groundapply',
            name='can_change',
            field=models.BooleanField(default=True, verbose_name='是否可改期'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.SmallIntegerField(choices=[(3, '被移除出活动通知'), (7, '被转让为负责人通知'), (2, '参与的活动被取消通知'), (9, '被移出管理员通知'), (6, '创建组织请求审批结果'), (8, '被设置为管理员通知'), (4, '新博雅通知'), (1, '参与的活动的内容变更通知'), (10, '管理的活动评论被修改的通知'), (5, '管理的活动被评价的通知')], verbose_name='通知类型'),
        ),
    ]
