#!/usr/bin/env python3
"""
Nacos版本管理工具 - Python版本
"""

import json
import re
import sys
import argparse
import urllib.request
import urllib.error
from typing import Optional, List, Dict
from pathlib import Path


class NacosVersionManager:
    """Nacos版本管理器"""
    
    GITHUB_API_BASE = "https://api.github.com/repos/alibaba/nacos"
    GITHUB_RELEASES_URL = "https://github.com/alibaba/nacos/releases"
    RSS_URL = "https://github.com/alibaba/nacos/releases.atom"
    
    def __init__(self):
        self.session_headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; NacosVersionManager/1.0)'
        }
    
    def _make_request(self, url: str) -> str:
        """发起HTTP请求"""
        try:
            req = urllib.request.Request(url, headers=self.session_headers)
            with urllib.request.urlopen(req, timeout=30) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            raise Exception(f"请求失败: {e}")
    
    def get_latest_version_api(self) -> str:
        """使用GitHub API获取最新版本"""
        try:
            url = f"{self.GITHUB_API_BASE}/releases/latest"
            response_text = self._make_request(url)
            data = json.loads(response_text)
            
            tag_name = data.get('tag_name')
            if not tag_name:
                raise Exception("API响应中没有找到tag_name")
            
            print(f"✅ 通过API获取到最新版本: {tag_name}")
            return tag_name
            
        except Exception as e:
            print(f"❌ API方法失败: {e}")
            raise
    
    def get_latest_version_html(self) -> str:
        """通过HTML页面解析获取最新版本"""
        try:
            # 使用urllib获取重定向URL
            req = urllib.request.Request(f"{self.GITHUB_RELEASES_URL}/latest", 
                                       headers=self.session_headers)
            
            # 不自动跟随重定向
            class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None
            
            opener = urllib.request.build_opener(NoRedirectHandler)
            
            try:
                opener.open(req)
            except urllib.error.HTTPError as e:
                if e.code in (301, 302, 303, 307, 308):
                    location = e.headers.get('Location')
                    if location:
                        # 从重定向URL中提取版本号
                        match = re.search(r'/tag/([^/]+)$', location)
                        if match:
                            version = match.group(1)
                            print(f"✅ 通过HTML重定向获取到版本: {version}")
                            return version
                
                raise Exception(f"无法从重定向中获取版本: {e}")
            
            raise Exception("没有发生预期的重定向")
            
        except Exception as e:
            print(f"❌ HTML方法失败: {e}")
            raise
    
    def get_latest_version_rss(self) -> str:
        """通过RSS Feed获取最新版本"""
        try:
            response_text = self._make_request(self.RSS_URL)
            
            # 从RSS中提取第一个版本号
            pattern = r'releases/tag/([^"]+)'
            matches = re.findall(pattern, response_text)
            
            if matches:
                version = matches[0]
                print(f"✅ 通过RSS获取到版本: {version}")
                return version
            else:
                raise Exception("RSS中没有找到版本信息")
                
        except Exception as e:
            print(f"❌ RSS方法失败: {e}")
            raise
    
    def get_all_versions(self, limit: int = 10) -> List[Dict]:
        """获取所有可用版本"""
        try:
            url = f"{self.GITHUB_API_BASE}/releases"
            response_text = self._make_request(url)
            releases = json.loads(response_text)
            
            versions = []
            for release in releases[:limit]:
                versions.append({
                    'tag_name': release.get('tag_name'),
                    'name': release.get('name'),
                    'published_at': release.get('published_at'),
                    'prerelease': release.get('prerelease', False),
                    'draft': release.get('draft', False)
                })
            
            return versions
            
        except Exception as e:
            print(f"❌ 获取版本列表失败: {e}")
            return []
    
    def validate_version(self, version: str) -> bool:
        """验证版本格式"""
        pattern = r'^v?[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9]+)?$'
        return bool(re.match(pattern, version))
    
    def compare_versions(self, v1: str, v2: str) -> int:
        """比较版本号 返回 -1, 0, 1"""
        # 移除v前缀并分割版本号
        v1_clean = v1.lstrip('v').split('.')
        v2_clean = v2.lstrip('v').split('.')
        
        # 补齐长度
        max_len = max(len(v1_clean), len(v2_clean))
        v1_clean.extend(['0'] * (max_len - len(v1_clean)))
        v2_clean.extend(['0'] * (max_len - len(v2_clean)))
        
        # 逐段比较
        for i in range(max_len):
            try:
                n1 = int(v1_clean[i])
                n2 = int(v2_clean[i])
                
                if n1 < n2:
                    return -1
                elif n1 > n2:
                    return 1
            except ValueError:
                # 如果包含非数字字符，按字符串比较
                if v1_clean[i] < v2_clean[i]:
                    return -1
                elif v1_clean[i] > v2_clean[i]:
                    return 1
        
        return 0
    
    def download_nacos(self, version: str, download_dir: str = "./downloads") -> bool:
        """下载指定版本的Nacos"""
        try:
            # 确保版本号有v前缀
            if not version.startswith('v'):
                version = f"v{version}"
            
            download_url = f"https://github.com/alibaba/nacos/releases/download/{version}/nacos-server-{version}.tar.gz"
            filename = f"nacos-server-{version}.tar.gz"
            
            # 创建下载目录
            Path(download_dir).mkdir(parents=True, exist_ok=True)
            filepath = Path(download_dir) / filename
            
            print(f"🔄 开始下载 Nacos {version}...")
            print(f"📥 下载URL: {download_url}")
            
            # 下载文件
            req = urllib.request.Request(download_url, headers=self.session_headers)
            
            with urllib.request.urlopen(req) as response:
                total_size = int(response.headers.get('content-length', 0))
                
                with open(filepath, 'wb') as f:
                    downloaded = 0
                    chunk_size = 8192
                    
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r📊 下载进度: {progress:.1f}% ({downloaded}/{total_size})", end='', flush=True)
            
            print(f"\n✅ 下载完成: {filepath}")
            print(f"📁 文件大小: {filepath.stat().st_size / 1024 / 1024:.1f} MB")
            
            return True
            
        except Exception as e:
            print(f"❌ 下载失败: {e}")
            return False
    
    def get_latest_version_all_methods(self) -> Optional[str]:
        """尝试所有方法获取最新版本"""
        methods = [
            ("GitHub API", self.get_latest_version_api),
            ("HTML重定向", self.get_latest_version_html),
            ("RSS Feed", self.get_latest_version_rss)
        ]
        
        for method_name, method_func in methods:
            try:
                print(f"🔄 尝试方法: {method_name}")
                version = method_func()
                if version and self.validate_version(version):
                    return version
            except Exception:
                continue
        
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Nacos版本管理工具')
    parser.add_argument('command', nargs='?', default='latest',
                       choices=['latest', 'api', 'html', 'rss', 'all', 'download', 'list', 'compare'],
                       help='要执行的命令')
    parser.add_argument('--version', '-v', help='指定版本号')
    parser.add_argument('--dir', '-d', default='./downloads', help='下载目录')
    parser.add_argument('--limit', '-l', type=int, default=10, help='版本列表限制')
    parser.add_argument('--version1', help='比较版本1')
    parser.add_argument('--version2', help='比较版本2')
    
    args = parser.parse_args()
    
    manager = NacosVersionManager()
    
    try:
        if args.command in ['latest', 'api']:
            version = manager.get_latest_version_api()
            print(version)
            
        elif args.command == 'html':
            version = manager.get_latest_version_html()
            print(version)
            
        elif args.command == 'rss':
            version = manager.get_latest_version_rss()
            print(version)
            
        elif args.command == 'all':
            version = manager.get_latest_version_all_methods()
            if version:
                print(version)
            else:
                print("❌ 所有方法都失败了", file=sys.stderr)
                sys.exit(1)
                
        elif args.command == 'download':
            version = args.version
            if not version:
                print("🔄 获取最新版本...")
                version = manager.get_latest_version_api()
            
            if manager.validate_version(version):
                success = manager.download_nacos(version, args.dir)
                if not success:
                    sys.exit(1)
            else:
                print(f"❌ 版本格式无效: {version}", file=sys.stderr)
                sys.exit(1)
                
        elif args.command == 'list':
            versions = manager.get_all_versions(args.limit)
            if versions:
                print("📋 可用版本列表:")
                for i, version_info in enumerate(versions, 1):
                    status = ""
                    if version_info['prerelease']:
                        status += " [预发布]"
                    if version_info['draft']:
                        status += " [草稿]"
                    
                    print(f"{i:2d}. {version_info['tag_name']:<12} "
                          f"{version_info['name'][:50]:<50} "
                          f"{version_info['published_at'][:10]}{status}")
            else:
                print("❌ 无法获取版本列表", file=sys.stderr)
                sys.exit(1)
                
        elif args.command == 'compare':
            v1 = args.version1
            v2 = args.version2
            
            if not v1 or not v2:
                print("❌ 需要提供两个版本号进行比较", file=sys.stderr)
                print("用法: python get_latest_nacos.py compare --version1 v2.3.1 --version2 v2.3.2")
                sys.exit(1)
            
            result = manager.compare_versions(v1, v2)
            if result == 0:
                print(f"📊 版本相同: {v1} == {v2}")
            elif result < 0:
                print(f"📊 版本比较: {v1} < {v2}")
            else:
                print(f"📊 版本比较: {v1} > {v2}")
            
            print(result)  # 输出数字结果供脚本使用
            
    except KeyboardInterrupt:
        print("\n❌ 用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 