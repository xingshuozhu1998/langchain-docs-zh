#!/usr/bin/env python3
"""将 Mintlify 官方静态导出适配到 GitHub Pages 项目路径，仅发布已确认的中英对照范围。"""
import argparse
import collections
import hashlib
import json
import sys
import re
import zipfile
from itertools import chain
from urllib.parse import unquote, urlsplit
from pathlib import Path

PREFIX = '/langchain-docs-zh'
SCOPE = re.compile(r'^oss/(?:(?:python|javascript)/(?:langchain|langgraph|deepagents)/|deepagents/code/|(?:python|javascript)/concepts/(?:context|memory|products|providers-and-models)(?:/|$))')
SCRIPTS = re.compile(r'<script>(.*?)</script>', re.S)
ATTR = re.compile(r'\b(href|src|srcset|poster|action)="(/(?!/)[^"]*)"')
CSS_URL = re.compile(r'(url\([\s\"\x27]*)(/(?!/)[^\s\"\x27)]*)')
NAVIGATION = r'''// 导出的运行时仍使用站点根资源路径，将动态资源指向项目目录。
function resourceUrl(value){return typeof value==="string"&&/^\/(?:_next|fonts)\//.test(value)?"/langchain-docs-zh"+value:value;}
for(const [type,prop] of [[HTMLScriptElement,"src"],[HTMLLinkElement,"href"]]){
  const d=Object.getOwnPropertyDescriptor(type.prototype,prop);
  Object.defineProperty(type.prototype,prop,{...d,set(value){d.set.call(this,resourceUrl(value));}});
}
const originalSetAttribute=Element.prototype.setAttribute;
Element.prototype.setAttribute=function(name,value){
  if((this.tagName==="SCRIPT"&&name==="src")||(this.tagName==="LINK"&&name==="href"))value=resourceUrl(value);
  return originalSetAttribute.call(this,name,value);
};
function destination(href){
  const u=new URL(href,location.href);
  if(u.origin!==location.origin)return u.href;
  const path=u.pathname.replace(/^\/langchain-docs-zh(?=\/)/,"");
  if(path==="/llms.txt")return "https://docs.langchain.com/llms.txt";
  if(/\.[a-z0-9]+$/i.test(path)||/^\/(?:_next|fonts|images)\//.test(path))return u.href;
  return LOCAL_ROUTES.has(path.replace(/\/$/,""))?location.origin+"/langchain-docs-zh"+path+u.search+u.hash:"https://docs.langchain.com"+path+u.search+u.hash;
}
// React 更新导航后也校正链接，使新标签页和复制链接保持相同去向。
function fixLinks(){for(const a of document.querySelectorAll("a[href]")){
  if(a.getAttribute("href").startsWith("#"))continue;
  const href=destination(a.href);if(a.href!==href)a.href=href;
}}
document.addEventListener("DOMContentLoaded",()=>{
  fixLinks();new MutationObserver(fixLinks).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:["href"]});
});
document.addEventListener("click",function(e){
  const a=e.target.closest("a[href]");
  if(!a||e.button!==0||e.ctrlKey||e.metaKey||e.shiftKey||e.altKey||a.target==="_blank"||a.hasAttribute("download"))return;
  const u=new URL(a.href);
  if(u.origin!==location.origin||u.pathname===location.pathname)return;
  const path=u.pathname.replace(/^\/langchain-docs-zh(?=\/)/,"");
  if(!LOCAL_ROUTES.has(path.replace(/\/$/,""))){u.href="https://docs.langchain.com"+path+u.search+u.hash;}
  else u.pathname="/langchain-docs-zh"+path;
  e.preventDefault();e.stopImmediatePropagation();location.href=u.href;
},true);
'''


def prefixed(path):
    return path if path.startswith(PREFIX + '/') else PREFIX + path


def resources(text):
    return re.sub(r'(?<![A-Za-z0-9/_-])/(?:_next|fonts)/', lambda m: PREFIX + m[0], text)


