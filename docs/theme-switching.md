# 🎨 主题切换功能说明

## 功能概述

Wide Research for Finance 现已支持亮暗主题切换，用户可以根据个人喜好和使用环境选择合适的主题。

## 功能特性

### ✨ 主要特点

1. **一键切换** - 点击导航栏右侧的月亮/太阳图标即可切换
2. **自动保存** - 主题偏好自动保存到 localStorage
3. **全局同步** - 所有页面共享同一主题设置
4. **平滑过渡** - 0.3秒的流畅过渡动画
5. **视觉反馈** - 图标旋转动画提供即时反馈

### 🌓 两种主题

#### 暗色主题（默认）
- 背景色: #0f172a → #1e293b
- 文字色: #f8fafc
- 适合: 夜间使用、长时间阅读
- 优点: 护眼、省电、专业感强

#### 亮色主题
- 背景色: #f8fafc → #ffffff  
- 文字色: #1e293b
- 适合: 白天使用、明亮环境
- 优点: 清晰明快、传统阅读体验

## 技术实现

### CSS 变量系统

```css
/* 暗色主题（root 默认）*/
:root {
    --bg-primary: #0f172a;
    --bg-secondary: #1e293b;
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #94a3b8;
    --border-color: rgba(148, 163, 184, 0.2);
}

/* 亮色主题 */
[data-theme="light"] {
    --bg-primary: #f8fafc;
    --bg-secondary: #ffffff;
    --text-primary: #1e293b;
    --text-secondary: #475569;
    --text-muted: #64748b;
    --border-color: rgba(148, 163, 184, 0.3);
}
```

### JavaScript 切换逻辑

```javascript
function toggleTheme() {
    const html = document.documentElement;
    const currentTheme = html.getAttribute('data-theme');
    const newTheme = currentTheme === 'light' ? 'dark' : 'light';
    
    html.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    
    // 更新图标
    const icon = document.getElementById('themeIcon');
    icon.textContent = newTheme === 'light' ? '☀️' : '🌙';
}
```

### 持久化存储

主题偏好使用 `localStorage` 保存：
- Key: `theme`
- Value: `'dark'` 或 `'light'`
- 页面加载时自动读取并应用

## 页面支持

✅ 已实现主题切换的页面：

1. **index.html** - 主仪表盘
   - 导航栏右侧有切换按钮
   - 所有组件完全支持

2. **overview.html** - 项目总览  
   - 导航栏右侧有切换按钮
   - 所有区域完全支持

3. **test.html** - 测试页面
   - 右上角浮动切换按钮
   - 完整功能演示

## 使用方法

### 切换主题

1. 找到页面右上角的主题切换按钮
   - 🌙 图标 = 当前为暗色主题
   - ☀️ 图标 = 当前为亮色主题

2. 点击按钮即可切换主题

3. 主题设置会自动保存，下次访问时生效

### 重置主题

如需重置为默认主题（暗色），可以：

1. 打开浏览器开发者工具（F12）
2. 在 Console 中输入：
   ```javascript
   localStorage.removeItem('theme');
   location.reload();
   ```

## 兼容性

### 浏览器支持
- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Opera 76+

### 功能降级
- CSS 变量不支持时，默认使用暗色主题
- localStorage 不可用时，仍可切换但不保存

## 设计原则

1. **对比度优先** - 确保文字在两种主题下都清晰可读
2. **色彩保留** - 渐变色、强调色保持不变，保持品牌一致性
3. **过渡流畅** - 0.3秒过渡动画，避免突兀感
4. **记忆功能** - 记住用户选择，提升体验

## 未来优化

- [ ] 添加系统主题自动跟随
- [ ] 更多主题选项（深蓝、护眼绿等）
- [ ] 自定义主题编辑器
- [ ] 定时自动切换（日出/日落）
- [ ] 主题预览功能

## 开发者指南

### 添加新组件

为新组件添加主题支持：

```css
.my-component {
    background: var(--bg-secondary);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
    transition: all 0.3s ease; /* 重要：添加过渡 */
}
```

### 使用的 CSS 变量

| 变量名 | 用途 | 暗色值 | 亮色值 |
|--------|------|--------|--------|
| `--bg-primary` | 主背景 | #0f172a | #f8fafc |
| `--bg-secondary` | 次背景/卡片 | #1e293b | #ffffff |
| `--text-primary` | 主文字 | #f8fafc | #1e293b |
| `--text-secondary` | 次要文字 | #cbd5e1 | #475569 |
| `--text-muted` | 弱化文字 | #94a3b8 | #64748b |
| `--border-color` | 边框 | rgba(148,163,184,0.2) | rgba(148,163,184,0.3) |

### 测试清单

✅ 已测试项目：
- [x] 主题切换功能正常
- [x] 主题保存功能正常
- [x] 页面刷新后主题保持
- [x] 所有文字可读性良好
- [x] 所有组件颜色正确
- [x] 过渡动画流畅
- [x] 按钮交互反馈正常

## 反馈与建议

如有任何问题或建议，欢迎通过以下方式反馈：
- GitHub Issues
- Pull Request

---

**功能状态**: ✅ 已完成  
**版本**: v2.0  
**更新日期**: 2025-01-18
