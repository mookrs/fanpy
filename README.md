# fanpy

[![Coverage Status](https://coveralls.io/repos/github/mookrs/fanpy/badge.svg?branch=master)](https://coveralls.io/github/mookrs/fanpy?branch=master)

`fanpy` is a Python tool that allows you to interact with [fanfou.com](http://fanfou.com/). This project is a clone from sixohsix's [Python Twitter Tools](https://github.com/sixohsix/twitter).

## 安装

`pip(3) install fanpy`

## fanpy

`fanpy` 是一个命令行工具，可实现以下功能：

- 查看个人时间轴（friends）和收到的回复（replies），并以不同的格式输出
- 使用关键词搜索（search）消息
- 关注（follow）和取关（leave）好友
- 发送（set）新消息

输入 `fanpy -h` 查看更多帮助。

## fanpy-archiver

`fanpy-archiver` 可以备份你的消息、收到的回复、私信、收藏，他人的消息、收藏。输入 `fanpy-archiver -h` 查看更多帮助。该工具仅供测试，如果想更好地备份消息，推荐使用 Windows 下超方便的 [饭盒](http://www.aoisnow.net/blog/fanhe)。

## fanpy-log

`fanpy-log` 可以在终端显示某个用户的全部消息。输入 `fanpy-log -h` 查看更多帮助。

## 与 Fanfou API 交互

饭否 API 文档请参考：

https://github.com/FanfouAPI/FanFouAPIDoc/wiki

示例：

```python
from fanpy import *

f = Fanfou(auth=OAuth(oauth_token, oauth_token_secret, consumer_key, consumer_secret))

# Get your home timeline
f.statuses.home_timeline()

# Get a particular friend's timeline
# To pass in the GET/POST parameter `id` you need to use `_id`
f.statuses.user_timeline(_id='ifanfou')

# To pass in GET/POST parameters, such as `count`
f.statuses.home_timeline(count=5)

# Update your status
f.statuses.update(status='Hello, world!')

# Send a direct message
f.direct_messages.new(user='ifanfou', text='I miss you!')

# An *optional* `_timeout` parameter can also be used for API
# calls which take much more time than normal:
f.search.public_timeline(q='|'.join(A_LIST_OF_100_WORDS), _timeout=1)

# Overriding Method: GET/POST
# you should not need to use this method as this library properly
# detects whether GET or POST should be used, Nevertheless
# to force a particular method, use `_method`
t.statuses.update(status='Hello, world!', _method='POST')


# Send image with your status:
# - Just read image from the web or from file the regular way:
with open('example.png', 'rb') as imagefile:
    imagedata = imagefile.read()
# - Then send the image with a status.
fanfou.photos.upload(photo=imagedata, status='Upload image.')
```

### 使用返回的数据

调用饭否 API 后默认返回 JSON 对象，并被自动转换成 `list` 或 `dict`：

```python
x = fanfou.statuses.home_timeline()

# The first status in the timeline
x[0]

# The name of the user who wrote the first status
x[0]['user']['name']
```

### 获取 XML 数据

如果你需要获取 XML 格式的数据，可以在初始化 Fanfou 对象时传入 `format='xml'` 参数:

```python
fanfou = Fanfou(format='xml')
```

## 授权

支持通过 OAuth 进行授权。

### OAuth 的认证流程

访问饭否开放平台并创建应用：

http://fanfou.com/apps.new

创建成功后，你将会得到相应的 `CONSUMER_KEY` 和 `CONSUMER_SECRET`。

用户在运行你的程序时，需要将账户授权给你的应用。具体的实现请查看 `fanpy.oauth_dance` 模块。如果你编写的是命令行程序，可以直接使用 `oauth_dance()` 函数。

执行 `oauth_dance()` 将获得授权所必需的 oauth token 和 oauth token secret，可以将这些信息保存在本地，之后就不用重复授权步骤了。

`read_token_file()` 和 `write_token_file()` 是读取和写入 oauth token 和 oauth token secret 的方法，其值以字符串形式存在文件中。

示例：

```python
from fanpy import *

MY_FANFOU_CREDS = os.path.expanduser('~/.my_app_credentials')
if not os.path.exists(MY_FANFOU_CREDS):
    oauth_dance('My App Name', CONSUMER_KEY, CONSUMER_SECRET, MY_FANFOU_CREDS)

oauth_token, oauth_token_secret = read_token_file(MY_FANFOU_CREDS)

fanfou = Fanfou(auth=OAuth(
    oauth_token, oauth_token_secret, CONSUMER_KEY, CONSUMER_SECRET))

# Now work with Fanfou
fanfou.statuses.update(status='Hello, world!')
```

## 其他饭友制作的工具

网上还有很多与 `fanpy` 项目类似的工具，`fanpy` 在改造 [Python Twitter Tools](https://github.com/sixohsix/twitter) 的过程从中获取了灵感，列于下方表示感谢，同时以供参考：

- [fanfou](https://github.com/akgnah/fanfou.bot/blob/master/fanfou.py) 饭否 OAuth (XAuth) 模块
- [饭盒](http://www.aoisnow.net/blog/fanhe) Windows 下的饭否用户数据管理工具集
- [pyfan](https://github.com/raptorz/pyfan) Fanfou client for python
- [pyfanfou](https://github.com/mcxiaoke/pyfanfou) 饭否数据备份和导出工具
- [fanfou-backup](https://github.com/heedless/fanfou-backup) 饭否消息备份工具
- [Treeholes](https://github.com/fanzeyi/Treeholes) An anonymous bot for Fanfou

## License

MIT
