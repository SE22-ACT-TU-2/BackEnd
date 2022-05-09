# Generated by Django 4.0.3 on 2022-04-16 21:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BUAA', '0009_alter_notification_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='userverify',
            name='student_id',
            field=models.CharField(default='-1', max_length=20, verbose_name='学号'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.SmallIntegerField(choices=[(10, '管理的活动评论被修改的通知'), (5, '管理的活动被评价的通知'), (3, '被移除出活动通知'), (1, '参与的活动的内容变更通知'), (2, '参与的活动被取消通知'), (9, '被移出管理员通知'), (4, '新博雅通知'), (7, '被转让为负责人通知'), (8, '被设置为管理员通知'), (6, '创建组织请求审批结果')], verbose_name='通知类型'),
        ),
    ]