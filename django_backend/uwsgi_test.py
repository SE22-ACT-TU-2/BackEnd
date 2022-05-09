# 测试uwsgi: uwsgi --http :8001 --wsgi-file uwsgi_test.py
# 在本机访问 http://114.116.194.3:8001/ 即可看到 Hello World
def application(env, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    test = "Hello World"
    return test.encode("utf-8")