def html_url(attr, path):
    route = urlsplit(path).path.rstrip('/')
    if attr == 'href' and route == '/llms.txt':
        return 'https://docs.langchain.com' + path
    if attr == 'href' and route not in LOCAL_ROUTES and not Path(route).suffix and not route.startswith(('/_next/', '/fonts/', '/images/')):
        return 'https://docs.langchain.com' + path
    return prefixed(path)


def adapt_html(text):
    # React 的内联数据包含按字节计长的内容，不能在其中直接替换 URL。
    # 只修改 HTML URL 属性，保留脚本正文与 React 管理的 style 文本。
    parts = re.split(r'(<script\b[^>]*>.*?</script>)', text, flags=re.S)
    for i in range(0, len(parts), 2):
        parts[i] = ATTR.sub(lambda m: m[1] + '="' + html_url(m[1], m[2]) + '"', parts[i])
    for i in range(1, len(parts), 2):
        opening, body = parts[i].split('>', 1)
        parts[i] = ATTR.sub(lambda m: m[1] + '="' + html_url(m[1], m[2]) + '"', opening) + '>' + body
    return ''.join(parts)


def prepare(root, source):
    pages = sorted(root.rglob('*.html'))
    global LOCAL_ROUTES
    LOCAL_ROUTES = {'/' + str(p.relative_to(root)).removesuffix('/index.html') for p in pages} | {''}
    shared = root / '_pages'; shared.mkdir(exist_ok=True)
    (shared / 'navigation.js').write_text('const LOCAL_ROUTES=new Set('+json.dumps(sorted(LOCAL_ROUTES))+');\n'+NAVIGATION)
    # 保留 HTML 中 React 管理的 style 文本，避免客户端接管时报不一致。
    # 使用后置样式表覆盖字体资源路径。
    font_styles = '\n'.join(style for style in re.findall(r'<style[^>]*>(.*?)</style>', pages[0].read_text(), re.S) if '@font-face' in style)
    (shared / 'fonts.css').write_text(CSS_URL.sub(lambda m: m[1] + prefixed(m[2]), font_styles))
    # GitHub Pages 没有 Next 服务端。页面跳转使用已导出的完整 HTML；
    # Mintlify 自身脚本仍负责页内标签、折叠面板和主题等交互。
    counts = collections.Counter()
    for page in pages:
        text = adapt_html(page.read_text())
        for match in SCRIPTS.finditer(text):
            body = match[1]
            if len(body) >= 4096:
                counts[hashlib.sha256(body.encode()).hexdigest()] += 1
    print(f'已分析 {len(pages)} 个页面的重复脚本，开始核对素材引用。', flush=True)
    # 官方导出会复制素材目录中的历史文件。仅排除文件名在所有源文档、
    # 组件、配置及已渲染页面中都没有出现的图片；不改上游源文件。
    names = re.compile(r'[\w%+@().-]+')
    referenced = set()
    for file in chain(source.rglob('*'), root.rglob('*')):
        if file.is_file() and file.suffix in {'.mdx', '.md', '.jsx', '.js', '.css', '.json', '.html', '.svg', '.txt'}:
            text = file.read_text(errors='ignore')
            if file.suffix == '.html':
                text = ' '.join(m[2] for m in ATTR.finditer(text)) + ' ' + ' '.join(m[2] for m in CSS_URL.finditer(text))
            for match in names.finditer(text):
                name = match[0].rstrip(').')
                if name.lower().endswith(('.gif', '.png', '.jpg', '.jpeg', '.webp', '.mp4')):
                    referenced.add(unquote(name))
    saved_images = 0
    for asset in root.rglob('*'):
        if (asset.is_file() and asset.suffix.lower() in {'.gif', '.png', '.jpg', '.jpeg', '.webp', '.mp4'}
                and asset.name.isascii() and not any(c.isspace() for c in asset.name)
                and asset.name not in referenced):
            saved_images += asset.stat().st_size
            asset.unlink()
    print(f'已核对素材引用，开始生成项目路径页面。', flush=True)
    written = set()
    saved_scripts = 0
    def externalize(match):
        nonlocal saved_scripts
        body = match[1]; key = hashlib.sha256(body.encode()).hexdigest()
        if counts[key] < 2:
            return match[0]
        if key not in written:
            (shared / (key + '.js')).write_text(body)
            written.add(key)
        else:
            saved_scripts += len(body.encode())
        # 不使用 async/defer，保持原始内联脚本的执行顺序。
        return f'<script src="{PREFIX}/_pages/{key}.js"></script>'
    for page in pages:
        text = adapt_html(page.read_text())
        text = SCRIPTS.sub(externalize, text)
        text = text.replace('<head>', f'<head><script src="{PREFIX}/_pages/navigation.js"></script>', 1)
        text = text.replace('</head>', f'<link rel="stylesheet" href="{PREFIX}/_pages/fonts.css"></head>', 1)
        page.write_text(text)
    # 字体 CSS 和动态分块资源也必须使用项目路径。
    for file in root.rglob('*'):
        if file.parent == shared or file.suffix not in ('.css', '.js', '.json', '.svg') or not file.is_file():
            continue
        text = file.read_text()
        text = CSS_URL.sub(lambda m: m[1] + prefixed(m[2]), text)
        text = text.replace('"/_next/', '"' + PREFIX + '/_next/').replace("'/_next/", "'" + PREFIX + '/_next/')
        text = resources(text)
        if file.name.startswith('turbopack-') and file.suffix == '.js':
            # RSC 模块路径仍以 /_next/ 开头；与已调整的分块缓存键保持一致。
            text = text.replace('return $(1,this.m.id,e)}', 'return $(1,this.m.id,e.startsWith("/_next/")?"/langchain-docs-zh"+e:e)}')
        file.write_text(text)
    (root / 'index.html').write_text('<!doctype html><meta charset="utf-8"><meta http-equiv="refresh" content="0;url='+PREFIX+'/oss/python/langchain/overview/"><a href="'+PREFIX+'/oss/python/langchain/overview/">LangChain 中英对照文档</a>')
    (root / '.nojekyll').touch()
    size = sum(f.stat().st_size for f in root.rglob('*') if f.is_file())
    print(f'页面数：{len(pages)}；发布体积：{size / 1_000_000:.1f} MB；共享脚本节省：{saved_scripts / 1_000_000:.1f} MB；排除未引用素材节省：{saved_images / 1_000_000:.1f} MB', flush=True)
    if size >= 1_000_000_000:
        raise SystemExit('站点超过 GitHub Pages 的 1 GB 限制，停止发布。')


def configure(path):
    """仅在部署副本中裁剪导航，官方源仓库保持原状。"""
    config = json.loads(path.read_text())
    containers = {'products', 'menu', 'dropdowns', 'tabs', 'groups', 'pages'}
    def select(node):
        if isinstance(node, str):
            return node if SCOPE.match(node + '/') else None
        result = dict(node)
        for key in containers & node.keys():
            result[key] = [v for child in node[key] if (v := select(child)) is not None]
            if not result[key]:
                return None
        if 'root' in result and not SCOPE.match(result['root'] + '/'):
            result.pop('root')
        return result if containers & node.keys() else None
    config['navigation'] = select(config['navigation'])
    config.pop('integrations', None)
    config['seo'] = {'metatags': {'canonical': 'https://xingshuozhu1998.github.io/langchain-docs-zh'}}
    config['redirects'] = []
    path.write_text(json.dumps(config, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--configure':
        configure(Path(sys.argv[2]))
        sys.exit(0)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.archive) as archive:
        for entry in archive.infolist():
            if not entry.is_dir() and (not entry.filename.endswith('.html') or SCOPE.match(entry.filename)):
                archive.extract(entry, args.output)
    prepare(args.output, args.source)
