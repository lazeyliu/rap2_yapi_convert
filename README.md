# rap2_yapi_convert
> **目测是目前 搜到的 转换最完美的了**


> 首先感谢 https://github.com/Gozap/rap2yapi 

> 本脚本 是借上面的内容修改的，本着取之于民，用之于民的原则开源了

> 修改脚本中的rap2 cookie

> 修改脚本中的yapi cookie

> 找到rap2 中的 project_id

> 找到yapi 中的 project_id

> 修改代码  load_interface_multi(56, 79)  
>   语法为  load_interface_multi(rap2_project_id, yapi_project_id)
> 具体脚本里有例子改改就好了，至于命令行的 懒得弄了

> 执行脚本


> 脚本特点：
>  1.响应数据  都可以导过来的了，包含 必填，注释，
>  2.请求头    放到了请求头里
>  3.请求参数  备注等
>  4.**不需要token**