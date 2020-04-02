# -*- coding:UTF-8 -*-
import requests,argparse,re,logging
from urllib.parse import urlparse

#配置命令行输入的参数
def config_param():
    parser=argparse.ArgumentParser()
    parser.add_argument("-u","--url",help="地址")
    parser.add_argument("-i","--input",help="输入包含js的文件")
    parser.add_argument("-o","--outurl",help="url文件")
    parser.add_argument("-s","--subdomain",help="子域名文件")
    args=parser.parse_args()
    return args

#获取页面内容
def get_content(url):
    raw_content=''
    try:
        headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36"}
        res=requests.get(url,headers=headers)
        raw_content=res.content.decode("utf-8")
    except:
        logger.warning('请求页面失败')
    return raw_content

#获取页面中相关的js链接
def find_js(url):
    js_lists=[str(url)]
    raw_content=get_content(url)
    if raw_content:
        #print(raw_content)
        pattern="<script.*src=.*<\/script>"
        script_lists=re.findall(pattern,raw_content)
        #print(script_lists)
        for script_list in script_lists:
            pattern2="src=.*\.js"
            var=re.findall(pattern2,script_list)
            #print(var)
            if var:
                if var[0][5:] not in js_lists:
                    js_lists.append(var[0][5:])
        return js_lists
    else:
        logger.warning('页面没有内容')

#修正所获得的url
def amend_url(url,js_url):
    result_url=''
    if url=='':
        return result_url
    info=urlparse(js_url)
    net=info.netloc
    scheme=info.scheme
    if url[0:4]=="http":
        result_url=url
    elif url[0:2]=='//':
        result_url=scheme+':'+str(url)
    elif url[0]=='/':
        result_url=scheme+'://'+net+str(url)
    else:
        result_url=scheme+'://'+net+'/'+str(url)
    return result_url

#获取js链接页面中的url
def find_url(js_link):
    js_url=[]
    raw_content=get_content(js_link)
    pattern=r"""
      (?:"|')                               # Start newline delimiter
      (
        ((?:[a-zA-Z]{1,10}://|//)           # Match a scheme [a-Z]*1-10 or //
        [^"'/]{1,}\.                        # Match a domainname (any character + dot)
        [a-zA-Z]{2,}[^"']{0,})              # The domainextension and/or path
        |
        ((?:/|\.\./|\./)                    # Start with /,../,./
        [^"'><,;| *()(%%$^/\\\[\]]          # Next character can't be...
        [^"'><,;|()]{1,})                   # Rest of the characters can't be
        |
        ([a-zA-Z0-9_\-/]{1,}/               # Relative endpoint with /
        [a-zA-Z0-9_\-/]{1,}                 # Resource name
        \.(?:[a-zA-Z]{1,4}|action)          # Rest + extension (length 1-4 or action)
        (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
        |
        ([a-zA-Z0-9_\-/]{1,}/               # REST API (no extension) with /
        [a-zA-Z0-9_\-/]{3,}                 # Proper REST endpoints usually have 3+ chars
        (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
        |
        ([a-zA-Z0-9_\-]{1,}                 # filename
        \.(?:php|asp|aspx|jsp|json|
             action|html|js|txt|xml)        # . + extension
        (?:[\?|#][^"|']{0,}|))              # ? or # mark with parameters
      )
      (?:"|')                               # End newline delimiter
    """
    pattern=re.compile(pattern,re.VERBOSE)
    url_lists=re.findall(pattern,str(raw_content))
    for i in range(len(url_lists)):
        url_lists[i]=list(set(url_lists[i]))
        url_lists[i].remove('')
        url_lists[i]=(url_lists[i])[0]
    #print(url_lists)
    if url_lists:
        for url_list in url_lists:
            if amend_url(url_list,js_link):
                js_url.append(amend_url(url_list,js_link))
        return js_url
    else:
        return None

#获得地址中的域名信息
def get_net(url):
    res=urlparse(url)
    net=res.netloc
    return net

#查找子域名信息
def find_subdomain(url,js_url):
    subdomain_lists=[]
    net=get_net(url)
    host='.'.join(net.split('.')[1:])
    for j in js_url:
        net1=get_net(j)
        if host in net1 and net1 not in subdomain_lists:
            subdomain_lists.append(net1)
    return subdomain_lists

#将查询结果写入文件中
def writeintofile(content,file):
    with open(file,'a+') as f:
        for i in content:
            f.write(i)
            f.write('\n')


if __name__=="__main__":
    logging.basicConfig(level=logging.INFO,format='%(asctime)s-%(levelname)s-%(message)s')
    logger=logging.getLogger()
    js_urls=[]
    args=config_param()
    if args.url==None:
        logger.warning("请输入正确格式的地址，比如https://www.baidu.com")
    else:
        logger.info("开始寻找%s内的相关信息"%args.url)
        #args.url="https://www.baidu.com"
        if args.input:
            result=[]
            with open(args.input, 'r') as f:
                line = f.readline().strip('\n')
                while line:
                    result.append(line)
                    line=f.readline().strip('\n')
                if result==[]:
                    logger.warning('该文件为空，请重新选择文件')
        else:
            result=find_js(args.url)
        for i in result:
            if find_url(i):
                for j in find_url(i):
                    if j not in js_urls:
                        js_urls.append(j)
        logger.info('查询到相关url%d条'%len(js_urls))
        #print(js_urls)
        logger.info(js_urls)
        result1=find_subdomain(args.url,js_urls)
        logger.info('查询到子域名%d条'%len(result1))
        #print(result1)
        logger.info(result1)
        if args.outurl:
            writeintofile(js_urls,args.outurl)
            logger.info('已经写入文件%s中'%args.outurl)
        if args.subdomain:
            writeintofile(result1,args.subdomain)
            logger.info('已经写入文件%s中'%args.subdomain)



