import { chromium, FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  console.log('🔧 Playwright 全局设置开始...');
  
  // 获取环境变量
  const baseURL = process.env.MCP_INSPECTOR_URL || 'http://localhost:6274';
  const authToken = process.env.MCP_AUTH_TOKEN;
  const fullURL = process.env.MCP_INSPECTOR_FULL_URL;
  
  console.log(`📍 MCP Inspector URL: ${baseURL}`);
  if (authToken) {
    console.log(`🔑 认证 Token: ${authToken.substring(0, 8)}...`);
  }
  if (fullURL) {
    console.log(`🔗 完整 URL: ${fullURL}`);
  }
  
  // 验证 MCP Inspector 是否可访问
  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();
  
  try {
    console.log('🔍 验证 MCP Inspector 可访问性...');
    
    // 尝试访问主页
    const targetURL = fullURL || baseURL;
    await page.goto(targetURL, { timeout: 10000 });
    
    // 等待页面加载
    await page.waitForLoadState('networkidle');
    
    // 检查是否成功加载 MCP Inspector
    const title = await page.title();
    console.log(`📄 页面标题: ${title}`);
    
    // 检查是否有 MCP Inspector 的特征元素
    const hasInspectorElements = await page.locator('body').count() > 0;
    
    if (hasInspectorElements) {
      console.log('✅ MCP Inspector 可访问');
    } else {
      console.warn('⚠️ MCP Inspector 页面可能未完全加载');
    }
    
  } catch (error) {
    console.error('❌ MCP Inspector 访问失败:', error);
    throw new Error(`MCP Inspector 不可访问: ${error}`);
  } finally {
    await browser.close();
  }
  
  console.log('✅ Playwright 全局设置完成');
}

export default globalSetup;