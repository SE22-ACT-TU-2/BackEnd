import requests
from django.core.cache import cache
import backend.settings as settings
# import datetime
from datetime import *
import json
import os
import traceback
from BUAA.serializers import *
import BUAA.views
import BUAA.models

BOYA_PATH = os.path.expanduser('~/boya/')


def get_access_token():
    print(str(datetime.now()) + " get_access_token")
    response = requests.get(
        f'https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={settings.APPID}&secret={settings.SECRET}')
    response = response.json()
    if response.get('access_token', ''):
        cache.set('access_token', response['access_token'])
        cache.expire('access_token', response['expires_in'])


def get_boya():
    try:
        print(str(datetime.now()) + " get_boya")
        files = os.listdir(BOYA_PATH)
        for file in files:
            if not file.endswith('.json'):
                continue
            with open(BOYA_PATH + file, 'r') as f:
                content = f.read()
            content = json.loads(content)
            add_to_activities(description='', **content)
            os.remove(BOYA_PATH + file)
    except:
        print('ERROR in get_boya:')
        print(traceback.format_exc())


def add_to_activities(name, description, contain, begin_time, end_time, location, **kwargs):
    serializer = AddressSerializer(
        data={"name": location, "longitude": 1.0, "latitude": 1.0})
    serializer.is_valid()
    serializer.save()
    address = serializer.data.get("id")
    data = {
        "name": name,
        "begin_time": begin_time,
        "end_time": end_time,
        "contain": contain,
        "description": description,
        "owner": 1,
        "block": 2,
        "location": address,
    }

    print(data)
    serializer = ActivitySerializer(data=data)
    serializer.is_valid()
    serializer.save()

    # send notif
    data['act'] = serializer.data['id']
    BUAA.views.send_new_boya_notf(data)


def remind_ground_apply():
    try:
        now = datetime.now()
        print(str(now) + " remind_ground_apply")
        later = now + timedelta(hours=1)
        applies = GroundApply.objects.filter(state=0).filter(begin_time__range=(now, later))
        # ##
        # now2 = now + timedelta(days=1)
        # later2 = now2 + timedelta(hours=1)
        # applies = GroundApply.objects.filter(state=0).filter(begin_time__range=(now2, later2))
        # ##
        BUAA.views.send_ground_apply_notif(applies)
        print("success remind_ground_apply")
    except:
        print('ERROR in remind_ground_apply:')
        print(traceback.format_exc())


def expire_ground_apply():
    try:
        now = datetime.now()
        print(str(now) + " expire_ground_apply")
        before = now - timedelta(hours=1)
        GroundApply.objects.filter(end_time__range=(before, now)).exclude(state=2).update(state=2, feedback="已过期")
        # ##
        # now2 = now + timedelta(days=1)
        # before2 = now2 - timedelta(hours=1)
        # GroundApply.objects.filter(end_time__range=(before2, now2)).exclude(state=2).update(state=2, feedback="已过期")
        # ##
        print("success expire_ground_apply")
    except:
        print('ERROR in expire_ground_apply:')
        print(traceback.format_exc())


if __name__ == "__main__":
    # data = {
    #     "name": 'boya_test',
    #     "begin_time": str(datetime.now()),
    #     "end_time": str(datetime.now()),
    #     "contain": 100,
    #     "description": str(datetime.now()),
    #     "owner": 1,
    #     "block": 2,
    #     "location": 1,
    # }
    # add_to_activities(description='无', **data)
    remind_ground_apply()
