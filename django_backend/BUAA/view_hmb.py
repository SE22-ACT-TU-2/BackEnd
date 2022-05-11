from rest_framework.viewsets import ModelViewSet
from BUAA.models import *
from BUAA.accessPolicy import *
from BUAA.authentication import *

# base_dir = '/root/server_files/'
base_dir = 'C:/test/'
web_dir = 'http://114.116.194.3/server_files/'


class HMBTestViewSet(ModelViewSet):
    authentication_classes = [UserAuthentication,
                              SuperAdminAuthentication, ErrorAuthentication]
    permission_classes = (WXUserAccessPolicy,)
    queryset = WXUser.objects.all()

    def hmb_test(self, request):
        return Response(data={"msg": "hmb_test"}, status=201)
