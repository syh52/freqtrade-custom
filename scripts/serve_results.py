#!/usr/bin/env python3
"""
启动一个简单的HTTP服务器来查看反转分析结果
"""
import http.server
import socketserver
import os
from pathlib import Path

# 切换到结果目录
results_dir = Path(__file__).parent.parent / "user_data" / "reversal_results"
os.chdir(results_dir)

PORT = 8888

print("\n" + "=" * 70)
print("  反转分析结果 - Web服务器")
print("=" * 70)
print(f"\n服务器启动在端口 {PORT}")
print(f"\n在浏览器中打开以下任意链接查看结果：\n")

# 列出所有HTML文件
html_files = sorted(results_dir.glob("*.html"), reverse=True)
for html_file in html_files:
    print(f"  http://localhost:{PORT}/{html_file.name}")

print(f"\n按 Ctrl+C 停止服务器")
print("=" * 70 + "\n")

# 启动服务器
Handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", PORT), Handler) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n服务器已停止")
