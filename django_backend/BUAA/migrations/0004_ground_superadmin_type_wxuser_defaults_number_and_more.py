# Generated by Django 4.0.3 on 2022-04-11 23:30

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('BUAA', '0003_alter_notification_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ground',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='场地名称')),
                ('area', models.CharField(blank=True, max_length=50, null=True, verbose_name='场地区域')),
                ('price', models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(1)], verbose_name='价格')),
                ('apply_needed', models.BooleanField(default=False, verbose_name='是否需要预约')),
                ('description', models.CharField(blank=True, max_length=500, null=True, verbose_name='场地信息')),
                ('avatar', models.CharField(blank=True, max_length=500, null=True, verbose_name='场地图片')),
            ],
        ),
        migrations.AddField(
            model_name='superadmin',
            name='type',
            field=models.CharField(default='normal', max_length=50, verbose_name='管理员类别'),
        ),
        migrations.AddField(
            model_name='wxuser',
            name='defaults_number',
            field=models.IntegerField(default=0, validators=[django.core.validators.MinValueValidator(1)], verbose_name='违约次数'),
        ),
        migrations.AddField(
            model_name='wxuser',
            name='is_csstd',
            field=models.BooleanField(default=False, verbose_name='是否是院内学生'),
        ),
        migrations.AddField(
            model_name='wxuser',
            name='money',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(1)], verbose_name='钱包'),
        ),
        migrations.AddField(
            model_name='wxuser',
            name='student_id',
            field=models.CharField(blank=True, max_length=10, null=True, verbose_name='学号'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='type',
            field=models.SmallIntegerField(choices=[(6, '创建组织请求审批结果'), (8, '被设置为管理员通知'), (2, '参与的活动被取消通知'), (7, '被转让为负责人通知'), (3, '被移除出活动通知'), (10, '管理的活动评论被修改的通知'), (9, '被移出管理员通知'), (4, '新博雅通知'), (1, '参与的活动的内容变更通知'), (5, '管理的活动被评价的通知')], verbose_name='通知类型'),
        ),
        migrations.CreateModel(
            name='UserVerify',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=30, verbose_name='用户名称')),
                ('student_number', models.CharField(max_length=20, verbose_name='学号')),
                ('avatar', models.CharField(max_length=500, verbose_name='校园卡图片')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BUAA.wxuser', verbose_name='审核用户id')),
            ],
        ),
        migrations.CreateModel(
            name='GroundApply',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('time', models.DateTimeField(verbose_name='申请时间')),
                ('period', models.SmallIntegerField(choices=[(0, 'xxx'), (1, 'xxx'), (2, 'xxx')], default=0, verbose_name='申请时间段')),
                ('state', models.SmallIntegerField(choices=[(0, '申请中'), (1, '已通过'), (2, '未通过')], default=0, verbose_name='申请状态')),
                ('feedback', models.CharField(max_length=500, verbose_name='申请反馈')),
                ('if_change', models.BooleanField(default=False, verbose_name='是否可改期')),
                ('ground_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BUAA.ground', verbose_name='预约的场地id')),
                ('user_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BUAA.wxuser', verbose_name='申请用户id')),
            ],
        ),
        migrations.AddField(
            model_name='ground',
            name='administrator',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BUAA.superadmin', verbose_name='场地管理员'),
        ),
    ]
