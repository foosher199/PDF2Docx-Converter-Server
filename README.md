# PDF 转换器 - 客户端测试页面

纯静态 HTML 页面，用于测试 Railway 部署的 PDF 转换 API。

## 使用方法

### 方式一：直接打开 HTML 文件

```bash
cd client
open index.html  # macOS
# 或双击 index.html 用浏览器打开
```

### 方式二：本地启动简单 HTTP 服务器

```bash
cd client
python -m http.server 8080
# 然后访问 http://localhost:8080
```

### 方式三：部署到静态托管

可以将 `client/index.html` 部署到：
- Vercel
- Netlify
- GitHub Pages
- Cloudflare Pages

## 功能

- 拖拽或点击上传 PDF
- 选择输出格式（Word/Excel/PPT）
- 自动轮询转换进度
- 转换完成后提供下载链接

## 配置

页面顶部有一个 API 地址输入框，默认指向 Railway 服务：
```
https://pdfconverter-production-2e3b.up.railway.app/api/v1
```

如果部署了新的 Railway 服务，修改这个地址即可。
