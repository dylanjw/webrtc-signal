## A webrtc signaling websocket server written in Python

``` bash
wscat --connect https://server
Connected (press CTRL+C to quit)
> {"action": "login", "data": "bob"}
< {"status": "success"}
> {"action": "get_user_list"}
< {"status": "success", "data": ["bob"]}
> {"action": "talk", "target": "bob", "data": "Hi Bob"}
< {"data": "Hi Bob", "sender": "bob"}
>
```

